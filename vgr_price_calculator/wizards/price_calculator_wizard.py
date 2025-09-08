from odoo import api, fields, models


class PriceCalculatorWizard(models.Model):
    _name = 'vgr.price.calculator.wizard'
    _description = 'Calculadora de Precios'

    product_id = fields.Many2one(
        'product.product',
        string='Producto',
        readonly=True
    )
    order_line_id = fields.Many2one(
        'sale.order.line',
        string='Línea de pedido'
    )
    price_total_without_integration = fields.Float(
        string='Precio calculado sin integración',
        digits='Product Price',
        readonly=True
    )
    price_total = fields.Float(
        string='Precio compra total de ck',
        digits='Product Price',
        readonly=True
    )
    price_group_id = fields.Many2one(
        'vgr.price.group',
        string='Grupo de precio',
    )
    price_group_price = fields.Float(
        string='Precio del grupo',
        compute='_compute_price_group_price',
        readonly=False,
    )

    @api.depends('price_group_id')
    def _compute_price_group_price(self):
        for record in self:
            if record.price_group_id and not record.price_group_price:
                record.price_group_price = record.price_group_id.price


    meters_linear = fields.Float(
        string='M/L',
    )
    elect_integration = fields.Boolean(
        string='Electro Integración',
        default=False
    )
    factory_cost = fields.Float(
        string='COSTO FABRICA',
        digits='Product Price'
    )
    factory_discount = fields.Float(
        string='% DESCUENTO FAB.',
        digits=(5, 2)
    )
    discounted_cost = fields.Float(
        string='COSTO CON DESC.',
        digits='Product Price',
        compute='_compute_discounted_cost'
    )
    percent_margin = fields.Float(
        string='% Margen',
        digits=(5, 2),
        default=0.0
    )
    margin = fields.Float(
        string='Margen',
        digits='Product Price',
        compute='_compute_margin'
    )
    price_mob = fields.Float(
        string='Precio Mob',
        digits='Product Price',
        default=0.0,
        compute='_compute_price_mob'
    )
    price_item_ids = fields.One2many(
        'vgr.price.calculator.line',
        'calculator_id',
        string='Elementos de Precio'
    )

    @api.depends('discounted_cost', 'margin', 'price_item_ids.price')
    def _compute_price_mob(self):
        for record in self:
            base_price = 0.0
            if record.discounted_cost:
                base_price = record.discounted_cost + record.margin

            # Sumamos los precios de todos los items
            items_price_total = sum(line.price for line in record.price_item_ids)

            # Precio final es la suma del precio base más el total de los items
            record.price_mob = base_price + items_price_total

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


    @api.onchange('elect_integration')
    def _onchange_elect_integration(self):
        if self.elect_integration:
            self.price_total = self.price_total_without_integration + 300
        else:
            self.price_total = self.price_total_without_integration

    @api.onchange('price_group_price', 'meters_linear')
    def _onchange_price_group(self):
        if self.price_group_id:
            self.price_total_without_integration = self.price_group_price * self.meters_linear

    def apply_calculated_price(self):
        if self.order_line_id:
            # Actualizamos la línea de pedido con el precio calculado
            self.order_line_id.write({
                'price_unit': self.price_mob,
                'purchase_price': self.discounted_cost,
            })

            # Eliminamos wizards anteriores de esta línea EXCEPTO este
            old_wizards = self.env['vgr.price.calculator.wizard'].search([
                ('order_line_id', '=', self.order_line_id.id),
                ('id', '!=', self.id)
            ])

            # Primero eliminamos las líneas asociadas a los wizards antiguos
            old_lines = self.env['vgr.price.calculator.line'].search([
                ('calculator_id', 'in', old_wizards.ids)
            ])
            old_lines.unlink()
            old_wizards.unlink()

            # Guardamos los valores del wizard actual
            values_to_save = {
                'order_line_id': self.order_line_id.id,
                'factory_cost': self.factory_cost or 0.0,
                'factory_discount': self.factory_discount or 0.0,
                'percent_margin': self.percent_margin or 0.0,
                'elect_integration': self.elect_integration or False,
                'price_mob': self.price_mob or 0.0,
            }
            if hasattr(self, 'price_mob_transport'):
                values_to_save['price_mob_transport'] = self.price_mob_transport or 0.0

            self.write(values_to_save)

            # Actualizamos todas las líneas para asegurar que están vinculadas correctamente
            for line in self.price_item_ids:
                line.write({
                    'calculator_id': self.id,
                    'sale_order_line_id': self.order_line_id.id
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
                              'elect_integration', 'price_mob_transport',
                              'meters_linear', 'price_group_id', 'price_mob']:
                    if field in fields_list and field in existing_wizard:
                        res[field] = existing_wizard[field]

            # Obtenemos las líneas existentes para usarlas como plantilla
            existing_lines = self.env['vgr.price.calculator.line'].search([
                ('sale_order_line_id', '=', order_line_id),
                ('calculator_id', '=', existing_wizard.id if existing_wizard else False)
            ])

            if existing_lines:
                # Creamos NUEVAS líneas basadas en las existentes
                res['price_item_ids'] = [(0, 0, {
                    'name': line.name,
                    'cost': line.cost,
                    'profit_percent': line.profit_percent,
                    'sale_order_line_id': order_line_id,
                }) for line in existing_lines]
            else:
                # Si no hay líneas previas, cargamos desde las plantillas
                template_items = self.env['vgr.price.template.item'].search([])
                if template_items:
                    res['price_item_ids'] = [(0, 0, {
                        'name': item.name,
                        'cost': 0.0,
                        'profit_percent': 0.0,
                        'sale_order_line_id': order_line_id,
                    }) for item in template_items]

        return res
