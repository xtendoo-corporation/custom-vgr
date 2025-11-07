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
                # Filtrar etapas visibles
                visible_stages = all_stages.filtered(lambda s: not s.hide_in_portal)
                project.visible_stage_ids = visible_stages[:5] if len(visible_stages) <= 5 else visible_stages[:5]
                continue

            # Si la etapa actual está oculta, buscar la anterior visible
            display_index = current_index
            if project.stage_id.hide_in_portal:
                # Buscar hacia atrás
                for i in range(current_index - 1, -1, -1):
                    if not all_stages[i].hide_in_portal:
                        display_index = i
                        break
                else:
                    # Si no hay anterior visible, buscar hacia adelante
                    for i in range(current_index + 1, len(all_stages)):
                        if not all_stages[i].hide_in_portal:
                            display_index = i
                            break

            # Calcular las etapas visibles expandiendo el rango si hay ocultas
            # Objetivo: mostrar aproximadamente 5 etapas visibles
            target_visible_count = 5
            start_idx = max(0, display_index - 2)
            end_idx = min(len(all_stages), display_index + 2)

            # Expandir el rango hacia atrás y adelante hasta conseguir suficientes etapas visibles
            visible_stages = all_stages[start_idx:end_idx].filtered(lambda s: not s.hide_in_portal)

            while len(visible_stages) < target_visible_count:
                expanded = False

                # Intentar expandir hacia atrás
                if start_idx > 0:
                    start_idx -= 1
                    expanded = True

                # Intentar expandir hacia adelante
                if end_idx < len(all_stages):
                    end_idx += 1
                    expanded = True

                # Si no se puede expandir más, salir del bucle
                if not expanded:
                    break

                # Recalcular etapas visibles con el nuevo rango
                visible_stages = all_stages[start_idx:end_idx].filtered(lambda s: not s.hide_in_portal)

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

        # Si la etapa actual está oculta, buscar la anterior visible más cercana
        display_current_index = current_index
        if stages_list[current_index]['hide_in_portal']:
            # Buscar la etapa visible anterior más cercana
            for i in range(current_index - 1, -1, -1):
                if not stages_list[i]['hide_in_portal']:
                    display_current_index = i
                    break
            else:
                # Si no hay anterior visible, buscar la siguiente visible
                for i in range(current_index + 1, len(stages_list)):
                    if not stages_list[i]['hide_in_portal']:
                        display_current_index = i
                        break

        # Calcular rango visible expandiendo si hay etapas ocultas
        # Objetivo: mostrar aproximadamente 5 etapas visibles
        target_visible_count = 5
        start_idx = max(0, display_current_index - 2)
        end_idx = min(len(stages_list), display_current_index + 2)

        # Filtrar etapas ocultas del rango inicial
        visible_stages = stages_list[start_idx:end_idx]
        filtered_stages = [s for s in visible_stages if not s['hide_in_portal']]

        # Expandir el rango si no tenemos suficientes etapas visibles
        while len(filtered_stages) < target_visible_count:
            expanded = False

            # Intentar expandir hacia atrás
            if start_idx > 0:
                start_idx -= 1
                # Añadir la nueva etapa si no está oculta
                if not stages_list[start_idx]['hide_in_portal']:
                    filtered_stages.insert(0, stages_list[start_idx])
                expanded = True

            # Intentar expandir hacia adelante
            if end_idx < len(stages_list):
                # Añadir la nueva etapa si no está oculta
                if not stages_list[end_idx]['hide_in_portal']:
                    filtered_stages.append(stages_list[end_idx])
                end_idx += 1
                expanded = True

            # Si no se puede expandir más, salir del bucle
            if not expanded:
                break

        # Marcar la etapa actual y las completadas
        for stage in filtered_stages:
            # Encontrar el índice real en la lista completa
            real_idx = next(i for i, s in enumerate(stages_list) if s['id'] == stage['id'])

            if real_idx < current_index:
                stage['status'] = 'completed'
            elif real_idx == display_current_index:
                stage['status'] = 'current'
            else:
                stage['status'] = 'pending'

        # Determinar el nombre de la etapa actual a mostrar
        current_stage_name = 'En proceso'
        if self.stage_id.hide_in_portal:
            # Si la etapa actual está oculta, mostrar la anterior visible
            display_stage = next((s for s in filtered_stages if s['status'] == 'current'), None)
            if display_stage:
                current_stage_name = display_stage['name']
        else:
            current_stage_name = self.stage_id.name

        return {
            'stages': filtered_stages,
            'current_stage': current_stage_name,
            'has_previous': start_idx > 0,
            'has_next': end_idx < len(stages_list),
        }

