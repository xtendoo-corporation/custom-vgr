from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    intermediary_price = fields.Float(string='Margen intermediario', compute='_compute_intermediary_price', store=True)
    net_margin = fields.Float(string='Margen neto', compute='_compute_net_margin', store=True)

    @api.depends('order_line.intermediary_price')
    def _compute_intermediary_price(self):
        for order in self:
            order.intermediary_price = sum(line.intermediary_price for line in order.order_line)

    @api.depends('order_line.net_margin')
    def _compute_net_margin(self):
        for order in self:
            order.net_margin = order.margin - order.intermediary_price
