from odoo import fields, models, api


class ProductCategory(models.Model):
    _inherit = 'product.category'

    calculate_cost_by_formula = fields.Boolean(
        string='Calculate Cost by Formula (Mobiliario)',
        help='Calcular coste mediante fórmula para mobiliario'
    )

    calculate_cost_by_formula_encimera = fields.Boolean(
        string='Calculate Cost by Formula (Encimera)',
        help='Calcular coste mediante fórmula para encimeras'
    )

    @api.onchange('calculate_cost_by_formula')
    def _onchange_calculate_cost_by_formula(self):
        if self.calculate_cost_by_formula:
            self.calculate_cost_by_formula_encimera = False

    @api.onchange('calculate_cost_by_formula_encimera')
    def _onchange_calculate_cost_by_formula_encimera(self):
        if self.calculate_cost_by_formula_encimera:
            self.calculate_cost_by_formula = False
