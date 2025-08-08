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

    @api.depends('product_id', 'product_id.categ_id.calculate_cost_by_formula')
    def _compute_needs_price_calculator(self):
        for line in self:
            line.needs_price_calculator = bool(line.product_id and
                                               line.product_id.categ_id and
                                               line.product_id.categ_id.calculate_cost_by_formula)

    @api.onchange('product_id')
    def product_id_change(self):
        if self.product_id and self.product_id.categ_id.calculate_cost_by_formula:
            return {
                'warning': {
                    'title': 'Calculadora de Precios',
                    'message': 'Este producto requiere calculadora de precios. Utilice el botón "Abrir Calculadora" después de guardar la línea.'
                }
            }
        return {}

    def action_open_price_calculator(self):
        self.ensure_one()
        if not self.needs_price_calculator:
            return
        return {
            'type': 'ir.actions.act_window',
            'name': 'Calculadora de Precios',
            'res_model': 'vgr.price.calculator.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.product_id.id,
                'default_order_line_id': self.id,
                'default_price_group_id': self.order_id.price_group_id.id if self.order_id.price_group_id else False,
                'default_meters_linear': self.order_id.meters_linear,
            }
        }
