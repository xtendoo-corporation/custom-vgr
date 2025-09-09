{
    'name': 'VGR Price Calculator',
    'version': '17.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': 'Calculate product cost using formula',
    'description': """
        This module adds the ability to calculate product cost using a formula
        in the product category configuration.
    """,
    'author': 'Abraham Carrasco (Xtendoo)',
    'website': '',
    'depends': ['stock_account', 'sale'],
    'data': [
        'views/product_category_views.xml',
        'views/price_group_views.xml',
        'views/sale_views.xml',
        'views/price_template_item_views.xml',
        'views/view_tree_quotation_sale_with_project.xml',
        'wizards/views/price_calculator_wizard_views.xml',
        'wizards/views/price_calculator_encimera_wizard.xml',
        "security/ir.model.access.csv",
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
