# -*- coding: utf-8 -*-
{
    'name': "baseball",
    'summary': """Baseball club management module""",
    'description': """

    """,
    'author': "Stanislas Sobieski",
    'website': "http://www.llnphoenix.be",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'website', 'calendar'],

    # always loaded
    'data': [
        'data/initial_values.xml',
        # 'data/delete.xml',
        'security/ir.model.access.csv',
        'views/menus.xml',
        'views/members.xml',
        'views/categories.xml',
        'views/teams.xml',
        'views/divisions.xml',
        'views/role.xml',
        'views/products.xml',
        'views/games.xml',
        'views/tournament.xml',
        'views/positions.xml',
        'views/venue.xml',
        'views/season.xml',
        'views/club.xml',
        'views/config.xml',
        'views/pages/layout.xml',
        'views/pages/homepage.xml',
    ],
}
