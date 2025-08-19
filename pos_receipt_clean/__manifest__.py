{
    'name': 'Clean POS Receipt',
    'version': '1.0.0',
    'category': 'Point of Sale',
    'summary': 'Clean POS receipt format',
    'description': 'A sales invoice receipt modifier for POS customizations',
    'author': 'Your Company',
    'depends': ['point_of_sale'],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_receipt_clean/static/src/xml/receipt.xml',
        ],
    },
    'installable': True,
    'auto_install': False,
}
