from odoo import api, fields, models


class PriceCalculatorEncimeraTemplate(models.Model):
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
    ml_measurement = fields.Float(
        'M/L (Medición Encimera)',
        digits=(16, 2),
        compute='_compute_ml_measurement',
        store=True,
        readonly=False
    )
    precio_ml_individual = fields.Float(
        string='Precio M/L Individual',
        digits='Product Price',
        default=0.0,
        help='Precio por metro lineal específico para esta línea. Si está vacío, se usará el precio global.'
    )
    unit_price = fields.Float(
        'M/L',
        digits=(16, 2),
        default=0.0,
        compute='_compute_unit_price',
        store=True,
        readonly=False
    )
    margin = fields.Float(
        'Margen (%)',
        digits=(16, 2),
        default=0.0,
        help='Porcentaje de margen a aplicar sobre el precio unitario. Ejemplo: 10 para 10%.'
    )
    total_price = fields.Float(
        'Precio Total',
        compute='_compute_total_price',
        store=True,
        digits=(16, 2)
    )

    @api.depends('length', 'width', 'is_special_measurement')
    def _compute_ml_measurement(self):
        """Calcular ml_measurement según las dimensiones"""
        for record in self:
            if record.is_special_measurement:
                record.ml_measurement = record.length * record.width * 0.60
            else:
                record.ml_measurement = record.length

    @api.depends('ml_measurement', 'precio_ml_individual', 'calculator_id.precio_ml')
    def _compute_unit_price(self):
        """Calcular unit_price según ml_measurement y el precio a usar"""
        for record in self:
            # Determinar qué precio usar
            if record.precio_ml_individual:
                precio_a_usar = record.precio_ml_individual
            elif record.calculator_id and record.calculator_id.precio_ml:
                precio_a_usar = record.calculator_id.precio_ml
            else:
                precio_a_usar = 0.0

            # Calcular unit_price
            record.unit_price = record.ml_measurement * precio_a_usar

    @api.depends('unit_price', 'margin')
    def _compute_total_price(self):
        for record in self:
            # Fórmula: total = unit_price + (unit_price * margin / 100)
            record.total_price = record.unit_price + (record.unit_price * record.margin / 100)
