# models/price_group.py
from odoo import fields, models, api


class PriceGroup(models.Model):
    _name = 'vgr.price.group'
    _description = 'Grupos de Precios'

    name = fields.Char(string='Grupo', required=True)
    description = fields.Char(string='Tipo', required=True)
    price = fields.Float(string='Precio', required=True, digits=(16, 2))

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.name} - {record.description} ({record.price} €)"
            result.append((record.id, name))
        return result
