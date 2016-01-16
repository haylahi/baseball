# -*- coding: utf-8 -*-
from datetime import timedelta
from openerp import models, fields, api, exceptions, tools
import urllib2
import xmltodict
from openerp.exceptions import ValidationError
from datetime import datetime
import werkzeug


class Members(models.Model):
    _inherit = 'res.partner'

    baseball_category_ids = fields.Many2many(
        'baseball.categories', string="Categories", compute='_players_in_categories')
    team_ids = fields.Many2many(
        'baseball.teams', string="Teams", relation="team_players")
    club_role_id = fields.Many2many('baseball.roles', string="Roles")
    main_club_role_id = fields.Many2one('baseball.roles', string="Main Role", compute='_compute_main_role', store=True)
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
    gender = fields.Selection([('male', 'Male'),('female', 'Female')], string="Gender")
    field_street = fields.Char('Field Street')
    field_city = fields.Char('Field City')
    field_zip = fields.Char('Field Zip')
    field_country_id = fields.Many2one('res.country', 'Field Country')
    debt = fields.Float(string="Debt", compute='_compute_debt', store=True)



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
        if self.env['baseball.season'].get_current_season() and self.env['baseball.season'].get_current_season().id in self.season_ids.mapped('season_id').ids :
            self.is_active_current_season = True
        else:
            self.is_active_current_season = False
    
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

    @api.one
    @api.depends('club_role_id')
    def _compute_main_role(self):
        if self.club_role_id:
            self.main_club_role_id = self.club_role_id[0]

    @api.one
    @api.depends('season_ids.fee_to_pay','season_ids.fee_paid')
    def _compute_debt(self):
        self.debt = round(sum(self.season_ids.mapped(lambda r: r.fee_to_pay - r.fee_paid)),2)

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

    @api.multi
    def google_map_img(self, zoom=8, width=298, height=298, field=False):
        if field:
            params = {
                'center': '%s, %s %s, %s' % (self.field_street or '', self.field_city or '', self.field_zip or '', self.field_country_id and self.field_country_id.name_get()[0][1] or ''),
                'size': "%sx%s" % (height, width),
                'zoom': zoom,
                'sensor': 'false',
            }
        else:
            params = {
                'center': '%s, %s %s, %s' % (self.street or '', self.city or '', self.zip or '', self.country_id and self.country_id.name_get()[0][1] or ''),
                'size': "%sx%s" % (height, width),
                'zoom': zoom,
                'sensor': 'false',
            }
        print urlplus('//maps.googleapis.com/maps/api/staticmap' , params)
        return urlplus('//maps.googleapis.com/maps/api/staticmap' , params)

    @api.multi
    def google_map_link(self, zoom=10, field=False):
        if field:
            params = {
                'q': '%s, %s %s, %s' % (self.field_street or '', self.field_city  or '', self.field_zip or '', self.field_country_id and self.field_country_id.name_get()[0][1] or ''),
                'z': zoom,
            }
        else:
            params = {
                'q': '%s, %s %s, %s' % (self.street or '', self.city  or '', self.zip or '', self.country_id and self.country_id.name_get()[0][1] or ''),
                'z': zoom,
            }
        print urlplus('https://maps.google.com/maps' , params)
        return urlplus('https://maps.google.com/maps' , params)

class Positions(models.Model):
    _name = 'baseball.positions'
    name = fields.Char(string="Name")
    code = fields.Char(string="Code")
    description = fields.Html()

def urlplus(url, params):
    return werkzeug.Href(url)(params or None)

class res_company(models.Model):
    _inherit = "res.company"

    def google_map_img(self, zoom=8, width=298, height=298, field=False):
        return self.sudo().partner_id and self.sudo().partner_id.google_map_img(zoom, width, height, field=field) or None
    def google_map_link(self, zoom=8, field=False):
        return self.sudo().partner_id and self.sudo().partner_id.google_map_link(zoom, field=field) or None






