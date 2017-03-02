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
from dateutil.relativedelta import relativedelta
import time

from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp import netsvc


class sale_order(osv.osv):
    _inherit = "sale.order"

######### Function to compute other charges split-ups in sale order ###########################
    def _compute_other_charges(self, cr, uid, ids, name, args, context=None):
        res = {}
        for obj in self.browse(cr, uid, ids, context=context):
            res[obj.id] = {
                'packing_charges': 0.0,
                'freight_charges': 0.0,
                'insurance_charges': 0.0,
            }
            packing_charges = freight_charges = insurance_charges = 0.00
            for line in obj.order_line:
                if line.pandf_value != 0.0:
                    packing_charges += line.pandf_value
                    res[obj.id]['packing_charges'] = packing_charges

                if line.freight_value != 0.0:
                    freight_charges += line.freight_value
                    res[obj.id]['freight_charges'] = freight_charges

                if line.insurance_value != 0.0:
                    insurance_charges += line.insurance_value
                    res[obj.id]['insurance_charges'] = insurance_charges
        return res

    def button_dummy(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        ctx = context.copy()
        ait_obj = self.pool.get('sale.tax.line')
        for id in ids:
            cr.execute("DELETE FROM sale_tax_line WHERE order_id=%s AND manual is False", (id,))
            partner = self.browse(cr, uid, id, context=ctx).partner_id
            if partner.lang:
                ctx.update({'lang': partner.lang})
            for taxe in ait_obj.compute(cr, uid, id, context=ctx).values():
                ait_obj.create(cr, uid, taxe)
        # Update the stored value (fields.function), so we write to trigger recompute
        self.pool.get('sale.order').write(cr, uid, ids, {'order_line':[]}, context=ctx)
        return True


    def button_compute(self, cr, uid, ids, context=None, set_total=False):
        self.button_dummy(cr, uid, ids, context)
        for sale in self.browse(cr, uid, ids, context=context):
            if set_total:
                self.pool.get('sale.order').write(cr, uid, [sale.id], {'amount_total': sale.amount_total})
        return True


    _columns = {
        'tax_line': fields.one2many('sale.tax.line', 'order_id', 'Tax Lines', readonly=True, states={'draft':[('readonly',False)]},copy=False),
        'packing_charges': fields.function(_compute_other_charges, method=True, string='Packing Charges', type='float', multi="all", readonly = False),
        'freight_charges': fields.function(_compute_other_charges, method=True, string='Freight', type='float', multi="all", readonly = False),
        'insurance_charges': fields.function(_compute_other_charges, method=True, string='Insurance', type='float', multi="all", readonly = False),
        }
    _defaults = {
        'packing_charges': 0.0,
        'freight_charges': 0.0,
        'insurance_charges': 0.0,
    }


sale_order()


class sale_order_line(osv.osv):
    _inherit = "sale.order.line"

    _columns = {
        'account_id': fields.many2one('account.account', 'Account',  domain=[('type','<>','view'), ('type', '<>', 'closed')], help="The income or expense account related to the selected product."),
        }

sale_order_line()

class sale_tax_line(osv.osv):
    _name = "sale.tax.line"
    _description = "Sales Tax"

    def _count_factor(self, cr, uid, ids, name, args, context=None):
        res = {}
        for sale_tax in self.browse(cr, uid, ids, context=context):
            res[sale_tax.id] = {
                'factor_base': 1.0,
                'factor_tax': 1.0,
            }
            if sale_tax.amount <> 0.0:
                factor_tax = sale_tax.tax_amount / sale_tax.amount
                res[sale_tax.id]['factor_tax'] = factor_tax

            if sale_tax.base <> 0.0:
                factor_base = sale_tax.base_amount / sale_tax.base
                res[sale_tax.id]['factor_base'] = factor_base
        return res

    _columns = {
        'order_id': fields.many2one('sale.order', 'Sale Order', ondelete='cascade', select=True),
        'name': fields.char('Tax Description', size=64, required=True),
        'account_id': fields.many2one('account.account', 'Tax Account', required=True, domain=[('type','<>','view'),('type','<>','income'), ('type', '<>', 'closed')]),
        'base': fields.float('Base', digits_compute=dp.get_precision('Account')),
        'amount': fields.float('Amount', digits_compute=dp.get_precision('Account')),
        'manual': fields.boolean('Manual'),
        'sequence': fields.integer('Sequence', help="Gives the sequence order when displaying a list of Sales tax."),
        'base_code_id': fields.many2one('account.tax.code', 'Base Code', help="The account basis of the tax declaration."),
        'base_amount': fields.float('Base Code Amount', digits_compute=dp.get_precision('Account')),
        'tax_code_id': fields.many2one('account.tax.code', 'Tax Code', help="The tax basis of the tax declaration."),
        'tax_amount': fields.float('Tax Code Amount', digits_compute=dp.get_precision('Account')),
        'company_id': fields.related('company_id', type='many2one', relation='res.company', string='Company', store=True, readonly=True),
        'factor_base': fields.function(_count_factor, method=True, string='Multipication factor for Base code', type='float', multi="all"),
        'factor_tax': fields.function(_count_factor, method=True, string='Multipication factor Tax code', type='float', multi="all")
    }


    _order = 'sequence'
    _defaults = {
        'manual': 1,
        'base_amount': 0.0,
        'tax_amount': 0.0,
    }


    def compute(self, cr, uid, order_id, context=None):
        tax_grouped = {}
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        sale = self.pool.get('sale.order').browse(cr, uid, order_id, context=context)
        cur = sale.currency_id
        company_currency = sale.company_id.currency_id.id
        for line in sale.order_line:            
            for tax in tax_obj.compute_all(cr, uid, line.tax_id, line.price_unit, line.product_uom_qty, sale.partner_invoice_id.id, line.product_id, sale.partner_id)['taxes']:
                val={}
                val['order_id'] = sale.id
                val['name'] = tax['name']
                val['amount'] = tax['amount']
                val['manual'] = False
                val['sequence'] = tax['sequence']
                val['base'] = tax['price_unit'] * line['product_uom_qty']
                val['base_code_id'] = tax['ref_base_code_id']
                val['tax_code_id'] = tax['ref_tax_code_id']
                val['base_amount'] = cur_obj.compute(cr, uid, sale.currency_id.id, company_currency, val['base'] * tax['ref_base_sign'], context={'date': sale.date_order or time.strftime('%Y-%m-%d')}, round=False)
                val['tax_amount'] = cur_obj.compute(cr, uid, sale.currency_id.id, company_currency, val['amount'] * tax['ref_tax_sign'], context={'date': sale.date_order or time.strftime('%Y-%m-%d')}, round=False)
                val['account_id'] = tax['account_paid_id']or line.account_id.id

                key = (val['tax_code_id'], val['base_code_id'], val['account_id'])
                if not key in tax_grouped:
                    tax_grouped[key] = val
                else:
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base'] += val['base']
                    tax_grouped[key]['base_amount'] += val['base_amount']
                    tax_grouped[key]['tax_amount'] += val['tax_amount']
        for t in tax_grouped.values():
            t['base'] =  t['base']
            t['amount'] = t['amount']
            t['base_amount'] = t['base_amount']
            t['tax_amount'] = t['tax_amount']
        return tax_grouped


    def move_line_get(self, cr, uid, order_id):
        res = []
        cr.execute('SELECT * FROM sale_tax_line WHERE order_id=%s', (order_id,))
        for t in cr.dictfetchall():
            if not t['amount'] \
                    and not t['tax_code_id'] \
                    and not t['tax_amount']:
                continue
            res.append({
                'type':'tax',
                'name':t['name'],
                'price_unit': t['amount'],
                'quantity': 1,
                'price': t['amount'] or 0.0,
                'account_id': t['account_id'],
                'tax_code_id': t['tax_code_id'],
                'tax_amount': t['tax_amount']
            })
        return res
sale_tax_line()
