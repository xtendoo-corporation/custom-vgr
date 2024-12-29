from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    profit_percentage = fields.Float(
        string='% de beneficio',
        default=0.0,
    )

