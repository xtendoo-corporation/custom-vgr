from odoo import models, api, exceptions, _

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def create(self, vals):
        # Si el usuario no tiene el permiso y no es admin
        if not self.env.user.has_group('vgr_restrictions_groups.group_create_products'):
            raise exceptions.AccessError(_('No tienes permisos para crear productos. Contacta con el administrador.'))
        return super(ProductTemplate, self).create(vals)

class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def create(self, vals):
        # Si el usuario no tiene el permiso y no es admin
        if not self.env.user.has_group('vgr_restrictions_groups.group_create_products'):
            raise exceptions.AccessError(_('No tienes permisos para crear variantes de producto. Contacta con el administrador.'))
        return super(ProductProduct, self).create(vals)
