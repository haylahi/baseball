# -*- coding: utf-8 -*-
from openerp import http
from openerp.http import request
from openerp import models, fields, api, exceptions, tools
from openerp.addons.auth_signup.controllers.main import AuthSignupHome
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime
from openerp.addons.website_blog.controllers.main import WebsiteBlog


DATE_FORMAT = "%d/%m/%Y"
TIME_FORMAT = "%H:%M"

class baseball_auth_signup(AuthSignupHome):

    @http.route('/web/signup', type='http', auth='public', website=True)
    def web_auth_signup(self, *args, **kw):
        res = super(baseball_auth_signup, self).web_auth_signup(*args, **kw)
        
        res.qcontext.update(self.signup_values())

        if 'error' not in res.qcontext and request.httprequest.method == 'POST':
            user_id = request.env['res.users'].sudo().search([('id','=',request.uid)])
            partner_id = user_id.partner_id
            self.update_partner(partner_id, **kw)

        return res

    @http.route('/web/update_profile', type='http', auth='public', website=True)
    def web_auth_update_profile(self, *args, **kw):
        qcontext = self.get_auth_signup_qcontext()

        if not qcontext.get('token') and not qcontext.get('signup_enabled'):
            raise werkzeug.exceptions.NotFound()

        if 'error' not in qcontext and request.httprequest.method == 'POST':
            user_id = request.env['res.users'].sudo().search([('id','=',request.uid)])
            partner_id = user_id.partner_id
            self.update_partner(partner_id, **kw)
        
        qcontext.update(self.signup_values())

        return request.render('auth_signup.update_profile', qcontext)


    def signup_values(self, data=None):
        env, uid, registry = request.env, request.uid, request.registry

        countries = env['res.country'].sudo().search([])
        partner_id = env['res.users'].sudo().browse(uid).partner_id
        categories = env['baseball.categories'].sudo().search([])
        teams = env['baseball.teams'].sudo().search([('is_opponent','=',False)])
        signup = {}

        # Default search by user country
        if not signup.get('country_id'):
            country_code = request.session['geoip'].get('country_code')
            if country_code:
                country_ids = registry.get('res.country').search([('code', '=', country_code)])
                if country_ids:
                    signup['country_id'] = country_ids[0]

        signup['email'] = partner_id.email
        signup['gender'] = partner_id.gender
        signup['name'] = partner_id.name if uid != env.ref('base.public_user').id else False
        signup['phone'] = partner_id.phone
        signup['mobile'] = partner_id.mobile
        signup['birthdate'] = partner_id.birthdate
        signup['street']  = partner_id.street
        signup['street2']  = partner_id.street2
        signup['city'] = partner_id.city
        signup['zip'] = partner_id.zip
        signup['country_id'] = partner_id.country_id
        signup['is_player'] = partner_id.is_player
        signup['baseball_category_ids'] = partner_id.baseball_category_ids.ids
        signup['team_ids'] = partner_id.team_ids.ids


        

        values = {
            'countries': countries,
            'categories': categories,
            'teams': teams,
            'signup': signup,
        }

        return values

    def update_partner(self, partner_id, **kw):
        current_season = request.env['baseball.season'].sudo().get_current_season()

        values = {
            'gender' :kw.get('gender'),
            'phone' :kw.get('phone'),
            'mobile' :kw.get('mobile'),
            'birthdate' :kw.get('birthdate'),
            'street' :kw.get('street'),
            'street2' :kw.get('street2'),
            'city' :kw.get('city'),
            'zip' :kw.get('zip'),
            'country_id' :kw.get('country_id'),
            'is_player' :kw.get('is_player') =='player',
            'team_ids' : [(6,0,[int(key.split('-')[1]) for key in kw if key.split('-')[0]=='team'])],
            # 'team_ids' : [(4,int(team),0) for team in kw.get('teams')],
            }

        photo = kw.get('photo')
        if photo and photo.filename and photo.content_type.split('/')[0] == 'image':
            values['image'] = photo.read().encode('base64')
        
        partner_id.write(values)
        partner_id.recalculat_current_category()

        registration_document = kw.get('registration_document')
        if registration_document and registration_document.filename and registration_document.content_type.split('/').pop() == 'pdf':
            attachment_value = {
                'name': registration_document.filename,
                'res_model': 'res.partner',
                'res_id': partner_id.id,
                'datas': registration_document.read().encode('base64'),
                'datas_fname': partner_id.name.lower().replace(' ', '_')  + current_season.name +'.pdf',
                }
            attachment = request.env['ir.attachment'].sudo().create(attachment_value)
            registration_id = partner_id.season_ids.filtered(lambda r: r.season_id == current_season)
            if registration_id:
                registration_id.is_certificate = True


class baseball_club(http.Controller):

    @http.route(['/page/teams/<int:team_id>'], type='http', auth="public", website=True)
    def team(self, team_id, **post):
        env, uid = request.env, request.uid
        team = env['baseball.teams'].sudo().browse(team_id)
        user = env['res.users'].sudo().browse(uid) if uid != env.ref('base.public_user').id else False
        values = {
            'team' : team,
            'user': user,
            'DATE_FORMAT' : DATE_FORMAT,
            'TIME_FORMAT': TIME_FORMAT,
            'DEFAULT_SERVER_DATETIME_FORMAT': DEFAULT_SERVER_DATETIME_FORMAT,
        }

        return request.render('baseball.team_page', values)

    @http.route(['/player'], type='json', auth="public", methods=['POST'], website=True)
    def modal_player(self, player_id, **kw):
        context, env = request.context, request.env

        website_context = kw.get('kwargs', {}).get('context', {})
        context = dict(context or {}, **website_context)

        player = env['res.partner'].sudo().browse(int(player_id))
        teams = env['baseball.teams'].sudo().search([('is_opponent','=',False)])
        is_coach =  player in teams.mapped('coaches_ids') 
        is_manager= player in teams.mapped('responsible_ids') 

        request.website = request.website.with_context(context)
        return request.website._render("baseball.modal_player", {
                'player': player,
                'player_image': player.image,
                'is_coach': is_coach, 
                'is_manager': is_manager,
            })


    @http.route(['/game'], type='json', auth="public", methods=['POST'], website=True)
    def modal_game(self, game_id, **kw):
        context, env, uid= request.context, request.env, request.uid
        website_context = kw.get('kwargs', {}).get('context', {})
        context = dict(context or {}, **website_context)

        game = env['baseball.game'].sudo().browse(int(game_id))
        request.website = request.website.with_context(context)

        user = env['res.users'].sudo().browse(uid) if uid != env.ref('base.public_user').id else False

        return request.website._render("baseball.modal_game", {
                'game': game,
                'user': user,
                'DATE_FORMAT' : DATE_FORMAT,
                'TIME_FORMAT': TIME_FORMAT,
                'DEFAULT_SERVER_DATETIME_FORMAT': DEFAULT_SERVER_DATETIME_FORMAT,                
            })


    @http.route(['/game/attend'], type='json', auth="public", methods=['POST'], website=True)
    def game_attend(self, game_id, **kw):
        env, uid = request.env, request.uid

        user_id = env['res.users'].sudo().browse(uid)
        game_id = env['baseball.game'].sudo().browse(int(game_id))

        game_id.present_players_ids |= user_id.partner_id 
        game_id.absent_players_ids -= user_id.partner_id 

        value = {'attending': True}  
        return value


    @http.route(['/game/absent'], type='json', auth="public", methods=['POST'], website=True)
    def game_absent(self, game_id, **kw):
        env, uid = request.env, request.uid

        user_id = env['res.users'].sudo().browse(uid)
        game_id = env['baseball.game'].sudo().browse(int(game_id))

        game_id.present_players_ids -= user_id.partner_id 
        game_id.absent_players_ids |= user_id.partner_id 

        value = {'attending': False}  
        return value

    @http.route(['/game/score'], type='json', auth="public", methods=['POST'], website=True)
    def game_score(self, game_id, **kw):
        env, uid = request.env, request.uid

        user_id = env['res.users'].sudo().browse(uid)
        game_id = env['baseball.game'].sudo().browse(int(game_id))
        game_id.scorer = user_id.partner_id 


        value = {
            'scoring': True,
            'scorer': user_id.partner_id.name,
            }  
        return value


    @http.route(['/game/umpire'], type='json', auth="public", methods=['POST'], website=True)
    def game_umpire(self, game_id, **kw):
        env, uid = request.env, request.uid

        user_id = env['res.users'].sudo().browse(uid)
        game_id = env['baseball.game'].sudo().browse(int(game_id))

        game_id.umpires = user_id.partner_id 

        value = {
            'umpiring': True,
            'umpire': user_id.partner_id.name,
        }  
        return value

    @http.route(['/page/upcoming_games'], type='http', auth="public", website=True)
    def upcoming_games(self, **kw):
        env, uid = request.env, request.uid
        games = env['baseball.game'].sudo()._get_upcoming_games()
        user = env['res.users'].sudo().browse(uid) if uid != env.ref('base.public_user').id else False
        values = {
            'games' : games,
            'user': user,
            'DATE_FORMAT' : DATE_FORMAT,
            'TIME_FORMAT': TIME_FORMAT,
            'DEFAULT_SERVER_DATETIME_FORMAT': DEFAULT_SERVER_DATETIME_FORMAT,
        }

        return request.render('baseball.upcoming_schedule', values)

    @http.route(['/profile'], type='http', auth="public", website=True)
    def get_profile(self, **kw):
        env, uid = request.env, request.uid
        if uid != env.ref('base.public_user').id:
            user = env['res.users'].sudo().browse(uid)
            values = {
                'user': user,
                'DATE_FORMAT' : DATE_FORMAT,
                'TIME_FORMAT': TIME_FORMAT,
                'DEFAULT_SERVER_DATETIME_FORMAT': DEFAULT_SERVER_DATETIME_FORMAT,
            }

            return request.render('baseball.profile', values)


class WebsiteBlog(WebsiteBlog):

    @http.route([
        """/blog/<model('blog.blog'):blog>/post/"""
        """<model('blog.post', '[("blog_id","=", "blog[0]")]'):blog_post>"""],
        type='http', auth="public", website=True)
    def blog_post(self, blog, blog_post,
                  tag_id=None, page=1, enable_editor=None, **post):
        response = super(WebsiteBlog, self).blog_post(
            blog, blog_post, tag_id=None, page=1, enable_editor=None, **post)
        response.qcontext['appId'] = request.website.facebook_appid
        response.qcontext['lang'] = request.context['lang']
        response.qcontext['numposts'] = request.website.facebook_numposts
        response.qcontext['base_url'] = request.httprequest.url
        return response
        