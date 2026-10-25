from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    qty_order_split = fields.Float(
        string="Max Qty per Order",
        digits='Product Unit',
        default=0.0,
        help="Maximum quantity of this product allowed on a single sale order "
             "line (expressed in the product's unit of measure). "
             "0 means no limit.",
    )

    @api.constrains('qty_order_split')
    def _check_qty_order_split(self):
        for product in self:
            if product.qty_order_split < 0:
                raise ValidationError(_("Max Qty per Order cannot be negative."))
