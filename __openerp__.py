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
    'depends': ['base', 'website', 'calendar', 'auth_signup', 'document', 'website_blog', 'sale', 'stock'],

    # always loaded
    'data': [
        'data/partners.xml',
        'data/initial_values.xml',
        'data/menus.xml',
        'data/teams.xml',
        'data/delete.xml',
        'data/product.xml',
        'data/cron.xml',
        'data/mails.xml',
        'security/ir.model.access.csv',
        'views/menus.xml',
        'views/members.xml',
        'views/categories.xml',
        'views/teams.xml',
        'views/divisions.xml',
        'views/role.xml',
        'views/logos.xml',
        'views/products.xml',
        'views/games.xml',
        'views/tournament.xml',
        'views/positions.xml',
        'views/venue.xml',
        'views/season.xml',
        'views/club.xml',
        'views/config.xml',
        'views/facebook_settings_view.xml',
        'views/pages/layout.xml',
        'views/pages/homepage.xml',
        'views/pages/signup.xml',
        'views/pages/teams.xml',
        'views/pages/baseball.xml',
        'views/pages/club.xml',
        'views/pages/calendar.xml',
        'views/pages/blog.xml',
        'views/snippets.xml',
        'views/pages/snippets/test.xml',
        'views/pages/profile.xml',

    ],
}
