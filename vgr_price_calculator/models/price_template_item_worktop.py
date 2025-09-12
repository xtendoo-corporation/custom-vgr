from odoo import api, fields, models


class PriceTemplateItemWorktop(models.Model):
    _name = 'vgr.price.template.item.worktop'
    _description = 'Plantilla de Elementos de Precio para Encimeras'

    name = fields.Char('Nombre', required=True)
    auxiliary_number = fields.Float('Nº Auxiliar')
    is_special_measurement = fields.Boolean('Requiere cálculo especial',
                                            help="Marcar si requiere regla de tres para medidas especiales")
