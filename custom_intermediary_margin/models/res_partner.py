from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    intermediary_margin = fields.Float(
        string='% Intermediación',
        default=0.0,
    )
