import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class PriceCalculatorMontajeWizard(models.Model):
    _name = 'vgr.price.calculator.montaje.wizard'
    _description = 'Calculadora de Precios para Montaje'

    product_id = fields.Many2one(
        'product.product',
        string='Producto',
        readonly=True
    )
    order_line_id = fields.Many2one(
        'sale.order.line',
        string='Línea de pedido'
    )

    montaje_template_ids = fields.One2many(
        'vgr.price.calculator.montaje.template',
        'calculator_id',
        string='Plantillas de Montaje'
    )

    total_price_montaje = fields.Float(
        string='Precio Total Montaje',
        digits='Product Price',
        compute='_compute_total_price_montaje'
    )

    @api.depends('montaje_template_ids.total_price')
    def _compute_total_price_montaje(self):
        for record in self:
            # Sumar el precio de las plantillas
            template_total = sum(template.total_price for template in record.montaje_template_ids)
            record.total_price_montaje = template_total

    @api.model
    def default_get(self, fields_list):
        _logger.info("Ejecutando default_get para calculadora de montaje")
        res = super(PriceCalculatorMontajeWizard, self).default_get(fields_list)
        order_line_id = self.env.context.get('default_order_line_id')

        if order_line_id:
            _logger.info(f"order_line_id: {order_line_id}")

            # Buscamos si ya existe un wizard para esta línea
            existing_wizard = self.search([('order_line_id', '=', order_line_id)], limit=1)

            if existing_wizard:
                _logger.info(f"Encontrado wizard existente ID: {existing_wizard.id}")

                # Buscamos plantillas existentes
                templates = self.env['vgr.price.calculator.montaje.template'].search([
                    ('calculator_id', '=', existing_wizard.id)
                ])

                if templates:
                    _logger.info(f"Encontradas {len(templates)} plantillas para cargar")
                    # Usamos (0, 0, {...}) para crear nuevas plantillas en memoria
                    res['montaje_template_ids'] = [(0, 0, {
                        'name': template.name,
                        'ml_measurement': template.ml_measurement,
                        'precio_ml_individual': template.precio_ml_individual,
                        'unit_price': template.unit_price,
                        'margin': template.margin,
                        'template_id': template.template_id.id if template.template_id else False,
                    }) for template in templates]
                else:
                    _logger.info("No hay plantillas existentes, creando por defecto")
                    self._create_default_templates_in_memory(res, order_line_id)
            else:
                _logger.info("No existe wizard, creando plantillas por defecto")
                self._create_default_templates_in_memory(res, order_line_id)

        return res

    def _create_default_templates_in_memory(self, res, order_line_id):
        # Método auxiliar para crear plantillas in-memory
        template_bases = self.env['vgr.price.template.item.montaje'].search([])
        _logger.info(f"Encontradas {len(template_bases)} plantillas base de montaje")

        if template_bases:
            template_data = []
            for template in template_bases:
                template_data.append({
                    'name': template.name,
                    'ml_measurement': 0.0,
                    'precio_ml_individual': 0.0,
                    'unit_price': 0.0,
                    'margin': 0.0,
                    'template_id': template.id,
                })

            res['montaje_template_ids'] = [(0, 0, data) for data in template_data]
            _logger.info(f"Creadas {len(template_bases)} plantillas in-memory")

    def apply_calculated_price(self):
        _logger.info(f"Aplicando calculadora montaje ID: {self.id}, precio: {self.total_price_montaje}")
        if self.order_line_id:
            # Actualizamos la línea de pedido con el precio
            self.order_line_id.write({
                'price_unit': self.total_price_montaje,
            })

            # Eliminar wizards antiguos EXCEPTO este
            old_wizards = self.env['vgr.price.calculator.montaje.wizard'].search([
                ('order_line_id', '=', self.order_line_id.id),
                ('id', '!=', self.id)
            ])

            # Eliminar plantillas asociadas a wizards antiguos
            old_templates = self.env['vgr.price.calculator.montaje.template'].search([
                ('calculator_id', 'in', old_wizards.ids)
            ])
            if old_templates:
                _logger.info(f"Eliminando {len(old_templates)} plantillas de wizards antiguos")
                old_templates.unlink()

            # Eliminar wizards antiguos
            if old_wizards:
                _logger.info(f"Eliminando {len(old_wizards)} wizards antiguos")
                old_wizards.unlink()

            # Guardar las plantillas actualizadas
            for template in self.montaje_template_ids:
                if template.calculator_id.id == self.id:
                    # Actualizar plantilla existente
                    template.write({
                        'name': template.name,
                        'ml_measurement': template.ml_measurement,
                        'precio_ml_individual': template.precio_ml_individual,
                        'unit_price': template.unit_price,
                        'margin': template.margin,
                    })
                else:
                    # Crear nueva plantilla si no está asociada al wizard actual
                    self.env['vgr.price.calculator.montaje.template'].create({
                        'calculator_id': self.id,
                        'name': template.name,
                        'ml_measurement': template.ml_measurement,
                        'precio_ml_individual': template.precio_ml_individual,
                        'unit_price': template.unit_price,
                        'margin': template.margin,
                        'template_id': template.template_id.id if template.template_id else False,
                    })

            # Forzar guardado inmediato
            self.env.cr.commit()

        return {'type': 'ir.actions.act_window_close'}

    def open_calculator_wizard(self, order_line_id):
        _logger.info(f"Abriendo calculadora de montaje para order_line_id: {order_line_id}")

        # Eliminar calculadoras duplicadas si existen
        existing_calculators = self.search([('order_line_id', '=', order_line_id)])
        if len(existing_calculators) > 1:
            duplicate_ids = existing_calculators.ids[1:]
            if duplicate_ids:
                _logger.info(f"Eliminando calculadoras duplicadas: {duplicate_ids}")
                self.browse(duplicate_ids).unlink()

        # Buscar calculadora existente o crear nueva
        calculator = self.search([('order_line_id', '=', order_line_id)], limit=1)

        if not calculator:
            _logger.info(f"Creando nueva calculadora de montaje para order_line_id: {order_line_id}")
            calculator = self.create({'order_line_id': order_line_id})
            _logger.info(f"Nueva calculadora de montaje creada ID: {calculator.id}")

        # Retornar ventana con la calculadora
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'vgr.price.calculator.montaje.wizard',
            'res_id': calculator.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_order_line_id': order_line_id}
        }
