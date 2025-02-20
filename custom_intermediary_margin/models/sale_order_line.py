from odoo import models, fields, api


class SaleOrderLine(models.Model):
    _inherit = ['sale.order.line']

    intermediary_percentage = fields.Float(
        string='% Intermediario',
        readonly=False
    )
    profit_percentage = fields.Float(
        string='% Beneficio',
        readonly=False
    )
    unit_price_without_margin_intermediary = fields.Float(
        string='Base intermediación',
        compute='_compute_margins',
        readonly=False,
        store=True
    )
    intermediary_price = fields.Float(
        string='Precio intermediación',
        store=True
    )
    net_margin = fields.Float(
        string='Margen neto',
        store=True
    )

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for record in self:
            if record.order_id.partner_id:
                record.intermediary_percentage = record.order_id.partner_id.intermediary_margin
            if record.product_id:
                record.profit_percentage = record.product_id.profit_percentage

    @api.depends('price_unit', 'purchase_price', 'intermediary_price', 'intermediary_percentage', 'net_margin', 'profit_percentage')
    def _compute_margins(self):
        self.net_margin = 0
        self.intermediary_price = 0
        self.unit_price_without_margin_intermediary = 0
        for record in self:
            if record.purchase_price:
                if record.profit_percentage > 0:
                    print("*" * 100)
                    print("Profit percentage: ",record.profit_percentage)
                    record.net_margin = record.purchase_price * (record.profit_percentage / 100)
                    record.unit_price_without_margin_intermediary = record.purchase_price + record.net_margin
                    if record.intermediary_percentage > 0:
                        print("*"*100)
                        print(record.intermediary_price)
                        record.intermediary_price = record.unit_price_without_margin_intermediary * (record.intermediary_percentage / 100)
                        print(record.intermediary_price)
                        record.price_unit = record.unit_price_without_margin_intermediary + record.intermediary_price
                    if record.intermediary_percentage == 0:
                        record.price_unit = record.unit_price_without_margin_intermediary

                if record.profit_percentage == 0:
                    record.net_margin = record.price_unit - record.purchase_price
                    if record.intermediary_percentage > 0:
                        record.intermediary_price = record.price_unit * (record.intermediary_percentage / 100)
                        record.unit_price_without_margin_intermediary = record.price_unit - record.intermediary_price
                    if record.intermediary_percentage == 0:
                        record.unit_price_without_margin_intermediary = record.price_unit

            if record.purchase_price == 0:
                record.net_margin = record.price_unit
                if record.intermediary_percentage > 0:
                    record.intermediary_price = record.price_unit * (record.intermediary_percentage / 100)
                    record.unit_price_without_margin_intermediary = record.price_unit - record.intermediary_price
                if record.intermediary_percentage == 0:
                    record.unit_price_without_margin_intermediary = record.price_unit

    def _prepare_invoice_line(self, **kwargs):
        res = super(SaleOrderLine, self)._prepare_invoice_line(**kwargs)
        res.update({
            'intermediary_percentage': self.intermediary_percentage,
            'profit_percentage': self.profit_percentage,
            'unit_price_without_margin_intermediary': self.unit_price_without_margin_intermediary,
            'intermediary_price': self.intermediary_price,
            'purchase_price': self.purchase_price,
        })
        return res

    @api.depends('price_subtotal', 'product_uom_qty', 'purchase_price', 'intermediary_price')
    def _compute_margin(self):
        for line in self:
            line.margin = (line.price_subtotal - (line.purchase_price * line.product_uom_qty)) - line.intermediary_price
            line.margin_percent = line.price_subtotal and line.margin / line.price_subtotal
