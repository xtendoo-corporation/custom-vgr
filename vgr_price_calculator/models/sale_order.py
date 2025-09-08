from odoo import api, fields, models

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # meters_linear = fields.Float(
    #     string='M/L',
    #     help='Metros lineales'
    # )
    # price_group_id = fields.Many2one(
    #     'vgr.price.group',
    #     string='Grupo de precio'
    # )
