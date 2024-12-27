from odoo import models, fields, api

class SaleReport(models.Model):
    _inherit = 'sale.report'

    total_cost = fields.Float(string='Total Cost', readonly=True)
    total_margin_percent = fields.Float(string='Total Margin %', readonly=True)
    total_margin_euros = fields.Float(string='Total Margin Euros', readonly=True)


    # def _select_sale(self):
    #     select = super(SaleReport, self)._select_sale() + ", SUM(l.purchase_price * l.product_uom_qty) AS total_cost, \
    #                                                        ((SUM(l.price_subtotal) - SUM(l.purchase_price * l.product_uom_qty)) / NULLIF(SUM(l.purchase_price * l.product_uom_qty), 0)) * 100 AS total_margin_percent, \
    #                                                        (SUM(l.price_subtotal) - SUM(l.purchase_price * l.product_uom_qty)) AS total_margin_euros"
    #
    #     print("*"*100)
    #     print(select)
    #     return select
    #
    # def _group_by_sale(self):
    #     return super(SaleReport, self)._group_by_sale() + ", l.purchase_price, l.product_uom_qty"
