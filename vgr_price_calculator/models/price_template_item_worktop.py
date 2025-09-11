from odoo import api, fields, models


class PriceTemplateItemWorktop(models.Model):
    _name = 'vgr.price.template.item.worktop'
    _description = 'Plantilla de Elementos de Precio para Encimeras'

    name = fields.Char('Nombre', required=True)
    length = fields.Float('Largo', required=True, digits=(16, 2))
    width = fields.Float('Ancho', required=True, digits=(16, 2))
    auxiliary_number = fields.Float('Nº Auxiliar')
    is_special_measurement = fields.Boolean('Requiere cálculo especial',
                                            help="Marcar si requiere regla de tres para medidas especiales")
    ml_measurement = fields.Float(
        'M/L (Medición Encimera)',
        compute='_compute_ml_measurement',
        inverse='_inverse_ml_measurement',  # Función inverse para permitir edición
        store=True,
        digits=(16, 2)
    )
    unit_price = fields.Float('M/L', digits=(16, 2))
    margin = fields.Float('Margen', digits=(16, 2))
    total_price = fields.Float('Precio Total', compute='_compute_total_price',
                               store=True, digits=(16, 2))
    external_price = fields.Boolean('Precio externo',
                                    help="Marcar si el precio viene de un marmolista externo")

    def _inverse_ml_measurement(self):
        """
        Esta función permite que el campo sea editable manualmente.
        No necesita implementación específica ya que el valor editado
        se almacena directamente en la base de datos.
        """
        pass

    @api.depends('length', 'width', 'is_special_measurement')
    def _compute_ml_measurement(self):
        for record in self:
            if record.is_special_measurement:
                # Aplicar fórmula: Largo * Ancho * 0.60
                record.ml_measurement = record.length * record.width * 0.60
            else:
                # Medición estándar - simplemente la cantidad escrita
                record.ml_measurement = record.length

    @api.depends('unit_price', 'margin', 'external_price')
    def _compute_total_price(self):
        for record in self:
            if not record.external_price:
                # Precio total = margen + precio unitario (sin multiplicar por ml_measurement)
                record.total_price = record.margin + record.unit_price
            else:
                # Si es externo, mantener el valor manual
                pass

    @api.onchange('external_price')
    def _onchange_external_price(self):
        """Permite editar manualmente el precio total cuando es de origen externo"""
        if self.external_price:
            return {
                'warning': {
                    'title': 'Precio Externo',
                    'message': 'Ahora puede editar manualmente el Precio Total'
                }
            }
