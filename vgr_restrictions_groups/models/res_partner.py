from odoo import models, api, exceptions, _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create(self, vals):
        # Si el usuario no tiene el permiso y no es admin
        if not self.env.user.has_group('vgr_restrictions_groups.group_create_partners') and not self.env.user._is_admin():
            raise exceptions.AccessError(_('No tienes permisos para crear contactos. Contacta con el administrador.'))
        return super(ResPartner, self).create(vals)
