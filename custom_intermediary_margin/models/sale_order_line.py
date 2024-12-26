from odoo import models, fields, api


class SaleOrderLine(models.Model):
    _inherit = ['sale.order.line']

    intermediary_margin = fields.Float(string='% Intermediario', related='order_id.partner_id.intermediary_margin',
                                       readonly=False, tracking=True)
    profit_percentage = fields.Float(string='% beneficio', related='product_id.profit_percentage', readonly=False,
                                     tracking=True)
    unit_price_without_margin = fields.Float(string='Base Unitaria', compute='_compute_unit_price_without_margin',
                                             readonly=False, tracking=True)
    intermediary_price = fields.Float(string='Intermediary Price', compute='_compute_intermediary_price', store=True)
    net_margin = fields.Float(string='Net Margin', compute='_compute_net_margin', store=True)

    @api.depends('purchase_price', 'intermediary_margin')
    def _compute_intermediary_price(self):
        for record in self:
            if record.purchase_price > 0 and record.intermediary_margin >= 0:
                record.intermediary_price = record.purchase_price * (record.intermediary_margin / 100)
            else:
                record.intermediary_price = 0

    @api.depends('price_unit', 'intermediary_price')
    def _compute_net_margin(self):
        for record in self:
            if record.price_unit > 0 and record.intermediary_price >= 0:
                record.net_margin = record.price_unit - record.intermediary_price
            else:
                record.net_margin = 0

    @api.onchange('purchase_price', 'profit_percentage')
    def _compute_unit_price_without_margin(self):
        for record in self:
            if record.purchase_price > 0 and record.profit_percentage >= 0:
                record.unit_price_without_margin = record.purchase_price * (1 + record.profit_percentage / 100)
            else:
                record.unit_price_without_margin = 0
            if record.purchase_price > 0 and record.profit_percentage >= 0 and record.intermediary_margin >= 0:
                record.price_unit = (record.purchase_price * (1 + record.profit_percentage / 100) *
                                     (1 + record.intermediary_margin / 100))
            else:
                record.price_unit = 0
            if record.purchase_price > 0 and record.price_unit > 0:
                record.profit_percentage = ((record.price_unit / (
                    1 + record.intermediary_margin / 100)) - record.purchase_price) / record.purchase_price * 100
            else:
                record.profit_percentage = 0

    @api.onchange('purchase_price', 'profit_percentage', 'intermediary_margin')
    def _onchange_profit_percentage(self):
        for record in self:
            # Verificar que purchase_price y profit_percentage no sean cero o nulos
            if record.purchase_price > 0 and record.profit_percentage >= 0 and record.intermediary_margin >= 0:
                # Calcular price_unit con los valores válidos
                record.price_unit = (record.purchase_price * (1 + record.profit_percentage / 100) *
                                     (1 + record.intermediary_margin / 100))
            else:
                # Si los valores no son válidos, dejar price_unit como está
                record.price_unit = 0

    @api.onchange('price_unit', 'purchase_price')
    def _onchange_price_unit(self):
        for record in self:
            if record.purchase_price > 0 and record.price_unit > 0:
                # Calcular profit_percentage correctamente
                record.profit_percentage = ((record.price_unit / (
                        1 + record.intermediary_margin / 100)) - record.purchase_price) / record.purchase_price * 100
            else:
                # Si el precio de compra o el price_unit son cero, no se puede calcular profit_percentage
                record.profit_percentage = 0

