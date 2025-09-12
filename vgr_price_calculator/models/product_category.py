from odoo import fields, models, api


class ProductCategory(models.Model):
    _inherit = 'product.category'

    calculate_cost_by_formula_type = fields.Selection([
        ('', 'Sin cálculo automático'),
        ('mobiliario', 'Calcular coste por fórmula (Mobiliario)'),
        ('encimera', 'Calcular coste por fórmula (Encimera)'),
    ], string='Tipo de Cálculo de Coste', default='',
       help='Seleccionar el tipo de cálculo automático de coste para esta categoría de producto')
