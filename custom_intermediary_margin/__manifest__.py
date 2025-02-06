{
    'name': 'Custom Intermediary Margin',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Adds intermediary margin and PVP with intermediation to sale order lines',
    'author': 'Abraham (Xtendoo)',
    'depends': ['sale', 'mail', 'sale_margin'],
    'data': [
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
        "views/product_template_views.xml",
        # "report/sale_report_views.xml",
        # "views/account_move_views.xml",
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
