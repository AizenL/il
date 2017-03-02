# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

import pytz
from openerp import SUPERUSER_ID, workflow
from datetime import datetime
from dateutil.relativedelta import relativedelta
from operator import attrgetter
from openerp.tools.safe_eval import safe_eval as eval
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.osv.orm import browse_record_list, browse_record, browse_null
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP
from openerp.tools.float_utils import float_compare


class purchase_order(osv.osv):
    _inherit = 'purchase.order'

    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('purchase.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()

    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        cur_obj=self.pool.get('res.currency')
        line_obj = self.pool['purchase.order.line']
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
                'other_charges': 0.0,
            }
            val = val1 = 0.0
            packing = freight = insurance = other_charges = 0.00
            cur = order.pricelist_id.currency_id
            for line in order.order_line:
                val1 += line.price_subtotal
                packing += line.pandf_value
                freight += line.freight_value
                insurance += line.insurance_value

                other_charges = packing + freight + insurance

                line_price = line_obj._calc_line_base_price(cr, uid, line,
                                                            context=context)
                line_qty = line_obj._calc_line_quantity(cr, uid, line,
                                                        context=context)
                for c in self.pool['account.tax'].compute_all(
                        cr, uid, line.taxes_id, line_price, line_qty,
                        line.product_id, order.partner_id)['taxes']:
                    val += c.get('amount', 0.0)
            res[order.id]['amount_tax']=cur_obj.round(cr, uid, cur, val)
            res[order.id]['amount_untaxed']=cur_obj.round(cr, uid, cur, val1)
            res[order.id]['other_charges'] = cur_obj.round(cr, uid, cur, other_charges)
            res[order.id]['amount_total']=res[order.id]['amount_untaxed'] + res[order.id]['amount_tax'] + res[order.id]['other_charges']
        return res

    _columns = {
    'amount_untaxed': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Untaxed Amount',
            store={
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums", help="The amount without tax", track_visibility='always'),
    'amount_tax': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Taxes',
        store={
            'purchase.order.line': (_get_order, None, 10),
        }, multi="sums", help="The tax amount"),
    'amount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total',
        store={
            'purchase.order.line': (_get_order, None, 10),
        }, multi="sums", help="The total amount"),
    'other_charges': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Other Charges',
        store={
            'purchase.order.line': (_get_order, None, 10),
        }, multi="sums", help="Other Charges"),
    
	}
purchase_order()



class purchase_order_line(osv.osv):
    _inherit = 'purchase.order.line'
    _columns = {
    'pandf_value' : fields.float(string = 'P/F Charges', copy = False),
    'freight_value' : fields.float(string = 'Freight Charges', copy = False),
    'insurance_value' : fields.float(string = 'Insurance Charges',copy = False),
    'excise_value' : fields.float(string = 'Excise Charges',copy = False),
    'vat_value' : fields.float(string = 'VAT Charges',copy = False),
    }
    
purchase_order_line()



class sale_order(osv.osv):
    _inherit = 'sale.order'

    def _amount_all_wrapper(self, cr, uid, ids, field_name, arg, context=None):
        """ Wrapper because of direct method passing as parameter for function fields """
        return self._amount_all(cr, uid, ids, field_name, arg, context=context)

    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
                'other_charges': 0.0,
            }
            val = val1 = 0.0
            packing = freight = insurance = other_charges =  0.00
            cur = order.pricelist_id.currency_id
            for line in order.order_line:
                val1 += line.price_subtotal
                packing += line.pandf_value
                freight += line.freight_value
                insurance += line.insurance_value
                # excise_amount +=

                other_charges = packing + freight + insurance               
                val += self._amount_line_tax(cr, uid, line, context=context)
            res[order.id]['amount_tax'] = cur_obj.round(cr, uid, cur, val)
            res[order.id]['amount_untaxed'] = cur_obj.round(cr, uid, cur, val1)
            res[order.id]['other_charges'] = cur_obj.round(cr, uid, cur, other_charges)
            res[order.id]['amount_total'] = res[order.id]['amount_untaxed'] + res[order.id]['amount_tax'] + res[order.id]['other_charges']
        return res

    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('sale.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()

    _columns = {
    'amount_untaxed': fields.function(_amount_all_wrapper, digits_compute=dp.get_precision('Account'), string='Untaxed Amount',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty','pandf_value','freight_value','insurance_value'], 10),
            },
            multi='sums', help="The amount without tax.", track_visibility='always'),
    'amount_tax': fields.function(_amount_all_wrapper, digits_compute=dp.get_precision('Account'), string='Taxes',
        store={
            'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
            'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty','pandf_value','freight_value','insurance_value'], 10),
        },
        multi='sums', help="The tax amount."),
    'amount_total': fields.function(_amount_all_wrapper, digits_compute=dp.get_precision('Account'), string='Total',
        store={
            'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
            'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty','pandf_value','freight_value','insurance_value'], 10),
        },
        multi='sums', help="The total amount."),
    'other_charges': fields.function(_amount_all_wrapper, digits_compute=dp.get_precision('Account'), string='Other Charges',
        store={
            'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
            'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty','pandf_value','freight_value','insurance_value'], 10),
        },
        multi='sums', help="Other additional Charges."),

    }
sale_order()

class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'
    _columns = {
    'pandf_value' : fields.float(string = 'P/F Charges',copy = False),
    'freight_value' : fields.float(string = 'Freight Charges',copy = False),
    'insurance_value' : fields.float(string = 'Insurance Charges',copy = False),
    'excise_amount' : fields.float(string= 'Excise Amount',copy = False),   
    }
        
sale_order_line()
