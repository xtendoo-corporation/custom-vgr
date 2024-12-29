from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # intermediary_price = fields.Float(string='Margen intermediario', compute='_compute_intermediary_price', store=True)
    # net_margin = fields.Float(string='Margen neto', compute='_compute_net_margin', store=True)

    total_sale = fields.Float(
        string='Total venta',
        compute='_compute_totals',
        store=True,
    )
    total_cost = fields.Float(
        string='Total coste',
        compute='_compute_totals',
        store=True
    )
    total_sale_intermediary = fields.Float(
        string='Total venta + intermediario',
        compute='_compute_totals',
        store=True
    )
    total_intermediary = fields.Float(
        string='Total intermediación',
        compute='_compute_totals',
        store=True
    )
    total_margin_euros = fields.Float(
        string='Total margen euros',
        compute='_compute_totals',
        store=True
    )
    total_margin_percent = fields.Float(
        string='Total margen %',
        compute='_compute_totals',
        store=True
    )

    @api.depends('order_line.price_total',
                 'order_line.purchase_price',
                 'order_line.intermediary_price',
                 'order_line.net_margin',
                 'order_line.profit_percentage')
    def _compute_totals(self):
        for order in self:
            order.total_intermediary = sum(line.intermediary_price for line in order.order_line)
            order.total_sale = sum((line.price_unit - line.intermediary_price) for line in order.order_line)
            order.total_cost = sum(line.purchase_price * line.product_uom_qty for line in order.order_line)
            order.total_sale_intermediary = sum(line.price_unit for line in order.order_line)
            order.total_margin_euros = sum(line.net_margin for line in order.order_line)
            order.total_margin_percent = sum(line.profit_percentage for line in order.order_line) / 100

