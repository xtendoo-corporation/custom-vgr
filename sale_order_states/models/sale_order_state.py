from odoo import models, fields

class SaleOrderState(models.Model):
    _name = 'sale.order.state'
    _description = 'Sale Order State'

    name = fields.Char(string='State Name', required=True)
