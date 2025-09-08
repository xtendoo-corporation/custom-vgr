from odoo import api,fields, models


class PriceTemplateItem(models.Model):
    _name = 'vgr.price.template.item'
    _description = 'Plantilla de Elementos de Precio'

    name = fields.Char('Nombre', required=True)
    cost = fields.Float('Costo', required=True, digits=(16, 2))
    profit_percent = fields.Float('% Beneficio', required=True, digits=(16, 2))
    price = fields.Float('Precio', compute='_compute_price', store=True, digits=(16, 2))

    @api.depends('cost', 'profit_percent')
    def _compute_price(self):
        for record in self:
            record.price = record.cost * (1 + record.profit_percent / 100)
