from odoo import fields, models, api
import logging
import re

_logger = logging.getLogger(__name__)


class ProjectTask(models.Model):
    _inherit = 'project.task'

    execution_date = fields.Datetime(
        string='Fecha realización',
        help='Fecha y hora de ejecución de la tarea'
    )

    related_contact_id = fields.Many2one(
        'res.partner',
        string='Contacto relacionado',
        help='Contacto relacionado con esta tarea'
    )

    project_state_on_completion = fields.Many2one(
        'project.project.stage',
        string='Estado del proyecto al completarse',
        help='Estado al que debe cambiar el proyecto cuando esta tarea se marque como completada'
    )

    calendar_color = fields.Integer(
        string='Color del calendario',
        compute='_compute_calendar_color',
        store=False
    )

    @api.depends('state')
    def _compute_calendar_color(self):
        """Compute calendar color based on task state"""
        color_map = {
            '1_done': 10,          # Verde - Completadas
            '01_in_progress': 4,   # Azul - En progreso
            '1_canceled': 1,       # Rojo - Canceladas
            '02_changes_requested': 3,  # Naranja - Cambios solicitados
            '03_approved': 9,      # Azul - Aprobadas
            '04_waiting_normal': 5 # Amarillo más brillante - En espera
        }

        for task in self:
            color = color_map.get(task.state, 0)
            task.calendar_color = color
            _logger.info(f"Task {task.name} - State: {task.state} - Color: {color}")

    def _add_state_icon_to_name(self):
        """Add state icon to task name based on current state"""
        if self.name:
            state_icons = {
                '1_done': '✅',           # Check mark - Completadas
                '01_in_progress': '🔄',   # Refresh - En progreso
                '1_canceled': '🛑',       # X roja (stop) - Canceladas
                '02_changes_requested': '🔄', # Refresh - Cambios solicitados
                '03_approved': '✅',      # Check mark - Aprobadas
                '04_waiting_normal': '⏳' # Hourglass - En espera
            }

            # Remover cualquier icono previo del nombre
            clean_name = re.sub(r'^[✅🔄🛑⏳📋]\s*', '', self.name)

            # Agregar el nuevo icono según el estado
            if self.state in state_icons:
                new_name = f"{state_icons[self.state]} {clean_name}"
            else:
                new_name = f"📋 {clean_name}"

            # Solo actualizar si el nombre cambió para evitar recursión
            if new_name != self.name:
                print("*"*100)
                print(f"Task {clean_name} state changed to {self.state} - Adding icon")
                print("*" * 100)
                # Usar super().write() para evitar recursión infinita
                super(ProjectTask, self).write({'name': new_name})

    def write(self, vals):
        """Override write to detect when task is marked as done and update project state"""
        # Guardar estados anteriores
        old_states = {task.id: task.state for task in self}

        # Llamar al método padre
        result = super().write(vals)

        # Si se cambió el estado, actualizar el icono en el nombre
        if 'state' in vals:
            for task in self:
                task._add_state_icon_to_name()

        # Verificar si alguna tarea cambió a estado completado
        for task in self:
            old_state = old_states.get(task.id)
            if (old_state != '1_done' and task.state == '1_done' and
                task.project_state_on_completion and task.project_id):

                # Cambiar el estado del proyecto
                old_project_stage = task.project_id.stage_id.name if task.project_id.stage_id else 'Sin estado'
                task.project_id.stage_id = task.project_state_on_completion

                # Crear mensaje en el chatter del proyecto
                task.project_id.message_post(
                    body=f"""
                    Estado del proyecto actualizado automáticamente
                    🎯Tarea completada: {task.name}
                    📊Estado anterior: {old_project_stage}
                    ✅ Nuevo estado: {task.project_state_on_completion.name}
                    Cambio automático basado en la configuración de la tarea.
                    """,
                    subject=f"Proyecto actualizado por tarea: {task.name}",
                    message_type='notification'
                )

                # También crear mensaje en el chatter de la tarea
                task.message_post(
                    body=f"""
                    ✅ Tarea completada - Proyecto actualizado
                    📊 El proyecto {task.project_id.name} ha cambiado al estado: {task.project_state_on_completion.name}
                    """,
                    subject="Tarea completada - Proyecto actualizado",
                    message_type='notification'
                )

        return result

    @api.model
    def create(self, vals):
        """Override create to add icon when task is created"""
        result = super().create(vals)
        # Agregar icono al nombre cuando se crea la tarea
        result._add_state_icon_to_name()
        return result
