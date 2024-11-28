from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    vgr_state_id = fields.Many2one('sale.order.state', string='Custom VGR States')

    @api.depends('vgr_state_id')
    def _compute_vgr_state_selection(self):
        for record in self:
            record.vgr_state_selection = record.vgr_state_id.id

    @api.model
    def _get_vgr_state_selection(self):
        states = self.env['sale.order.state'].search([])
        return [(state.id, state.name) for state in states]

    vgr_state_selection = fields.Selection(
        selection='_get_vgr_state_selection',
        string='Custom VGR States (Selection)',
        compute='_compute_vgr_state_selection',
        store=True
    )
