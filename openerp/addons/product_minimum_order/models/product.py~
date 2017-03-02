# -*- coding: utf-8 -*-
##############################################################################
#
##############################################################################
from openerp.osv import fields, osv


class product_product(osv.Model):

    _inherit = 'product.product'

    _columns = {

        'min_quantity':fields.float('Min Order Quantity', size=64),

        }

    _defaults = {
        'min_quantity': '0',
    }

product_product()
