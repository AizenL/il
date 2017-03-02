# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013-Today OpenERP SA (<http://www.openerp.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import openerp
from openerp import tools

from openerp.osv import fields, osv
from openerp.tools.translate import _

import werkzeug
import pdb
from openerp import SUPERUSER_ID
from openerp import http
from openerp.http import request
from openerp import pooler


class website(osv.osv):
    _inherit = 'website'
    
   
    def is_product_in_cart(self, cr, uid, product_id, context=None):
        if isinstance(product_id, (list, tuple)):
            product_id = product_id[0]
        ses_order_recs = request.website.sale_get_order(force_create=1)
       
        product_uom_qty= 0.0
        if ses_order_recs:
            so_line_obj = self.pool.get('sale.quotation.order.line')
            so_line_ids = so_line_obj.search(cr, SUPERUSER_ID, [('order_id', '=', ses_order_recs.id), ('product_id', '=', product_id)], context=context)
            for so_line_id in so_line_ids:
                product_uom_qty += so_line_obj.browse(cr, SUPERUSER_ID, so_line_id, context=context).product_uom_qty
            return int(product_uom_qty)
        return int(product_uom_qty)
    
    def request_quote_qty(self, cr, uid, context=None):
        qpl_obj = self.pool.get('quote.product.list')
        get_quote_id = request.session.get('get_quote_id')
        #pdb.set_trace()
        if get_quote_id:
            checkDuplicateid = qpl_obj.search(cr, SUPERUSER_ID, [('get_your_quote', '=', get_quote_id)], context=context)
            lenth = len(checkDuplicateid)
        else:
            lenth = None
        #pdb.set_trace()
        return lenth 

website()


