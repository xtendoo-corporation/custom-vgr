# -*- coding: utf-8 -*-
from odoo import fields, models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.depends('invoice_ids.payment_state', 'invoice_ids.amount_residual')
    def _compute_has_paid_invoice(self):
        """Compute si hay alguna factura pagada asociada al pedido"""
        for order in self:
            has_payment = False
            for invoice in order.invoice_ids.filtered(lambda inv: inv.move_type == 'out_invoice'):
                if invoice.payment_state in ('paid', 'in_payment') or invoice.amount_residual == 0:
                    has_payment = True
                    break
            order.has_paid_invoice = has_payment

    has_paid_invoice = fields.Boolean(
        string='Tiene factura pagada',
        compute='_compute_has_paid_invoice',
        store=True,
        help='Indica si al menos una factura asociada a este pedido tiene algún pago registrado'
    )

    def _portal_ensure_token(self):
        """Override para asegurar que se compute el campo has_paid_invoice"""
        result = super()._portal_ensure_token()
        self._compute_has_paid_invoice()
        return result
