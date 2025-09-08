import logging
from odoo import api, fields, models
from odoo.exceptions import ValidationError

class PriceCalculatorEncimeraWizard(models.TransientModel):
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
        digits=(4, 1),  # Permite decimales para valores intermedios
        default=12.0,
    )

    # Validación para el rango permitido
    @api.constrains('grosor')
    def _check_grosor_range(self):
        for record in self:
            if record.grosor < 12.0 or record.grosor > 20.0:
                raise ValidationError("El grosor debe estar entre 12 y 20 mm (ambos incluidos).")


    marca = fields.Char(
        string='Marca'
    )

    encimera_canto = fields.Char(
        string='Encimera Canto',
    )

    metros_lineales = fields.Float(
        string='M/L',
        digits=(16, 2)
    )

    material = fields.Char(
        string='Material',
        compute='_compute_material',
        store=True
    )

    @api.depends('product_id', 'order_line_id')
    def _compute_material(self):
        for record in self:
            material_value = False

            # Intentar primero obtener el valor de los atributos del producto
            product = record.order_line_id.product_id if record.order_line_id else record.product_id

            if product:
                for attribute_value in product.product_template_attribute_value_ids:
                    if attribute_value.attribute_id.name == 'ENCIMERA MATERIAL':
                        material_value = attribute_value.product_attribute_value_id.name
                        break

            # Si no se encontró en los atributos, buscar en la descripción de la línea
            if not material_value and record.order_line_id and record.order_line_id.name:
                description = record.order_line_id.name

                # Buscar con formato exacto
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

    precio_ml = fields.Float(
        string='Precio M/L del Material',
        digits='Product Price'
    )

    price = fields.Float(
        string='Precio calculado',
        digits='Product Price',
        compute='_compute_price'
    )

    @api.depends('metros_lineales', 'precio_ml')
    def _compute_price(self):
        for record in self:
            record.price = record.metros_lineales * record.precio_ml

    def apply_calculated_price(self):
        if self.order_line_id and self.price:
            self.order_line_id.write({
                'price_unit': self.price,
            })
        return {'type': 'ir.actions.act_window_close'}
