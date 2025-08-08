from odoo import fields, models


class PriceTemplateItem(models.Model):
    _name = 'vgr.price.template.item'
    _description = 'Plantilla de Elementos de Precio'

    name = fields.Char('Nombre', required=True)
