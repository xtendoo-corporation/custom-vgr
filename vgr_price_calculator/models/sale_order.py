from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # meters_linear = fields.Float(
    #     string='M/L',
    #     help='Metros lineales'
    # )
    # price_group_id = fields.Many2one(
    #     'vgr.price.group',
    #     string='Grupo de precio'
    # )
    related_project_ids = fields.Many2many(
        'project.project',
        string='Proyectos',
        compute='_compute_related_projects',
        store=False,
    )

    @api.depends('analytic_account_id')
    def _compute_related_projects(self):
        for order in self:
            projects = self.env['project.project'].search([])
            related_projects = self.env['project.project']

            # Buscar por cuenta analítica directa
            if order.analytic_account_id:
                analytic_projects = self.env['project.project'].search([
                    ('analytic_account_id', '=', order.analytic_account_id.id)
                ])
                related_projects |= analytic_projects

            # Buscar proyectos que tengan este pedido como origen
            sale_projects = self.env['project.project'].search([
                ('sale_order_id', '=', order.id)
            ])
            related_projects |= sale_projects

            order.related_project_ids = related_projects
            order.related_project_ids = related_projects

    def copy(self, default=None):
        _logger.info(f"=== Copiando pedido de venta {self.name} (ID: {self.id}) ===")
        
        # Primero, copiamos el pedido (esto copia las líneas automáticamente)
        new_order = super(SaleOrder, self).copy(default)
        _logger.info(f"=== Nuevo pedido creado: {new_order.name} (ID: {new_order.id}) ===")
        
        # Ahora necesitamos mapear las líneas antiguas a las nuevas
        # Odoo mantiene el orden, así que podemos hacer zip
        old_lines = self.order_line
        new_lines = new_order.order_line
        
        _logger.info(f"Líneas del pedido original: {len(old_lines)}")
        _logger.info(f"Líneas del nuevo pedido: {len(new_lines)}")
        
        if len(old_lines) != len(new_lines):
            _logger.warning(f"¡ADVERTENCIA! El número de líneas no coincide. Puede haber problemas con la copia de calculadoras.")
        
        # Mapear líneas y copiar calculadoras
        for old_line, new_line in zip(old_lines, new_lines):
            _logger.info(f"Mapeando línea antigua {old_line.id} -> nueva línea {new_line.id} (Producto: {old_line.product_id.name})")
            
            # Copiar calculadora de encimera
            encimera_calculators = self.env['vgr.price.calculator.encimera.wizard'].search([
                ('order_line_id', '=', old_line.id)
            ])
            for calc in encimera_calculators:
                _logger.info(f"  Copiando calculadora de encimera {calc.id} a la nueva línea {new_line.id}")
                # Copiar el wizard primero
                new_calc = calc.copy({'order_line_id': new_line.id})
                _logger.info(f"  Nueva calculadora de encimera creada: {new_calc.id}")
                
                # Eliminar plantillas automáticamente creadas (si las hay)
                new_calc.worktop_template_ids.unlink()
                
                # Crear manualmente cada plantilla con todos sus datos
                for line in calc.worktop_template_ids:
                    line_data = line.copy_data()[0]
                    line_data['calculator_id'] = new_calc.id
                    created_template = self.env['vgr.price.calculator.encimera.template'].create(line_data)
                    _logger.info(f"    Plantilla de encimera copiada: {line.name} (ID: {created_template.id})")

            # Copiar calculadora de montaje
            montaje_calculators = self.env['vgr.price.calculator.montaje.wizard'].search([
                ('order_line_id', '=', old_line.id)
            ])
            for calc in montaje_calculators:
                _logger.info(f"  Copiando calculadora de montaje {calc.id} a la nueva línea {new_line.id}")
                # Copiar el wizard primero
                new_calc = calc.copy({'order_line_id': new_line.id})
                _logger.info(f"  Nueva calculadora de montaje creada: {new_calc.id}")
                
                # Eliminar plantillas automáticamente creadas (si las hay)
                new_calc.montaje_template_ids.unlink()
                
                # Crear manualmente cada plantilla con todos sus datos
                for line in calc.montaje_template_ids:
                    line_data = line.copy_data()[0]
                    line_data['calculator_id'] = new_calc.id
                    created_template = self.env['vgr.price.calculator.montaje.template'].create(line_data)
                    _logger.info(f"    Plantilla de montaje copiada: {line.name} (ID: {created_template.id})")

            # Copiar calculadora de mobiliario
            mobiliario_calculators = self.env['vgr.price.calculator.wizard'].search([
                ('order_line_id', '=', old_line.id)
            ])
            for calc in mobiliario_calculators:
                _logger.info(f"  Copiando calculadora de mobiliario {calc.id} a la nueva línea {new_line.id}")
                # Copiar el wizard primero
                new_calc = calc.copy({'order_line_id': new_line.id})
                _logger.info(f"  Nueva calculadora de mobiliario creada: {new_calc.id}")
                
                # Eliminar líneas automáticamente creadas (si las hay)
                new_calc.price_item_ids.unlink()
                
                # Crear manualmente cada línea con todos sus datos
                for line in calc.price_item_ids:
                    line_data = line.copy_data()[0]
                    line_data['calculator_id'] = new_calc.id
                    line_data['sale_order_line_id'] = new_line.id
                    created_item = self.env['vgr.price.calculator.line'].create(line_data)
                    _logger.info(f"    Línea de mobiliario copiada: {line.name} (ID: {created_item.id})")
        
        _logger.info(f"=== Finalizada copia de calculadoras para el pedido {new_order.name} ===")
        return new_order
