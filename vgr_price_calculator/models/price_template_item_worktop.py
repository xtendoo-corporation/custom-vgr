from odoo import api, fields, models


class PriceTemplateItemWorktop(models.Model):
    _name = 'vgr.price.template.item.worktop'
    _description = 'Plantilla de Elementos de Precio para Encimeras'

    name = fields.Char('Nombre', required=True)
    n_aux = fields.Float(
        string='N Auxiliar',
        digits=(16, 2),
        default=0.0,
        help='Campo auxiliar para cálculos adicionales.'
    )
    length = fields.Float('Largo', digits=(16, 2))
    width = fields.Float('Ancho', digits=(16, 2))
    skip_price_calculation = fields.Boolean(
        string='No calcular precio',
        default=False,
        help='Si está marcado, el precio unitario no se calculará automáticamente en el wizard.'
    )
