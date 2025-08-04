from odoo import models, fields, api


class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    def action_recalculate_sequences(self):
        """Recalcula las secuencias de las líneas basándose en la fecha"""
        for statement in self:
            # Ordenar las líneas por fecha y luego por ID para mantener consistencia
            lines = statement.line_ids.sorted(lambda l: (l.date, l.id))

            # Asignar nuevas secuencias
            for index, line in enumerate(lines, start=1):
                line.sequence = index * 10  # Incrementos de 10 para permitir inserciones

        return True

    def action_recalculate_internal_index(self):
        """Fuerza el recálculo del internal_index de todas las líneas"""
        for statement in self:
            # Filtrar líneas que tienen ID (están guardadas en la base de datos)
            lines_with_id = statement.line_ids.filtered(lambda l: l._origin.id)

            # Forzar el recálculo del internal_index
            for line in lines_with_id:
                line._compute_internal_index()

        return True

    def action_delete_lines(self):
        """Borra todas las líneas del extracto bancario"""
        for statement in self:
            # Borrar todas las líneas del extracto
            statement.line_ids.unlink()

        return True


class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    def _compute_simple_internal_index(self):
        for st_line in self.filtered(lambda line: line._origin.id):
            st_line.internal_index = f'{st_line.date.strftime("%Y%m%d")}' \
                                      f'{st_line.sequence:0>10}' \
                                      f'{st_line._origin.id:0>10}'
