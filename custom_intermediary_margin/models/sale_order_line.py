from odoo import models, fields, api


class SaleOrderLine(models.Model):
    _inherit = ['sale.order.line']

    intermediary_margin = fields.Float(string='% Intermediario', readonly=False)
    profit_percentage = fields.Float(string='% beneficio', readonly=False)
    unit_price_without_margin_intermediary = fields.Float(string='Base Unitaria',
                                                          compute='_compute_unit_price_without_margin_intermediary',
                                                          readonly=False)
    intermediary_price = fields.Float(string='Intermediary Price', compute='_compute_net_margin_and_intermediary_price', store=True, readonly=True)
    net_margin = fields.Float(string='Net Margin', compute='_compute_net_margin_and_intermediary_price', store=True)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for record in self:
            print(f"Onchange product_id: {record.product_id}")
            if record.order_id.partner_id:
                record.intermediary_margin = record.order_id.partner_id.intermediary_margin
                print(f"Set intermediary_margin: {record.intermediary_margin}")
            if record.product_id:
                record.profit_percentage = record.product_id.profit_percentage
                print(f"Set profit_percentage: {record.profit_percentage}")

    @api.depends('price_unit', 'purchase_price', 'intermediary_price','intermediary_margin')
    def _compute_net_margin_and_intermediary_price(self):
        for record in self:
            print(f"Computing intermediary_price for record: {record}")
            print(f"Computing net_margin for record: {record}")
            if record.price_unit and record.purchase_price and record.intermediary_price:
                record.net_margin = record.price_unit - record.purchase_price - record.intermediary_price
                print(f"Computed net_margin: {record.net_margin}")
            else:
                record.net_margin = 0
                print("Set net_margin to 0")
            if record.purchase_price and record.intermediary_margin > 0:
                record.intermediary_price = record.purchase_price * (record.intermediary_margin / 100)
                print(f"Computed intermediary_price: {record.intermediary_price}")
            else:
                record.intermediary_price = 0
                print("Set intermediary_price to 0")

    @api.depends('purchase_price', 'net_margin')
    def _compute_unit_price_without_margin_intermediary(self):
        for record in self:
            print(f"Computing unit_price_without_margin_intermediary for record: {record}")
            if record.purchase_price > 0 and record.net_margin >= 0:
                record.unit_price_without_margin_intermediary = record.purchase_price + record.net_margin
                print(
                    f"Computed unit_price_without_margin_intermediary: {record.unit_price_without_margin_intermediary}")
            else:
                record.unit_price_without_margin_intermediary = 0
                print("Set unit_price_without_margin_intermediary to 0")



