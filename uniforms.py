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
