from odoo import fields, models, api


class ProjectProjectStage(models.Model):
    _inherit = 'project.project.stage'

    hide_in_portal = fields.Boolean(
        string='Oculto en portal (Vista cliente)',
        default=False,
        help='Si está marcado, los clientes no podrán ver esta etapa desde el portal'
    )

    @api.model
    def get_portal_visible_stages(self):
        """Retorna las etapas que son visibles en el portal"""
        return self.search([('hide_in_portal', '=', False)])


