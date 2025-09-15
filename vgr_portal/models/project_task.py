# -*- coding: utf-8 -*-
from odoo import fields, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    portal_visible = fields.Boolean(
        string='Visible en portal',
        default=True,
        help='Determina si esta tarea será visible para los clientes en el portal'
    )
