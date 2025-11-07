{
    'name': 'VGR Proyectos',
    'version': '17.0.1.0.0',
    'category': 'Project',
    'summary': 'Extensiones para el módulo de proyectos de VGR',
    'description': """
        Módulo para extender las funcionalidades del módulo de proyectos:
        - Añade campo Fecha de ejecución a las tareas
        - Añade campo Contacto relacionado a las tareas
        - Plantillas de email automáticas
        - Portal personalizado con tracking de etapas
    """,
    'author': 'Xtendoo (Abraham)',
    'website': '',
    'depends': [
        'project',
        'base',
        'portal',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/mail_template_data.xml',
        'views/project_task_views.xml',
        'views/project_project_views.xml',
        'views/portal_templates.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
