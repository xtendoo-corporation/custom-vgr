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

    marca = fields.Char(string='Marca')
    encimera_canto = fields.Char(string='Encimera Canto')
    metros_lineales = fields.Float(string='M/L', digits=(16, 2))
    material = fields.Char(string='Material', compute='_compute_material', store=True)
    precio_ml = fields.Float(string='Precio M/L del Material', digits='Product Price')
    price = fields.Float(string='Precio calculado', digits='Product Price', compute='_compute_price')

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

    @api.depends('metros_lineales', 'precio_ml')
    def _compute_price(self):
        for record in self:
            record.price = record.metros_lineales * record.precio_ml

    @api.depends('price', 'worktop_template_ids.total_price')
    def _compute_total_price_encimera(self):
        for record in self:
            template_total = sum(template.total_price for template in record.worktop_template_ids)
            record.total_price_encimera = record.price + template_total

    @api.onchange('precio_ml')
    def _onchange_precio_ml_templates(self):
        if self.precio_ml and self.worktop_template_ids:
            for template in self.worktop_template_ids:
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
                # Cargamos valores básicos del wizard existente
                for field in ['grosor', 'marca', 'encimera_canto', 'metros_lineales', 'precio_ml']:
                    if field in fields_list and hasattr(existing_wizard, field):
                        res[field] = existing_wizard[field]

                # Buscamos plantillas existentes
                existing_templates = self.env['vgr.price.calculator.encimera.template'].search([
                    ('calculator_id', '=', existing_wizard.id)
                ])

                if existing_templates:
                    _logger.info(f"Encontradas {len(existing_templates)} plantillas existentes")
                    # CORREGIDO: Usar comando (6, 0, ids) para vincular plantillas existentes
                    res['worktop_template_ids'] = [(6, 0, existing_templates.ids)]
                else:
                    _logger.info("No se encontraron plantillas para el wizard existente, creando nuevas")
                    self._create_default_templates_in_memory(res, order_line_id)
            else:
                _logger.info("No se encontró wizard existente, creando plantillas por defecto")
                self._create_default_templates_in_memory(res, order_line_id)

        return res

    def _create_default_templates_in_memory(self, res, order_line_id):
        # Método auxiliar para crear plantillas in-memory (igual que la calculadora que funciona)
        template_bases = self.env['vgr.price.template.item.worktop'].search([])
        _logger.info(f"Encontradas {len(template_bases)} plantillas base")

        if template_bases:
            # Creamos plantillas in-memory usando comandos Odoo (0, 0, {...})
            # IMPORTANTE: Esto es lo que hace la calculadora que funciona
            res['worktop_template_ids'] = [(0, 0, {
                'name': template.name,
                'length': template.length,
                'width': template.width,
                'is_special_measurement': template.is_special_measurement,
                'ml_measurement': template.ml_measurement,
                'unit_price': template.unit_price,  # CLAVE: Copiar exactamente
                'margin': template.margin,  # CLAVE: Copiar exactamente
                'template_id': template.id,
            }) for template in template_bases]
            _logger.info(f"Creadas {len(template_bases)} plantillas in-memory")

    def apply_calculated_price(self):
        _logger.info(f"Aplicando calculadora ID: {self.id}, precio: {self.total_price_encimera}")
        if self.order_line_id:
            # Actualizamos la línea de pedido con el precio calculado
            self.order_line_id.write({
                'price_unit': self.total_price_encimera,
            })

            # Guardamos los valores del wizard actual
            self.write({
                'grosor': self.grosor,
                'marca': self.marca,
                'encimera_canto': self.encimera_canto,
                'metros_lineales': self.metros_lineales,
                'precio_ml': self.precio_ml,
            })

            # CORREGIDO: Ya no eliminamos plantillas, solo actualizamos las existentes
            for template in self.worktop_template_ids:
                template.write({
                    'name': template.name,
                    'length': template.length,
                    'width': template.width,
                    'is_special_measurement': template.is_special_measurement,
                    'ml_measurement': template.ml_measurement,
                    'unit_price': template.unit_price,
                    'margin': template.margin,
                })

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
