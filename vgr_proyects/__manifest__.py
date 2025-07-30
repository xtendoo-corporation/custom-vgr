{
    'name': 'VGR Proyectos',
    'version': '17.0.1.0.0',
    'category': 'Project',
    'summary': 'Extensiones para el módulo de proyectos de VGR',
    'description': """
        Módulo para extender las funcionalidades del módulo de proyectos:
        - Añade campo Fecha de ejecución a las tareas
        - Añade campo Contacto relacionado a las tareas
    """,
    'author': 'Xtendoo (Abraham)',
    'website': '',
    'depends': [
        'project',
        'base',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/project_task_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
