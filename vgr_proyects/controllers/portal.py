# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class ProjectPortalController(CustomerPortal):

    @http.route(['/my/project/tracking/<int:project_id>'], type='http', auth="user", website=True)
    def portal_my_project_tracking(self, project_id=None, **kw):
        """Vista detalle de un proyecto con tracking de etapas"""
        print(f"\n[VGR PORTAL] ========== ACCESO AL PORTAL ==========")
        print(f"[VGR PORTAL] URL: /my/project/tracking/{project_id}")
        print(f"[VGR PORTAL] Usuario: {request.env.user.name} (ID: {request.env.user.id})")

        Project = request.env['project.project']

        # Buscar el proyecto
        project = Project.sudo().browse(project_id)

        # Verificar que el proyecto existe
        if not project.exists():
            print(f"[VGR PORTAL] ERROR: Proyecto {project_id} NO EXISTE")
            print(f"[VGR PORTAL] Redirigiendo a /my")
            return request.redirect('/my')

        print(f"[VGR PORTAL] Proyecto encontrado: {project.name}")
        print(f"[VGR PORTAL] Cliente del proyecto: {project.partner_id.name if project.partner_id else 'SIN CLIENTE'}")
        print(f"[VGR PORTAL] Partner del usuario: {request.env.user.partner_id.name if request.env.user.partner_id else 'SIN PARTNER'}")
        print(f"[VGR PORTAL] Usuario es interno: {not request.env.user.share}")

        # Verificar acceso: permitir si es usuario interno O si es el cliente del proyecto
        is_internal_user = not request.env.user.share  # Usuario empleado/interno
        is_project_partner = request.env.user.partner_id and project.partner_id.id == request.env.user.partner_id.id

        if not is_internal_user and not is_project_partner:
            print(f"[VGR PORTAL] ERROR: Usuario NO tiene acceso al proyecto")
            print(f"[VGR PORTAL] No es usuario interno y no es el cliente del proyecto")
            print(f"[VGR PORTAL] Redirigiendo a /my")
            return request.redirect('/my')

        print(f"[VGR PORTAL] Acceso PERMITIDO - Usuario interno: {is_internal_user}, Es cliente: {is_project_partner}")

        print(f"[VGR PORTAL] Acceso permitido - Generando vista")

        # Obtener información de etapas para el tracking
        stage_info = project._get_portal_stage_info()
        print(f"[VGR PORTAL] Stage info obtenido: {len(stage_info.get('stages', []))} etapas")

        # Obtener tareas visibles en el portal
        tasks = request.env['project.task'].sudo().search([
            ('project_id', '=', project.id),
        ], order='date_deadline asc')
        print(f"[VGR PORTAL] Tareas encontradas: {len(tasks)}")

        values = {
            'project': project,
            'page_name': 'project',
            'stage_info': stage_info,
            'tasks': tasks,
        }

        print(f"[VGR PORTAL] Renderizando template: vgr_proyects.portal_my_project")
        print(f"[VGR PORTAL] ============================================\n")
        return request.render("vgr_proyects.portal_my_project", values)

