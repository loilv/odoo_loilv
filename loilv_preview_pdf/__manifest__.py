{
    'name': 'Loilv PDF Preview',
    'version': '1.0',
    'category': 'Tools',
    'summary': 'Preview PDF using window.print without opening a new tab',
    'depends': ['web'],
    'author': "loilv",
    'website': "loilv.295@gmail.com",
    'data': [],
    'assets': {
        'web.assets_backend': [
            'loilv_preview_pdf/static/src/js/pdf_preview.js',
        ],
    },
    'installable': True,
    'application': False,
}