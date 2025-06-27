# python
from odoo import models, fields, api

class MailActivity(models.Model):
    _inherit = 'mail.activity'

    sale_order_partner_id = fields.Many2one(
        'res.partner',
        string='Cliente del Pedido',
        compute='_compute_sale_order_partner_id',
        store=True,
    )
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Pedido de Venta',
        required=True,
    )
    description = fields.Text(
        string='Descripción',
        help='Descripción de la actividad relacionada con el pedido de venta.',
    )
    date_start = fields.Date(string='Fecha de inicio')

    @api.depends('res_model', 'res_id')
    def _compute_sale_order_partner_id(self):
        for activity in self:
            if activity.res_model == 'sale.order' and activity.res_id:
                sale_order = self.env['sale.order'].browse(activity.res_id)
                activity.sale_order_partner_id = sale_order.partner_id
            else:
                activity.sale_order_partner_id = False

    @api.onchange('sale_order_id')
    def _onchange_sale_order_id(self):
        if self.sale_order_id:
            self.res_model = 'sale.order'
            self.res_id = self.sale_order_id.id

    @api.onchange('activity_type_id', 'sale_order_id')
    def _onchange_summary(self):
        if self.activity_type_id and self.sale_order_id:
            self.summary = f"{self.activity_type_id.name} - {self.sale_order_id.client_order_ref or ''}"
