{
    'name': 'Control de Permisos de Creación',
    'version': '17.0.1.0.0',
    'category': 'Extra Rights',
    'summary': 'Controla permisos de usuario para crear clientes y productos',
    'description': """
        Este módulo añade campos booleanos a los usuarios que controlan si pueden
        crear clientes (partners) y productos.
    """,
    'author': 'VGR',
    'depends': ['base', 'product', 'sale'],
    'data': [
        'views/res_users_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'user_create_permissions/static/src/js/list_controller.js',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
