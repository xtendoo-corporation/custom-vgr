from odoo import models, fields, api


class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    def action_vgr_recalculate_sequences(self):
        """Recalcula las secuencias de las líneas basándose en la fecha"""
        for statement in self:
            lines = statement.line_ids.sorted('date')
            sequence = 1
            for line in lines:
                line.sequence = sequence
                sequence += 1
        return True

    def action_vgr_recalculate_internal_index(self):
        """Fuerza el recálculo del internal_index de todas las líneas"""
        for statement in self:
            # Forzamos el recálculo del campo computado internal_index
            statement.line_ids._compute_simple_internal_index()
        return True

    def action_vgr_recalculate_running_balance(self):
        """Recalcula el running_balance de todas las líneas del extracto de forma determinista.

        En lugar de usar un "hack" que escribe en `sequence` para forzar recomputos, aquí forzamos
        los computes apropiados en las líneas del extracto. Esto mantiene la lógica en los
        métodos compute del core y evita efectos secundarios inesperados.
        """
        for statement in self:
            # Forzamos que las líneas tengan internal_index calculado
            lines = statement.line_ids
            if not lines:
                continue
            try:
                if hasattr(lines, '_compute_internal_index'):
                    lines._compute_internal_index()
            except Exception:
                pass

            # Llamamos a la implementación determinista local que hace el cálculo en Python
            self._recompute_running_balance_for_statement(statement)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Recálculo completado',
                'message': 'El running balance ha sido recalculado para las líneas seleccionadas.',
                'type': 'success',
                'sticky': False,
            }
        }

    def _recompute_running_balance_for_statement(self, statement):
        """Recalcula el running_balance de `statement` de forma determinista en Python.

        Algoritmo:
        - Ordena las líneas por `internal_index` (ascendente).
        - Busca el "anchor" (último statement previo con first_line_index < min_index del extracto e mismo journal)
          y usa su balance_start como punto inicial; si no lo hay, se usa 0.0.
        - Itera las líneas: si la línea tiene move.state == 'posted' suma su amount a current_running_balance.
        - Asigna el valor en memoria a `line.running_balance` (compute field no almacenado).

        Esto hace que la UI muestre inmediatamente los valores recalculados.
        """
        lines = statement.line_ids.sorted('internal_index')
        if not lines:
            return

        # Determinar el anchor: buscar statement previo con first_line_index < min_index y mismo journal
        min_index = lines[0].internal_index
        journal = statement.journal_id
        current_running_balance = 0.0

        if min_index and journal:
            self.env.cr.execute(
                """
                SELECT COALESCE(balance_start, 0.0)
                FROM account_bank_statement
                WHERE first_line_index < %s
                  AND journal_id = %s
                ORDER BY first_line_index DESC
                LIMIT 1
                """,
                (min_index, journal.id),
            )
            row = self.env.cr.fetchone()
            if row:
                current_running_balance = row[0] or 0.0

        # Iterar y asignar running_balance
        for line in lines:
            # Solo las líneas con estado 'posted' modifican el saldo; esto replica la lógica del core
            move_state = getattr(line.move_id, 'state', None)
            if move_state == 'posted':
                current_running_balance += line.amount or 0.0
            # Asignar en memoria (campo compute no almacenado)
            try:
                line.running_balance = current_running_balance
            except Exception:
                # Si por alguna razón no se puede asignar (campo readonly), se ignora
                pass

        return True

    def action_vgr_delete_lines(self):
        """Elimina líneas que no tienen statement_id"""
        lines_to_delete = self.env['account.bank.statement.line'].search([
            ('statement_id', '=', False)
        ])
        lines_to_delete.unlink()
        return True


class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    def _compute_simple_internal_index(self):
        for st_line in self.filtered(lambda line: line._origin.id):
            st_line.internal_index = f'{st_line.date.strftime("%Y%m%d")}' \
                                      f'{st_line.sequence:0>10}' \
                                      f'{st_line._origin.id:0>10}'

    def action_open_journal_entry(self):
        """Abre las entradas del diario relacionadas con esta línea"""
        self.ensure_one()
        if self.move_id:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Entradas del Diario',
                'res_model': 'account.move',
                'res_id': self.move_id.id,
                'view_mode': 'form',
                'target': 'current',
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': 'No hay entrada del diario asociada a esta línea.',
                    'type': 'warning',
                    'sticky': False,
                }
            }

    @api.model
    def new(self, values=None, origin=None, ref=None):
        """Override new para evitar conflictos con journal_id durante la creación"""
        if values is None:
            values = {}

        # Si estamos creando desde un bank statement, asegurar journal_id correcto
        if self._context.get('default_journal_id') and 'journal_id' not in values:
            values['journal_id'] = self._context.get('default_journal_id')

        return super().new(values=values, origin=origin, ref=ref)
