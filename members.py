# -*- coding: utf-8 -*-
from datetime import timedelta
from openerp import models, fields, api, exceptions, tools
import urllib2
import xmltodict
from openerp.exceptions import ValidationError, Warning
from datetime import datetime
import werkzeug


class Members(models.Model):
    _inherit = 'res.partner'

    firstname = fields.Char('First name',)
    lastname = fields.Char('Last name',)
    name = fields.Char(
        compute="_compute_name",
        inverse="_inverse_name_after_cleaning_whitespace",
        required=False,
        store=True)
    baseball_category_ids = fields.Many2many(
        'baseball.categories', string="Categories", compute='_players_in_categories')
    team_ids = fields.Many2many(
        'baseball.teams', string="Teams", relation="team_players")
    club_role_id = fields.Many2many('baseball.roles', string="Roles")
    main_club_role_id = fields.Many2one('baseball.roles', string="Main Role", compute='_compute_main_role', store=True)
    is_in_order = fields.Boolean(readonly=True, string="Is in order", compute='_is_in_order', store=True)
    is_registered = fields.Boolean(readonly=True, string="Licenced", compute='_is_in_order', store=True)
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
    is_certificate = fields.Boolean('Certificate', default=False, compute='_is_in_order', store=True)
    is_player = fields.Boolean('Player', default=True)
    game_ids = fields.Many2many(
        'baseball.game', string="Games", compute="_compute_games")
    gender = fields.Selection([('male', 'Male'),('female', 'Female')], string="Gender")
    field_street = fields.Char('Field Street')
    field_city = fields.Char('Field City')
    field_zip = fields.Char('Field Zip')
    field_country_id = fields.Many2one('res.country', 'Field Country')
    debt = fields.Float(string="Debt", compute='_compute_debt', store=True)
    parent_user_id = fields.Many2one('res.partner', 'Parent member')
    child_partner_ids = fields.One2many('res.partner', 'parent_user_id', string="Child members")
    is_user = fields.Boolean('User', compute="_is_user")
    fee_to_pay = fields.Float(string="Season Fee", compute='_compute_fee', store=True)
    fee_paid = fields.Float(string="Season Paid", compute='_compute_fee', store=True)
    email2 = fields.Char(string="Email 2")
    mobile2 = fields.Char(string="Mobile 2")

    @api.model
    def create(self, vals):
        """Add inverted names at creation if unavailable."""
        context = dict(self.env.context)
        name = vals.get("name", context.get("default_name"))

        if name is not None:
            # Calculate the splitted fields
            inverted = self._get_inverse_name(
                self._get_whitespace_cleaned_name(name),
                vals.get("is_company",
                         self.default_get(["is_company"])["is_company"]))

            for key, value in inverted.iteritems():
                if not vals.get(key) or context.get("copy"):
                    vals[key] = value

            # Remove the combined fields
            if "name" in vals:
                del vals["name"]
            if "default_name" in context:
                del context["default_name"]

        return super(Members, self.with_context(context)).create(vals)

    @api.multi
    def copy(self, default=None):
        """Ensure partners are copied right.
        Odoo adds ``(copy)`` to the end of :attr:`~.name`, but that would get
        ignored in :meth:`~.create` because it also copies explicitly firstname
        and lastname fields.
        """
        return super(Members, self.with_context(copy=True)).copy(default)

    @api.model
    def default_get(self, fields_list):
        """Invert name when getting default values."""
        result = super(Members, self).default_get(fields_list)

        inverted = self._get_inverse_name(
            self._get_whitespace_cleaned_name(result.get("name", "")),
            result.get("is_company", False))

        for field in inverted.keys():
            if field in fields_list:
                result[field] = inverted.get(field)

        return result
        
    @api.model
    def _get_computed_name(self, lastname, firstname):
        return u" ".join((p for p in (firstname , lastname) if p))

    @api.one
    @api.depends("firstname", "lastname")
    def _compute_name(self):
        """Write the 'name' field according to splitted data."""
        self.name = self._get_computed_name(self.lastname, self.firstname)

    @api.one
    def _inverse_name_after_cleaning_whitespace(self):
        # Remove unneeded whitespace
        clean = self._get_whitespace_cleaned_name(self.name)

        # Clean name avoiding infinite recursion
        if self.name != clean:
            self.name = clean

        # Save name in the real fields
        else:
            self._inverse_name()

    @api.model
    def _get_whitespace_cleaned_name(self, name):
        return u" ".join(name.split(None)) if name else name

    @api.model
    def _get_inverse_name(self, name, is_company=False):
        """Compute the inverted name.
        - If the partner is a company, save it in the lastname.
        - Otherwise, make a guess.
        This method can be easily overriden by other submodules.
        You can also override this method to change the order of name's
        attributes
        When this method is called, :attr:`~.name` already has unified and
        trimmed whitespace.
        """
        # Company name goes to the lastname
        if is_company or not name:
            parts = [name or False, False]
        # Guess name splitting
        else:
            parts = name.strip().split(" ", 1)
            while len(parts) < 2:
                parts.append(False)
        return {"lastname": parts[1], "firstname": parts[0]}

    @api.one
    def _inverse_name(self):
        """Try to revert the effect of :meth:`._compute_name`."""
        parts = self._get_inverse_name(self.name, self.is_company)
        self.lastname, self.firstname = parts["lastname"], parts["firstname"]

    # @api.one
    # @api.constrains("firstname", "lastname")
    # def _check_name(self):
    #     """Ensure at least one name is set."""
    #     if ((self.type == 'contact' or self.is_company) and
    #             not (self.firstname or self.lastname)):
    #         raise exceptions.EmptyNamesError(self)

    @api.one
    @api.onchange("firstname", "lastname")
    def _onchange_subnames(self):
        """Avoid recursion when the user changes one of these fields.
        This forces to skip the :attr:`~.name` inversion when the user is
        setting it in a not-inverted way.
        """
        # Modify self's context without creating a new Environment.
        # See https://github.com/odoo/odoo/issues/7472#issuecomment-119503916.
        self.env.context = self.with_context(skip_onchange=True).env.context

    @api.one
    @api.onchange("name")
    def _onchange_name(self):
        """Ensure :attr:`~.name` is inverted in the UI."""
        if self.env.context.get("skip_onchange"):
            # Do not skip next onchange
            self.env.context = (
                self.with_context(skip_onchange=False).env.context)
        else:
            self._inverse_name_after_cleaning_whitespace()

    @api.model
    def _install_partner_firstname(self):
        """Save names correctly in the database.
        Before installing the module, field ``name`` contains all full names.
        When installing it, this method parses those names and saves them
        correctly into the database. This can be called later too if needed.
        """
        # Find records with empty firstname and lastname
        records = self.search([("firstname", "=", False),
                               ("lastname", "=", False)])

        # Force calculations there
        records._inverse_name()

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
    @api.depends('season_ids.season_id.is_current')
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
                old_registration = self.season_ids
                new_registration = self.env['baseball.registration'].create({
                    'season_id': current_season.id,
                    'category_id': category.id
                    })
                self.season_ids = old_registration | new_registration

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

    @api.one
    @api.depends('user_ids')
    def _is_user(self):
        self.is_user = True if self.user_ids else False


    @api.one
    @api.depends('season_ids.fee_paid', 'season_ids.fee_to_pay')
    def _compute_fee(self):
        for current_registration in self.season_ids.filtered(lambda r: r.season_id.is_current):
            self.fee_paid = current_registration.fee_paid
            self.fee_to_pay = current_registration.fee_to_pay


    @api.one
    def create_user(self):
        existing_user = self.env['res.users'].search([('login','=',self.email)])
        if existing_user and not self.user_ids:
            raise Warning('Cannot create user. A user with the same email address already exists! Either link the member to a parent member or change the email address.')
        if self.email and not self.user_ids:
            self.env['res.users'].create({
                'partner_id': self.id,
                'login': self.email,
                'groups_id': [(6,0, self.env.ref('base.group_portal').ids)],
                'active': True,
                })

    _sql_constraints = [(
        'check_name',
        "CHECK( 1=1 )",
        'Contacts require a name.'
    )]

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






