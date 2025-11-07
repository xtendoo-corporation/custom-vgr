# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ProjectProject(models.Model):
    _inherit = 'project.project'

    @api.depends('stage_id')
    def _compute_visible_stages(self):
        """Calcula las etapas visibles para el tracking (actual, 2 anteriores, 2 siguientes)"""
        for project in self:
            if not project.stage_id:
                project.visible_stage_ids = self.env['project.project.stage']
                continue

            # Obtener todas las etapas ordenadas por secuencia
            all_stages = self.env['project.project.stage'].search(
                [('fold', '=', False)],
                order='sequence asc'
            )

            # Encontrar el índice de la etapa actual
            current_index = None
            for idx, stage in enumerate(all_stages):
                if stage.id == project.stage_id.id:
                    current_index = idx
                    break

            if current_index is None:
                project.visible_stage_ids = all_stages[:5] if len(all_stages) <= 5 else all_stages[:5]
                continue

            # Calcular las etapas visibles (2 anteriores, actual, 2 siguientes)
            start_idx = max(0, current_index - 2)
            end_idx = min(len(all_stages), current_index + 3)

            visible_stages = all_stages[start_idx:end_idx]
            project.visible_stage_ids = visible_stages

    visible_stage_ids = fields.Many2many(
        'project.project.stage',
        compute='_compute_visible_stages',
        string='Etapas Visibles en Portal',
        help='Etapas visibles en el tracking del portal (actual + 2 anteriores + 2 siguientes)'
    )

    def _get_portal_stage_info(self):
        """Retorna información de las etapas para el portal"""
        self.ensure_one()

        # Obtener todas las etapas no plegadas ordenadas
        all_stages = self.env['project.project.stage'].search(
            [('fold', '=', False)],
            order='sequence asc'
        )

        if not self.stage_id:
            return {
                'stages': [],
                'current_stage': None,
            }

        # Encontrar el índice de la etapa actual
        current_index = None
        stages_list = []

        for idx, stage in enumerate(all_stages):
            if stage.id == self.stage_id.id:
                current_index = idx
            stages_list.append({
                'id': stage.id,
                'name': stage.name,
                'sequence': stage.sequence,
                'hide_in_portal': stage.hide_in_portal,
            })

        if current_index is None:
            current_index = 0

        # Calcular rango visible (2 anteriores, actual, 2 siguientes)
        start_idx = max(0, current_index - 2)
        end_idx = min(len(stages_list), current_index + 3)

        visible_stages = stages_list[start_idx:end_idx]

        # Marcar la etapa actual y las completadas
        for i, stage in enumerate(visible_stages):
            actual_idx = start_idx + i
            if actual_idx < current_index:
                stage['status'] = 'completed'
            elif actual_idx == current_index:
                stage['status'] = 'current'
            else:
                stage['status'] = 'pending'

        return {
            'stages': visible_stages,
            'current_stage': self.stage_id.name if not self.stage_id.hide_in_portal else 'En proceso',
            'has_previous': start_idx > 0,
            'has_next': end_idx < len(stages_list),
        }

