# -*- coding: utf-8 -*-
from datetime import timedelta
from openerp import models, fields, api, exceptions, tools
import urllib2
import xmltodict
from openerp.exceptions import ValidationError
from datetime import datetime


class Members(models.Model):
    _inherit = 'res.partner'

    baseball_category_ids = fields.Many2many(
        'baseball.categories', string="Categories", compute='_players_in_categories')
    team_ids = fields.Many2many(
        'baseball.teams', string="Teams", relation="team_players")
    club_role_id = fields.Many2many('baseball.roles', string="Roles")
    is_in_order = fields.Boolean(readonly=True, string="Is in order", compute='_is_in_order')
    is_registered = fields.Boolean(readonly=True, string="Licenced", compute='_is_in_order')
    is_photo = fields.Boolean(
        default=False, string="Photo", compute='_check_photo')
    licence_number = fields.Char(string="Licence")
    jerseys_ids = fields.One2many(
        'baseball.jerseysitem', 'member_id', string="Jerseys")
    season_ids = fields.One2many(
        'baseball.registration', 'member_id', string="Seasons")
    present_games_ids = fields.Many2many(
        'baseball.game', string="Attended Games", relation="game_attend")
    absent_games_ids = fields.Many2many(
        'baseball.game', string="Missed Games", relation="game_absent")
    positions_ids = fields.Many2many('baseball.positions', string="Positions")
    personal_comments = fields.Html()
    private_comments = fields.Html()
    is_active_current_season = fields.Boolean('Active current season', default=False, compute='_is_active_this_season', store=True)
    is_certificate = fields.Boolean('Certificate', default=False, compute='_is_in_order')
    is_player = fields.Boolean('Player', default=True)
    game_ids = fields.Many2many(
        'baseball.game', string="Games", compute="_compute_games")

    @api.one
    @api.depends('team_ids')
    def _players_in_categories(self):
        ids = []
        for team_id in self.team_ids:
            ids += self.env['baseball.categories'].search(
                [('teams_ids', 'in', team_id.id)]).ids
        self.baseball_category_ids = ids

    @api.one
    @api.depends('image')
    def _check_photo(self):
        if self.image:
            self.is_photo = True


    @api.one
    @api.depends('season_ids')
    def _is_active_this_season(self):
        if self.env['baseball.season'].get_current_season().id in self.season_ids.mapped('season_id').ids :
            self.is_active_current_season = True
    
    @api.one
    @api.depends('is_photo','season_ids')
    def _is_in_order(self):
        if self.env['baseball.season'].get_current_season().id in self.season_ids.mapped('season_id').ids :
            current_register = self.season_ids.filtered(lambda r: r.season_id == self.env['baseball.season'].get_current_season())
            self.is_certificate = current_register.is_certificate
            self.is_registered = current_register.is_registered
            self.is_in_order = all([self.is_photo,current_register.is_certificate, current_register.fee_to_pay <= current_register.fee_paid])

    @api.one
    def _compute_games(self):
        self.game_ids = self.team_ids.mapped('game_ids').sorted(key=lambda r: r.start_time)

    @api.onchange('baseball_category_ids')
    def recalculat_current_category(self):
        current_season = self.env['baseball.season'].get_current_season()
        current_registration_id = self.season_ids.filtered(lambda r: r.season_id == current_season)

        categories = self.baseball_category_ids.sorted(lambda r: r.cotisation, reverse=True)
        if categories:
            category = categories[0]

            if current_registration_id:
                current_registration_id.category_id = category
            else:
                new_registration = self.env['baseball.registration'].create({
                    'season_id': current_season.id,
                    'category_id': category.id
                    })
                self.season_ids += new_registration

class Positions(models.Model):
    _name = 'baseball.positions'
    name = fields.Char(string="Name")
    description = fields.Html()







