from odoo import models, fields, api

class SaleReport(models.Model):
    _inherit = 'sale.report'

    total_cost = fields.Float(string='Coste total', readonly=True)
    total_margin_percent = fields.Float(string='Total Margen %', readonly=True)
    total_margin_euros = fields.Float(string='Total Margen Euros', readonly=True)

    def _select_sale(self):
        select = super(SaleReport, self)._select_sale()
        select += ", SUM(l.purchase_price * l.product_uom_qty) AS total_cost, \
                           ((SUM(l.price_subtotal) - SUM(l.purchase_price * l.product_uom_qty)) / NULLIF(SUM(l.purchase_price * l.product_uom_qty), 0)) * 100 AS total_margin_percent, \
                           (SUM(l.net_margin * l.product_uom_qty)) AS total_margin_euros"
        return select

    def _group_by_sale(self):
        group_by = super(SaleReport, self)._group_by_sale()
        group_by += ", l.purchase_price, l.product_id"
        return group_by

    def _query(self):
        with_ = self._with_sale()
        query = f"""
            {"WITH" + with_ + "(" if with_ else ""}
            SELECT {self._select_sale()}
            FROM {self._from_sale()}
            WHERE {self._where_sale()}
            GROUP BY {self._group_by_sale()}
            {")" if with_ else ""}
        """
        return query
