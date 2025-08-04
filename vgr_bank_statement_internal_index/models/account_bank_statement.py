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


class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    def _compute_simple_internal_index(self):
        for st_line in self.filtered(lambda line: line._origin.id):
            st_line.internal_index = f'{st_line.date.strftime("%Y%m%d")}' \
                                      f'{st_line.sequence:0>10}' \
                                      f'{st_line._origin.id:0>10}'

