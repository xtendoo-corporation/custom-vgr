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

                templates = self.env['vgr.price.calculator.aplacado.template'].search([
                    ('calculator_id', '=', existing_wizard.id)
                ])

                if templates:
                    res['aplacado_template_ids'] = [(0, 0, {
                        'name': t.name,
                        'length': t.length,
                        'ml_measurement': t.ml_measurement,
                        'precio_ml_individual': t.precio_ml_individual,
                        'unit_price': t.unit_price,
                        'margin': t.margin,
                        'encastre_enchufe': t.encastre_enchufe,
                        'intermediario': t.intermediario,
                        'skip_price_calculation': t.skip_price_calculation,
                        'template_id': t.template_id.id if t.template_id else False,
                    }) for t in templates]
                else:
                    # crear plantillas por defecto a partir de vgr.price.template.item
                    base_items = self.env['vgr.price.template.item'].search([])
                    template_data = []
                    for item in base_items:
                        template_data.append({
                            'name': item.name,
                            'length': 0.0,
                            'ml_measurement': 0.0,
                            'precio_ml_individual': 0.0,
                            'unit_price': 0.0,
                            'margin': 0.0,
                            'encastre_enchufe': 0.0,
                            'intermediario': 0.0,
                            'skip_price_calculation': False,
                            'template_id': item.id,
                        })

                    res['aplacado_template_ids'] = [(0, 0, d) for d in template_data]

        return res

    def apply_calculated_price(self):
        if self.order_line_id:
            self.order_line_id.write({'price_unit': self.total_price_aplacado})

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
                        'encastre_enchufe': template.encastre_enchufe,
                        'intermediario': template.intermediario,
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
                        'encastre_enchufe': template.encastre_enchufe,
                        'intermediario': template.intermediario,
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
        if not calculator:
            calculator = self.create({'order_line_id': order_line_id})

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'vgr.price.calculator.aplacado.wizard',
            'res_id': calculator.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_order_line_id': order_line_id}
        }

