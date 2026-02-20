# -*- coding: utf-8 -*-

from odoo import fields, models


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    show_in_portal = fields.Boolean(
        string='Show in Portal',
        default=True,
        help="If checked, this bank account will be displayed in the portal payment instructions."
    )
