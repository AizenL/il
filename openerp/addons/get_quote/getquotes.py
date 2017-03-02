import logging

from openerp import models, fields

class get_your_quote(models.Model):
    _name = 'get.your.quote'
    
    identification = fields.Char(string='Identification')
    product_list= fields.One2many('quote.product.list', 'get_your_quote', string=" Product List")


class quote_product_list(models.Model):
    _name = 'quote.product.list'

    product_id = fields.Many2one('product.template',  string="Product id", )
    get_your_quote= fields.Many2one('get.your.quote',  string="QuoteId",ondelete='CASCADE')


    
