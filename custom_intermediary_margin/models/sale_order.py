from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # intermediary_price = fields.Float(string='Margen intermediario', compute='_compute_intermediary_price', store=True)
    # net_margin = fields.Float(string='Margen neto', compute='_compute_net_margin', store=True)

    total_sale = fields.Float(string='Total venta', compute='_compute_totals', store=True)
    total_cost = fields.Float(string='Total coste', compute='_compute_totals', store=True)
    total_sale_intermediary = fields.Float(string='Total venta + intermediario', compute='_compute_totals', store=True)
    total_margin_euros = fields.Float(string='Total margen euros', compute='_compute_totals', store=True)
    total_margin_percent = fields.Float(string='Total margen %', compute='_compute_totals', store=True)

    @api.depends('order_line.price_total', 'order_line.purchase_price', 'order_line.intermediary_price',
                 'order_line.net_margin', 'order_line.profit_percentage')
    def _compute_totals(self):
        for order in self:
            total_sale = total_cost = total_sale_intermediary = total_margin_euros = total_margin_percent = 0.0
            for line in order.order_line:
                total_sale += line.price_unit - line.intermediary_price
                total_cost += line.purchase_price * line.product_uom_qty
                total_sale_intermediary += line.price_unit
                total_margin_euros += line.net_margin
                total_margin_percent += line.profit_percentage
            order.total_sale = total_sale
            order.total_cost = total_cost
            order.total_sale_intermediary = total_sale_intermediary
            order.total_margin_euros = total_margin_euros
            order.total_margin_percent = total_margin_percent / 100 # Para visualizacion correcta con el widget percentage

