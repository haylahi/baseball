# -*- coding: utf-8 -*-
from datetime import timedelta
from openerp import models, fields, api, exceptions, tools
import urllib2
import xmltodict
from openerp.exceptions import ValidationError
from datetime import datetime


class Members(models.Model):
    _name = 'res.partner'
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

class Club(models.Model):
    _inherit = 'res.company'

    current_season_id = fields.Many2one('baseball.season', string="Current season", compute='_compute_current_season')

    @api.one
    def _compute_current_season(self):
        self.current_season_id = self.env['baseball.season'].get_current_season()

class Season(models.Model):
    _name = 'baseball.season'

    name = fields.Char('Year')
    members_qty = fields.Integer('Members quantity', compute='_compute_members_qty')
    amount_left_to_collect = fields.Float('Amount to get', compute='_compute_to_collect')
    is_current = fields.Boolean('Current')

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
        self.amount_left_to_collect = 0

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
    fee_to_pay = fields.Float(string="Fee", compute='_compute_fee')
    fee_paid = fields.Float(string="Paid")

    @api.one
    @api.depends('category_id', 'season_id')
    def _compute_fee(self):
        cotisation_id = self.env['baseball.fee'].search([('category_id','=',self.category_id.id),('season_id', '=', self.season_id.id)])
        if cotisation_id:
            self.fee_to_pay = cotisation_id.fee
        else:
            self.fee_to_pay = 0


class Categories(models.Model):
    _name = 'baseball.categories'

    name = fields.Char(string="Name", required=True)

    players_ids = fields.Many2many(
        'res.partner', string="Players", compute='_players_in_teams')
    description = fields.Html()
    teams_ids = fields.Many2many('baseball.teams', string="Teams")
    cotisation = fields.Float(string="Fee", compute='_compute_fee', inverse='_set_fee')
    start_date = fields.Date(string="Beginning")
    end_date = fields.Date(string="End")
    active = fields.Boolean(default=True)
    game_ids = fields.Many2many(
        'baseball.game', string="Games", compute="_compute_games")


    @api.one
    @api.depends('teams_ids')
    def _players_in_teams(self):
        players_ids = self.env['res.partner']
        for team_id in self.teams_ids:
             players_ids |= team_id.players_ids
        self.players_ids = players_ids

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

class Fee(models.Model):
    _name = 'baseball.fee'

    fee = fields.Float(string="Fee")
    season_id = fields.Many2one("baseball.season", string="Season")
    category_id = fields.Many2one("baseball.categories", string="Category")


class Teams(models.Model):
    _name = 'baseball.teams'

    name = fields.Char(string="Name", required=True)
    name_from_federation = fields.Char(
        string="Name on federation website", required=True)
    players_ids = fields.Many2many(
        'res.partner', string="Players", compute='_players_in_team')
    coaches_ids = fields.Many2many(
        'res.partner', string="Coaches", relation="team_coaches")
    responsible_ids = fields.Many2many(
        'res.partner', string="Manager", relation="team_responsibles")
    image = fields.Binary('Image')
    game_ids = fields.Many2many(
        'baseball.game', string="Games", compute="_compute_games")
    division_ids = fields.Many2many(
        'baseball.divisions', ondelete='set null', string="Divisions")
    is_official_umpires = fields.Boolean(
        default=False, string="Official Umpires")
    is_official_scorers = fields.Boolean(
        default=False, string="Official Scorers")
    is_opponent = fields.Boolean(default=False, string='Opponent')
    active = fields.Boolean(default=True)
    multiple_teams = fields.Boolean(default=False)
    subteams_ids = fields.Many2one('baseball.teams', string="Multiple teams")
    db_name = fields.Char(string="Database name")
    description = fields.Html()
    venue = fields.Many2one('baseball.venue', string="Venue")
    result_games = fields.Float(string="G", compute="_compute_standing", digits=(4,0))
    result_wins = fields.Float(string="W", compute="_compute_standing", digits=(4,0))
    result_losses = fields.Float(string="L", compute="_compute_standing", digits=(4,0))
    result_ties = fields.Float(string="T", compute="_compute_standing", digits=(4,0))
    result_not_played = fields.Float(string="NP", compute="_compute_standing", digits=(4,0))
    result_forfeits = fields.Float(string="FF", compute="_compute_standing", digits=(4,0))
    result_average = fields.Float(string="AVG", compute="_compute_standing", digits=(4,3))

    @api.multi
    @api.depends('division_ids', 'name')
    def name_get(self):
        result = []
        for team in self:

            result.append(
                (team.id, '%s (%s)' % (team.name, ','.join(team.division_ids.mapped('name')))))
        return result

    @api.one
    def _players_in_team(self):
        self.players_ids = self.env['res.partner'].search([('team_ids','in',self.id)]).filtered(lambda r: r.is_active_current_season and r.is_player)

    @api.one
    def _compute_games(self):
        self.game_ids = self.env['baseball.game'].search(['|', ('home_team','=',self.id),('away_team','=',self.id)]).sorted(key=lambda r: r.start_time)

    @api.one
    def _compute_standing(self):
        game_ids = self.game_ids.filtered(lambda r: r.score_home or r.score_away)
        game_played = game_ids.filtered(lambda r: r.score_home.isdigit() and  r.score_away.isdigit())
        game_forfeited = game_ids.filtered(lambda r:  'ff' in r.score_home.lower() or 'ff' in r.score_away.lower())

        self.result_not_played = len(game_ids.filtered(lambda r: r.score_home == 'NP' and r.score_away == 'NP'))
        self.result_games = len(game_ids) - self.result_not_played
        self.result_wins = len(game_played.filtered(lambda r: ( (int(r.score_home) > int(r.score_away)) and r.home_team==self ) or ( (int(r.score_home) < int(r.score_away)) and r.away_team==self)) ) + len(game_ids.filtered(lambda r:  ('ff' in r.score_home.lower() and r.away_team==self) or ('ff' in r.score_away.lower() and r.home_team==self)) )
        self.result_losses = len(game_played.filtered(lambda r: ( (int(r.score_home) < int(r.score_away)) and r.home_team==self) or ((int(r.score_home) > int(r.score_away)) and r.away_team==self)) )
        self.result_ties = len(game_played.filtered(lambda r: int(r.score_home) == int(r.score_away)) )
        self.result_forfeits = len(game_ids.filtered(lambda r:  ('ff' in r.score_home.lower() and r.home_team==self) or ('ff' in r.score_away.lower() and r.away_team==self)) )
        self.result_average = self.result_wins/self.result_games

class Venues(models.Model):
    _name = 'baseball.venue'

    name = fields.Char(string="Name")
    street = fields.Char(string="Street")
    street2 = fields.Char(string="Street2")
    zip_code = fields.Char(string="Zip")
    city = fields.Char(string="City")
    state_id = fields.Many2one("res.country.state", string="State")
    country_id = fields.Many2one("res.country", string="Country")


class Positions(models.Model):
    _name = 'baseball.positions'
    name = fields.Char(string="Name")
    description = fields.Html()


class SubTeams(models.Model):
    _inherit = 'baseball.teams'
    _name = 'baseball.subteams'


class Divisions(models.Model):
    _name = 'baseball.divisions'

    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", required=True)
    description = fields.Html()
    team_ids = fields.Many2many('baseball.teams', string="Teams", compute="_compute_order_standing")
    # related_division_ids = fields.Many2many('baseball.divisions', relation="related_divisions", string="Related divisions")

    @api.one
    def _compute_order_standing(self):
        self.team_ids = self.env['baseball.teams'].search([('division_ids', 'in', self.id)]).sorted(key=lambda r: r.result_average, reverse=True)

class Roles(models.Model):
    _name = 'baseball.roles'

    name = fields.Char(string="Title", required=True)
    description = fields.Html()


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


class Game(models.Model):
    _name = 'baseball.game'

    name = fields.Char(string="Name")

    game_number = fields.Char(required=True, string="Game number")
    division = fields.Many2one('baseball.divisions', string="Division")

    start_time = fields.Datetime(string="Start Time")
    end_time = fields.Datetime(string="End Time")

    home_team = fields.Many2one('baseball.teams', string="Home Team")
    away_team = fields.Many2one('baseball.teams', string="Away Team")
    score_home = fields.Char(string="Score Home")
    score_away = fields.Char(string="Score Away")

    scorer = fields.Many2one(
        'res.partner', string="Scorers", relation="game_scorer")
    umpires = fields.Many2many(
        'res.partner', string="Umpires", relation="game_umpire")
    present_players_ids = fields.Many2many(
        'res.partner', string="Attendees", relation="game_attend")
    absent_players_ids = fields.Many2many(
        'res.partner', string="Absentees", relation="game_absent")
    game_type = fields.Selection([
        ('competition', "Competition game"),
        ('friendly', "Friendly game"),
        ('tournament', "Tournament"),
    ])
    venue = fields.Many2one('baseball.venue', string="Venue")

    _sql_constraints = [
        ('game_number',
         'UNIQUE(game_number)',
         "The game number must be unique"),
    ]

    @api.multi
    def action_get_games_database(self):

        xml_frbbs_calendar = self.env['ir.config_parameter'].get_param('xml_frbbs_calendar')
        # "http://www.frbbs.be/xmlGames.php?token=ed54@dAff5d!f6gDH%28T54sdF6-fJ5:9hvF!b"
        file = urllib2.urlopen(xml_frbbs_calendar)
        data = file.read()
        file.close()

        data = xmltodict.parse(data)

        # games = []
        for k, v in data.items():
            for game in v['GameInfo']:
                ga = {}

                ga['game_number'] = game['game'].encode('utf-8')
                ga['division'] = game['division'].encode('utf-8')
                ga['date'] = game['date'].encode('utf-8')
                if ga['date'] == '0000-00-00':
                    continue
                ga['time'] = game['time'].encode('utf-8')
                ga['venue'] = game['field'].encode('utf-8')
                ga['home'] = game['home'].encode('utf-8')
                ga['away'] = game['away'].encode('utf-8')
                ga['score'] = game['score'].encode('utf-8')

                current_game = self.env['baseball.game'].search(
                    [('game_number', '=', ga['game_number'])])
                division = self.env['baseball.divisions'].search(
                    [('code', '=', ga['division'])])
                if not division:
                    division = self.env['baseball.divisions'].create(
                        {'name': ga['division'], 'code': ga['division']})

                home = self.env['baseball.teams'].search(
                    [('name_from_federation', '=', ga['home']), ('division_ids', 'in', division.id)])
                if not home:
                    home = self.env['baseball.teams'].create({'name_from_federation': ga['home'], 'name': ga[
                                                            'home'], 'division_ids': [(4, division.id)], 'is_opponent': True})

                away = self.env['baseball.teams'].search(
                    [('name_from_federation', '=', ga['away']), ('division_ids', 'in', division.id)])
                if not away:
                    away = self.env['baseball.teams'].create({'name_from_federation': ga['away'], 'name': ga[
                                                            'away'], 'division_ids': [(4, division.id)], 'is_opponent': True})

                venue = self.env['baseball.venue'].search(
                    [('name', 'ilike', ga['venue'])])
                if not venue:
                    venue = self.env['baseball.venue'].create(
                        {'name': ga['venue']})

                values = {
                    'game_number': ga['game_number'],
                    'division': division.id,
                    'start_time': (game['date'] + ' ' + game['time']).encode('utf-8'),
                    'home_team': home.id,
                    'away_team': away.id,
                    'venue': venue.id,
                    'game_type': 'competition',
                }
                if ga['score'] != 'null' and ga['score'] != 'NP':
                    values.update(
                        {'score_home':  (ga['score'].split('-')[0])}),
                    values.update(
                        {'score_away':  (ga['score'].split('-')[1])}),

                if current_game:
                    current_game.write(values)
                else:
                    current_game.create(values)


class Tournament(models.Model):
    _name = 'baseball.tournament'
    _inherit = 'calendar.event'

    participating_team = fields.Many2one(
        'baseball.teams', string="Club Participant")
    organising_team = fields.Many2one('baseball.teams', string="Organiser")
    away_team = fields.Many2one('baseball.teams', string="Away Team")



