# -*- coding: utf-8 -*-
from datetime import timedelta
from openerp import models, fields, api, exceptions, tools
import urllib2
import xmltodict
from openerp.exceptions import ValidationError
from datetime import datetime


class Res_users(models.Model):
    _inherit = 'res.users'

    current_partner_id = fields.Many2one('res.partner', string="Current partner", default=lambda self: self.partner_id)
    child_partner_ids = fields.One2many('res.partner', 'parent_user_id', string="Current partner")


    @api.one
    def set_current_partner(self, partner_id):
        self.current_partner_id = partner_id