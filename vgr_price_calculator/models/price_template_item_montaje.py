from odoo import api, fields, models


class PriceTemplateItemMontaje(models.Model):
    _name = 'vgr.price.template.item.montaje'
    _description = 'Plantilla de Elementos de Precio para Montaje'

    name = fields.Char('Nombre', required=True)

