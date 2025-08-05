from odoo import models, fields, api


class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    def action_recalculate_sequences(self):
        """Recalcula las secuencias de las líneas basándose en la fecha"""
        for statement in self:
            lines = statement.line_ids.sorted('date')
            sequence = 1
            for line in lines:
                line.sequence = sequence
                sequence += 1
        return True

    def action_recalculate_internal_index(self):
        """Fuerza el recálculo del internal_index de todas las líneas"""
        for statement in self:
            # Forzamos el recálculo del campo computado internal_index
            statement.line_ids._compute_simple_internal_index()
        return True

    def action_delete_lines(self):
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
