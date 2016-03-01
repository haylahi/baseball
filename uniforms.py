# -*- coding: utf-8 -*-
from datetime import timedelta
from openerp import models, fields, api, exceptions, tools
import urllib2
import xmltodict
from openerp.exceptions import ValidationError
from datetime import datetime

class JerseyItem(models.Model):
    _name = 'baseball.jerseysitem'

    size = fields.Many2one(
        'product.attribute.value',
        'Size',
    )
    color = fields.Many2one(
        'product.attribute.value',
        'Color',
    )
    number = fields.Integer(string="Number", required=True)
    state = fields.Selection([
        ('stock', "In Stock"),
        ('sold', "Sold"),
        ('sold_paid', "Sold and Paid"),
        ('rented', "Rented"),
        ('rented_paid', "Rented and paid"),
        ('lost', "Lost"),
        ('borrow', "Borrowed"),
    ], default='stock')
    time_rent = fields.Selection([
        (1, "1 year"),
        (2, "2 years"),
        (3, "3 years"),
    ])
    member_id = fields.Many2one('res.partner', string="Member")
    product_id = fields.Many2one('product.product', string="Related product", compute="_get_product", store=True)
    gender = fields.Selection(related="member_id.gender", string="Gender", readonly=True, store=True)
    team_ids  = fields.Many2many(
        related="member_id.team_ids", string="Teams", readonly=True, store=True)
    comment = fields.Text(string="Comments")
    season_id = fields.Many2one("baseball.season", string="Last active season", compute="_get_last_season", store=True)
    firstname = fields.Char(related="member_id.firstname", string="First name", readonly=True, store=True)
    lastname = fields.Char(related="member_id.lastname", string="Last name", readonly=True, store=True)


    @api.one
    @api.depends('color','size')
    def _get_product(self):
        if self.color and self.size:
            self.product_id = self.env['product.product'].search([('attribute_value_ids','in',self.color.id),('attribute_value_ids','in',self.size.id)])
        else:
            self.product_id = self.env['product.product']

    @api.one
    @api.depends('member_id.season_ids.season_id')
    def _get_last_season(self):
        season_ids = self.member_id.season_ids.mapped('season_id')
        if season_ids:
            self.season_id = season_ids[0]

class Product(models.Model):
    _inherit = 'product.product'

    jersey_ids = fields.Many2many("baseball.jerseysitem",string="Jerseys",compute="_get_jersey_ids")

    @api.one
    def _get_jersey_ids(self):
        self.jersey_ids = self.env['baseball.jerseysitem'].search([('product_id','=',self.id)])

class Product_template(models.Model):
    _inherit = 'product.template'

    jersey_ids = fields.Many2many("baseball.jerseysitem",string="Jerseys",compute="_get_jersey_ids")

    @api.one
    @api.depends('product_variant_ids.jersey_ids')
    def _get_jersey_ids(self):
        self.jersey_ids = self.product_variant_ids.mapped('jersey_ids')
