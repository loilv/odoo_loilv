# -*- coding: utf-8 -*-
{
    'name': "Report Advanced",

    'summary': """Giúp tạo báo cáo thuận tiện hơn""",

    'description': """
    Ăn quả nhớ kẻ trồng cây ^^!
    """,

    'author': "LOILV",
    'website': "",
    "license": "LGPL-3",

    'category': 'Generic Modules',
    'version': '16.0.1.0.0',

    'depends': [
        'base',
        'web',
    ],

    'data': [
        'security/ir.model.access.csv',
        'views/report_setup.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'loilv_report_advanced/static/src/xml/**/*',
            'loilv_report_advanced/static/src/css/**/*',
            'loilv_report_advanced/static/src/js/**/*',

        ]
    }
}
