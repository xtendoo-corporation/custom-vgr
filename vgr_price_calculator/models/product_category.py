from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = 'product.category'

    calculate_cost_by_formula = fields.Boolean(
        string='Calculate Cost by Formula',
        help='If enabled, the cost will be calculated using a formula instead of standard methods'
    )
