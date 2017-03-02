# -*- coding: utf-8 -*-

from openerp import models, fields, api

# class website_sale_search_extra(models.Model):
#     _name = 'website_sale_search_extra.website_sale_search_extra'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100