# -*- coding: utf-8 -*-
from datetime import timedelta
from openerp import models, fields, api, exceptions, tools
import urllib2
import xmltodict
from openerp.exceptions import ValidationError
from datetime import datetime


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
                    alternative_home = self.env['baseball.teams'].search([('name_from_federation', '=', ga['home'])])
                    alternative_home = alternative_home.filtered(lambda r: division in r.division_ids.mapped('parent_related_division_ids') | r.division_ids.mapped('parent_related_division_ids').mapped('child_related_division_ids') | r.division_ids.mapped('child_related_division_ids') )
                    if alternative_home: 
                        alternative_home.write({'division_ids': [(4, division.id)]})
                        home = alternative_home
                if not home:
                    home = self.env['baseball.teams'].create({'name_from_federation': ga['home'], 'name': ga[
                                                            'home'], 'division_ids': [(4, division.id)], 'is_opponent': True})

                away = self.env['baseball.teams'].search(
                    [('name_from_federation', '=', ga['away']), ('division_ids', 'in', division.id)])
                if not away:
                    alternative_away = self.env['baseball.teams'].search([('name_from_federation', '=', ga['away'])])
                    alternative_away = alternative_away.filtered(lambda r: division in r.division_ids.mapped('parent_related_division_ids') | r.division_ids.mapped('parent_related_division_ids').mapped('child_related_division_ids') | r.division_ids.mapped('child_related_division_ids') )
                    if alternative_away: 
                        alternative_away.write({'division_ids': [(4, division.id)]})
                        away = alternative_away
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



