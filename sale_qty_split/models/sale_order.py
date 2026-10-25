from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    has_qty_split_violation = fields.Boolean(
        string="Has Lines Over Qty Limit",
        compute='_compute_has_qty_split_violation',
    )

    @api.depends('order_line.qty_over_limit')
    def _compute_has_qty_split_violation(self):
        for order in self:
            order.has_qty_split_violation = bool(order._get_over_limit_lines())

    def _get_over_limit_lines(self):
        self.ensure_one()
        digits = self.env['decimal.precision'].precision_get('Product Unit')
        return self.order_line.filtered(
            lambda l: not l.display_type
            and float_compare(l.qty_over_limit, 0.0, precision_digits=digits) > 0
        )

    def action_confirm(self):
        errors = []
        for order in self:
            for line in order._get_over_limit_lines():
                errors.append(_(
                    "%(order)s: %(product)s - ordered %(qty)s, maximum per order is %(limit)s",
                    order=order.name or _("New"),
                    product=line.product_id.display_name,
                    qty=line.product_uom_qty,
                    limit=line.qty_split_limit,
                ))
        if errors:
            raise UserError(
                _("You cannot confirm an order with quantities above the "
                  "per-order limit. Use the \"Split Over-Limit Lines\" button "
                  "to move the excess onto new order(s).\n\n%s",
                  "\n".join(errors)))
        return super().action_confirm()

    def action_split_over_limit(self, line_ids=None):
        """Cap over-limit lines at the product limit and move the excess onto
        new draft order(s). Each new order respects the limit itself, so a very
        large quantity may produce several orders.

        :param line_ids: optional list of order line ids. When given, only
            those lines are split (line widget); otherwise every over-limit
            line is split (banner button).
        """
        self.ensure_one()
        if self.state not in ('draft', 'sent'):
            raise UserError(_("Only quotations can be split."))
        lines = self._get_over_limit_lines()
        if line_ids:
            lines = lines.filtered(lambda l: l.id in line_ids)
        if not lines:
            raise UserError(_("No line exceeds its per-order limit."))

        digits = self.env['decimal.precision'].precision_get('Product Unit')
        remaining = {l.id: l.qty_over_limit for l in lines}
        limits = {l.id: l.qty_split_limit for l in lines}
        new_orders = self.browse()

        def pending():
            return [l for l in lines
                    if float_compare(remaining[l.id], 0.0, precision_digits=digits) > 0]

        while pending():
            new_order = self.copy(default={'order_line': []})
            for line in pending():
                chunk = min(limits[line.id], remaining[line.id])
                line.copy({'order_id': new_order.id, 'product_uom_qty': chunk})
                remaining[line.id] -= chunk
            new_orders |= new_order

        for line in lines:
            line.product_uom_qty = limits[line.id]

        links = ", ".join(new_orders.mapped('name'))
        self.message_post(body=_(
            "Quantities above the per-order limit were moved to: %s", links))
        for new_order in new_orders:
            new_order.message_post(body=_(
                "Created by splitting over-limit quantities from %s", self.name))

        window_action = {
            'type': 'ir.actions.act_window',
            'name': _("Split Orders"),
            'res_model': 'sale.order',
        }
        if len(new_orders) == 1:
            window_action.update(res_id=new_orders.id, view_mode='form',
                                 views=[(False, 'form')])
            message = _(
                "Excess quantity was moved to %(new)s. You are now on the new "
                "order. To go back to %(origin)s, click \"%(origin)s\" in the "
                "breadcrumb at the top of the page.",
                new=links, origin=self.name)
        else:
            window_action.update(domain=[('id', 'in', new_orders.ids)],
                                 view_mode='list,form',
                                 views=[(False, 'list'), (False, 'form')])
            message = _(
                "Excess quantity was moved to %(new)s. You are now viewing the "
                "list of new orders. To go back to %(origin)s, click the "
                "breadcrumb at the top of the page.",
                new=links, origin=self.name)

        # Shown on both the banner button and the line widget, then redirects.
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Order split successfully"),
                'message': message,
                'type': 'success',
                'sticky': True,
                'next': window_action,
            },
        }
