from odoo import _, api, fields, models
from odoo.osv.expression import OR

from odoo.addons.payment_custom import const
import logging

_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    def action_recompute_pending_msg(self):
        """ Recompute the pending message to include the existing bank accounts. """
        account_payment_module = self.env['ir.module.module']._get('account_payment')
        _logger.info("[action_recompute_pending_msg] account_payment_module.state: %s", account_payment_module.state)
        if account_payment_module.state == 'installed':
            for provider in self.filtered(lambda p: p.custom_mode == 'wire_transfer'):
                company_id = provider.company_id.id
                _logger.info("[action_recompute_pending_msg] Procesando provider ID: %s, company_id: %s", provider.id, company_id)
                journals = self.env['account.journal'].search([
                    *self.env['account.journal']._check_company_domain(company_id),
                    ('type', '=', 'bank'),
                ])
                _logger.info("[action_recompute_pending_msg] Journals encontrados: %s", [j.display_name for j in journals])
                accounts_to_show = []
                for journal in journals:
                    if journal.bank_account_id and journal.bank_account_id.show_in_portal:
                        accounts_to_show.append(journal.bank_account_id.display_name)
                
                if accounts_to_show:
                    _logger.info("[action_recompute_pending_msg] Cuentas seleccionadas: %s", accounts_to_show)
                    account_names = "".join(f"<li><pre>{name}</pre></li>" for name in accounts_to_show)
                else:
                    _logger.info("[action_recompute_pending_msg] Ninguna cuenta bancaria encontrada con show_in_portal=True")
                    account_names = ""
                provider.pending_msg = f'<div>' \
                    f'<h5>{_("Please use the following transfer details")}</h5>' \
                    f'<p><br></p>' \
                    f'<h6>{_("Bank Account")}</h6>' \
                    f'<ul>{account_names}</ul>'\
                    f'<p><br></p>' \
                    f'</div>'
