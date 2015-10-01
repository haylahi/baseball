# -*- coding: utf-8 -*-
from datetime import timedelta
from openerp import models, fields, api, exceptions, tools
import urllib2
import xmltodict
from openerp.exceptions import ValidationError
from datetime import datetime

class ProductCategory(models.Model):
    _name = 'baseball.product'
    name = fields.Char(string="Name", required=True)
    image = fields.Char()
    price = fields.Float(string="Price")
    stock = fields.Integer(string="Stock")
    description = fields.Html()


class Cap(models.Model):
    _name = 'baseball.caps'
    _inherit = 'baseball.product'
    caps_size = fields.Many2many('baseball.caps_size', string="Caps")


class Jersey(models.Model):
    _name = 'baseball.jerseys'
    _inherit = 'baseball.product'
    jerseys_ids = fields.Many2many('baseball.jerseysitem', string="Size")


class JerseyItem(models.Model):
    _name = 'baseball.jerseysitem'

    color = fields.Selection(
        [('navy', 'Navy'), ('orange', 'Orange')], default="navy")
    size = fields.Selection([
        ('yS', "youth Small"),
        ('yM', "youth Medium"),
        ('yL', "youth Large"),
        ('S', "Small"),
        ('M', "Medium"),
        ('L', "Large"),
        ('XL', "X Large"),
        ('XXL', "XX Large"),
        ('XXXL', "XXX Large"),
    ])
    number = fields.Integer(string="Number", required=True)
    state = fields.Selection([
        ('stock', "In Stock"),
        ('sold', "Sold"),
        ('rented', "Rented"),
        ('lost', "Lost"),
    ], default='stock')
    member_id = fields.Many2one('res.partner', string="Member")


class JerseySize(models.Model):
    _name = 'baseball.jerseys_size'
    name = fields.Char(string="Name")
    code = fields.Char(string="Code")


class CapSize(models.Model):
    _name = 'baseball.caps_size'
    code = fields.Char(string="Size")
    stock = fields.Integer(string="Stock")

