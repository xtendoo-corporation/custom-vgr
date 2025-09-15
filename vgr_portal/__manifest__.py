# -*- coding: utf-8 -*-
{
    'name': 'VGR Portal',
    'version': '17.0.1.0.0',
    'category': 'Website/Website',
    'summary': 'Portal customizations for VGR',
    'description': """
VGR Portal
==========

This module provides portal customizations for VGR.
    """,
    'author': 'VGR',
    'website': '',
    'license': 'AGPL-3',
    'depends': [
        'project',
        'hr_timesheet',
        'portal',
        'sale',
        'account',
    ],
    'data': [
        'views/portal_templates.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
