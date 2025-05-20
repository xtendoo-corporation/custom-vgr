from odoo import models, api, exceptions, _

class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def _check_modify_quotations_group(self):
        if not self.env.user.has_group('vgr_restrictions_groups.group_modify_quotations'):
            raise exceptions.UserError(_('No tienes permisos para modificar o eliminar asientos contables'))

    def write(self, vals):
        self._check_modify_quotations_group()
        return super(AccountMove, self).write(vals)

    def unlink(self):
        self._check_modify_quotations_group()
        return super(AccountMove, self).unlink()
