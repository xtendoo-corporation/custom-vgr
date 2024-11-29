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
        states = self.env['sale.order.state'].search([], order='sequence')
        # Devolvemos los estados ordenados para el campo de selección
        return [(state.name, state.name) for state in states]

    vgr_state_selection = fields.Selection(
        selection='_get_vgr_state_selection',
        string='Custom VGR States (Selection)',
        store=True
    )

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

