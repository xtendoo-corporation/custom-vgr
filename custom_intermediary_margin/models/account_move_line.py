from odoo import models, fields, api

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    intermediary_percentage = fields.Float(string='% Intermediario', readonly=True)
    profit_percentage = fields.Float(string='% Beneficio', readonly=True)
    unit_price_without_margin_intermediary = fields.Float(string='Base Unitaria', readonly=True)
    intermediary_price = fields.Float(string='Margen Intermediario', readonly=True)
    purchase_price = fields.Float(string='Coste', readonly=True)
