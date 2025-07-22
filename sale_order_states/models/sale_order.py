from odoo import models, fields, api, _

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    vgr_state_id = fields.Many2one(
        'sale.order.state',
        string='Custom VGR States',
    )

    payment_text = fields.Text(
        string='Forma de pago',
        default='Forma de pago\n50% a la aceptación\n50% antes del montaje\nBBVA: ES81 0182 3288 6802 0161 6795',
        store=True
    )

    @api.model
    def _get_vgr_state_selection(self):
        states = self.env['sale.order.state'].search([
            ('company_id', '=', self.env.company.id),
            '|',
            ('visible_presupuesto', '=', True),
            ('visible_pedido', '=', True)
        ], order='sequence')
        return [(state.name, state.name) for state in states]

    vgr_state_selection = fields.Selection(
        selection='_get_vgr_state_selection',
        string='Custom VGR States (Selection)',
        store=True,
        group_expand = "_read_group_vgr_state_id",
        company_dependent=True
    )

    vgr_state_presupuesto = fields.Selection(
        selection='_get_vgr_state_presupuesto',
        string='VGR State Presupuesto',
        store=True,
        company_dependent=True,
        group_expand="_read_group_vgr_state_id"
    )

    vgr_state_pedido = fields.Selection(
        selection='_get_vgr_state_pedido',
        string='VGR State Pedido',
        store=True,
        company_dependent=True,
        group_expand="_read_group_vgr_state_id"
    )

    @api.onchange('company_id')
    def _onchange_company_id(self):
        if self.company_id:
            self.vgr_state_presupuesto = False
            self.vgr_state_pedido = False

    def _get_vgr_state_presupuesto(self):
            states = self.env['sale.order.state'].search([
                ('company_id', '=', self.env.company.id),
                ('visible_presupuesto', '=', True)
            ], order='sequence')
            return [(state.name, state.name) for state in states]

    def _get_vgr_state_pedido(self):
            states = self.env['sale.order.state'].search([
                ('company_id', '=', self.env.company.id),
                ('visible_pedido', '=', True)
            ], order='sequence')
            return [(state.name, state.name) for state in states]

    @api.model
    def _read_group_vgr_state_id(self, stages, domain, order):
        return self.env['sale.order.state'].search([]).mapped('name')

    vgr_alert_type = fields.Selection(
        [('normal', 'Normal'), ('warning', 'Aviso'), ('danger', 'Peligro')],
        string='Alert Type',
        compute='_compute_vgr_alert_type',
        store=True
    )

    @api.depends('vgr_state_selection')
    def _compute_vgr_alert_type(self):
        for order in self:
            state = self.env['sale.order.state'].search([('name', '=', order.vgr_state_selection)], limit=1)
            order.vgr_alert_type = state.alert_type if state else 'normal'

    # Campo para contar actividades
    activity_schedule_count = fields.Integer(
        string='Número de Actividades',
        compute='_compute_activity_schedule_count'
    )

    @api.depends()
    def _compute_activity_schedule_count(self):
        for record in self:
            record.activity_schedule_count = self.env['mail.activity.schedule'].search_count([
                ('res_model', '=', 'sale.order'),
                ('res_id', '=', record.id)
            ])

    def action_view_activity_schedules(self):
        """Método para abrir las actividades del pedido en vista calendario"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Actividades de {self.name}',
            'res_model': 'mail.activity.schedule',
            'view_mode': 'calendar',
            'domain': [('res_model', '=', 'sale.order'), ('res_id', '=', self.id)],
            'context': {
                'default_res_model': 'sale.order',
                'default_res_id': self.id,
                'default_sale_order_id': self.id,
            },
            'target': 'current',
        }
