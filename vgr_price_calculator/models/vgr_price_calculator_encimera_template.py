from odoo import api, fields, models


class PriceCalculatorEncimeraTemplate(models.Model):  # Cambiado a persistente
    _name = 'vgr.price.calculator.encimera.template'
    _description = 'Plantilla temporal para cálculos de encimera'

    calculator_id = fields.Many2one(
        'vgr.price.calculator.encimera.wizard',
        string='Calculadora',
        ondelete='cascade'
    )
    template_id = fields.Many2one(
        'vgr.price.template.item.worktop',
        string='Plantilla Original'
    )
    name = fields.Char('Nombre', required=True)
    length = fields.Float('Largo', digits=(16, 2))
    width = fields.Float('Ancho', digits=(16, 2))
    is_special_measurement = fields.Boolean('Requiere cálculo especial')
    ml_measurement = fields.Float('M/L (Medición Encimera)', digits=(16, 2))
    unit_price = fields.Float('M/L', digits=(16, 2), default=0.0)
    margin = fields.Float('Margen', digits=(16, 2), default=0.0)
    total_price = fields.Float(
        'Precio Total',
        compute='_compute_total_price',
        store=True,
        digits=(16, 2)
    )

    @api.depends('ml_measurement', 'unit_price', 'margin')
    def _compute_total_price(self):
        for record in self:
            # Fórmula corregida: margen + precio unitario (sin multiplicar por ml_measurement)
            record.total_price = record.margin + record.unit_price

    @api.onchange('length', 'width', 'is_special_measurement')
    def _onchange_dimensions(self):
        for record in self:
            if record.is_special_measurement:
                record.ml_measurement = record.length * record.width * 0.60
            else:
                record.ml_measurement = record.length

    @api.onchange('ml_measurement')
    def _onchange_unit_price(self):
        if self.calculator_id and self.calculator_id.precio_ml:
            self.unit_price = self.ml_measurement * self.calculator_id.precio_ml
