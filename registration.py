# -*- coding: utf-8 -*-
from datetime import timedelta
from openerp import models, fields, api, exceptions, tools
import urllib2
import xmltodict
from openerp.exceptions import ValidationError
from datetime import datetime


class Season(models.Model):
    _name = 'baseball.season'

    name = fields.Char('Year')
    members_qty = fields.Integer('Members quantity', compute='_compute_members_qty')
    amount_left_to_collect = fields.Float('Amount to get', compute='_compute_to_collect')
    is_current = fields.Boolean('Current')
    certificate_id = fields.Many2one(
        'ir.attachment',
        'Certificate',
    )
    @api.constrains('is_current')
    def _check_current(self):
        if len(self.search([('is_current','=', True)]))> 1:
            raise ValidationError("Only one current season")

    @api.constrains('name')
    def _check_name(self):
        if len(self.search([('name','=', self.name)]))> 1:
            raise ValidationError("Field year must be unique")

    @api.one
    def _compute_members_qty(self):
        members_current_season = self.env['res.partner'].search([]).filtered(lambda r: self.id in r.season_ids.mapped('season_id').ids )
        self.members_qty = len(members_current_season)

    @api.one
    def _compute_to_collect(self):
        registration_ids = self.env['baseball.registration'].search([('season_id','=',self.id)])
        self.amount_left_to_collect = sum(registration_ids.mapped(lambda r: r.fee_to_pay - r.fee_paid))

    @api.model
    def get_current_season(self):
        current_id = self.env['baseball.season'].search([('is_current','=',True)])
        if not current_id:
            current_ids = self.env['baseball.season'].search([]).sorted(lambda r : r.name, reverse=True)
            if current_ids:
                current_id = current_ids[0]
                current_id.is_current = True
            else:
                current_id = self.env['baseball.season'].create({
                    'name': str(datetime.today().year),
                    'is_current': True,
                    })

        return current_id

class Registration(models.Model):
    _name = 'baseball.registration'

    season_id = fields.Many2one("baseball.season", string="Season")
    category_id = fields.Many2one("baseball.categories", string="Category")
    member_id = fields.Many2one("res.partner", string="Member")
    is_registered = fields.Boolean(default=False, string="Licensed")
    is_certificate = fields.Boolean(default=False, string="Certificate")
    fee_to_pay = fields.Float(string="Fee", compute='_compute_fee', inverse="_set_fee", store=True)
    fee_paid = fields.Float(string="Paid")

    @api.one
    @api.depends('category_id.cotisation', 'season_id')
    def _compute_fee(self):
        cotisation_id = self.env['baseball.fee'].search([('category_id','=',self.category_id.id),('season_id', '=', self.season_id.id)])
        if cotisation_id:
            self.fee_to_pay = cotisation_id.fee
        else:
            self.fee_to_pay = 0

    @api.one
    def _set_fee(self):
        return

class Fee(models.Model):
    _name = 'baseball.fee'

    fee = fields.Float(string="Fee")
    season_id = fields.Many2one("baseball.season", string="Season")
    category_id = fields.Many2one("baseball.categories", string="Category")
