from odoo import models, fields, api
from odoo.exceptions import UserError
import re

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

    def get_portal_url(self):
        """Retorna la URL del portal para este proyecto"""
        self.ensure_one()
        return f'/my/project/tracking/{self.id}'

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

        # Realizar la copia y guardar el resultado
        new_project = super().copy(default)

        # Buscar todas las tareas asociadas al nuevo proyecto
        tasks = self.env['project.task'].search([('project_id', '=', new_project.id)])

        # Actualizar el nombre de cada tarea para incluir el nombre del proyecto
        for task in tasks:
            # Limpiar cualquier referencia anterior al proyecto
            clean_name = re.sub(r'\s*\[.*\]\s*$', '', task.name)

            # Añadir el nombre del proyecto al final
            new_name = f"{clean_name} [{new_project.name}]"

            # Actualizar el nombre sin desencadenar el flujo normal de write
            super(models.Model, task).write({'name': new_name})

        return new_project

    def unlink(self):
        for project in self:
            if getattr(project, 'is_template', False):
                # Mostrar mensaje informativo en vez de error
                raise UserError('No se puede eliminar un proyecto marcado como plantilla.')
        return super().unlink()

    def write(self, vals):
        # Guardar resultado de la operación write original
        result = super().write(vals)


        # Verificar si se modificó el nombre del proyecto
        if 'name' in vals:
            project_name = vals['name']

            # Buscar todas las tareas asociadas a este proyecto
            tasks = self.env['project.task'].search([('project_id', 'in', self.ids)])

            # Actualizar el nombre de cada tarea para incluir el nombre del proyecto
            for task in tasks:
                # Limpiar cualquier referencia anterior al proyecto
                clean_name = re.sub(r'\s*\[.*\]\s*$', '', task.name)

                # Añadir el nombre del proyecto al final
                new_name = f"{clean_name} [{project_name}]"

                # Actualizar el nombre sin desencadenar el flujo normal de write
                # para evitar recursión con el método personalizado de tareas
                super(models.Model, task).write({'name': new_name})


        return result

    def name_get(self):
        """Personalizar el nombre que se muestra en los emails para evitar 'Su Proyecto #...'"""
        return super().name_get()

    def _message_notification_recipients(self, message, recipients_data, **kwargs):
        """Personalizar los destinatarios de notificación para evitar 'Su Proyecto #...'"""
        # Ejecutar con contexto que oculte el nombre del documento
        return super(ProjectProject, self.with_context(mail_post_autofollow=False))._message_notification_recipients(
            message, recipients_data, **kwargs
        )

    def _notify_record_by_email(self, message, recipients_data, msg_vals=False,
                                 model_description=False, mail_auto_delete=True, check_existing=False,
                                 force_send=True, send_after_commit=True, **kwargs):
        """Sobrescribir para eliminar el título 'Su Proyecto #...' de los emails"""
        # Cambiar la descripción del modelo para evitar el prefijo
        model_description = False
        return super()._notify_record_by_email(
            message, recipients_data, msg_vals=msg_vals,
            model_description=model_description, mail_auto_delete=mail_auto_delete,
            check_existing=check_existing, force_send=force_send,
            send_after_commit=send_after_commit, **kwargs
        )

    def _notify_get_reply_to(self, default=None):
        """Personalizar el reply-to del email"""
        return super()._notify_get_reply_to(default=default)

    def _notify_get_groups(self, msg_vals=None):
        """Sobrescribir para evitar mostrar información del proyecto en la cabecera del email"""
        groups = super()._notify_get_groups(msg_vals=msg_vals)
        return groups

    def _message_compute_subject(self):
        """Sobrescribir para personalizar el subject del correo y evitar 'Su Proyecto #...'"""
        # Si estamos enviando un email desde una plantilla, no modificar
        if self._context.get('mail_notify_author'):
            return super()._message_compute_subject()

        # Personalizar el subject para que sea más limpio
        for project in self:
            if project.partner_id:
                return f"Actualización de su Proyecto"
        return "Actualización de Proyecto"

    def _notify_get_action_link(self, link_type, **kwargs):
        """Personalizar el enlace de acción para eliminar el prefijo 'Su Proyecto #...'"""
        if link_type == 'view':
            return self.get_portal_url()
        return super()._notify_get_action_link(link_type, **kwargs)

    def _message_get_default_recipients(self):
        """Personalizar destinatarios para evitar 'Su Proyecto #...' en notificaciones"""
        return {
            record.id: {
                'partner_ids': [record.partner_id.id] if record.partner_id else [],
                'email_to': False,
                'email_cc': False,
            }
            for record in self
        }

    def _notify_by_email_get_layout_render_values(self, message, recipients_group, msg_vals=None):
        """Sobrescribir para eliminar el record_name de los emails"""
        result = super()._notify_by_email_get_layout_render_values(message, recipients_group, msg_vals=msg_vals)
        # Eliminar el record_name y subtitles para que no aparezca la cabecera
        result['record_name'] = False
        result['subtitles'] = []
        return result


