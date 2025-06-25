# models/sale_order.py
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    needs_price_calculator = fields.Boolean(
        string='Necesita calculadora',
        compute='_compute_needs_price_calculator',
        store=True,
        default=False,
    )
    elect_integration = fields.Boolean(string='Electro Integración', default=False)
    percent_margin = fields.Float(string='% Margen', digits=(5, 2), default=0.0)
    transport_cost = fields.Float(string='Transporte')
    factory_cost = fields.Float(string='COSTO FABRICA')
    factory_discount = fields.Float(string='% DESCUENTO FAB.')
    price_mob_transport = fields.Float(string='Precio Mob+Trans')

    def write(self, vals):
        tracked_fields = [
            'elect_integration', 'percent_margin', 'transport_cost',
            'factory_cost', 'factory_discount', 'price_mob_transport'
        ]
        percent_fields = ['percent_margin', 'factory_discount']
        # Guardar valores originales antes de escribir
        originals = {}
        for line in self:
            originals[line.id] = {field: getattr(line, field) for field in tracked_fields if field in vals}
        res = super().write(vals)
        for line in self:
            changed = {}
            for field in tracked_fields:
                if field in vals:
                    old_value = originals.get(line.id, {}).get(field)
                    new_value = getattr(line, field)
                    if old_value != new_value:
                        changed[field] = (old_value, new_value)
            if changed and line.order_id:
                product_name = line.product_id.display_name or 'Sin producto'
                msg = f"Producto: {product_name}\n\n"
                msg += f"Usuario: {line.env.user.display_name}\n\n"
                msg += "Se han modificado los siguientes campos en la línea de pedido:\n\n"
                for field, (old, new) in changed.items():
                    label = line._fields[field].string
                    if field in percent_fields:
                        msg += f"- {label}: {old * 100:.2f}% → {new * 100:.2f}%\n\n"
                    else:
                        msg += f"- {label}: {old} → {new}\n\n"
                line.order_id.message_post(
                    body=msg,
                    message_type='comment',
                    subtype_xmlid='mail.mt_note'
                )
        return res

    @api.depends('product_id', 'product_id.categ_id.calculate_cost_by_formula')
    def _compute_needs_price_calculator(self):
        for line in self:
            line.needs_price_calculator = bool(line.product_id and
                                               line.product_id.categ_id and
                                               line.product_id.categ_id.calculate_cost_by_formula)

    @api.onchange('product_id')
    def product_id_change(self):
        if self.product_id and self.product_id.categ_id.calculate_cost_by_formula:
            return {
                'warning': {
                    'title': 'Calculadora de Precios',
                    'message': 'Este producto requiere calculadora de precios. Utilice el botón "Abrir Calculadora" después de guardar la línea.'
                }
            }
        return {}

    def action_open_price_calculator(self):
        self.ensure_one()
        if not self.needs_price_calculator:
            return
        return {
            'type': 'ir.actions.act_window',
            'name': 'Calculadora de Precios',
            'res_model': 'vgr.price.calculator.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.product_id.id,
                'default_order_line_id': self.id,
                'default_price_group_id': self.order_id.price_group_id.id if self.order_id.price_group_id else False,
                'default_meters_linear': self.order_id.meters_linear,
            }
        }
