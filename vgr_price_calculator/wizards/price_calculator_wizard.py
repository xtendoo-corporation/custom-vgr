from odoo import api, fields, models


class PriceCalculatorWizard(models.TransientModel):
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
        if self.order_line_id and self.price_mob_transport:
            self.order_line_id.write({
                'price_unit': self.price_mob_transport,
                'purchase_price': self.build_cost + self.discounted_cost,
            })
        return {'type': 'ir.actions.act_window_close'}
