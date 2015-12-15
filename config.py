# -*- coding: utf-8 -*-


# from openerp.osv import osv, fields
# class baseball_config_settings(osv.TransientModel):
#     _inherit = 'base.config.settings'

#     _columns = {
#         'xml_frbbs_calendar': fields.char('Federation calendar (XML format)'),
#     }

#     def get_default_calendar(self, cr, uid, ids, context=None):
#         xml_frbbs_calendar = self.pool.get("ir.config_parameter").get_param(cr, uid, "xml_frbbs_calendar", default=None, context=context)
#         return {'xml_frbbs_calendar': xml_frbbs_calendar or False}

#     def set_calendar(self, cr, uid, ids, context=None):
#         config_parameters = self.pool.get("ir.config_parameter")
#         for record in self.browse(cr, uid, ids, context=context):
#             config_parameters.set_param(cr, uid, "xml_frbbs_calendar", record.xml_frbbs_calendar or '', context=context)


from openerp import api, fields, models, _


class BaseballConfigSettings(models.TransientModel):
    _inherit = 'base.config.settings'

    xml_frbbs_calendar = fields.Char(string='Federation calendar (XML format)',
        help="""URL to an XML file from the federation with access to games information""")

    @api.multi
    def get_default_calendar(self):
        xml_frbbs_calendar = self.env['ir.config_parameter'].get_param("xml_frbbs_calendar", default=None)
        return {'xml_frbbs_calendar': xml_frbbs_calendar or False}

    @api.multi
    def set_calendar(self):
        config_parameters = self.env['ir.config_parameter']
        for record in self:
            config_parameters.set_param("xml_frbbs_calendar", record.xml_frbbs_calendar)