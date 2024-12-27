from odoo import models, fields, api

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    intermediary_percentage = fields.Float(string='% Intermediario', readonly=False)
    profit_percentage = fields.Float(string='% Beneficio', readonly=False)
    unit_price_without_margin_intermediary = fields.Float(string='Base Unitaria', readonly=False)
    intermediary_price = fields.Float(string='Margen Intermediario', readonly=True)
    net_margin = fields.Float(string='Net Margin', readonly=True)
