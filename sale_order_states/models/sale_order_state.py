from odoo import models, fields


class SaleOrderState(models.Model):
    _name = 'sale.order.state'
    _description = 'Sale Order State'

    name = fields.Char(
        string='Nombre del estado',
        required=True
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )

    alert_type = fields.Selection(
        [('normal', 'Normal'), ('warning', 'Aviso'), ('danger', 'Peligro')],
        string='Tipo de Alerta',
        default='normal'
    )

    def write(self, vals):
        res = super(SaleOrderState, self).write(vals)
        if 'sequence' in vals:
            # Lógica para actualizar el otro modelo
            orders = self.env['sale.order'].search([('vgr_state_id', 'in', self.ids)])
            for order in orders:
                order.vgr_state_selection = order._get_vgr_state_selection()[0][
                    0] if order._get_vgr_state_selection() else False
        return res
