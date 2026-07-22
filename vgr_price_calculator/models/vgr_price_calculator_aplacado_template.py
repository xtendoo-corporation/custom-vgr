from odoo import api, fields, models


class PriceCalculatorAplacadoTemplate(models.Model):
    _name = 'vgr.price.calculator.aplacado.template'
    _description = 'Plantilla temporal para cálculos de aplacado'

    calculator_id = fields.Many2one(
        'vgr.price.calculator.aplacado.wizard',
        string='Calculadora',
        ondelete='cascade'
    )
    template_id = fields.Many2one(
        'vgr.price.template.item',
        string='Plantilla Original'
    )
    name = fields.Char('Nombre', required=True)
    length = fields.Float('Largo', digits=(16, 2))
    ml_measurement = fields.Float(
        'M/L',
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
        'Precio M/L Total',
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
        help='Porcentaje de margen a aplicar sobre el precio unitario.'
    )
    encastre_enchufe = fields.Float(
        'Encastre enchufe (Coste)',
        digits='Product Price',
        default=0.0,
    )
    intermediario = fields.Float(
        'Intermediario (Coste)',
        digits='Product Price',
        default=0.0,
    )
    total_price = fields.Float(
        'Precio + Margen',
        compute='_compute_total_price',
        store=True,
        digits=(16, 2)
    )
    skip_price_calculation = fields.Boolean(
        string='No calcular precio',
        default=False,
        help='Si está marcado, el precio unitario no se calculará automáticamente en el wizard.'
    )

    @api.depends('length')
    def _compute_ml_measurement(self):
        """Para aplacado el M/L por defecto será el largo (1 dimensión)."""
        for record in self:
            record.ml_measurement = record.length

    @api.depends('ml_measurement', 'precio_ml_individual', 'calculator_id.precio_ml', 'skip_price_calculation')
    def _compute_unit_price(self):
        for record in self:
            if record.skip_price_calculation:
                # mantener valor actual si se seleccionó saltar cálculo
                record.unit_price = record.unit_price
                continue

            if record.precio_ml_individual:
                precio_a_usar = record.precio_ml_individual
            elif record.calculator_id and record.calculator_id.precio_ml:
                precio_a_usar = record.calculator_id.precio_ml
            else:
                precio_a_usar = 0.0

            record.unit_price = record.ml_measurement * precio_a_usar

    @api.depends('unit_price', 'margin', 'encastre_enchufe', 'intermediario')
    def _compute_total_price(self):
        for record in self:
            subtotal = (record.unit_price or 0.0) + (record.encastre_enchufe or 0.0) + (record.intermediario or 0.0)
            record.total_price = subtotal + (subtotal * (record.margin or 0.0) / 100.0)

