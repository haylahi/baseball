# -*- coding: utf-8 -*-
from datetime import timedelta
from openerp import models, fields, api, exceptions, tools
import urllib2
import xmltodict
from openerp.exceptions import ValidationError
from datetime import datetime


class Categories(models.Model):
    _name = 'baseball.categories'
    _order = 'sequence'

    name = fields.Char(string="Name", required=True)

    players_ids = fields.Many2many(
        'res.partner', string="Players", compute='_players_in_teams')
    description = fields.Html()
    teams_ids = fields.Many2many('baseball.teams', string="Teams")
    cotisation = fields.Float(string="Fee", compute='_compute_fee', inverse='_set_fee')
    start_date = fields.Integer(string="Beginning (year)")
    end_date = fields.Integer(string="End (year)")
    active = fields.Boolean(default=True)
    game_ids = fields.Many2many(
        'baseball.game', string="Games", compute="_compute_games")
    sequence = fields.Integer(string='Sequence')
    published = fields.Boolean('Published', default=True)

    @api.one
    @api.depends('teams_ids')
    def _players_in_teams(self):
        players_ids = self.env['res.partner']
        for team_id in self.teams_ids:
             players_ids |= team_id.players_ids

    @api.one
    def _set_fee(self):
        cotisation_id = self.env['baseball.fee'].search([('category_id','=',self.id),('season_id', '=', self.env['res.users'].browse(self._uid).company_id.current_season_id.id)])
        if cotisation_id:
            cotisation_id.fee =  self.cotisation
        else:
            self.env['baseball.fee'].create({
                'fee': self.cotisation,
                'season_id': self.env['baseball.season'].get_current_season().id,
                'category_id': self.id,
                })
        return

    @api.one
    def _compute_fee(self):
        cotisation_id = self.env['baseball.fee'].search([('category_id','=',self.id),('season_id', '=', self.env['baseball.season'].get_current_season().id)])
        if cotisation_id:
            self.cotisation = cotisation_id.fee
        else:
            self.cotisation = 0

    @api.one
    def _compute_games(self):
        self.game_ids = self.teams_ids.mapped('game_ids').sorted(key=lambda r: r.start_time)
