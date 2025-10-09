import logging
import json
from odoo import api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PriceCalculatorEncimeraWizard(models.Model):
    _name = 'vgr.price.calculator.encimera.wizard'
    _description = 'Calculadora de Precios para Encimeras'

    product_id = fields.Many2one(
        'product.product',
        string='Producto',
        readonly=True
    )
    order_line_id = fields.Many2one(
        'sale.order.line',
        string='Línea de pedido'
    )

    # Campos específicos para encimeras
    grosor = fields.Float(
        string='Grosor de Encimera (mm)',
        required=True,
        digits=(4, 1),
        default=12.0,
    )

    @api.constrains('grosor')
    def _check_grosor_range(self):
        for record in self:
            if record.grosor < 12.0 or record.grosor > 20.0:
                raise ValidationError("El grosor debe estar entre 12 y 20 mm (ambos incluidos).")

    # Campos de cabecera trasladados desde el modelo de plantillas
    length = fields.Float('Largo', digits=(16, 2), help="Largo de la encimera")
    width = fields.Float('Ancho', digits=(16, 2), help="Ancho de la encimera")

    marca = fields.Char(string='Marca')
    encimera_canto = fields.Char(string='Encimera Canto')
    metros_lineales = fields.Float(string='M/L', digits=(16, 2))
    material = fields.Char(string='Material', compute='_compute_material', store=True)
    precio_ml = fields.Float(string='Precio M/L del Material', digits='Product Price')

    worktop_template_ids = fields.One2many(
        'vgr.price.calculator.encimera.template',
        'calculator_id',
        string='Plantillas de Encimeras'
    )

    total_price_encimera = fields.Float(
        string='Precio Total Encimera',
        digits='Product Price',
        compute='_compute_total_price_encimera'
    )

    @api.depends('product_id', 'order_line_id')
    def _compute_material(self):
        for record in self:
            material_value = False
            product = record.order_line_id.product_id if record.order_line_id else record.product_id

            if product:
                for attribute_value in product.product_template_attribute_value_ids:
                    if attribute_value.attribute_id.name == 'ENCIMERA MATERIAL':
                        material_value = attribute_value.product_attribute_value_id.name
                        break

            if not material_value and record.order_line_id and record.order_line_id.name:
                description = record.order_line_id.name
                if 'ENCIMERA MATERIAL:' in description:
                    parts = description.split('ENCIMERA MATERIAL:')
                    if len(parts) > 1:
                        material_part = parts[1].strip()

                        # Si hay otros atributos después, separar por la primera coma o salto de línea
                        for separator in [',', '\n']:
                            if separator in material_part:
                                material_part = material_part.split(separator)[0].strip()

                        material_value = material_part

                # Intentar con otros formatos posibles
                elif 'Material:' in description or 'MATERIAL:' in description:
                    for prefix in ['Material:', 'MATERIAL:']:
                        if prefix in description:
                            parts = description.split(prefix)
                            if len(parts) > 1:
                                material_part = parts[1].strip()
                                for separator in [',', '\n']:
                                    if separator in material_part:
                                        material_part = material_part.split(separator)[0].strip()
                                material_value = material_part
                                break

            record.material = material_value

    @api.depends('metros_lineales', 'precio_ml', 'worktop_template_ids.total_price')
    def _compute_total_price_encimera(self):
        for record in self:
            # Sumar el precio de las plantillas
            template_total = sum(template.total_price for template in record.worktop_template_ids)
            record.total_price_encimera =  template_total

    @api.onchange('precio_ml')
    def _onchange_precio_ml_templates(self):
        if self.precio_ml and self.worktop_template_ids:
            for template in self.worktop_template_ids:
                # Solo actualizar si la plantilla NO tiene un precio individual definido
                if not template.precio_ml_individual:
                    template.unit_price = template.ml_measurement * self.precio_ml

    # Nuevo onchange para actualizar las plantillas cuando cambian length o width
    @api.onchange('length', 'width')
    def _onchange_dimensions(self):
        if self.worktop_template_ids:
            for template in self.worktop_template_ids:
                # Solo actualizar dimensiones para plantillas que requieren cálculo especial
                if template.is_special_measurement:
                    # Actualizar las dimensiones de las plantillas con los valores de cabecera
                    template.length = self.length
                    template.width = self.width
                    # Recalcular ml_measurement para cálculo especial
                    template.ml_measurement = template.length * template.width * 0.60
                else:
                    # Para plantillas sin cálculo especial, no usar dimensiones de cabecera
                    # ml_measurement se mantendrá como está o se puede editar manualmente
                    pass

                # Recalcular unit_price solo si NO tiene precio individual
                if not template.precio_ml_individual and self.precio_ml:
                    template.unit_price = template.ml_measurement * self.precio_ml

    @api.model
    def default_get(self, fields_list):
        _logger.info("Ejecutando default_get para calculadora de encimeras")
        res = super(PriceCalculatorEncimeraWizard, self).default_get(fields_list)
        order_line_id = self.env.context.get('default_order_line_id')

        if order_line_id:
            _logger.info(f"order_line_id: {order_line_id}")

            # Buscamos si ya existe un wizard para esta línea
            existing_wizard = self.search([('order_line_id', '=', order_line_id)], limit=1)

            if existing_wizard:
                _logger.info(f"Encontrado wizard existente ID: {existing_wizard.id}")

                # Copiamos los valores básicos incluyendo los nuevos campos de cabecera
                for field in ['grosor', 'marca', 'encimera_canto', 'metros_lineales', 'precio_ml', 'length', 'width']:
                    if field in fields_list:
                        res[field] = existing_wizard[field]

                # Buscamos plantillas existentes
                templates = self.env['vgr.price.calculator.encimera.template'].search([
                    ('calculator_id', '=', existing_wizard.id)
                ])

                if templates:
                    _logger.info(f"Encontradas {len(templates)} plantillas para cargar")
                    # Usamos (0, 0, {...}) para crear nuevas plantillas en memoria
                    res['worktop_template_ids'] = [(0, 0, {
                        'name': template.name,
                        'length': template.length,
                        'width': template.width,
                        'is_special_measurement': template.is_special_measurement,
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
        template_bases = self.env['vgr.price.template.item.worktop'].search([])
        _logger.info(f"Encontradas {len(template_bases)} plantillas base")

        if template_bases:
            # Creamos plantillas in-memory usando comandos Odoo (0, 0, {...})
            # Solo usar dimensiones de cabecera para plantillas que requieren cálculo especial
            default_length = res.get('length', 0.0)
            default_width = res.get('width', 0.0)

            template_data = []
            for template in template_bases:
                if template.is_special_measurement:
                    # Para plantillas con cálculo especial, usar dimensiones de cabecera
                    template_data.append({
                        'name': template.name,
                        'length': default_length,
                        'width': default_width,
                        'is_special_measurement': template.is_special_measurement,
                        'ml_measurement': default_length * default_width * 0.60,
                        'precio_ml_individual': 0.0,
                        'unit_price': 0.0,
                        'margin': 0.0,
                        'template_id': template.id,
                    })
                else:
                    # Para plantillas sin cálculo especial, no usar dimensiones de cabecera
                    template_data.append({
                        'name': template.name,
                        'length': 0.0,  # No heredar de cabecera
                        'width': 0.0,   # No heredar de cabecera
                        'is_special_measurement': template.is_special_measurement,
                        'ml_measurement': 0.0,  # Se editará manualmente
                        'precio_ml_individual': 0.0,
                        'unit_price': 0.0,
                        'margin': 0.0,
                        'template_id': template.id,
                    })

            res['worktop_template_ids'] = [(0, 0, data) for data in template_data]
            _logger.info(f"Creadas {len(template_bases)} plantillas in-memory")

    def apply_calculated_price(self):
        _logger.info(f"Aplicando calculadora ID: {self.id}, precio: {self.total_price_encimera}")
        if self.order_line_id:
            # Actualizamos la línea de pedido con el precio
            self.order_line_id.write({
                'price_unit': self.total_price_encimera,
            })

            # CORRECCIÓN: Eliminar wizards antiguos EXCEPTO este
            old_wizards = self.env['vgr.price.calculator.encimera.wizard'].search([
                ('order_line_id', '=', self.order_line_id.id),
                ('id', '!=', self.id)
            ])

            # Eliminar plantillas asociadas a wizards antiguos
            old_templates = self.env['vgr.price.calculator.encimera.template'].search([
                ('calculator_id', 'in', old_wizards.ids)
            ])
            if old_templates:
                _logger.info(f"Eliminando {len(old_templates)} plantillas de wizards antiguos")
                old_templates.unlink()

            # Eliminar wizards antiguos
            if old_wizards:
                _logger.info(f"Eliminando {len(old_wizards)} wizards antiguos")
                old_wizards.unlink()

            # Actualizamos el wizard actual
            self.write({
                'grosor': self.grosor,
                'marca': self.marca,
                'encimera_canto': self.encimera_canto,
                'metros_lineales': self.metros_lineales,
                'precio_ml': self.precio_ml,
            })

            # Guardar las plantillas actualizadas
            for template in self.worktop_template_ids:
                if template.calculator_id.id == self.id:
                    # Actualizar plantilla existente
                    template.write({
                        'name': template.name,
                        'length': template.length,
                        'width': template.width,
                        'is_special_measurement': template.is_special_measurement,
                        'ml_measurement': template.ml_measurement,
                        'precio_ml_individual': template.precio_ml_individual,
                        'unit_price': template.unit_price,
                        'margin': template.margin,
                    })
                else:
                    # Crear nueva plantilla si no está asociada al wizard actual
                    self.env['vgr.price.calculator.encimera.template'].create({
                        'calculator_id': self.id,
                        'name': template.name,
                        'length': template.length,
                        'width': template.width,
                        'is_special_measurement': template.is_special_measurement,
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
        _logger.info(f"Abriendo calculadora para order_line_id: {order_line_id}")

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
            _logger.info(f"Creando nueva calculadora para order_line_id: {order_line_id}")
            calculator = self.create({'order_line_id': order_line_id})
            _logger.info(f"Nueva calculadora creada ID: {calculator.id}")

        # Retornar ventana con la calculadora
        # NOTA: Ya no creamos plantillas aquí, se crearán en default_get
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'vgr.price.calculator.encimera.wizard',
            'res_id': calculator.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_order_line_id': order_line_id}
        }
