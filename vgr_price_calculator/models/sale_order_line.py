from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    needs_price_calculator = fields.Boolean(
        string='Necesita calculadora',
        compute='_compute_needs_price_calculator',
        store=True,
        default=False,
    )

    @api.depends('product_id', 'product_id.categ_id.calculate_cost_by_formula_type')
    def _compute_needs_price_calculator(self):
        for line in self:
            line.needs_price_calculator = bool(line.product_id and
                                               line.product_id.categ_id and
                                               line.product_id.categ_id.calculate_cost_by_formula_type in ('mobiliario', 'encimera', 'montaje'))

    @api.onchange('product_id')
    def product_id_change(self):
        if (self.product_id and
            self.product_id.categ_id.calculate_cost_by_formula_type in ('mobiliario', 'encimera', 'montaje')):
            calculator_types = {
                'mobiliario': 'Mobiliario',
                'encimera': 'Encimera',
                'montaje': 'Montaje'
            }
            calculator_type = calculator_types.get(self.product_id.categ_id.calculate_cost_by_formula_type, 'Mobiliario')
            return {
                'warning': {
                    'title': f'Calculadora de Precios ({calculator_type})',
                    'message': f'Este producto requiere calculadora de precios de {calculator_type.lower()}. Utilice el botón "Abrir Calculadora" después de guardar la línea.'
                }
            }
        return {}

    def action_open_price_calculator(self):
        self.ensure_one()
        if not self.needs_price_calculator:
            return

        # Determinar qué tipo de calculadora usar basado en el nuevo campo Selection
        formula_type = self.product_id.categ_id.calculate_cost_by_formula_type

        res_model = ''
        name = ''
        if formula_type == 'encimera':
            res_model = 'vgr.price.calculator.encimera.wizard'
            name = 'Calculadora de Precios (Encimera)'
        elif formula_type == 'montaje':
            res_model = 'vgr.price.calculator.montaje.wizard'
            name = 'Calculadora de Precios (Montaje)'
        elif formula_type == 'mobiliario':
            res_model = 'vgr.price.calculator.wizard'
            name = 'Calculadora de Precios (Mobiliario)'

        if not res_model:
            return

        # Buscar si ya existe un wizard para esta línea
        existing_wizard = self.env[res_model].search([('order_line_id', '=', self.id)], limit=1)

        result = {
            'type': 'ir.actions.act_window',
            'name': name,
            'res_model': res_model,
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.product_id.id,
                'default_order_line_id': self.id,
            }
        }

        if existing_wizard:
            result['res_id'] = existing_wizard.id

        return result

    def copy(self, default=None):
        _logger.info(f"Copiando línea de pedido {self.id} (Producto: {self.product_id.name})")
        new_line = super(SaleOrderLine, self).copy(default)
        _logger.info(f"Nueva línea creada: {new_line.id}")

        # Copiar calculadora de encimera
        encimera_calculators = self.env['vgr.price.calculator.encimera.wizard'].search([('order_line_id', '=', self.id)])
        for calc in encimera_calculators:
            _logger.info(f"Copiando calculadora de encimera {calc.id} a la nueva línea {new_line.id}")
            # Copiar el wizard primero
            new_calc = calc.copy({'order_line_id': new_line.id})
            _logger.info(f"Nueva calculadora de encimera creada: {new_calc.id}")
            
            # Eliminar plantillas automáticamente creadas (si las hay)
            new_calc.worktop_template_ids.unlink()
            
            # Crear manualmente cada plantilla con todos sus datos
            for line in calc.worktop_template_ids:
                line_data = line.copy_data()[0]
                line_data['calculator_id'] = new_calc.id
                self.env['vgr.price.calculator.encimera.template'].create(line_data)
                _logger.info(f"Plantilla de encimera copiada: {line.name}")

        # Copiar calculadora de montaje
        montaje_calculators = self.env['vgr.price.calculator.montaje.wizard'].search([('order_line_id', '=', self.id)])
        for calc in montaje_calculators:
            _logger.info(f"Copiando calculadora de montaje {calc.id} a la nueva línea {new_line.id}")
            # Copiar el wizard primero
            new_calc = calc.copy({'order_line_id': new_line.id})
            _logger.info(f"Nueva calculadora de montaje creada: {new_calc.id}")
            
            # Eliminar plantillas automáticamente creadas (si las hay)
            new_calc.montaje_template_ids.unlink()
            
            # Crear manualmente cada plantilla con todos sus datos
            for line in calc.montaje_template_ids:
                line_data = line.copy_data()[0]
                line_data['calculator_id'] = new_calc.id
                self.env['vgr.price.calculator.montaje.template'].create(line_data)
                _logger.info(f"Plantilla de montaje copiada: {line.name}")

        # Copiar calculadora de mobiliario
        mobiliario_calculators = self.env['vgr.price.calculator.wizard'].search([('order_line_id', '=', self.id)])
        for calc in mobiliario_calculators:
            _logger.info(f"Copiando calculadora de mobiliario {calc.id} a la nueva línea {new_line.id}")
            # Copiar el wizard primero
            new_calc = calc.copy({'order_line_id': new_line.id})
            _logger.info(f"Nueva calculadora de mobiliario creada: {new_calc.id}")
            
            # Eliminar líneas automáticamente creadas (si las hay)
            new_calc.price_item_ids.unlink()
            
            # Crear manualmente cada línea con todos sus datos
            for line in calc.price_item_ids:
                line_data = line.copy_data()[0]
                line_data['calculator_id'] = new_calc.id
                line_data['sale_order_line_id'] = new_line.id
                self.env['vgr.price.calculator.line'].create(line_data)
                _logger.info(f"Línea de mobiliario copiada: {line.name}")

        return new_line
