# -*- coding: utf-8 -*-
{
    'name': "Report Advanced LOILV",

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
            'forlife_report_advanced/static/src/xml/**/*',
            'forlife_report_advanced/static/src/css/**/*',
            'forlife_report_advanced/static/src/js/**/*',

        ]
    }
}
