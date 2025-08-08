from odoo import api, fields, models


class PriceCalculatorLine(models.Model):
    _name = 'vgr.price.calculator.line'
    _description = 'Línea de Calculadora de Precios'

    calculator_id = fields.Many2one('vgr.price.calculator.wizard', string='Calculadora')
    name = fields.Char('Nombre', required=True)
    cost = fields.Float('Coste')
    profit_percent = fields.Float('% Beneficio')
    price = fields.Float('Precio', compute='_compute_price', store=True)

    sale_order_line_id = fields.Many2one('sale.order.line', string='Línea de Pedido de Venta')

    @api.depends('cost', 'profit_percent')
    def _compute_price(self):
        for line in self:
            line.price = line.cost * (1 + line.profit_percent)
