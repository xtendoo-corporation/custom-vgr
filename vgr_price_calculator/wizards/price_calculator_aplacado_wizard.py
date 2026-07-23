import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class PriceCalculatorAplacadoWizard(models.Model):
    _name = 'vgr.price.calculator.aplacado.wizard'
    _description = 'Calculadora de Precios para Aplacado'

    product_id = fields.Many2one('product.product', string='Producto', readonly=True)
    order_line_id = fields.Many2one('sale.order.line', string='Línea de pedido')

    precio_ml = fields.Float(string='Precio M/L del Material', digits='Product Price')

    aplacado_template_ids = fields.One2many(
        'vgr.price.calculator.aplacado.template',
        'calculator_id',
        string='Plantillas de Aplacado'
    )

    total_price_aplacado = fields.Float(
        string='Precio Total Aplacado',
        digits='Product Price',
        compute='_compute_total_price_aplacado'
    )

    @api.depends('aplacado_template_ids.total_price')
    def _compute_total_price_aplacado(self):
        for record in self:
            record.total_price_aplacado = sum(t.total_price for t in record.aplacado_template_ids)

    @api.onchange('precio_ml')
    def _onchange_precio_ml_templates(self):
        if self.precio_ml and self.aplacado_template_ids:
            for template in self.aplacado_template_ids:
                if not template.precio_ml_individual and not template.skip_price_calculation:
                    template.unit_price = template.ml_measurement * self.precio_ml

    @api.model
    def default_get(self, fields_list):
        _logger.info("default_get para calculadora aplacado")
        res = super(PriceCalculatorAplacadoWizard, self).default_get(fields_list)
        order_line_id = self.env.context.get('default_order_line_id')

        if order_line_id:
            existing_wizard = self.search([('order_line_id', '=', order_line_id)], limit=1)
            if existing_wizard:
                for field in ['precio_ml']:
                    if field in fields_list:
                        res[field] = existing_wizard[field]
                # Asegurar que el product_id se propague al default_get para mostrarlo en la vista
                if 'product_id' in fields_list:
                    res['product_id'] = existing_wizard.product_id.id if existing_wizard.product_id else None
            else:
                # si no existe wizard persistente, permitir que el contexto provea product_id
                if 'product_id' in fields_list:
                    res['product_id'] = self.env.context.get('default_product_id')

                # Filtrar plantillas existentes para que solo aparezcan las específicas de aplacado
                default_names = ['M/L Aplacado', 'Encastre enchufe', 'Intermediario']
                templates = self.env['vgr.price.calculator.aplacado.template'].search([
                    ('calculator_id', '=', existing_wizard.id)
                ])

                # Mantener solo las plantillas que coincidan por nombre con default_names
                filtered = templates.filtered(lambda t: (t.name in default_names) or (t.template_id and t.template_id.name in default_names))

                if filtered:
                    res['aplacado_template_ids'] = [(0, 0, {
                        'name': t.name,
                        'length': t.length,
                        'ml_measurement': t.ml_measurement,
                        'precio_ml_individual': t.precio_ml_individual,
                        'unit_price': t.unit_price,
                        'margin': t.margin,
                        'skip_price_calculation': t.skip_price_calculation,
                        'template_id': t.template_id.id if t.template_id else False,
                    }) for t in filtered]
                else:
                    # Si no hay plantillas filtradas, creamos las filas por defecto
                    _logger.info("existing_wizard: no hay plantillas de aplacado filtradas, creando por defecto")
                    base_items = self.env['vgr.price.template.item'].search([('name', 'in', default_names)])
                    template_data = []
                    if base_items:
                        for item in base_items:
                            template_data.append({
                                'name': item.name,
                                'length': 0.0,
                                'ml_measurement': 0.0,
                                'precio_ml_individual': 0.0,
                                'unit_price': 0.0,
                                'margin': 0.0,
                                'skip_price_calculation': False,
                                'template_id': item.id,
                            })
                    else:
                        for name in default_names:
                            template_data.append({
                                'name': name,
                                'length': 0.0,
                                'ml_measurement': 0.0,
                                'precio_ml_individual': 0.0,
                                'unit_price': 0.0,
                                'margin': 0.0,
                                'skip_price_calculation': False,
                                'template_id': False,
                            })

                    res['aplacado_template_ids'] = [(0, 0, d) for d in template_data]
                    _logger.info(f"default_get: creadas {len(template_data)} plantillas in-memory para aplacado: {[d.get('name') for d in template_data]}")

        return res

    def apply_calculated_price(self):
        if self.order_line_id:
            # guardar precio en la línea
            self.order_line_id.write({'price_unit': self.total_price_aplacado})
            # asegurar que el wizard persistente tenga el product_id de la línea
            try:
                if self.order_line_id.product_id:
                    self.product_id = self.order_line_id.product_id
            except Exception:
                _logger.exception('Error al asignar product_id al wizard durante apply_calculated_price')

            # limpiamos wizards antiguos
            old_wizards = self.search([('order_line_id', '=', self.order_line_id.id), ('id', '!=', self.id)])
            old_templates = self.env['vgr.price.calculator.aplacado.template'].search([
                ('calculator_id', 'in', old_wizards.ids)
            ])
            if old_templates:
                old_templates.unlink()
            if old_wizards:
                old_wizards.unlink()

            # guardar/crear plantillas asociadas
            for template in self.aplacado_template_ids:
                if template.calculator_id.id == self.id:
                    template.write({
                        'name': template.name,
                        'length': template.length,
                        'ml_measurement': template.ml_measurement,
                        'precio_ml_individual': template.precio_ml_individual,
                        'unit_price': template.unit_price,
                        'margin': template.margin,
                        'skip_price_calculation': template.skip_price_calculation,
                    })
                else:
                    self.env['vgr.price.calculator.aplacado.template'].create({
                        'calculator_id': self.id,
                        'name': template.name,
                        'length': template.length,
                        'ml_measurement': template.ml_measurement,
                        'precio_ml_individual': template.precio_ml_individual,
                        'unit_price': template.unit_price,
                        'margin': template.margin,
                        'skip_price_calculation': template.skip_price_calculation,
                        'template_id': template.template_id.id if template.template_id else False,
                    })

            self.env.cr.commit()

        return {'type': 'ir.actions.act_window_close'}

    def open_calculator_wizard(self, order_line_id):
        # eliminar duplicados
        existing_calculators = self.search([('order_line_id', '=', order_line_id)])
        if len(existing_calculators) > 1:
            duplicate_ids = existing_calculators.ids[1:]
            if duplicate_ids:
                self.browse(duplicate_ids).unlink()

        calculator = self.search([('order_line_id', '=', order_line_id)], limit=1)
        # obtener el producto de la línea para adjuntarlo al wizard persistente
        order_line = self.env['sale.order.line'].browse(order_line_id)
        product_id = order_line.product_id.id if order_line and order_line.product_id else False
        if not calculator:
            calculator = self.create({'order_line_id': order_line_id, 'product_id': product_id})
        else:
            # Asegurar que el wizard persistente tenga product_id si falta
            if not calculator.product_id and product_id:
                try:
                    calculator.product_id = product_id
                except Exception:
                    _logger.exception('No se pudo escribir product_id en wizard existente')
            # Si ya existe calculadora pero sin plantillas, crear las plantillas por defecto
            try:
                if not calculator.aplacado_template_ids:
                    _logger.info(f"open_calculator_wizard: wizard existente {calculator.id} sin plantillas, creando por defecto")
                    base_items = self.env['vgr.price.template.item'].search([])
                    if base_items:
                        for item in base_items:
                            self.env['vgr.price.calculator.aplacado.template'].create({
                                'calculator_id': calculator.id,
                                'name': item.name,
                                'length': 0.0,
                                'ml_measurement': 0.0,
                                'precio_ml_individual': 0.0,
                                'unit_price': 0.0,
                                'margin': 0.0,
                                'skip_price_calculation': False,
                                'template_id': item.id,
                            })
                    else:
                        for name in ['M/L Aplacado', 'Encastre enchufe', 'Intermediario']:
                            self.env['vgr.price.calculator.aplacado.template'].create({
                                'calculator_id': calculator.id,
                                'name': name,
                                'length': 0.0,
                                'ml_measurement': 0.0,
                                'precio_ml_individual': 0.0,
                                'unit_price': 0.0,
                                'margin': 0.0,
                                'skip_price_calculation': False,
                                'template_id': False,
                            })
                    # Forzar que los cambios estén disponibles inmediatamente
                    self.env.cr.commit()
            except Exception as e:
                _logger.exception(f"Error creando plantillas por defecto para calculadora existente: {e}")

        # Asegurar que existan las filas por defecto solo si no hay plantillas
        try:
            default_names = ['M/L Aplacado', 'Encastre enchufe', 'Intermediario']
            existing_templates = self.env['vgr.price.calculator.aplacado.template'].search([('calculator_id', '=', calculator.id)])
            if not existing_templates:
                # crear solo las plantillas que necesitamos
                base_items = self.env['vgr.price.template.item'].search([('name', 'in', default_names)])
                if base_items:
                    for item in base_items:
                        self.env['vgr.price.calculator.aplacado.template'].create({
                            'calculator_id': calculator.id,
                            'name': item.name,
                            'length': 0.0,
                            'ml_measurement': 0.0,
                            'precio_ml_individual': 0.0,
                            'unit_price': 0.0,
                            'margin': 0.0,
                            'skip_price_calculation': False,
                            'template_id': item.id,
                        })
                else:
                    for name in default_names:
                        self.env['vgr.price.calculator.aplacado.template'].create({
                            'calculator_id': calculator.id,
                            'name': name,
                            'length': 0.0,
                            'ml_measurement': 0.0,
                            'precio_ml_individual': 0.0,
                            'unit_price': 0.0,
                            'margin': 0.0,
                            'skip_price_calculation': False,
                            'template_id': False,
                        })
                self.env.cr.commit()
                _logger.info(f"open_calculator_wizard: creadas plantillas por defecto para wizard id={calculator.id}")
            else:
                # Si ya hay plantillas, asegurarse de que existan las tres entradas
                for name in default_names:
                    if not existing_templates.filtered(lambda t, n=name: t.name == n):
                        self.env['vgr.price.calculator.aplacado.template'].create({
                            'calculator_id': calculator.id,
                            'name': name,
                            'length': 0.0,
                            'ml_measurement': 0.0,
                            'precio_ml_individual': 0.0,
                            'unit_price': 0.0,
                            'margin': 0.0,
                            'skip_price_calculation': False,
                            'template_id': False,
                        })
                # No eliminar plantillas existentes para no perder datos del usuario
        except Exception:
            _logger.exception("Error al asegurar plantillas por defecto para wizard antes de abrir")

        # Abrir la ventana sobre el wizard persistente para que las filas se muestren
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'vgr.price.calculator.aplacado.wizard',
            'res_id': calculator.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_order_line_id': order_line_id}
        }

    @api.model_create_multi
    def create(self, vals_list):
        """Asegurarnos de que al crear un wizard programáticamente se generen
        las plantillas por defecto (filas) si no vienen en vals.
        Esto cubre la ruta en la que se crea el wizard antes de abrir la vista
        (por ejemplo cuando otro helper llama a create y luego devuelve res_id),
        evitando que la ventana se abra sin filas.
        """
        # No crear plantillas desde create() para evitar duplicados.
        records = super(PriceCalculatorAplacadoWizard, self).create(vals_list)
        for record in records:
            _logger.info(f"create() wizard aplacado creado id={record.id}; no se crearán plantillas aquí para evitar duplicados")
        return records

