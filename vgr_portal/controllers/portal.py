# -*- coding: utf-8 -*-
from odoo import http
from odoo.addons.project.controllers.portal import ProjectCustomerPortal


class ProjectCustomerPortalInherit(ProjectCustomerPortal):

    def _task_get_page_view_values(self, task, access_token, **kwargs):
        """Override para verificar si la tarea es visible en portal"""
        values = super()._task_get_page_view_values(task, access_token, **kwargs)

        # Si la tarea no es visible en portal, retornar error 404
        if not task.portal_visible:
            raise http.NotFound()

        return values

    def _prepare_tasks_domain(self, partner):
        """Override para añadir filtro de visibilidad en portal"""
        domain = super()._prepare_tasks_domain(partner)
        # Agregar condición para solo mostrar tareas visibles en portal
        domain += [('portal_visible', '=', True)]
        return domain
