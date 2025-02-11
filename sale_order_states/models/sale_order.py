from odoo import models, fields, api, _

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    vgr_state_id = fields.Many2one(
        'sale.order.state',
        string='Custom VGR States',
    )

    @api.model
    def _get_vgr_state_selection(self):
        # Recuperamos todos los estados ordenados por la secuencia
        states = self.env['sale.order.state'].search([
            ('company_id', '=', self.env.company.id),
            '|',
            ('visible_presupuesto', '=', True),
            ('visible_pedido', '=', True)
        ], order='sequence')
        # Imprimimos los estados para verlos
        print("Estados recuperados:", states)
        # Devolvemos los estados ordenados para el campo de selección
        return [(state.name, state.name) for state in states]

    vgr_state_selection = fields.Selection(
        selection='_get_vgr_state_selection',
        string='Custom VGR States (Selection)',
        store=True,
        group_expand = "_read_group_vgr_state_id",
        domain="[('company_id', '=', user.company_id.id),'|', ('visible_presupuesto', '=', True), ('visible_pedido', '=', True)]"
    )

    vgr_state_presupuesto = fields.Selection(
        selection='_get_vgr_state_presupuesto',
        string='VGR State Presupuesto',
        store=True,
        group_expand="_read_group_vgr_state_id"
    )

    vgr_state_pedido = fields.Selection(
        selection='_get_vgr_state_pedido',
        string='VGR State Pedido',
        store=True,
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

