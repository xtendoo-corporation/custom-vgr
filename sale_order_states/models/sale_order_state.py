from odoo import models, fields, api, _


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

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )
    visible_presupuesto = fields.Boolean(
        string='Visible Presupuesto',
        default=False
    )
    visible_pedido = fields.Boolean(
        string='Visible Pedido',
        default=False
    )



