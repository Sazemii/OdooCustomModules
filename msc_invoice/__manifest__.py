{
    'name': 'MSC Invoice Report',
    'version': '1.0.0',
    'category': 'Accounting',
    'summary': 'Custom invoice report with company branch information',
    'description': """
        Custom invoice report
    """,
    'author': 'Your Company',
    'license': 'LGPL-3',
    'depends': ['account', 'base'],
    'data': [
        'security/ir.model.access.csv',
        'views/company_view.xml',
        'views/account_move_views.xml',
        'views/report_sim_invoice.xml',
        'views/report_sis_invoice.xml',
        'data/report_actions.xml',
    ],
    'installable': True,
    'auto_install': False,
}
