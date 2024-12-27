from odoo import models, fields, api


class SaleOrderLine(models.Model):
    _inherit = ['sale.order.line']

    intermediary_percentage = fields.Float(string='% Intermediario', readonly=False)
    profit_percentage = fields.Float(string='% Beneficio', readonly=False)
    unit_price_without_margin_intermediary = fields.Float(string='Base Unitaria',
                                                          compute='_compute_margins',
                                                          readonly=False, store=True)
    intermediary_price = fields.Float(string='Precio Intermediario', compute='_compute_margins', store=True, readonly=True)
    net_margin = fields.Float(string='Net Margin', compute='_compute_margins', store=True)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for record in self:
            if record.order_id.partner_id:
                record.intermediary_percentage = record.order_id.partner_id.intermediary_margin
            if record.product_id:
                record.profit_percentage = record.product_id.profit_percentage

    @api.depends('price_unit', 'purchase_price', 'intermediary_price', 'intermediary_percentage', 'net_margin', 'profit_percentage')
    def _compute_margins(self):
        for record in self:
            if record.purchase_price and record.profit_percentage > 0:
                record.net_margin = record.purchase_price * (record.profit_percentage / 100)
            if record.purchase_price and record.intermediary_percentage > 0:
                record.intermediary_price = record.purchase_price * (record.intermediary_percentage / 100)
            if record.purchase_price > 0 and record.net_margin > 0:
                record.unit_price_without_margin_intermediary = record.purchase_price + record.net_margin
            if record.net_margin > 0 and record.intermediary_price > 0 and record.purchase_price > 0:
                record.price_unit = record.purchase_price + record.net_margin + record.intermediary_price
            if record.price_unit > 0:
                record.unit_price_without_margin_intermediary = record.price_unit - record.intermediary_price


