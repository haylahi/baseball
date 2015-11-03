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
        ('rented', "Rented"),
        ('lost', "Lost"),
    ], default='stock')
    member_id = fields.Many2one('res.partner', string="Member")
    product_id = fields.Many2one('product.product', string="Related product", compute="_get_product", store=True)

    @api.one
    @api.depends('color','size')
    def _get_product(self):
        if self.color and self.size:
            self.product_id = self.env['product.product'].search([('attribute_value_ids','in',self.color.id),('attribute_value_ids','in',self.size.id)])
        else:
            self.product_id = self.env['product.product']

class JerseySize(models.Model):
    _name = 'baseball.jerseys_size'
    name = fields.Char(string="Name")
    code = fields.Char(string="Code")


class CapSize(models.Model):
    _name = 'baseball.caps_size'
    code = fields.Char(string="Size")
    stock = fields.Integer(string="Stock")

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
