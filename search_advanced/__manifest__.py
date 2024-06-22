# -*- coding: utf-8 -*-
{
    'name': "Search Advanced",

    'summary': """
        Search easier with odoo
        """,

    'description': """
        Search easier with odoo
    """,

    'author': "Udu",
    'website': "loilv.295@gmail.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'App/',
    'sequence': 1,
    'version': '1.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'web'],

    # always loaded
    'data': [

    ],
    'assets': {
        'mail.assets_messaging': [
        ],
        'web.assets_backend': [
            'search_advanced/static/src/xml/search_advanced_view.xml',
            'search_advanced/static/src/js/search_advanced.js',
            # 'search_advanced/static/src/js/custom_width_tree.js',
            'search_advanced/static/src/js/custom_auto_complete.js',
            'search_advanced/static/src/css/search_advanced.scss',
        ],
        'web.assets_tests': [
        ],
        'web.qunit_suite_tests': [

        ],
    },
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
