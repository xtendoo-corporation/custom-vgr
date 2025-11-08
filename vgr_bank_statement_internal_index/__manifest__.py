{
    'name': 'VGR Bank Statement Internal Index',
    'version': '17.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Show internal_index field in bank statement lines',
    'license': 'LGPL-3',
    'author': 'Xtendoo Software',
    'website': 'https://xtendoo.es',
    'depends': [
        'account',
        'account_statement_base',
    ],
    'data': [
        'data/server_actions.xml',
        'views/account_bank_statement_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
