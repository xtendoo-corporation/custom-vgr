# models/sale_order.py
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    needs_price_calculator = fields.Boolean(
        string='Necesita calculadora',
        compute='_compute_needs_price_calculator',
        store=True,
        default=False,
    )

    @api.depends('product_id', 'product_id.categ_id.calculate_cost_by_formula_type')
    def _compute_needs_price_calculator(self):
        for line in self:
            line.needs_price_calculator = bool(line.product_id and
                                               line.product_id.categ_id and
                                               line.product_id.categ_id.calculate_cost_by_formula_type in ('mobiliario', 'encimera', 'montaje'))

    @api.onchange('product_id')
    def product_id_change(self):
        if (self.product_id and
            self.product_id.categ_id.calculate_cost_by_formula_type in ('mobiliario', 'encimera', 'montaje')):
            calculator_types = {
                'mobiliario': 'Mobiliario',
                'encimera': 'Encimera',
                'montaje': 'Montaje'
            }
            calculator_type = calculator_types.get(self.product_id.categ_id.calculate_cost_by_formula_type, 'Mobiliario')
            return {
                'warning': {
                    'title': f'Calculadora de Precios ({calculator_type})',
                    'message': f'Este producto requiere calculadora de precios de {calculator_type.lower()}. Utilice el botón "Abrir Calculadora" después de guardar la línea.'
                }
            }
        return {}

    def action_open_price_calculator(self):
        self.ensure_one()
        if not self.needs_price_calculator:
            return

        # Determinar qué tipo de calculadora usar basado en el nuevo campo Selection
        formula_type = self.product_id.categ_id.calculate_cost_by_formula_type

        if formula_type == 'encimera':
            # Usar calculadora de encimera
            return {
                'type': 'ir.actions.act_window',
                'name': 'Calculadora de Precios (Encimera)',
                'res_model': 'vgr.price.calculator.encimera.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_product_id': self.product_id.id,
                    'default_order_line_id': self.id,
                }
            }
        elif formula_type == 'montaje':
            # Usar calculadora de montaje
            return {
                'type': 'ir.actions.act_window',
                'name': 'Calculadora de Precios (Montaje)',
                'res_model': 'vgr.price.calculator.montaje.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_product_id': self.product_id.id,
                    'default_order_line_id': self.id,
                }
            }
        elif formula_type == 'mobiliario':
            # Usar calculadora de mobiliario (original)
            return {
                'type': 'ir.actions.act_window',
                'name': 'Calculadora de Precios (Mobiliario)',
                'res_model': 'vgr.price.calculator.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_product_id': self.product_id.id,
                    'default_order_line_id': self.id,
                }
            }
