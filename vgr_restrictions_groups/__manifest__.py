{
    'name': 'VGR Restricciones de Presupuestos',
    'version': '17.0.1.0.0',
    'category': 'Sales, stock, account',
    'author': 'Abraham (Xtendoo)',
    'website': 'https://xtendoo.es',
    'summary': 'Restricciones de presupuestos para productos y variantes',
    'description': """
        Este módulo restringe la creación de productos y variantes de producto
        a usuarios con permisos específicos. Si un usuario intenta crear un
        producto o variante sin los permisos adecuados, se lanzará un error
        de acceso.
    """,
    'license': 'LGPL-3',
    'depends': ['sale', 'stock', 'account'],
    'data': [
        'security/security.xml',
    ],
    'installable': True,
    'application': False,
}
