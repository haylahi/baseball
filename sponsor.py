# -*- coding: utf-8 -*-
from datetime import timedelta
from openerp import models, fields, api, exceptions, tools
import urllib2
import xmltodict
from openerp.exceptions import ValidationError
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT


class Sponsoring(models.Model):
    _name = 'baseball.sponsoring'

    dossier_id = fields.Many2one(
        'ir.attachment',
        'Sponsor kit',
    )

    line_ids = fields.One2many(
        'baseball.sponsoring.line', compute="_get_sponsors", string="Lines")

    @api.one
    def _get_sponsors(self):
        line_ids = self.env['baseball.sponsor.line'].search([])
        season_ids = line_ids.mapped('season_id')
        for season_id in season_ids:
            lines = line_ids.filtered(lambda r: r.season_id == season_id)
            self.line_ids |= self.env['baseball.sponsoring.line'].create({
                'season_id': season_id.id,
                'sponsors': len(lines.mapped('sponsor_id')),
                'amount_paid': sum(lines.mapped('amount_paid')), 
                })


class Sponsor_line(models.TransientModel):
    _name = 'baseball.sponsoring.line'


    sponsors = fields.Integer(string="Sponsors")
    season_id = fields.Many2one('baseball.season', string="Season")
    amount_paid = fields.Float(string="Amount paid")

class Sponsor(models.Model):
    _name = 'baseball.sponsor'
    _order = 'sequence,name'

    name = fields.Char('Name', required=True,)
    image = fields.Binary(string='Logo')
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    url = fields.Char(string="URL")
    website_description = fields.Html(string="Description")
    notes = fields.Text(string="Notes")
    line_ids = fields.One2many(
        'baseball.sponsor.line', 'sponsor_id', string="Lines")
    sequence = fields.Integer('Sequence')

    @api.model
    def get_active_sponsors(self):
        today = datetime.strftime(datetime.today(),DEFAULT_SERVER_DATE_FORMAT)
        return self.search([('start_date','<=',today), ('end_date','>=',today)])

class Sponsor_line(models.Model):
    _name = 'baseball.sponsor.line'


    sponsor_id = fields.Many2one('baseball.sponsor', string="Sponsor")
    season_id = fields.Many2one('baseball.season', string="Season")
    amount_paid = fields.Float(string="Amount paid")
