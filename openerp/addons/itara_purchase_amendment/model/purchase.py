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


# Purchase Order Inherit for additional fields

class purchase_order(osv.osv):
    _inherit = "purchase.order"

    STATE_SELECTION = [
        ('draft', 'Draft PO'),
        ('waiting_for_approval', 'Waiting For Approvals'),
        ('sent', 'RFQ'),
        ('bid', 'Bid Received'),
        ('confirmed', 'Waiting Approval'),
        ('amended', 'Amended'),
        ('approved', 'Purchase Confirmed'),
        ('except_picking', 'Shipping Exception'),
        ('except_invoice', 'Invoice Exception'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ]

    _columns = {
        'state': fields.selection(STATE_SELECTION, 'Status', readonly=True,
                                  help="The status of the purchase order or the quotation request. "
                                       "A request for quotation is a purchase order in a 'Draft' status. "
                                       "Then the order has to be confirmed by the user, the status switch "
                                       "to 'Confirmed'. Then the supplier must confirm the order to change "
                                       "the status to 'Approved'. When the purchase order is paid and "
                                       "received, the status becomes 'Done'. If a cancel action occurs in "
                                       "the invoice or in the receipt of goods, the status becomes "
                                       "in exception.",
                                  select=True, copy=False),
        'amendment_no' : fields.integer('Amendment No', readonly=True, copy=False, help="Number of time the Purchase order as been amendment"),
        'date_amendment' : fields.datetime('Amendment Date', select=True, readonly=True, copy=False, help="Last amendment date and time will be capture"),
        'order_line': fields.one2many('purchase.order.line', 'order_id', 'Order Lines', readonly=True, states={'draft':[('readonly',False)], 'amended': [('readonly', False)]},copy=True),
    }

    _defaults={
        'amendment_no' : 0,
    }



#    # test_moves_done Function is inherited to check the state in done and also cancel

    def test_moves_done(self, cr, uid, ids, context=None):
        '''PO is done at the delivery side if all the incoming shipments are done'''
        picking_state = []
        for purchase in self.browse(cr, uid, ids, context=context):
            for picking in purchase.picking_ids:
                picking_state.append(picking.state)
            if 'done' not in picking_state:
                return False
        return True


#    # Amendment Button Function

    def action_button_amendment(self, cr, uid, ids, context=None):
        history_line = []
        picking_obj = self.pool.get('stock.picking')
        invoice_obj = self.pool.get('account.invoice')

        #compute the number of delivery orders to display
        pick_ids = []
        inv_ids = []
        for po in self.browse(cr, uid, ids, context=context):
            pick_ids += [picking.id for picking in po.picking_ids]
            inv_ids += [invoice.id for invoice in po.invoice_ids]
        for each_picking in pick_ids:
            picking_brow = picking_obj.browse(cr, uid, each_picking)
            if picking_brow.state in ('done'):
                raise osv.except_osv(_('Warning!'), _("The Picking in 'Done' state can not be amended."))
            for each_move in picking_brow.move_lines:
                if each_move.state in ('done'):
                    raise osv.except_osv(_('Warning!'), _("The Move in 'Done' state can not be amended."))
            if not picking_brow.state == 'cancel':
                raise osv.except_osv(_('Warning!'), _("You should first cancel all the picking generated for the Purchase order %s.")%(po.name))
        for each_inv in inv_ids:
            invoice_brow = invoice_obj.browse(cr, uid, each_inv, context)
            if not invoice_brow.state == 'cancel':
                raise osv.except_osv(_('Warning!'), _("The Invoice as been generated for the Purchase order %s.")%(po.name))
        purchase_bro = self.browse(cr, uid, ids, context)
        purchase_bro.delete_workflow() # Deleting the Previous Workflow Details 
        purchase_bro.create_workflow()
        for line in purchase_bro.order_line:
            lines = self.pool.get('purchase.amendment.history.line').create(cr, uid,{
                    'name': line.name or '/',
                    'product_id': line.product_id.id or False,
                    'price_unit': line.price_unit or 0.00,
                    'price_subtotal': line.price_subtotal or 0.00,
                    'tax_id': [(6, 0, [x.id for x in line.taxes_id])] or False,
                    'product_qty': line.product_qty or 0.00,
                    'account_analytic_id': line.account_analytic_id.id or False,
                    'product_uom': line.product_uom.id or False,
                    'state': line.state,
                    })
            history_line.append(lines)
        history_create = self.pool.get('purchase.amendment.history').create(cr, uid, {
                                    'name': purchase_bro.name,
                                    'origin': purchase_bro.origin,
                                    'amendment_no' : purchase_bro.amendment_no+1,
                                    'date_amendment' : time.strftime("%Y-%m-%d %H:%M:%S") or False,
                                    'date_order': purchase_bro.date_order or False,
                                    'user_id': uid or False,
                                    'partner_id': purchase_bro.partner_id.id or False,
                                    'partner_ref': purchase_bro.partner_ref or False,
                                    'history_line': [(6,0, history_line)],
                                    'note': purchase_bro.notes,
                                    'amount_untaxed': purchase_bro.amount_untaxed or 0.00,
                                    'amount_tax': purchase_bro.amount_tax or 0.00,
                                    'amount_total': purchase_bro.amount_total or 0.00,
                                    'company_id': purchase_bro.company_id.id or False,
                                    'pricelist_id': purchase_bro.pricelist_id.id or False,
                                    'currency_id': purchase_bro.currency_id.id or False,
                                    'payment_term_id': purchase_bro.payment_term_id.id or False,
                       })
        self.write(cr, uid, [purchase_bro.id], {'state': 'amended','amendment_no': purchase_bro.amendment_no+1, 'date_amendment': time.strftime("%Y-%m-%d %H:%M:%S")})
        return False


    # Received Invoice Functionally as been Inherited to list all the Invoice related to the PO

    def view_invoice(self, cr, uid, ids, context=None):
        '''
        This function returns an action that display existing invoices of given sales order ids. It can either be a in a list or in a form view, if there is only one invoice to show.
        '''
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')

        result = mod_obj.get_object_reference(cr, uid, 'account', 'action_invoice_tree2')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        inv_ids = []
        for po in self.browse(cr, uid, ids, context=context):
            inv_ids+= [invoice.id for invoice in po.invoice_ids]
        if not inv_ids:
            raise osv.except_osv(_('Error!'), _('Please create Invoices.'))
         #choose the view_mode accordingly
        if len(inv_ids)>1:
            result['domain'] = "[('id','in',["+','.join(map(str, inv_ids))+"])]"
        else:
            res = mod_obj.get_object_reference(cr, uid, 'account', 'invoice_supplier_form')
            result['views'] = [(res and res[1] or False, 'form')]
            result['res_id'] = inv_ids and inv_ids[0] or False
        return result


purchase_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
