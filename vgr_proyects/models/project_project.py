from odoo import models, fields, api
from odoo.exceptions import UserError

class ProjectProject(models.Model):
    _inherit = 'project.project'

    customer_name = fields.Char(string='Nombre', required=True)
    customer_phone = fields.Char(string='Teléfono', required=True)
    customer_address = fields.Char(string='Dirección', required=True)
    template_project_id = fields.Many2one(
        'project.project',
        string='Proyecto plantilla',
        help='Selecciona un proyecto plantilla para copiar sus tareas y configuración al crear este proyecto.'
    )

    @api.onchange('partner_id')
    def _onchange_partner_id_fill_customer_fields(self):
        if self.partner_id:
            self.customer_name = self.partner_id.name or ''
            self.customer_phone = self.partner_id.mobile or ''
            address = self.partner_id.contact_address or ''
            self.customer_address = address
        else:
            self.customer_name = ''
            self.customer_phone = ''
            self.customer_address = ''

    @api.model
    def create(self, vals):
        # Si no se ha especificado un nombre, generar uno automáticamente
        if not vals.get('name'):
            last_project = self.search([('name', 'like', '#%')], order='id desc', limit=1)
            last_number = 0
            if last_project and last_project.name and last_project.name.startswith('#'):
                try:
                    last_number = int(last_project.name[1:])
                except Exception:
                    last_number = 0
            vals['name'] = f"#{last_number + 1}"
        # Crear el proyecto normalmente
        project = super().create(vals)
        # Si se seleccionó un proyecto plantilla, copiar sus tareas
        if vals.get('template_project_id'):
            template = self.browse(vals['template_project_id'])
            for task in template.task_ids:
                task.copy({'project_id': project.id})
        return project

    def copy(self, default=None):
        default = dict(default or {})
        # Generar nuevo nombre como en create
        last_project = self.search([('name', 'like', '#%')], order='id desc', limit=1)
        last_number = 0
        if last_project and last_project.name and last_project.name.startswith('#'):
            try:
                last_number = int(last_project.name[1:])
            except Exception:
                last_number = 0
        default['name'] = f"#{last_number + 1}"
        return super().copy(default)

    def unlink(self):
        for project in self:
            if getattr(project, 'is_template', False):
                # Mostrar mensaje informativo en vez de error
                raise UserError('No se puede eliminar un proyecto marcado como plantilla.')
        return super().unlink()
