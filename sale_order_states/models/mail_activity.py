# python
from odoo import models, fields, api

class MailActivity(models.TransientModel):
    _inherit = 'mail.activity.schedule'

    res_id = fields.Integer(
        string='ID de registro relacionado',
        help='ID del registro relacionado (por ejemplo, Pedido de Venta).',
    )
    sale_order_partner_id = fields.Many2one(
        'res.partner',
        string='Cliente del Pedido',
        compute='_compute_sale_order_partner_id',
        store=True,
    )
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Pedido de Venta',
    )
    description = fields.Text(
        string='Descripción',
        help='Descripción de la actividad relacionada con el pedido de venta.',
    )
    date_start = fields.Date(
        string='Fecha de inicio',
        default=fields.Date.context_today
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        res_model = (
            self.env.context.get('default_res_model')
            or self.env.context.get('active_model')
            or 'sale.order'  # Valor por defecto seguro
        )
        res_id = self.env.context.get('default_res_id') or self.env.context.get('active_id')
        if res_model == 'sale.order' and res_id:
            res['sale_order_id'] = res_id
            res['res_id'] = res_id
            res['res_model'] = 'sale.order'
        elif not res.get('res_model'):
            res['res_model'] = res_model  # Nunca False
        return res

    @api.depends('sale_order_id')
    def _compute_sale_order_partner_id(self):
        for activity in self:
            if activity.sale_order_id:
                activity.sale_order_partner_id = activity.sale_order_id.partner_id
            else:
                activity.sale_order_partner_id = False

    @api.onchange('sale_order_id')
    def _onchange_sale_order_id(self):
        if self.sale_order_id:
            self.res_model = 'sale.order'
            self.res_id = self.sale_order_id.id

    @api.onchange('activity_type_id', 'sale_order_id')
    def _onchange_summary(self):
        if self.activity_type_id and self.sale_order_id:
            self.summary = f"{self.activity_type_id.name} - {self.sale_order_id.client_order_ref or ''}"

    name = fields.Char(string='Nombre', compute='_compute_name', store=True)

    @api.depends('summary')
    def _compute_name(self):
        for rec in self:
            rec.name = rec.summary or ''

    def name_get(self):
        result = []
        for rec in self:
            name = rec.summary or rec.name or str(rec.id)
            if '-' in name:
                name = name.replace('-', '\n', 1)  # Solo el primer guion
            result.append((rec.id, name))
        return result

    color = fields.Integer(string='Color')

    # Campo para verificar si la actividad está completada
    is_activity_completed = fields.Boolean(
        string='Actividad Completada',
        compute='_compute_is_activity_completed',
        store=False
    )

    @api.depends('res_model', 'res_id', 'activity_type_id', 'summary', 'activity_user_id')
    def _compute_is_activity_completed(self):
        """Verificar si la actividad real asociada está completada"""
        for record in self:
            record.is_activity_completed = False

            # Solo verificar si el registro ya existe (no es un registro nuevo en creación)
            if not record.id:
                continue

            if record.res_model and record.res_id and record.summary and record.activity_user_id:
                # Primero verificar si existe una actividad activa (no completada)
                active_activity = self.env['mail.activity'].search([
                    ('res_model', '=', record.res_model),
                    ('res_id', '=', record.res_id),
                    ('activity_type_id', '=', record.activity_type_id.id),
                    ('summary', '=', record.summary),
                    ('user_id', '=', record.activity_user_id.id),
                ], limit=1)

                # Si no hay actividad activa, buscar si fue completada
                if not active_activity:
                    # Buscar mensajes de actividades completadas de forma más específica
                    completed_message = self.env['mail.message'].search([
                        ('model', '=', record.res_model),
                        ('res_id', '=', record.res_id),
                        ('message_type', '=', 'notification'),
                        ('subtype_id.name', '=', 'Activities'),
                        ('body', 'like', f'%{record.summary}%'),
                        ('body', 'like', '%completada%'),  # Buscar específicamente que mencione completada
                    ], limit=1)

                    if completed_message:
                        record.is_activity_completed = True

    @api.model
    def create(self, vals):
        """Override para crear automáticamente la actividad real cuando se crea una programada"""
        # Crear la actividad programada
        activity_schedule = super().create(vals)

        # Si tiene res_model y res_id, crear también la actividad real
        if activity_schedule.res_model and activity_schedule.res_id:
            # Obtener el res_model_id desde el modelo ir.model
            res_model_record = self.env['ir.model'].search([('model', '=', activity_schedule.res_model)], limit=1)
            if res_model_record:
                # Crear la actividad real para que aparezca en el chatter
                activity_vals = {
                    'res_model': activity_schedule.res_model,
                    'res_model_id': res_model_record.id,
                    'res_id': activity_schedule.res_id,
                    'activity_type_id': activity_schedule.activity_type_id.id,
                    'summary': activity_schedule.summary or '',
                    'note': activity_schedule.description or '',
                    'user_id': activity_schedule.activity_user_id.id,
                    'date_deadline': activity_schedule.date_deadline,
                }

                # Crear la actividad real
                self.env['mail.activity'].create(activity_vals)

        return activity_schedule

    def write(self, vals):
        """Override para actualizar la actividad real cuando se modifica la programada"""
        # Campos que deben sincronizarse entre actividad programada y real
        sync_fields = ['summary', 'description', 'activity_type_id', 'activity_user_id', 'date_deadline']

        # Solo procesar si se modificaron campos relevantes
        if any(field in vals for field in sync_fields):
            # Primero obtenemos los valores antiguos antes de hacer el write
            old_values = {}
            for record in self:
                if record.res_model and record.res_id:
                    old_values[record.id] = {
                        'summary': record.summary,
                        'activity_type_id': record.activity_type_id.id,
                        'user_id': record.activity_user_id.id,
                    }

        # Ejecutar el write original
        result = super().write(vals)

        # Ahora sincronizar con las actividades reales usando los valores antiguos
        if any(field in vals for field in sync_fields):

            print("Syncing activities with old values...")

            for record in self:
                if record.res_model and record.res_id and record.id in old_values:
                    old_vals = old_values[record.id]

                    # Buscar la actividad real asociada usando los valores antiguos
                    related_activity = self.env['mail.activity'].search([
                        ('res_model', '=', record.res_model),
                        ('res_id', '=', record.res_id),
                        ('activity_type_id', '=', old_vals['activity_type_id']),
                        ('user_id', '=', old_vals['user_id']),
                        ('summary', '=', old_vals['summary']),
                    ], limit=1)

                    # Si no encuentra con valores antiguos, buscar con valores actuales
                    if not related_activity:
                        related_activity = self.env['mail.activity'].search([
                            ('res_model', '=', record.res_model),
                            ('res_id', '=', record.res_id),
                            ('activity_type_id', '=', record.activity_type_id.id),
                            ('user_id', '=', record.activity_user_id.id),
                        ], limit=1)

                    # Log para verificar la actividad relacionada encontrada
                    print(f"Related activity found: {related_activity.id if related_activity else 'None'}")

                    if related_activity:
                        # Preparar valores para actualizar la actividad real
                        activity_update_vals = {}

                        if 'summary' in vals:
                            activity_update_vals['summary'] = record.summary
                        if 'description' in vals:
                            activity_update_vals['note'] = record.description or ''
                        if 'activity_type_id' in vals:
                            activity_update_vals['activity_type_id'] = record.activity_type_id.id
                        if 'activity_user_id' in vals:
                            activity_update_vals['user_id'] = record.activity_user_id.id
                        if 'date_deadline' in vals:
                            activity_update_vals['date_deadline'] = record.date_deadline

                        # Actualizar la actividad real
                        if activity_update_vals:
                            try:
                                related_activity.write(activity_update_vals)
                            except Exception as e:
                                # Log del error para debugging
                                import logging
                                _logger = logging.getLogger(__name__)
                                _logger.warning(f"Error actualizando actividad {related_activity.id}: {e}")

        return result
