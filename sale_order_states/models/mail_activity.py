# python
from odoo import models, fields, api

class MailActivity(models.TransientModel):
    _inherit = 'mail.activity.schedule'

    res_id = fields.Integer(
        string='ID de registro relacionado',
        help='ID del registro relacionado (por ejemplo, Pedido de Venta).',
    )
    sale_order_partner_id = fields.Many2one(
        'res.partner',
        string='Cliente del Pedido',
        compute='_compute_sale_order_partner_id',
        store=True,
    )
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Pedido de Venta',
    )
    description = fields.Text(
        string='Descripción',
        help='Descripción de la actividad relacionada con el pedido de venta.',
    )
    date_start = fields.Date(
        string='Fecha de inicio',
        default=fields.Date.context_today
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        res_model = (
            self.env.context.get('default_res_model')
            or self.env.context.get('active_model')
            or 'sale.order'  # Valor por defecto seguro
        )
        res_id = self.env.context.get('default_res_id') or self.env.context.get('active_id')
        if res_model == 'sale.order' and res_id:
            res['sale_order_id'] = res_id
            res['res_id'] = res_id
            res['res_model'] = 'sale.order'
        elif not res.get('res_model'):
            res['res_model'] = res_model  # Nunca False
        return res

    @api.depends('sale_order_id')
    def _compute_sale_order_partner_id(self):
        for activity in self:
            if activity.sale_order_id:
                activity.sale_order_partner_id = activity.sale_order_id.partner_id
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

    # def action_open_document(self):
    #     # Lógica para abrir el documento relacionado
    #     pass

    def name_get(self):
        result = []
        for record in self:
            name = record.summary or str(record.id)
            result.append((record.id, name))
        return result

    name = fields.Char(string='Nombre', compute='_compute_name', store=True)

    @api.depends('summary')
    def _compute_name(self):
        for rec in self:
            rec.name = rec.summary or ''

    def name_get(self):
        result = []
        for rec in self:
            name = rec.summary or rec.name or str(rec.id)
            result.append((rec.id, name))
        return result

    color = fields.Integer(string='Color')
