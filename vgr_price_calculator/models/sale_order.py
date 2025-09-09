from odoo import api, fields, models

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # meters_linear = fields.Float(
    #     string='M/L',
    #     help='Metros lineales'
    # )
    # price_group_id = fields.Many2one(
    #     'vgr.price.group',
    #     string='Grupo de precio'
    # )
    related_project_ids = fields.Many2many(
        'project.project',
        string='Proyectos',
        compute='_compute_related_projects',
        store=False,
    )

    @api.depends('analytic_account_id')
    def _compute_related_projects(self):
        for order in self:
            projects = self.env['project.project'].search([])
            related_projects = self.env['project.project']

            # Buscar por cuenta analítica directa
            if order.analytic_account_id:
                analytic_projects = self.env['project.project'].search([
                    ('analytic_account_id', '=', order.analytic_account_id.id)
                ])
                related_projects |= analytic_projects

            # Buscar proyectos que tengan este pedido como origen
            sale_projects = self.env['project.project'].search([
                ('sale_order_id', '=', order.id)
            ])
            related_projects |= sale_projects

            order.related_project_ids = related_projects
