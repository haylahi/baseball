# -*- coding: utf-8 -*-
from datetime import timedelta
from openerp import models, fields, api, exceptions, tools
import urllib2
import xmltodict
from openerp.exceptions import ValidationError
from datetime import datetime


class Club(models.Model):
    _inherit = 'res.company'

    current_season_id = fields.Many2one('baseball.season', string="Current season", compute='_compute_current_season')

    @api.one
    def _compute_current_season(self):
        self.current_season_id = self.env['baseball.season'].get_current_season()


class Roles(models.Model):
    _name = 'baseball.roles'

    name = fields.Char(string="Title", required=True)
    description = fields.Html()
