# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    not_printable = fields.Boolean(
        string='No Imprimir',
        default=False,
        help='Si está marcado, esta línea no se mostrará en los reportes de facturas'
    )
