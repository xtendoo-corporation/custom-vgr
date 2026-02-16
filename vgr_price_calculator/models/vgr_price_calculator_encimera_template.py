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
    n_aux = fields.Float(
        string='N Auxiliar',
        digits=(16, 2),
        default=0.0,
        help='Campo auxiliar para cálculos adicionales.'
    )
    skip_price_calculation = fields.Boolean(
        string='No calcular precio',
        default=False,
        help='Si está marcado, el precio unitario no se calculará automáticamente en el wizard.'
    )

    @api.depends('length', 'width', 'n_aux')
    def _compute_ml_measurement(self):
        """Calcular ml_measurement según las dimensiones"""
        for record in self:
            if record.n_aux > 0:
                record.ml_measurement = record.length * record.width / record.n_aux
            else:
                record.ml_measurement = record.length

    @api.depends('ml_measurement', 'precio_ml_individual', 'calculator_id.precio_ml', 'skip_price_calculation')
    def _compute_unit_price(self):
        """Calcular unit_price según ml_measurement y el precio a usar"""
        for record in self:
            if record.skip_price_calculation:
                # Si se debe saltar el cálculo, mantenemos el valor actual (o 0.0 si es NULL)
                # No hacemos nada, el campo es store=True y readonly=False, así que el usuario puede editarlo
                # y el compute no lo sobrescribirá si no cambiamos nada aquí.
                # Sin embargo, para un compute, generalmente se espera que asigne un valor.
                # Si queremos permitir edición manual, el compute debe ser inteligente.
                # En Odoo, si un campo computado con store=True es modificado manualmente,
                # el compute no se vuelve a disparar a menos que cambien las dependencias.
                # Aquí añadimos 'skip_price_calculation' como dependencia.
                # Si cambia a True, no deberíamos forzar un valor, pero el ORM requiere que se asigne algo
                # si el registro se está creando o si se recalcula.
                # ESTRATEGIA: Si skip es True, no calculamos. Pero el ORM podría poner 0.0 si no asignamos.
                # Vamos a asignar su propio valor actual para "no cambiarlo".
                record.unit_price = record.unit_price
                continue

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
