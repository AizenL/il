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


class procurement_group(osv.osv):
    _inherit = "procurement.group"

procurement_group()

# Sale Order Inherit for additional fields

class sales_order(osv.osv):
    _inherit = "sale.order"

    _columns = {
        'state': fields.selection([
            ('draft', 'Draft Quotation'),
            ('waiting_for_approval', 'Waiting For Approvals'),
            ('sent', 'Quotation Sent'),
            ('cancel', 'Cancelled'),
            ('waiting_date', 'Waiting Schedule'),
            ('amended','Amended'),
            ('progress', 'Sales Order'),
            ('manual', 'Sale to Invoice'),
            ('shipping_except', 'Shipping Exception'),
            ('invoice_except', 'Invoice Exception'),
            ('done', 'Done'),
            ], 'Status', readonly=True, copy=False, help="Gives the status of the quotation or sales order.\
              \nThe exception status is automatically set when a cancel operation occurs \
              in the invoice validation (Invoice Exception) or in the picking list process (Shipping Exception).\nThe 'Waiting Schedule' status is set when the invoice is confirmed\
               but waiting for the scheduler to run on the order date.", select=True),
        'amendment_no' : fields.integer('Amendment No', readonly=True, copy=False, help="Number of time the sale order as been amendment"),
        'date_amendment' : fields.datetime('Amendment Date', select=True, readonly=True, copy=False, help="Last amendment date and time will be capture"),
        'order_line': fields.one2many('sale.order.line', 'order_id', 'Order Lines', readonly=True, states={'draft': [('readonly', False)], 'amended': [('readonly', False)]}, copy=True),
    }

    _defaults={
        'amendment_no' : 0,
    }

#    # Amendment Button Function

    def action_button_amendment(self, cr, uid, ids, context=None):
        history_line = []
        picking_obj = self.pool.get('stock.picking')
        invoice_obj = self.pool.get('account.invoice')

        #compute the number of delivery orders to display
        pick_ids = []
        inv_ids = []
        for so in self.browse(cr, uid, ids, context=context):
            pick_ids += [picking.id for picking in so.picking_ids]
            inv_ids += [invoice.id for invoice in so.invoice_ids]
        for each_picking in pick_ids:
            picking_brow = picking_obj.browse(cr, uid, each_picking)
            if picking_brow.state in ('done'):
                raise osv.except_osv(_('Warning!'), _("The Picking in 'Done' state can not be amended"))
            for each_move in picking_brow.move_lines:
                if each_move.state in ('done'):
                    raise osv.except_osv(_('Warning!'), _("The Move in 'Done' state can not be amended"))
            if not picking_brow.state == 'cancel':
                raise osv.except_osv(_('Warning!'), _("You should first cancel all the picking generated for the sale order %s.")%(so.name))
        for each_inv in inv_ids:
            invoice_brow = invoice_obj.browse(cr, uid, each_inv, context)
            if not invoice_brow.state == 'cancel':
                raise osv.except_osv(_('Warning!'), _("The Invoice as been generated for the Sale order %s.")%(so.name))
        sale_bro = self.browse(cr, uid, ids, context)
        for line in sale_bro.order_line:
            self.pool.get('sale.order.line').write(cr, uid, [line.id], {'state':'draft'})
            if line.product_id.type != 'service':
                self.pool.get('procurement.order').unlink(cr, uid, [line.procurement_ids.id], context) # Unlink the Previous Procurment Id and re creating while Confirming the sales
        self.pool.get('procurement.group').unlink(cr, uid, sale_bro.procurement_group_id.id) # Unlink the Previous Procurment Group Id and re creating, while Confirming the sales
        sale_bro.delete_workflow() # Deleting the Previous Workflow Details 
        sale_bro.create_workflow()
        for line in sale_bro.order_line:
            lines = self.pool.get('sale.amendment.history.line').create(cr, uid,{
                    'name': line.name or '/',
                    'product_id': line.product_id.id or False,
                    'sequence': line.sequence or 0,
                    'price_unit': line.price_unit or 0.00,
                    'price_subtotal': line.price_subtotal or 0.00,
                    'tax_id': [(6, 0, [x.id for x in line.tax_id])] or False,
                    'product_uom_qty': line.product_uom_qty or 0.00,
                    'product_uom': line.product_uom.id or False,
                    'product_uos_qty': line.product_uos_qty or 0.00,
                    'product_uos': line.product_uos.id or False,
                    'discount': line.discount or 0.00,
                    'state': line.state,
                    })
            history_line.append(lines)
        history_create = self.pool.get('sale.amendment.history').create(cr, uid, {
                                    'name': sale_bro.name,
                                    'origin': sale_bro.origin,
                                    'client_order_ref': sale_bro.client_order_ref,
                                    'amendment_no' : sale_bro.amendment_no+1,
                                    'date_amendment' : time.strftime("%Y-%m-%d %H:%M:%S") or False,
                                    'date_order': sale_bro.date_order or False,
                                    'user_id': sale_bro.user_id.id or False,
                                    'partner_id': sale_bro.partner_id.id or False,
                                    'partner_invoice_id': sale_bro.partner_invoice_id.id or False,
                                    'partner_shipping_id': sale_bro.partner_shipping_id.id or False,
                                    'project_id': sale_bro.project_id.id or False,
                                    'history_line': [(6,0, history_line)],
                                    'note': sale_bro.note,
                                    'amount_untaxed': sale_bro.amount_untaxed or 0.00,
                                    'amount_tax': sale_bro.amount_tax or 0.00,
                                    'amount_total': sale_bro.amount_total or 0.00,
                                    'company_id': sale_bro.company_id.id or False,
                                    'pricelist_id': sale_bro.pricelist_id.id or False,
                                    'currency_id': sale_bro.currency_id.id or False,
        })
        self.write(cr, uid, [sale_bro.id], {'state': 'amended','amendment_no': sale_bro.amendment_no+1, 'date_amendment' : time.strftime("%Y-%m-%d %H:%M:%S")})
        return False

sales_order()

# Sale Order Amendment History Details

class sale_amendment_history(osv.osv):
    _name = "sale.amendment.history"
    _description = "Sale Order Amendment Details"

    _columns={
        'name': fields.char('Order Number', copy=False, select=True),
        'origin': fields.char('Source Document', copy=False),
        'client_order_ref': fields.char('Reference/Description', copy=False),
        'amendment_no' : fields.integer('Amendment No', copy=False),
        'date_amendment' : fields.datetime('Amendment Date', copy=False, help="Last revisied date and time will be capture"),
        'date_order': fields.date('Order Date', select=True, copy=False),
        'user_id': fields.many2one('res.users', 'Salesperson', select=True, copy=False),
        'partner_id': fields.many2one('res.partner', 'Customer', select=True, copy=False),
        'partner_invoice_id': fields.many2one('res.partner', 'Invoice Address', copy=False, help="Invoice address for current sales order."),
        'partner_shipping_id': fields.many2one('res.partner', 'Delivery Address', help="Delivery address for current sales order.", copy=False),
        'project_id': fields.many2one('account.analytic.account', 'Contract / Analytic', copy=False),
        'history_line': fields.one2many('sale.amendment.history.line', 'amendment_history_id', 'Order Lines', copy=False),
        'note': fields.text('Terms and conditions', copy=False),
        'amount_untaxed': fields.float('Untaxed Amount', help="The amount without tax.", copy=False),
        'amount_tax': fields.float('Taxes', help="The tax amount.", copy=False),
        'amount_total': fields.float('Total', help="The total amount.", copy=False),
        'company_id': fields.many2one('res.company', 'Company', copy=False),
        'pricelist_id': fields.many2one('product.pricelist', 'Pricelist', readonly=True, help="Pricelist for current sales order."),
        'currency_id': fields.related('pricelist_id', 'currency_id', type="many2one", relation="res.currency", string="Currency", readonly=True),
    }


sale_amendment_history()


# Sale Amendment History Details Line

class sale_amendment_history_line(osv.osv):
    _name = "sale.amendment.history.line"
    _description = "Sale Order Amendment Line Details"

    _columns = {
        'amendment_history_id': fields.many2one('sale.amendment.history', 'Order Reference', select=True, copy=False,),
        'name': fields.text('Description', copy=False),
        'sequence': fields.integer('Sequence', copy=False),
        'product_id': fields.many2one('product.product', 'Product', copy=False),
        'price_unit': fields.float('Unit Price', copy=False),
        'price_subtotal': fields.float('Subtotal', copy=False),
        'tax_id': fields.many2many('account.tax', 'sale_amendment_history_tax', 'history_line_id', 'tax_id', 'Taxes', copy=False),
        'product_uom_qty': fields.float('Quantity', copy=False),
        'product_uom': fields.many2one('product.uom', 'Unit of Measure ', copy=False),
        'product_uos_qty': fields.float('Quantity (UoS)', copy=False),
        'product_uos': fields.many2one('product.uom', 'Product UoS', copy=False),
        'discount': fields.float('Discount (%)', copy=False),
        'state': fields.selection([('cancel', 'Cancelled'),('draft', 'Draft'),('confirmed', 'Confirmed'),('exception', 'Exception'),('done', 'Done')], 'Status', copy=False),
    }

sale_amendment_history_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
