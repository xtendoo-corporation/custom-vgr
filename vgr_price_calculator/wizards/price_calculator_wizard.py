from odoo import api, fields, models


class PriceCalculatorWizard(models.Model):
    _name = 'vgr.price.calculator.wizard'
    _description = 'Calculadora de Precios'

    product_id = fields.Many2one('product.product', string='Producto', readonly=True)
    order_line_id = fields.Many2one('sale.order.line', string='Línea de pedido')
    price_total_without_integration = fields.Float(string='Precio calculado sin integración', digits='Product Price', readonly=True)
    price_total = fields.Float(string='Precio compra total de ck', digits='Product Price', readonly=True)
    price_group_id = fields.Many2one('vgr.price.group', string='Grupo de precio', readonly=True)
    meters_linear = fields.Float(string='M/L', readonly=True)
    elect_integration = fields.Boolean(string='Electro Integración', default=False)
    build_cost = fields.Float(string='Coste de montaje', digits='Product Price', compute='_compute_build_cost')

    factory_cost = fields.Float(string='COSTO FABRICA', digits='Product Price')
    factory_discount = fields.Float(string='% DESCUENTO FAB.', digits=(5, 2))
    discounted_cost = fields.Float(string='COSTO CON DESC.', digits='Product Price',
                                   compute='_compute_discounted_cost')

    percent_margin = fields.Float(string='% Margen', digits=(5, 2), default=0.0)
    margin = fields.Float(string='Margen', digits='Product Price', compute='_compute_margin')
    transport_cost = fields.Float(string='Transporte', digits='Product Price', default=0.0)
    price_mob_transport = fields.Float(string='Precio Mob+Trans', digits='Product Price', default=0.0, compute='_compute_price_mob_transport')

    price_item_ids = fields.One2many('vgr.price.calculator.line', 'calculator_id',
                                     string='Elementos de Precio')

    @api.depends('transport_cost', 'discounted_cost','margin')
    def _compute_price_mob_transport(self):
        for record in self:
            if record.transport_cost and record.discounted_cost:
                record.price_mob_transport = record.transport_cost + record.discounted_cost + record.margin
            else:
                record.price_mob_transport = 0.0

    @api.depends('discounted_cost', 'percent_margin')
    def _compute_margin(self):
        for record in self:
            if record.discounted_cost and record.percent_margin:
                record.margin = record.discounted_cost * record.percent_margin
            else:
                record.margin = 0.0

    @api.depends('factory_cost', 'factory_discount')
    def _compute_discounted_cost(self):
        for record in self:
            record.discounted_cost = record.factory_cost * record.factory_discount + record.factory_cost

    @api.depends('meters_linear')
    def _compute_build_cost(self):
        for record in self:
            record.build_cost = record.meters_linear * 195

    @api.onchange('elect_integration')
    def _onchange_elect_integration(self):
        if self.elect_integration:
            self.price_total = self.price_total_without_integration + 300
        else:
            self.price_total = self.price_total_without_integration

    @api.onchange('price_group_id')
    def _onchange_price_group(self):
        if self.price_group_id:
            self.price_total_without_integration = self.price_group_id.price * self.meters_linear

    def apply_calculated_price(self):
        if self.order_line_id:
            # Actualizamos la línea de pedido con el precio calculado (solo si hay price_mob_transport)
            if self.price_mob_transport:
                self.order_line_id.write({
                    'price_unit': self.price_mob_transport,
                    'purchase_price': self.build_cost + self.discounted_cost,
                })

            # Eliminamos wizards anteriores de esta línea si existen
            old_wizards = self.env['vgr.price.calculator.wizard'].search([
                ('order_line_id', '=', self.order_line_id.id),
                ('id', '!=', self.id)
            ])
            old_wizards.unlink()

            # Guardamos TODOS los valores del wizard actual usando write en lugar de SQL directo
            # Esto garantiza que se guarden todos los campos y relaciones correctamente
            values_to_save = {
                'order_line_id': self.order_line_id.id,
                'factory_cost': self.factory_cost or 0.0,
                'factory_discount': self.factory_discount or 0.0,
                'percent_margin': self.percent_margin or 0.0,
                'transport_cost': self.transport_cost or 0.0,
                'elect_integration': self.elect_integration or False,
                'price_mob_transport': self.price_mob_transport or 0.0,  # Añadimos el precio calculado
            }
            self.write(values_to_save)

            # Aseguramos que las líneas estén vinculadas tanto al wizard como a la línea de pedido
            for item in self.price_item_ids:
                item.write({
                    'sale_order_line_id': self.order_line_id.id,
                    'calculator_id': self.id
                })

        return {'type': 'ir.actions.act_window_close'}

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        order_line_id = self.env.context.get('default_order_line_id')

        if order_line_id:
            # Buscamos si ya existe un wizard para esta línea
            existing_wizard = self.env['vgr.price.calculator.wizard'].search([
                ('order_line_id', '=', order_line_id)
            ], limit=1)

            if existing_wizard:
                # Cargamos los valores del wizard existente
                for field in ['factory_cost', 'factory_discount', 'percent_margin',
                            'transport_cost', 'elect_integration', 'price_mob_transport']:
                    if field in fields_list:
                        res[field] = existing_wizard[field]

            calculator_lines = self.env['vgr.price.calculator.line'].search([
                ('sale_order_line_id', '=', order_line_id)
            ])

            if calculator_lines:
                # Si existen líneas, las usamos con todos sus valores
                res['price_item_ids'] = [(6, 0, calculator_lines.ids)]
            else:
                # Si no hay líneas previas, cargamos desde las plantillas
                template_items = self.env['vgr.price.template.item'].search([])
                if template_items:
                    res['price_item_ids'] = [(0, 0, {
                        'name': item.name,
                        'cost': 0.0,
                        'profit_percent': 0.0,
                    }) for item in template_items]

        return res
