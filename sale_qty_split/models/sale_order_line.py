from odoo import api, fields, models
from odoo.tools import float_compare, float_round


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    qty_split_limit = fields.Float(
        string="Max Qty per Order",
        compute='_compute_qty_split',
        digits='Product Unit',
        help="Product limit expressed in this line's unit of measure (0 = no limit).",
    )
    qty_over_limit = fields.Float(
        string="Qty Over Limit",
        compute='_compute_qty_split',
        digits='Product Unit',
    )

    def _get_line_uom(self):
        self.ensure_one()
        if 'product_uom_id' in self._fields:
            return self.product_uom_id
        return self.product_uom

    @api.depends('product_id', 'product_uom_qty', 'product_uom_id', 'display_type')
    def _compute_qty_split(self):
        digits = self.env['decimal.precision'].precision_get('Product Unit')
        for line in self:
            limit = over = 0.0
            product = line.product_id
            tmpl_limit = product.product_tmpl_id.qty_order_split
            if not line.display_type and product and tmpl_limit > 0:
                limit = tmpl_limit
                uom = line._get_line_uom()
                if uom and product.uom_id and uom != product.uom_id:
                    limit = product.uom_id._compute_quantity(
                        tmpl_limit, uom, round=False)
                limit = float_round(limit, precision_digits=digits)
                if float_compare(line.product_uom_qty, limit, precision_digits=digits) > 0:
                    over = line.product_uom_qty - limit
            line.qty_split_limit = limit
            line.qty_over_limit = over
