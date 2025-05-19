from odoo import models, fields, api

class ResUsers(models.Model):
    _inherit = 'res.users'

    can_create_partners = fields.Boolean(
        string='Puede crear clientes',
        default=True,
        help='Si está habilitado, el usuario puede crear nuevos clientes'
    )
    can_create_products = fields.Boolean(
        string='Puede crear productos',
        default=True,
        help='Si está habilitado, el usuario puede crear nuevos productos'
    )
