# -*- coding: utf-8 -*-
from datetime import timedelta
from openerp import models, fields, api, exceptions, tools
import urllib2
import xmltodict
from openerp.exceptions import ValidationError
from datetime import datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
import uuid
import pytz



class Venues(models.Model):
    _name = 'baseball.venue'

    name = fields.Char(string="Name")
    street = fields.Char(string="Street")
    street2 = fields.Char(string="Street2")
    zip_code = fields.Char(string="Zip")
    city = fields.Char(string="City")
    state_id = fields.Many2one("res.country.state", string="State")
    country_id = fields.Many2one("res.country", string="Country")

class Game(models.Model):
    _name = 'baseball.game'
    _order = "start_time"


    @api.model
    def _default_game_type(self):
        return self.env.context.get('game_type', 'competition')


    name = fields.Char(string="Name")
    game_number = fields.Char(required=True, string="Game number")
    division = fields.Many2one('baseball.divisions', string="Division")
    start_time = fields.Datetime(string="Start Time")
    start_date = fields.Char(string="Start Date", compute="_compute_end_time")
    start_hour = fields.Char(string="Start Hour", compute="_compute_end_time")
    end_time = fields.Datetime(string="End Time", compute="_compute_end_time")
    end_time_tournament = fields.Datetime(string="End Time")
    end_date_tournament = fields.Char(string="Start Date", compute="_compute_end_time_tournament")
    end_hour_tournament = fields.Char(string="Start Hour", compute="_compute_end_time_tournament")    
    home_team = fields.Many2one('baseball.teams', string="Home Team")
    away_team = fields.Many2one('baseball.teams', string="Away Team")
    score_home = fields.Char(string="Score Home")
    score_away = fields.Char(string="Score Away")
    scorer = fields.Many2one(
        'res.partner', string="Scorers", compute="_get_scorer", inverse="_set_official", store=True)
    umpires = fields.Many2one(
        'res.partner', string="Umpires", compute="_get_umpires", inverse="_set_official", store=True)
    present_players_ids = fields.Many2many(
        'res.partner', string="Attendees", relation="game_attend")
    absent_players_ids = fields.Many2many(
        'res.partner', string="Absentees", relation="game_absent")
    invitation_ids = fields.One2many(
        'baseball.game.invitation', 'game_id', string="Invitations")
    game_type = fields.Selection([
        ('competition', "Competition game"),
        ('friendly', "Friendly game"),
        ('tournament', "Tournament"),
    ], default=_default_game_type)
    venue = fields.Many2one('baseball.venue', string="Venue")
    is_opponent = fields.Boolean(string="Opponent", compute="_get_is_opponent", store=True)
    result = fields.Selection([
        ('home', "Home"),
        ('away', "Away"),
        ('tie', "Tie"),
        ('np', "Not played"),
    ], string="Result", compute="_compute_result")


    _sql_constraints = [
        ('game_number',
         'UNIQUE(game_number)',
         "The game number must be unique"),
    ]

    @api.one
    def _set_official(self):
        return

    @api.one
    @api.depends('home_team.is_opponent', 'away_team.is_opponent')
    def _get_is_opponent(self):
        self.is_opponent = self.home_team.is_opponent and self.away_team.is_opponent

    @api.one
    @api.depends('score_away', 'score_home')
    def _compute_result(self):
        if self.score_home:
            if  self.score_home.isdigit() and self.score_away.isdigit():
                if int(self.score_home) > int(self.score_away):
                    self.result = 'home'
                elif int(self.score_home) < int(self.score_away):
                    self.result = 'away'
                elif int(self.score_home) == int(self.score_away):
                    self.result = 'tie'
                else:
                    self.result = 'np'
            else:
                if 'ff' in self.score_home.lower():
                    self.result = 'away'
                elif 'ff' in self.score_away.lower():
                    self.result = 'home'
                else:
                    self.result = 'np'
        else: 
            self.result = 'np'

    @api.one
    @api.depends('home_team.is_official_umpires', 'away_team.is_official_umpires', 'game_type')
    def _get_umpires(self):
        if (self.home_team.is_official_umpires or self.away_team.is_official_umpires) and self.game_type == 'competition':
            self.umpires = self.env.ref('baseball.partner_frbbs_official')

    @api.one
    @api.depends('home_team.is_official_scorers', 'away_team.is_official_scorers', 'game_type')
    def _get_scorer(self):
        if (self.home_team.is_official_scorers or self.away_team.is_official_scorers) and self.game_type == 'competition':
            self.scorer = self.env.ref('baseball.partner_frbbs_official')
    
    @api.one
    @api.depends('start_time', 'division.average_duration')
    def _compute_end_time(self):
        if not self.division.average_duration:
            duration = timedelta(hours=1)
        else:
            duration = timedelta(hours=self.division.average_duration)
        if self.start_time:
            start = fields.Datetime.from_string(self.start_time)
            self.end_time = start + duration

            self.start_date = start.strftime("%d/%m/%Y")
            self.start_hour = start.strftime("%H:%M")

    @api.one
    @api.depends('end_time_tournament')
    def _compute_end_time_tournament(self):
        if self.end_time_tournament:
            end = fields.Datetime.from_string(self.end_time_tournament)
            self.end_date_tournament = end.strftime("%d/%m/%Y")
            self.end_hour_tournament = end.strftime("%H:%M")


    @api.model
    def _get_upcoming_games(self, limit=None):
        today = datetime.strftime(datetime.today(),DEFAULT_SERVER_DATE_FORMAT)
        return self.search([('start_time','>=',today), '|', ('home_team.is_opponent','=',False), ('away_team.is_opponent','=',False)], limit=limit)

    @api.multi
    @api.depends('game_number', 'home_team', 'away_team')
    def name_get(self):
        result = []
        for game in self:
            result.append(
                (game.id, '[%s] %s @ %s' % (game.game_number, game.away_team.name, game.home_team.name)))
        return result

    @api.one
    def invite_team(self):
        team = (self.home_team + self.away_team).filtered(lambda r: not r.is_opponent)
        player_ids = team.players_ids.filtered(lambda r: r not in self.invitation_ids.mapped('partner_id') and r not in self.absent_players_ids and r not in self.present_players_ids)
        for player_id in player_ids:
            invite_id = self.env['baseball.game.invitation'].create({
                    'partner_id': player_id.id,
                    'game_id': self.id
                })
            invite_id._send_mail_to_attendees()

    @api.model
    def invite_upcoming(self, days=7):
        now = fields.Datetime.to_string(datetime.now())
        later = fields.Datetime.to_string(datetime.now()+timedelta(days=days))
        games = self.env['baseball.game'].search([('start_time','>',now),('start_time','<',later)])
        games = games.filtered(lambda r: not r.is_opponent)
        games.invite_team()


    @api.model
    def action_get_games_database(self):
        local = pytz.timezone ("Europe/Brussels")

        def get_or_create_team(team_name, division):
            tag_name = self.env['baseball.teams.dbname'].search([('name','=',team_name)])  
            if not tag_name:
                tag_name = self.env['baseball.teams.dbname'].create({'name': team_name})  
            tag_name = tag_name[0]

            team = self.env['baseball.teams'].search(
                [('division_ids', 'in', division.id)]).filtered(lambda r: tag_name in r.name_from_federation)
            if not team:
                alternative_team = self.env['baseball.teams'].search([]).filtered(lambda r: tag_name in r.name_from_federation)
                alternative_team = alternative_team.filtered(lambda r: division in r.division_ids.mapped('parent_related_division_ids') | r.division_ids.mapped('parent_related_division_ids').mapped('child_related_division_ids') | r.division_ids.mapped('child_related_division_ids') )
                if alternative_team: 
                    alternative_team.write({'division_ids': [(4, division.id)]})
                    team = alternative_team
            if not team:
                team = self.env['baseball.teams'].create({'name_from_federation': [(4,tag_name.id)], 'name': team_name, 'division_ids': [(4, division.id)], 'is_opponent': True})
            return team


        xml_frbbs_calendar = self.env['ir.config_parameter'].get_param('xml_frbbs_calendar')
        if not xml_frbbs_calendar:
            return
        # "http://www.frbbs.be/xmlGames.php?token=ed54@dAff5d!f6gDH%28T54sdF6-fJ5:9hvF!b"
        file = urllib2.urlopen(xml_frbbs_calendar)
        data = file.read()
        file.close()

        if not data:
            return
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

                home = get_or_create_team(ga['home'], division) 
                away = get_or_create_team(ga['away'], division) 

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

                local_dt = local.localize(fields.Datetime.from_string(values.get('start_time')), is_dst=None)
                values.update({'start_time': fields.Datetime.to_string(local_dt.astimezone(pytz.utc))})
                if current_game:
                    current_game.write(values)
                else:
                    current_game.create(values)

        for logo_id in self.env['baseball.logo'].search([]):
            teams_without_logo = self.env['baseball.teams'].search([('logo_id','=',False),('name_from_federation','ilike',logo_id.name)])
            teams_without_logo.write({'logo_id': logo_id.id})

# class Tournament(models.Model):
#     _name = 'baseball.tournament'
#     _inherit = 'calendar.event'

#     participating_team = fields.Many2one(
#         'baseball.teams', string="Club Participant")
#     organising_team = fields.Many2one('baseball.teams', string="Organiser")
#     away_team = fields.Many2one('baseball.teams', string="Away Team")


class Invitation(models.Model):
    _name = 'baseball.game.invitation'

    partner_id = fields.Many2one('res.partner', string="Player", required=True)
    game_id = fields.Many2one(
        'baseball.game', string="Game")
    state = fields.Selection([
        ('accepted', "Accepted"),
        ('declined', "Declined"),
    ], string="Answer")
    token = fields.Char('Token', readonly=True)
    is_sent = fields.Boolean('Is sent')


    @api.model
    def create(self, values):
        values['token'] = uuid.uuid4().hex
        return super(Invitation, self).create(values)
    
    @api.multi
    def write(self, vals):
        result = super(Invitation, self).write(vals)
        if vals.get('state') and result:
            for record in self:
                if record.state == 'accepted':
                    record.game_id.present_players_ids |= record.partner_id
                    record.game_id.absent_players_ids -= record.partner_id
                if record.state == 'declined':
                    record.game_id.present_players_ids -= record.partner_id
                    record.game_id.absent_players_ids |= record.partner_id
        return result

    @api.one
    def _send_mail_to_attendees(self, template_xmlid='baseball.mail_template_game_invitation'):
        template_id = self.env.ref(template_xmlid)
        mail_id = template_id.send_mail(self.id)
        self.is_sent = True
        return mail_id
