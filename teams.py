# -*- coding: utf-8 -*-
from datetime import timedelta
from openerp import models, fields, api, exceptions, tools
import urllib2
import xmltodict
from openerp.exceptions import ValidationError
from datetime import datetime
import dateutil
import math
import pytz


class Teams(models.Model):
    _name = 'baseball.teams'
    _order = 'sequence'
    
    name = fields.Char(string="Name", required=True)
    name_from_federation = fields.Many2many('baseball.teams.dbname', string="Name on federation website", required=True)

    players_ids = fields.Many2many(
        'res.partner', string="Players", compute='_players_in_team')
    coaches_ids = fields.Many2many(
        'res.partner', string="Coaches", relation="team_coaches")
    responsible_ids = fields.Many2many(
        'res.partner', string="Manager", relation="team_responsibles")
    image = fields.Binary('Image')
    photo = fields.Binary('Photo')
    game_ids = fields.Many2many(
        'baseball.game', string="Games", compute="_compute_games")
    category_ids = fields.Many2many('baseball.categories', string="Categories")

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
    logo_id = fields.Many2one('baseball.logo', string="Logo")
    sequence = fields.Integer(string='Sequence')
    practices_ids = fields.Many2many(
        'baseball.teams.practice', string="Practices", relation="team_practices_rel")



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

class Divisions(models.Model):
    _name = 'baseball.divisions'

    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", required=True)
    description = fields.Html()
    team_ids = fields.Many2many('baseball.teams', string="Teams")
    average_duration = fields.Float(string="Average length")
    standings_ids = fields.Many2many('baseball.standings', string="Teams", compute="_compute_order_standing")
    parent_related_division_ids = fields.Many2many(
        comodel_name='baseball.divisions',
        column1="parent",
        column2="child", 
        relation="related_divisions", 
        string="Parent divisions")
    child_related_division_ids = fields.Many2many(
        comodel_name='baseball.divisions',
        column1="child",
        column2="parent", 
        relation="related_divisions", 
        string="Child divisions")

    @api.one
    def _compute_order_standing(self):
        standings = self.env['baseball.standings']
        for team in self.team_ids:
            standings += self.env['baseball.standings'].create({'team_id':team.id, 'division_id':self.id,})
        self.standings_ids=  standings.sorted(key=lambda r: r.result_average, reverse=True)

class Standings(models.TransientModel):
    _name = 'baseball.standings'

    team_id = fields.Many2one('baseball.teams', string="Team")
    division_id = fields.Many2one('baseball.divisions', string="Division")
    is_opponent = fields.Boolean(string='Opponent', related="team_id.is_opponent")

    result_games = fields.Float(string="G", compute="_compute_standing", digits=(4,0))
    result_wins = fields.Float(string="W", compute="_compute_standing", digits=(4,0))
    result_losses = fields.Float(string="L", compute="_compute_standing", digits=(4,0))
    result_ties = fields.Float(string="T", compute="_compute_standing", digits=(4,0))
    result_not_played = fields.Float(string="NP", compute="_compute_standing", digits=(4,0))
    result_forfeits = fields.Float(string="FF", compute="_compute_standing", digits=(4,0))
    result_average = fields.Float(string="AVG", compute="_compute_standing", digits=(4,3))


    @api.one
    def _compute_standing(self):
        if self.division_id.parent_related_division_ids:
            game_ids = self.team_id.game_ids.filtered(lambda r: (r.score_home or r.score_away) and (r.division.id == self.division_id.id or r.division.id in self.division_id.parent_related_division_ids.ids))
        else:
            game_ids = self.team_id.game_ids.filtered(lambda r: (r.score_home or r.score_away) and r.division.id == self.division_id.id)
        game_played = game_ids.filtered(lambda r: r.score_home.isdigit() and  r.score_away.isdigit())
        game_forfeited = game_ids.filtered(lambda r:  'ff' in r.score_home.lower() or 'ff' in r.score_away.lower())

        self.result_not_played = len(game_ids.filtered(lambda r: r.score_home == 'NP' and r.score_away == 'NP'))
        self.result_games = len(game_ids) - self.result_not_played
        self.result_wins = len(game_played.filtered(lambda r: ( (int(r.score_home) > int(r.score_away)) and r.home_team==self.team_id ) or ( (int(r.score_home) < int(r.score_away)) and r.away_team==self.team_id)) ) + len(game_ids.filtered(lambda r:  ('ff' in r.score_home.lower() and r.away_team==self.team_id) or ('ff' in r.score_away.lower() and r.home_team==self.team_id)) )
        self.result_losses = len(game_played.filtered(lambda r: ( (int(r.score_home) < int(r.score_away)) and r.home_team==self.team_id) or ((int(r.score_home) > int(r.score_away)) and r.away_team==self.team_id)) )
        self.result_ties = len(game_played.filtered(lambda r: int(r.score_home) == int(r.score_away)) )
        self.result_forfeits = len(game_ids.filtered(lambda r:  ('ff' in r.score_home.lower() and r.home_team==self.team_id) or ('ff' in r.score_away.lower() and r.away_team==self.team_id)) )

        self.result_average = self.result_wins/self.result_games if self.result_games else 0

class Teams_dbname(models.Model):
    _name = 'baseball.teams.dbname'
    
    name = fields.Char(string="Name", required=True)

class Logos(models.Model):
    _name = 'baseball.logo'

    name = fields.Char(string="Name", required=True)
    image = fields.Binary('Image')

class Practices(models.Model):
    _name = 'baseball.teams.practice'
    _order = "dayofweek, hour_from"

    dayofweek = fields.Selection([(0,'Monday'),(1,'Tuesday'),(2,'Wednesday'),(3,'Thursday'),(4,'Friday'),(5,'Saturday'),(6,'Sunday')], 'Day of Week', required=True, select=True)
    hour_from = fields.Float("Start")
    hour_to = fields.Float("End")
    team_ids = fields.Many2many(
        'baseball.teams', string="Teams", relation="team_practices_rel", domain="[('is_opponent','=',False)]")
    season = fields.Selection([('summer','Summer'),('winter','Winter')], default='summer')
    venue_id = fields.Many2one('baseball.venue', string="Venue")
    practice_event_ids = fields.One2many(
        'baseball.teams.practice.event', 'practice_id', string="Practices")

class Practices_serie(models.Model):
    _name = 'baseball.teams.practice.serie'

    practice_event_ids = fields.One2many(
        'baseball.teams.practice.event', 'serie_id', string="Practices")


class Practices_event(models.Model):
    _name = 'baseball.teams.practice.event'
    _order = "start_time, team_id"

    start_time = fields.Datetime(string="Start Time")
    end_time = fields.Datetime(string="End Time")
    team_id = fields.Many2one('baseball.teams', string="Team", domain="[('is_opponent','=',False)]")
    venue_id = fields.Many2one('baseball.venue', string="Venue")
    serie_id = fields.Many2one('baseball.teams.practice.serie', string="Serie", ondelete="cascade")
    practice_id = fields.Many2one('baseball.teams.practice', string="Practice", ondelete="cascade")


class Practice_wizard(models.TransientModel):
    _name = 'baseball.teams.practice.wizard'


    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)
    practice_id = fields.Many2one('baseball.teams.practice', string="Practice", required=True)



    @api.one
    def generate_practice(self):
        dates = dateutil.rrule.rrule(
            dateutil.rrule.MONTHLY,
            byweekday=self.practice_id.dayofweek, 
            byhour=int(math.floor(self.practice_id.hour_from)), 
            byminute=int(math.floor((self.practice_id.hour_from%1)*60)), 
            dtstart=fields.Date.from_string(self.start_date), 
            until=fields.Date.from_string(self.end_date))[:]
        dates = [pytz.timezone(self._context.get('tz')).localize(x, is_dst=None).astimezone(pytz.utc) for x in dates]

        for team in self.practice_id.team_ids:
            serie  = self.env['baseball.teams.practice.serie'].create({})
            self.practice_id.write({
                'practice_event_ids': [(0,0,{
                    'start_time': fields.Datetime.to_string(date),
                    'end_time': fields.Datetime.to_string(date + dateutil.relativedelta.relativedelta(hours=(self.practice_id.hour_to - self.practice_id.hour_from),) ),
                    'team_id': team.id,
                    'venue_id': self.practice_id.venue_id.id,
                    'serie_id': serie.id,
                }) for date in dates],
            })





