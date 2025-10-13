{
    'name': 'VGR Bank Statement Internal Index',
    'version': '17.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Show internal_index field in bank statement lines',
    'depends': ['account', 'account_statement_base'],
    'data': [
        'views/account_bank_statement_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
