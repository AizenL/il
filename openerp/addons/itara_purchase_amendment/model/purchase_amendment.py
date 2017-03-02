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

from datetime import datetime, timedelta
import time
from openerp import SUPERUSER_ID
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
import openerp.addons.decimal_precision as dp
from openerp import workflow


# Purchase Order Amendment History Details

class purchase_amendment_history(osv.osv):
    _name = "purchase.amendment.history"
    _description = "Purchase Order Amendment Details"

    _columns={
        'name': fields.char('Order Reference', copy=False, select=True),
        'origin': fields.char('Source Document', copy=False),
        'amendment_no' : fields.integer('Amendment No', copy=False),
        'date_amendment' : fields.datetime('Amendment Date', copy=False, help="Last amended date and time will be capture"),
        'date_order': fields.date('Order Date', select=True, copy=False),
        'user_id': fields.many2one('res.users', 'Entered By', select=True, copy=False),
        'partner_id': fields.many2one('res.partner', 'Supplier', select=True, copy=False),
        'partner_ref': fields.char('Supplier Reference', select=True, copy=False),
        'history_line': fields.one2many('purchase.amendment.history.line', 'amendment_history_id', 'Order Lines', copy=False),
        'note': fields.text('Terms and conditions', copy=False),
        'amount_untaxed': fields.float('Untaxed Amount', help="The amount without tax.", copy=False),
        'amount_tax': fields.float('Taxes', help="The tax amount.", copy=False),
        'amount_total': fields.float('Total', help="The total amount.", copy=False),
        'company_id': fields.many2one('res.company', 'Company', copy=False),
        'payment_term_id': fields.many2one('account.payment.term', 'Payment Term', copy=False),
        'pricelist_id': fields.many2one('product.pricelist', 'Pricelist', readonly=True, help="Pricelist for current Purchase order."),
        'currency_id': fields.related('pricelist_id', 'currency_id', type="many2one", relation="res.currency", string="Currency", readonly=True),
    }


purchase_amendment_history()


# Purchase Amendment History Line Details

class purchase_amendment_history_line(osv.osv):
    _name = "purchase.amendment.history.line"
    _description = "Purchase Order Amendment Line Details"

    _columns = {
        'amendment_history_id': fields.many2one('purchase.amendment.history', 'Order Reference', select=True, copy=False,),
        'name': fields.text('Description', copy=False),
        'product_id': fields.many2one('product.product', 'Product', copy=False),
        'price_unit': fields.float('Unit Price', copy=False),
        'price_subtotal': fields.float('Subtotal', copy=False),
        'tax_id': fields.many2many('account.tax', 'purchase_amendment_history_tax', 'history_line_id', 'tax_id', 'Taxes', copy=False),
        'account_analytic_id':fields.many2one('account.analytic.account', 'Analytic Account', copy=False),
        'product_qty': fields.float('Quantity', copy=False),
        'product_uom': fields.many2one('product.uom', 'Unit of Measure ', copy=False),
        'state': fields.selection([('cancel', 'Cancelled'),('draft', 'Draft'),('confirmed', 'Confirmed'),('exception', 'Exception'),('done', 'Done')], 'Status', copy=False),
    }

purchase_amendment_history_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
