from odoo import fields, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    execution_date = fields.Datetime(
        string='Fecha realización',
        help='Fecha y hora programada para la ejecución de la tarea'
    )

    related_contact_id = fields.Many2one(
        'res.partner',
        string='Contacto relacionado',
        help='Contacto relacionado con esta tarea'
    )
