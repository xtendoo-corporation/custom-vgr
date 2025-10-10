from odoo import api, fields, models


class PriceCalculatorMontajeTemplate(models.Model):
    _name = 'vgr.price.calculator.montaje.template'
    _description = 'Plantilla temporal para cálculos de montaje'

    calculator_id = fields.Many2one(
        'vgr.price.calculator.montaje.wizard',
        string='Calculadora',
        ondelete='cascade'
    )
    template_id = fields.Many2one(
        'vgr.price.template.item.montaje',
        string='Plantilla Original'
    )
    name = fields.Char('Nombre', required=True)
    ml_measurement = fields.Float(
        'M/L (Medición Montaje)',
        digits=(16, 2),
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
    margin = fields.Float('Margen', digits=(16, 2), default=0.0)
    total_price = fields.Float(
        'Precio Total',
        compute='_compute_total_price',
        store=True,
        digits=(16, 2)
    )

    @api.depends('ml_measurement', 'precio_ml_individual')
    def _compute_unit_price(self):
        """Calcular unit_price según ml_measurement y el precio a usar"""
        for record in self:
            # Determinar qué precio usar
            if record.precio_ml_individual:
                precio_a_usar = record.precio_ml_individual
            else:
                precio_a_usar = 0.0

            # Calcular unit_price
            record.unit_price = record.ml_measurement * precio_a_usar

    @api.depends('unit_price', 'margin')
    def _compute_total_price(self):
        for record in self:
            # Fórmula: margen + precio unitario
            record.total_price = record.margin + record.unit_price
