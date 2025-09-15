# -*- coding: utf-8 -*-
from odoo import http
from odoo.addons.sale.controllers.portal import CustomerPortal as SaleCustomerPortal
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
import base64


class SalePortalInherit(SaleCustomerPortal):

    @http.route(['/my/orders/<int:order_id>'], type='http', auth="public", website=True)
    def portal_order_page(self, order_id, report_type=None, access_token=None, message=False, download=False, **kw):
        """Override del método que muestra la página del pedido en el portal"""

        # Llamar al método padre para obtener la respuesta original
        response = super().portal_order_page(order_id, report_type, access_token, message, download, **kw)

        # Si es descarga o redirección, devolver tal como está
        if download or not hasattr(response, 'qcontext'):
            return response

        # Agregar datos adicionales al contexto existente
        if response.qcontext:
            # Buscar la variable correcta (puede ser 'order' o 'sale_order')
            order = response.qcontext.get('sale_order') or response.qcontext.get('order')

            if order:
                # Buscar archivos adjuntos del pedido
                order_attachments = request.env['ir.attachment'].sudo().search([
                    ('res_model', '=', 'sale.order'),
                    ('res_id', '=', order.id)
                ])

                # Agregar al contexto existente
                response.qcontext.update({
                    'order_attachments': order_attachments,
                    'has_attachments': bool(order_attachments),
                })

        return response

    @http.route(['/my/orders/<int:order_id>/attachment/<int:attachment_id>'],
                type='http', auth="public", methods=['GET'])
    def portal_order_attachment(self, order_id, attachment_id, access_token=None, **kw):
        """Ruta específica para manejar acceso a archivos adjuntos de pedidos"""
        try:
            # Verificar acceso al pedido
            order_sudo = self._document_check_access('sale.order', order_id, access_token)

            # Verificar que el attachment pertenece al pedido
            attachment = request.env['ir.attachment'].sudo().search([
                ('id', '=', attachment_id),
                ('res_model', '=', 'sale.order'),
                ('res_id', '=', order_id)
            ], limit=1)

            if not attachment:
                return request.render('vgr_portal.attachment_access_denied', {
                    'order': order_sudo,
                    'attachment_name': 'Archivo no encontrado'
                })

            # Verificar si hay pagos en las facturas asociadas
            if not order_sudo.has_paid_invoice:
                return request.render('vgr_portal.attachment_access_denied', {
                    'order': order_sudo,
                    'attachment_name': attachment.name
                })

            # Si hay pagos, permitir descarga usando el sistema nativo de Odoo
            if attachment.datas:
                # Decodificar el contenido del archivo
                file_content = base64.b64decode(attachment.datas)

                # Crear respuesta con el archivo
                response = request.make_response(
                    file_content,
                    headers=[
                        ('Content-Type', attachment.mimetype or 'application/octet-stream'),
                        ('Content-Disposition', f'attachment; filename="{attachment.name}"'),
                        ('Content-Length', len(file_content))
                    ]
                )
                return response
            else:
                return request.render('vgr_portal.attachment_access_denied', {
                    'order': order_sudo,
                    'attachment_name': attachment.name + ' (archivo vacío)'
                })

        except (AccessError, MissingError):
            return request.render('vgr_portal.attachment_access_denied', {
                'order': None,
                'attachment_name': 'Archivo'
            })
