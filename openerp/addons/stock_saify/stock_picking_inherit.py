# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-today OpenERP SA (<http://www.openerp.com>)
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

from datetime import datetime, date
from lxml import etree
import time

from openerp import SUPERUSER_ID
from openerp import tools
from openerp.addons.resource.faces import task as Task
from openerp.osv import fields, osv
from openerp.tools import float_is_zero
from openerp.tools.translate import _
import pdb
from collections import OrderedDict
import datetime
from openerp.tools import amount_to_text_in
from openerp import api, _




class stock_picking_inherit(osv.osv):
    _inherit = "stock.move"
    _description = "stock move"
    _columns = {
        'state': fields.selection([('draft', 'New'),
                                   ('cancel', 'Cancelled'),
                                   ('waiting', 'Waiting Another Move'),
                                   ('confirmed', 'Waiting Availability'),
                                   ('assigned', 'Ready To Transfer'),
                                   ('done', 'Done'),
                                   ], 'Status', readonly=True, select=True, copy=False,
                                  help="* New: When the stock move is created and not yet confirmed.\n" \
                                       "* Waiting Another Move: This state can be seen when a move is waiting for another one, for example in a chained flow.\n" \
                                       "* Waiting Availability: This state is reached when the procurement resolution is not straight forward. It may need the scheduler to run, a component to me manufactured...\n" \
                                       "* Available: When products are reserved, it is set to \'Available\'.\n" \
                                       "* Done: When the shipment is processed, the state is \'Done\'."),
        'new_stock_id':fields.one2many('manufacturer','new_id','Manufacturer / Dealer Details'),
        'unit_price' : fields.float(string='Unit Price', store=True, related='procurement_id.sale_line_id.price_unit'),
        'sequence' : fields.integer('Sequence', help="Gives the sequence order when displaying a list of sales order lines.", default=99999),
        'il_part_no' : fields.related('product_id', 'default_code', type='char', relation='product.product', string='IL Part NO', store=True, readonly=True),

       
       
        
     }
class stock_warehouse(osv.osv):
    _inherit="stock.warehouse"
    def create_sequences_and_picking_types(self, cr, uid, warehouse, context=None):

        seq_obj = self.pool.get('ir.sequence')
        picking_type_obj = self.pool.get('stock.picking.type')
        #create new sequences
        in_seq_id = seq_obj.create(cr, SUPERUSER_ID, {'name': warehouse.name + _(' Sequence in'), 'prefix': warehouse.code + '/IN/'+'%(year)s'+'/3', 'padding': 5,'reset_required':1}, context=context)
        out_seq_id = seq_obj.create(cr, SUPERUSER_ID, {'name': warehouse.name + _(' Sequence out'), 'prefix': warehouse.code + '/OUT/'+'%(year)s'+'/4', 'padding': 5,'reset_required':1}, context=context)
        pack_seq_id = seq_obj.create(cr, SUPERUSER_ID, {'name': warehouse.name + _(' Sequence packing'), 'prefix': warehouse.code + '/PACK/', 'padding': 5}, context=context)
        pick_seq_id = seq_obj.create(cr, SUPERUSER_ID, {'name': warehouse.name + _(' Sequence picking'), 'prefix': warehouse.code + '/PICK/', 'padding': 5}, context=context)
        int_seq_id = seq_obj.create(cr, SUPERUSER_ID, {'name': warehouse.name + _(' Sequence internal'), 'prefix': warehouse.code + '/INT/', 'padding': 5}, context=context)

        wh_stock_loc = warehouse.lot_stock_id
        wh_input_stock_loc = warehouse.wh_input_stock_loc_id
        wh_output_stock_loc = warehouse.wh_output_stock_loc_id
        wh_pack_stock_loc = warehouse.wh_pack_stock_loc_id

        #fetch customer and supplier locations, for references
        customer_loc, supplier_loc = self._get_partner_locations(cr, uid, warehouse.id, context=context)

        #create in, out, internal picking types for warehouse
        input_loc = wh_input_stock_loc
        if warehouse.reception_steps == 'one_step':
            input_loc = wh_stock_loc
        output_loc = wh_output_stock_loc
        if warehouse.delivery_steps == 'ship_only':
            output_loc = wh_stock_loc

        #choose the next available color for the picking types of this warehouse
        color = 0
        available_colors = [c%9 for c in range(3, 12)]  # put flashy colors first
        all_used_colors = self.pool.get('stock.picking.type').search_read(cr, uid, [('warehouse_id', '!=', False), ('color', '!=', False)], ['color'], order='color')
        #don't use sets to preserve the list order
        for x in all_used_colors:
            if x['color'] in available_colors:
                available_colors.remove(x['color'])
        if available_colors:
            color = available_colors[0]

        #order the picking types with a sequence allowing to have the following suit for each warehouse: reception, internal, pick, pack, ship.
        max_sequence = self.pool.get('stock.picking.type').search_read(cr, uid, [], ['sequence'], order='sequence desc')
        max_sequence = max_sequence and max_sequence[0]['sequence'] or 0

        in_type_id = picking_type_obj.create(cr, uid, vals={
            'name': _('Receipts'),
            'warehouse_id': warehouse.id,
            'code': 'incoming',
            'sequence_id': in_seq_id,
            'default_location_src_id': supplier_loc.id,
            'default_location_dest_id': input_loc.id,
            'sequence': max_sequence + 1,
            'color': color}, context=context)
        out_type_id = picking_type_obj.create(cr, uid, vals={
            'name': _('Delivery Orders'),
            'warehouse_id': warehouse.id,
            'code': 'outgoing',
            'sequence_id': out_seq_id,
            'return_picking_type_id': in_type_id,
            'default_location_src_id': output_loc.id,
            'default_location_dest_id': customer_loc.id,
            'sequence': max_sequence + 4,
            'color': color}, context=context)
        picking_type_obj.write(cr, uid, [in_type_id], {'return_picking_type_id': out_type_id}, context=context)
        int_type_id = picking_type_obj.create(cr, uid, vals={
            'name': _('Internal Transfers'),
            'warehouse_id': warehouse.id,
            'code': 'internal',
            'sequence_id': int_seq_id,
            'default_location_src_id': wh_stock_loc.id,
            'default_location_dest_id': wh_stock_loc.id,
            'active': True,
            'sequence': max_sequence + 2,
            'color': color}, context=context)
        pack_type_id = picking_type_obj.create(cr, uid, vals={
            'name': _('Pack'),
            'warehouse_id': warehouse.id,
            'code': 'internal',
            'sequence_id': pack_seq_id,
            'default_location_src_id': wh_pack_stock_loc.id,
            'default_location_dest_id': output_loc.id,
            'active': warehouse.delivery_steps == 'pick_pack_ship',
            'sequence': max_sequence + 3,
            'color': color}, context=context)
        pick_type_id = picking_type_obj.create(cr, uid, vals={
            'name': _('Pick'),
            'warehouse_id': warehouse.id,
            'code': 'internal',
            'sequence_id': pick_seq_id,
            'default_location_src_id': wh_stock_loc.id,
            'default_location_dest_id': output_loc.id if warehouse.delivery_steps == 'pick_ship' else wh_pack_stock_loc.id,
            'active': warehouse.delivery_steps != 'ship_only',
            'sequence': max_sequence + 2,
            'color': color}, context=context)

        #write picking types on WH
        vals = {
            'in_type_id': in_type_id,
            'out_type_id': out_type_id,
            'pack_type_id': pack_type_id,
            'pick_type_id': pick_type_id,
            'int_type_id': int_type_id,
        }
        super(stock_warehouse, self).write(cr, uid, warehouse.id, vals=vals, context=context)


class stock_picking_inheritsss(osv.osv):
    _inherit = "stock.picking"
    _description = "stock picking"
    _columns = {
        'select_stage':fields.selection([('first', 'First Stage Dealer'), ('secon', 'Second Stage Dealer')],'Stage'),
	'return_voucher':fields.boolean('Is Return Voucher'),
        'referance':fields.char('Vendor Reference'),
        'sale_order_ref' : fields.related('sale_id','client_order_ref',type='char',readonly='True',string='Customer Reference',store=True),
        'internal_use':fields.boolean('Internal USe'),
       
     }

    _defualts = {
	'return_voucher':False,
    'internal_use':False,
		}

    def _get_period(self, cr, uid, context=None):
        periods = self.pool.get('account.period').find(cr, uid, context=context)
        if periods:
            return periods[0]
        return False


    @api.multi
    def internal_consumption(self):
        

        vals={}
        
        
        account_obj=self.env['account.account']
        #period_ids=_get_period
        account_move_obj = self.env['account.move']
        date_creation=self.date
        vals.update({'ref':'Internal Consumption','journal_id':5,'date':date_creation,'period_id':15,'state':'posted'})
        account_move_id = account_move_obj.create(vals)


        pack_operation_obj = self.pack_operation_ids
        for lot_line in pack_operation_obj:
            #pdb.set_trace()
            from_loc = self.picking_type_id.default_location_src_id.partner_id.state_id
            cust_loc = self.picking_type_id.default_location_src_id.partner_id.state_id
            product_name=lot_line.product_id
            categ=product_name.categ_id.id
            loc_tax_search = self.env['delivery.location.tax'].search([('name', '=', from_loc.id),('to_state', '=', cust_loc.id)])
            categ_tax_search = self.env['tax.category'].search([('tax_id', 'in', loc_tax_search.ids),('name', '=', categ)])

            if categ_tax_search:
                tax = self.env['tax.category'].browse(categ_tax_search.id).account_tax_input
                if tax:
                    tax_amount=tax.amount
                    tax_account=tax.account_collected_id
            

            
            

            picking_qty=lot_line.product_qty
            name_picking=self.name
            
            stock_count_obj = self.env['stock.quant']
            stock_move_obj=self.env['stock.move']
            lot_ids=stock_count_obj.search([('lot_id','=',lot_line.lot_id.id)])
            purchase_stock_move_id = stock_move_obj.search([('quant_ids', 'in', lot_ids.ids),('picking_id.picking_type_id', '=', 1),('picking_id.return_voucher', '=', False),])
            purchase_stock_move=purchase_stock_move_id[0]
            product_price=stock_move_obj.browse(purchase_stock_move.id).purchase_line_id.price_unit
            total_product_price=picking_qty*product_price
            tax_price_total=total_product_price*tax_amount
            total_product_price_with_tax=total_product_price+tax_price_total

            #journal_obj=self.env['account.invoice.line']
            #journal_obj_id=journal_obj.search([('lot_id','=',lot_ids[0])])

            # if lot_ids[0]:
            #     inventory_cost_price=lot_ids[0].qty*lot_ids[0].cost
            
            account_move_line_obj=self.env['account.move.line']
            
            
            
            

            #vals.update()
            res={}
            credit_line = {'name':name_picking,'debit':total_product_price_with_tax,'credit':0.0,'account_id':246,'move_id':account_move_id.id,}
            account_move_line_obj.create(credit_line)

            #product_name=lot_line.product_id
            purchase_account_id=product_name.categ_id.property_account_expense_categ
            debit_line = {'name':name_picking,'debit':0.0,'credit':total_product_price,'account_id':purchase_account_id.id,'move_id':account_move_id.id,}
            debit_line2 = {'name':name_picking,'debit':0.0,'credit':tax_price_total,'account_id':tax_account.id,'move_id':account_move_id.id,}
            account_move_line_obj.create(debit_line)
            account_move_line_obj.create(debit_line2)

        # credit_line = {
        #     'name':description,
        #     'credit':expense_total,
        #     'debit':0.0,
        #     # 'analytic_account_id' : expense_lines.project_acc.id,
        #     'account_id': credit_account_id,
        #     'move_id':account_move_id,
        #     }
        # self.pool.get('account.move.line').create(cr,uid,credit_line)
        self.internal_use=True

        return True
    @api.multi
    def _reset_sequence(self):
        for rec in self:
            current_sequence = 1
            for line in rec.move_lines:
                line.write({'sequence': current_sequence})
                current_sequence += 1

    @api.model
    # reset line sequence number during create
    def create(self, line_values):
        res = super(stock_picking_inheritsss, self).create(line_values)
        res._reset_sequence()
        return res

    @api.multi
    # reset line sequence number during write
    def write(self, line_values):
        res = super(stock_picking_inheritsss, self).write(line_values)

        self._reset_sequence()

        return res
    def _get_invoice_vals(self, cr, uid, key, inv_type, journal_id, move, context=None):
        if context is None:
            context = {}
        partner, currency_id, company_id, user_id = key
#	pdb.set_trace()
        if inv_type in ('out_invoice', 'out_refund'):
            account_id = partner.property_account_receivable.id
            payment_term = partner.property_payment_term.id or False
	    so_name = move.picking_id.origin
	    sale_obj = self.pool.get('sale.order')
	    sale_id = sale_obj.search(cr,uid,[('name','=',so_name)])
	    sale_rec = sale_obj.browse(cr,uid,sale_id)
	    payment_term_id = sale_rec.sale_order_payment_information
	    ship_term_id = sale_rec.sale_order_shipping_information
	    supplier_reference = sale_rec.client_order_ref
	    if payment_term_id :
		    pay_term = payment_term_id.id
	    else:
		    pay_term = False
	    if ship_term_id:
		    ship_term = ship_term_id.id
	    else:
		    ship_term=False
	else:
	    account_id = partner.property_account_payable.id
            payment_term = partner.property_supplier_payment_term.id or False
	    po_name = move.picking_id.origin
	    purchase_obj = self.pool.get('purchase.order')
	    purchase_id = purchase_obj.search(cr,uid,[('name','=',po_name)])
	    purchase_rec = purchase_obj.browse(cr,uid,purchase_id)
	    payment_term_id = purchase_rec.purchase_payment
	    ship_term_id = purchase_rec.purchase_shipping
	    supplier_reference = purchase_rec.partner_ref
	    if payment_term_id :
		    pay_term = payment_term_id.id
	    else:
		    pay_term = False
	    if ship_term_id:
		    ship_term = ship_term_id.id
	    else:
		    ship_term=False


        return {
	    'name':supplier_reference,
            'origin': move.picking_id.name,
            'date_invoice': context.get('date_inv', False),
            'user_id': user_id,
            'partner_id': partner.id,
            'account_id': account_id,
            'payment_term': payment_term,
            'type': inv_type,
            'fiscal_position': partner.property_account_position.id,
            'company_id': company_id,
            'currency_id': currency_id,
            'journal_id': journal_id,
            'pay_term':pay_term,
            'ship_term':ship_term,
            'select_stage':move.picking_id.select_stage,
        }

    

class account_invoice_line_inherit(osv.osv):
    _inherit = "account.invoice.line"
    _description = "Account Invoice line Inherit"
    _columns = {
        'customer_part_no':fields.char('Customer Part No'),
        'lot_id':fields.many2one('stock.production.lot','Lot No'),
     }



class account_invoice_inherit(osv.osv):
    _inherit = "account.invoice"
    _description = "Account Invoice Inherit"
    _columns = {
        'pay_term':fields.many2one('payment.terms','Payment Terms'),
        'ship_term':fields.many2one('shipping.terms','Shipping Terms'),
        'select_stage':fields.selection([('first', 'First Stage Dealer'), ('secon', 'Second Stage Dealer')],'Stage'),
        'is_excise':fields.boolean('Is Excise Invoice'),
        'invoice_datetime':fields.datetime('Invoice Date and Time'),       
     }
    @api.multi
    def action_cancel(self):
        moves = self.env['account.move']
        for inv in self:
            if inv.move_id:
                moves += inv.move_id
            if inv.payment_ids:
                for move_line in inv.payment_ids:
                    if move_line.reconcile_partial_id.line_partial_ids:
                        raise except_orm(_('Error!'), _('You cannot cancel an invoice which is partially paid. You need to unreconcile related payment entries first.'))

        # First, set the invoices as cancelled and detach the move ids
        self.sent=False
        self.write({'state': 'cancel', 'move_id': False})
        if moves:
            # second, invalidate the move(s)
            moves.button_cancel()
            # delete the move this invoice was pointing to
            # Note that the corresponding move_lines and move_reconciles
            # will be automatically deleted too
            moves.unlink()
        self._log_event(-1.0, 'Cancel Invoice')
        return True
    @api.multi
    def action_date_assign(self):

        for inv in self:
            res = inv.onchange_payment_term_date_invoice(inv.payment_term.id, inv.date_invoice)
            if res and res.get('value'):
                inv.write(res['value'])
            inv.write({'invoice_datetime':datetime.datetime.now()})
        return True

    @api.multi
    def print_all_copies_invoice(self):
        assert len(self) == 1
        
        self.sent = True
        #pdb.set_trace()
        return self.env['report'].get_action(self, 'sales_invoice.report_mom_new')
        #return self.env['report'].get_action(self, 'sales_invoice.report_mom_extra')
    @api.multi
    def print_extra_invoice(self):
        
        return self.env['report'].get_action(self, 'sales_invoice.report_mom_extra')
    @api.multi
    def print_commerciaal_invoice(self):
        assert len(self) == 1
        #pdb.set_trace()
        #if self.sent==False:
        self.sent = True
        #pdb.set_trace()
        return self.env['report'].get_action(self, 'sales_invoice.report_invoice_new')
        #return self.env['report'].get_action(self, 'sales_invoice.report_invoice_extra')
    @api.multi
    def print_commerciaal_extra_invoice(self):
        
        return self.env['report'].get_action(self, 'sales_invoice.report_invoice_extra')

    @api.multi
    def action_date_assign(self):
        for inv in self:
            res = inv.onchange_payment_term_date_invoice(inv.payment_term.id, inv.date_invoice)
            if res and res.get('value'):
                inv.write(res['value'])
            inv.write({'invoice_datetime':datetime.datetime.now()})
        return True



    def cess_amount_to_text_tax(self, cr, uid, doc_ids, currency, sub_currency,sec_ed_cess_amount,ed_cess_amount,context=None):
        total1 = sec_ed_cess_amount+ed_cess_amount
        total = total1
        amt_en = amount_to_text_in.amount_to_text(total, 'en', currency, sub_currency)
        return amt_en
    def total_duty_amount_to_text_tax(self, cr, uid, doc_ids, currency, sub_currency,total_duty_amount,context=None):
        total = total_duty_amount
        
        amt_en = amount_to_text_in.amount_to_text(total, 'en', currency, sub_currency)
        return amt_en




    def exi_amount_to_text(self, cr, uid, doc_ids, currency, sub_currency,context=None):
        total = 0.0
        paylisp_row = self.browse(cr, uid, doc_ids, context=context).amount_total
        #payslip_line_ids = paylisp_row.line_ids
        if paylisp_row:
            total = paylisp_row
        amt_en = amount_to_text_in.amount_to_text(total, 'en', currency, sub_currency)
        return amt_en
    def exi_amount_to_text_tax(self, cr, uid, doc_ids, currency, sub_currency,context=None):
        total = 0.0
        paylisp_tax = self.browse(cr, uid, doc_ids, context=context).amount_tax
        #payslip_line_ids = paylisp_row.line_ids
        if paylisp_tax:
            total= paylisp_tax
        amt_en = amount_to_text_in.amount_to_text(total, 'en', currency, sub_currency)
        return amt_en


    def amount_to_text(self, cr, uid, doc_ids, currency, sub_currency,context=None):
        total = 0.0
        paylisp_row = self.browse(cr, uid, doc_ids, context=context).amount_total

        #payslip_line_ids = paylisp_row.line_ids
        if paylisp_row:
            total = paylisp_row

        amt_en = amount_to_text_in.amount_to_text(total, 'en', currency, sub_currency)
        #print amt_en
        #print "---------------------------------------------------------------"

        return amt_en

    def amount_to_text_tax(self, cr, uid, doc_ids, currency, sub_currency,context=None):
        total = 0.0

        paylisp_tax = self.browse(cr, uid, doc_ids, context=context).amount_tax
        #payslip_line_ids = paylisp_row.line_ids

        if paylisp_tax:
            total= paylisp_tax
        amt_en = amount_to_text_in.amount_to_text(total, 'en', currency, sub_currency)
        #print amt_en
        #print "---------------------------------------------------------------"

        return amt_en


    def get_whdate(self,cr,uid,var1,context=None):
        val3=self.pool.get("stock.picking").search(cr,uid,[('name','=',var1)])
        val4=self.pool.get("stock.picking").browse(cr, uid, val3, context=context).date_done
        return val4
    def get_sale_order(self,cr,uid,var1,context=None):
        picking_origin=self.pool.get("stock.picking").search(cr,uid,[('name','=',var1)])

        sale_order_origin=self.pool.get("stock.picking").browse(cr,uid,picking_origin).group_id.name

        sale_order_id=self.pool.get("sale.order").search(cr,uid,[('name','=',sale_order_origin)])
        sale_order_name=self.pool.get("sale.order").browse(cr,uid,sale_order_id)
        #print "-------------------------------------------------------------"
        #print sale_order_id
        #print sale_order_name
        #print sale_order_origin
        return sale_order_origin
    def get_sale_order_date(self,cr,uid,var1,context=None):
        picking_origin=self.pool.get("stock.picking").search(cr,uid,[('name','=',var1)])

        sale_order_origin=self.pool.get("stock.picking").browse(cr,uid,picking_origin).group_id.name

        sale_order_id=self.pool.get("sale.order").search(cr,uid,[('name','=',sale_order_origin)])
        sale_order_name=self.pool.get("sale.order").browse(cr,uid,sale_order_id).date_order
        
        return sale_order_name


    def get_saleinvoice_consignee_address(self,cr,uid,var1,context=None):
        full_address=[]
        picking_origin=self.pool.get("stock.picking").search(cr,uid,[('name','=',var1)])

        sale_order_origin=self.pool.get("stock.picking").browse(cr,uid,picking_origin).group_id.name

        sale_order_id=self.pool.get("sale.order").search(cr,uid,[('name','=',sale_order_origin)])
        sale_order_name=self.pool.get("sale.order").browse(cr,uid,sale_order_id)
        if sale_order_name.partner_id.parent_id:
            address=str(sale_order_name.partner_id.parent_id.name or ''),
        else:
            address=str(sale_order_name.partner_id.name or '')
        tup=address
        address=''.join(tup)
        full_address.append(address)
        street=str(sale_order_name.partner_id.street or '')+' '+str(sale_order_name.partner_id.street2 or ''),
        tup=street
        street=''.join(tup)
        full_address.append(street)

        location=str(sale_order_name.partner_id.state_id.name or '')+' '+str(sale_order_name.partner_id.city or'')+' '+str(sale_order_name.partner_id.zip or '')
        full_address.append(location)
        vat=str(sale_order_name.partner_id.vat_tin or '')
        full_address.append(vat)
        exise=str(sale_order_name.partner_id.excise_reg_no or '')
        full_address.append(exise)
        #print "---------------------------------------------------------------"
        #print full_address

        return full_address

    def get_saleinvoice_delivery_address(self,cr,uid,var1,context=None):
        full_address=[]
        picking_origin=self.pool.get("stock.picking").search(cr,uid,[('name','=',var1)])

        sale_order_origin=self.pool.get("stock.picking").browse(cr,uid,picking_origin).group_id.name

        sale_order_id=self.pool.get("sale.order").search(cr,uid,[('name','=',sale_order_origin)])
        sale_order_name=self.pool.get("sale.order").browse(cr,uid,sale_order_id)
        if sale_order_name.partner_shipping_id.parent_id:
            address=str(sale_order_name.partner_shipping_id.parent_id.name)
        else:
            address=str(sale_order_name.partner_shipping_id.name or ''),
        tup=address
        address=''.join(tup)
        full_address.append(address)
        street=str(sale_order_name.partner_shipping_id.street or '')+' '+str(sale_order_name.partner_shipping_id.street2 or ''),
        tup=street
        street=''.join(tup)
        full_address.append(street)

        location=str(sale_order_name.partner_shipping_id.state_id.name or '')+' '+str(sale_order_name.partner_shipping_id.city or'')+' '+str(sale_order_name.partner_shipping_id.zip or '')
        full_address.append(location)
        vat=str(sale_order_name.partner_shipping_id.vat_tin or '')
        full_address.append(vat)
        exise=str(sale_order_name.partner_shipping_id.excise_reg_no or '')
        full_address.append(exise)
        #print "---------------------------------------------------------------"
        #print full_address

        return full_address
	
	



    def get_tariff(self, cr, uid, lot_id, context=None):
#	pdb.set_trace()
        stock_quant_obj = self.pool.get("stock.quant")
        stock_move_obj = self.pool.get("stock.move")
	purchase_quant = stock_quant_obj.search(cr, uid, [('lot_id', '=', lot_id.id)])
	purchase_stock_move_id = stock_move_obj.search(cr, uid,
	                                                                    [('quant_ids', 'in', purchase_quant),
	                                                                     ('picking_id.picking_type_id', '=', 1),
									     ('picking_id.return_voucher', '=', False),
	                                                                     ])
        purchase_stock_move = purchase_stock_move_id[0]
	tarrif=''
        for manufacturer_row in stock_move_obj.browse(cr,uid,purchase_stock_move).new_stock_id:
                    manufacturer_key = str(manufacturer_row.type_stage)
                    if manufacturer_key=='manifacturer':
			tarrif = manufacturer_row.tarrif
        return tarrif
    #New Code Begins Here
    def get_invoice_lot_id(self, cr, uid, invoice_id, context=None):
        #all_details = {}
        all_details = {}
        manufacturers_tuple = ()
        dealer_tuple = ()
        manufacturers_dict = {}
        dealer_dict = {}
        lot_id_list=[]
        invoice_recs=self.pool.get("account.invoice").browse(cr, uid, invoice_id)
        stock_quant_obj = self.pool.get("stock.quant")
        stock_move_obj = self.pool.get("stock.move")
        for lot_rec in invoice_recs.invoice_line:
            lot_id_list.append(lot_rec.lot_id)

        for lot_num in lot_id_list:

            
            purchase_quant = stock_quant_obj.search(cr, uid, [('lot_id', '=', lot_num.id)])
            purchase_stock_move_id = stock_move_obj.search(cr, uid,[('quant_ids', 'in', purchase_quant),('picking_id.picking_type_id', '=', 1),('picking_id.return_voucher', '=', False),])
            purchase_stock_move = purchase_stock_move_id[0]
            for manufacturer_row in stock_move_obj.browse(cr,uid,purchase_stock_move).new_stock_id:
                    dealer_dict1 = {}
                    manufacturers_dict1 = {}

                    pur_supplier_name = manufacturer_row.new_company_selection.id
                    manufacturer_key = str(manufacturer_row.new_company_selection.type)
                    if manufacturer_key=='dealer':

                        manufacturer_key= str(manufacturer_row.new_company_selection.type)
                        supplier_name=str(manufacturer_row.new_company_selection.name or ''),
                        product_name = stock_move_obj.browse(cr,uid,purchase_stock_move).product_id.name
                        dealer_dict1.update({
                            'supplier_id': str(manufacturer_row.new_company_selection.type or''),
                            'supplier_name': str(manufacturer_row.new_company_selection.name or ''),
                            'supplier_address':str(manufacturer_row.new_company_selection.address or ''),
                            'supplier_range': str(manufacturer_row.new_company_selection.range or ''),
                            'supplier_division_name': str(manufacturer_row.new_company_selection.division_name or ''),
                            'supplier_commissionerate': str(manufacturer_row.new_company_selection.commissionerate or''),
                            'supplier_excise_reg_no': str(manufacturer_row.new_company_selection.excise_reg_no or ''),


                                    })
                        dealer_dict.update({supplier_name:dealer_dict1})

                    elif manufacturer_key=='manifacturer':

                        manufacturer_key= str(manufacturer_row.new_company_selection.type)
                        supplier_name=str(manufacturer_row.new_company_selection.name or ''),
                        product_name = stock_move_obj.browse(cr,uid,purchase_stock_move).product_id.name
                        manufacturers_dict1.update({
                            'supplier_id': str(manufacturer_row.new_company_selection.type or ''),
                            'supplier_name': str(manufacturer_row.new_company_selection.name or ''),
                            'supplier_address': str(manufacturer_row.new_company_selection.address or ''),
                            'supplier_range': str(manufacturer_row.new_company_selection.range or ''),
                            'supplier_division_name': str(manufacturer_row.new_company_selection.division_name or ''),
                            'supplier_commissionerate': str(manufacturer_row.new_company_selection.commissionerate or ''),
                            'supplier_excise_reg_no': str(manufacturer_row.new_company_selection.excise_reg_no or ''),

                                    })
                        manufacturers_dict.update({supplier_name:manufacturers_dict1})
        dealer_tuple += (dealer_dict,)
        manufacturers_tuple += (manufacturers_dict,)
        all_details.update({'dealer':dealer_dict,'manufacturer':manufacturers_dict,'invoice_lot_id':lot_id_list,})
        #print all_details

        return all_details
    def lot_get_product_get_detail(self, cr, uid, lot_id,invoice_id, context=None):
        #pdb.set_trace()
        product_tuple = ()
        manufacturers_info={}
        manufacturers_detail={}
        stock_quant_obj = self.pool.get("stock.quant")
        stock_move_obj = self.pool.get("stock.move")
        #stock_move_obj = self.pool.get("account.invoice").browse(cr,uid,472).invoice_line
        account_invoice_line_obj = self.pool.get('account.invoice.line')

        company=[]
        for lot_num in lot_id:

            manufacturers_dict1={}
            purchase_quant = stock_quant_obj.search(cr, uid, [('lot_id', '=', lot_num.id)])
            purchase_stock_move_id = stock_move_obj.search(cr, uid,[('quant_ids', 'in', purchase_quant),('picking_id.picking_type_id', '=', 1),('picking_id.return_voucher', '=', False),])
            purchase_stock_move = purchase_stock_move_id[0]
            product_name=stock_move_obj.browse(cr,uid,purchase_stock_move).name
            invoice_line_id = account_invoice_line_obj.search(cr,uid,[('lot_id','=',lot_num.id),('invoice_id','=',invoice_id)])
            if invoice_line_id:
                invoice_qty = account_invoice_line_obj.browse(cr,uid,invoice_line_id).quantity
            #print invoice_qty
            new_stock_id_detail=stock_move_obj.browse(cr,uid,purchase_stock_move)
            if len(new_stock_id_detail.new_stock_id)>1:
                for name_supplier in new_stock_id_detail.new_stock_id:
                    #manufacturer_key = str(manufacturer_row.type_stage)
                    if name_supplier.new_company_selection.type=='dealer':
                        #company.append(str(manufacturer_row.comapny_name or ''))
                        #print manufacturer_row.comapny_name or ''
                        manufacturers_dict1.update({

                            'product_name': str(new_stock_id_detail.product_id.name or ''),

                            # 'manufacturer' : manufacturer.comapny_name,
                            # 'product_name':rec.product_id.name,
                            'excise_reg_no': str(name_supplier.reg_num or ''),
                'quantity':name_supplier.quantity,
                            'invoice_no':str(name_supplier.invoice_no or '')+' '+str(name_supplier.invoice_date or ''),
                            'tarrif':str(name_supplier.tarrif or ''),
                            'duty_per_unit':name_supplier.duty_per_unit,
                            'total_duty_amount':name_supplier.total_duty_amount,
                            'new_division': str(name_supplier.division or ''),
                            'range': str(name_supplier.range or ''),
                            'commissionerate': str(name_supplier.commissionerate or ''),
                            'supplier_type': str(name_supplier.type_stage),
                            'supplier_id': name_supplier.new_company_selection,
                            'assessable_value': (name_supplier.assessable_value/name_supplier.quantity)*invoice_qty,
                            'rate_bed_amount': name_supplier.rate_bed_amount,
                            'bed_amount': (name_supplier.bed_amount/name_supplier.quantity)*invoice_qty,
                            'rate_ed_cess_amount': name_supplier.rate_ed_cess_amount,
                            'ed_cess_amount': (name_supplier.ed_cess_amount/name_supplier.quantity)*invoice_qty,
                            'rate_sec_ed_cess_amount': name_supplier.rate_sec_ed_cess_amount,
                            'sec_ed_cess_amount': (name_supplier.sec_ed_cess_amount/name_supplier.quantity)*invoice_qty,
                            # 'reg_num': manufacturer_row.reg_num,
                            'comapny_name': str(name_supplier.comapny_name or ''),
                            'company_address': str(name_supplier.addrress or ''),

                            'division': str(name_supplier.division or '') + str(name_supplier.range or '') + str(
                                name_supplier.commissionerate or ''),
                            'invoice_no': str(name_supplier.invoice_no or '') + "/" + str(
                                name_supplier.invoice_date or ''),
                            'seller': name_supplier.seller,
                            'invoice_quantity':invoice_qty

                        })
                        product_tuple += (manufacturers_dict1,)
            elif len(new_stock_id_detail.new_stock_id)==1:
                for name_supplier in new_stock_id_detail.new_stock_id:
                    if name_supplier.new_company_selection.type=='manifacturer':
                        manufacturers_dict1.update({
                            'product_name': str(new_stock_id_detail.product_id.name or ''),

                            # 'manufacturer' : manufacturer.comapny_name,
                            # 'product_name':rec.product_id.name,
                            'excise_reg_no': str(name_supplier.reg_num or ''),
                'quantity':name_supplier.quantity,
                            'invoice_no':str(name_supplier.invoice_no or '')+' '+str(name_supplier.invoice_date or ''),
                            'tarrif':str(name_supplier.tarrif or ''),
                            'duty_per_unit':name_supplier.duty_per_unit,
                            'total_duty_amount':name_supplier.total_duty_amount,
                            'new_division': str(name_supplier.division or ''),
                            'range': str(name_supplier.range or ''),
                            'commissionerate': str(name_supplier.commissionerate or ''),
                            'supplier_type': str(name_supplier.type_stage),
                            'supplier_id': name_supplier.new_company_selection,
                            'assessable_value': (name_supplier.assessable_value/name_supplier.quantity)*invoice_qty,
                            'rate_bed_amount': name_supplier.rate_bed_amount,
                            'bed_amount': (name_supplier.bed_amount/name_supplier.quantity)*invoice_qty,
                            'rate_ed_cess_amount': name_supplier.rate_ed_cess_amount,
                            'ed_cess_amount': (name_supplier.ed_cess_amount/name_supplier.quantity)*invoice_qty,
                            'rate_sec_ed_cess_amount': name_supplier.rate_sec_ed_cess_amount,
                            'sec_ed_cess_amount': (name_supplier.sec_ed_cess_amount/name_supplier.quantity)*invoice_qty,
                            # 'reg_num': manufacturer_row.reg_num,
                            'comapny_name': str(name_supplier.comapny_name or ''),
                            'company_address': str(name_supplier.addrress or ''),

                            'division': str(name_supplier.division or '') + str(name_supplier.range or '') + str(
                                name_supplier.commissionerate or ''),
                            'invoice_no': str(name_supplier.invoice_no or '') + "/" + str(
                                name_supplier.invoice_date or ''),
                            'seller': name_supplier.seller,
                            'invoice_quantity':invoice_qty

                        })
                        product_tuple += (manufacturers_dict1,)
        return product_tuple

    def lot_get_product_detail(self,cr, uid,ids, variable1,variable2,context=None):
        tup=variable2
        variable2=''.join(tup)
        stock_quant_obj = self.pool.get("stock.quant")
        stock_move_obj = self.pool.get("stock.move")
        #stock_move_obj = self.pool.get("account.invoice").browse(cr,uid,472).invoice_line
        account_invoice_line_obj = self.pool.get('account.invoice.line')
        manufacturers_dict={}
        product_tuple=()
        for lot_num in variable1:
            manufacturers_dict1={}
            purchase_quant = stock_quant_obj.search(cr, uid, [('lot_id', '=', lot_num.id)])
            purchase_stock_move_id = stock_move_obj.search(cr, uid,[('quant_ids', 'in', purchase_quant),('picking_id.picking_type_id', '=', 1),('picking_id.return_voucher', '=', False),])
            purchase_stock_move = purchase_stock_move_id[0]
            product_name=stock_move_obj.browse(cr,uid,purchase_stock_move).name
            new_stock_id_detail=stock_move_obj.browse(cr,uid,purchase_stock_move)
            #print new_stock_id_detail

            if new_stock_id_detail :
                for name_supplier in new_stock_id_detail.new_stock_id :
                    manufacturers_dict1 = {}
                    #print "-----------------------------"
                    #print str(variable2)
                    #print name_supplier.comapny_name
                    #print "------------------------------"
                    if variable2==name_supplier.comapny_name:
                        #pdb.set_trace()

                        manufacturers_dict1.update({
                            'product_name':str(new_stock_id_detail.product_id.name or ''),
                            'excise_reg_no': str(name_supplier.reg_num or ''),
                            'quantity':name_supplier.quantity,
                            'invoice_no':str(name_supplier.invoice_no or '')+' '+str(name_supplier.invoice_date or ''),
                            'tarrif':str(name_supplier.tarrif or ''),
                            'duty_per_unit':name_supplier.duty_per_unit,
                            'total_duty_amount':name_supplier.total_duty_amount,
                            'new_division': str(name_supplier.division or ''),
                            'range': str(name_supplier.range or ''),
                            'commissionerate': str(name_supplier.commissionerate or ''),
                            'supplier_type': str(name_supplier.type_stage),
                            'supplier_id': name_supplier.new_company_selection,
                            'assessable_value': name_supplier.assessable_value,
                            'rate_bed_amount': name_supplier.rate_bed_amount,
                            'bed_amount': name_supplier.bed_amount,
                            'rate_ed_cess_amount': name_supplier.rate_ed_cess_amount,
                            'ed_cess_amount': name_supplier.ed_cess_amount,
                            'rate_sec_ed_cess_amount': name_supplier.rate_sec_ed_cess_amount,
                            'sec_ed_cess_amount': name_supplier.sec_ed_cess_amount,
                            'comapny_name': str(name_supplier.comapny_name or ''),
                            'company_address': str(name_supplier.addrress or ''),
                            'division': str(name_supplier.division or '') + str(name_supplier.range or '') + str(
                                name_supplier.commissionerate or ''),
                            'invoice_no': str(name_supplier.invoice_no or '') + "/" + str(
                                name_supplier.invoice_date or ''),
                            'seller': name_supplier.seller,

                        })
                        product_tuple+=(manufacturers_dict1,)
        return product_tuple

    #New Code Ends Here


    def get_lotnumber(self, cr, uid, variable,invoice_id, context=None):
        #pdb.set_trace()
        manufacturers_info={}
        manufacturers_detail={}
        val1=self.pool.get("stock.picking").search(cr, uid, [('name','=',variable)])
        val2=self.pool.get('stock.picking').browse(cr, uid, val1, context=context)
        invoice_recs=self.pool.get("account.invoice").browse(cr, uid, invoice_id)
	product_list = []
	product_dict = {}
	purchase_stock_list=[]
	for invoice_rec in invoice_recs.invoice_line :
		product_list.append(invoice_rec.product_id.id)
		product_dict.update({invoice_rec.product_id.id:invoice_rec.lot_id.id})

        stock_quant_obj = self.pool.get("stock.quant")
        stock_move_obj = self.pool.get("stock.move")
	invoice_stock_move_ids = stock_move_obj.search(cr,uid,[('product_id','in',product_list),('picking_id','=',val1)])
	if invoice_stock_move_ids :
		stock_moves = stock_move_obj.browse(cr,uid,invoice_stock_move_ids)
        manufacturers_row=[]

        for obj in stock_moves:
		all_details = {}
		manufacturers_tuple = ()
		dealer_tuple = ()
		manufacturers_dict = {}
		dealer_dict = {}

		purchase_quant = stock_quant_obj.search(cr, uid, [('lot_id', '=', product_dict[obj.product_id.id])])
		purchase_stock_move_id = stock_move_obj.search(cr, uid,
		                                                                    [('quant_ids', 'in', purchase_quant),
		                                                                     ('picking_id.picking_type_id', '=', 1),
										     ('picking_id.return_voucher', '=', False),
		                                                                     ])
        	purchase_stock_list.append(purchase_stock_move_id[0])
	        purchase_stock_move = purchase_stock_move_id[0]

                for manufacturer_row in stock_move_obj.browse(cr,uid,purchase_stock_move).new_stock_id:
                    dealer_dict1 = {}
                    manufacturers_dict1 = {}

                    pur_supplier_name = manufacturer_row.new_company_selection.id
                    manufacturer_key = str(manufacturer_row.new_company_selection.type)
                    if manufacturer_key=='dealer':

                        manufacturer_key= str(manufacturer_row.new_company_selection.type)
                        supplier_name=manufacturer_row.new_company_selection.name,
                        product_name = stock_move_obj.browse(cr,uid,purchase_stock_move).product_id.name
                        dealer_dict1.update({
                            'supplier_id': str(manufacturer_row.new_company_selection.type or''),
                            'supplier_name': str(manufacturer_row.new_company_selection.name or ''),
                            'supplier_address':str(manufacturer_row.new_company_selection.address or ''),
                            'supplier_range': str(manufacturer_row.new_company_selection.range or ''),
                            'supplier_division_name': str(manufacturer_row.new_company_selection.division_name or ''),
                            'supplier_commissionerate': str(manufacturer_row.new_company_selection.commissionerate or''),
                            'supplier_excise_reg_no': str(manufacturer_row.new_company_selection.excise_reg_no or ''),


                                    })
                        dealer_dict.update({supplier_name:dealer_dict1})

                    elif manufacturer_key=='manifacturer':

                        manufacturer_key= str(manufacturer_row.new_company_selection.type)
                        supplier_name=manufacturer_row.new_company_selection.name,
                        product_name = stock_move_obj.browse(cr,uid,purchase_stock_move).product_id.name
                        manufacturers_dict1.update({
                            'supplier_id': str(manufacturer_row.new_company_selection.type or ''),
                            'supplier_name': str(manufacturer_row.new_company_selection.name or ''),
                            'supplier_address': str(manufacturer_row.new_company_selection.address or ''),
                            'supplier_range': str(manufacturer_row.new_company_selection.range or ''),
                            'supplier_division_name': str(manufacturer_row.new_company_selection.division_name or ''),
                            'supplier_commissionerate': str(manufacturer_row.new_company_selection.commissionerate or ''),
                            'supplier_excise_reg_no': str(manufacturer_row.new_company_selection.excise_reg_no or ''),

                                    })
                        manufacturers_dict.update({supplier_name:manufacturers_dict1})
		dealer_tuple += (dealer_dict,)
		manufacturers_tuple += (manufacturers_dict,)
		all_details.update({'dealer':dealer_dict,'manufacturer':manufacturers_dict,'stock_move_id':purchase_stock_list})

        return all_details

    def get_product_detail(self,cr, uid,ids, variable1,variable2,context=None):
        tup=variable2
        variable2=''.join(tup)
        manufacturers_dict={}
        product_tuple=()

        for vaar1 in variable1:
            stock_move_obj = self.pool.get("stock.move")
            new_stock_id_detail=stock_move_obj.browse(cr,uid,vaar1)
            product_name=str(new_stock_id_detail.product_id.name or '')
            if new_stock_id_detail :
                for name_supplier in new_stock_id_detail.new_stock_id :
                    manufacturers_dict1 = {}
                    if variable2==name_supplier.comapny_name:

                        manufacturers_dict1.update({
                            'product_name':str(new_stock_id_detail.product_id.name or ''),
                            'excise_reg_no': str(name_supplier.reg_num or ''),
                            'quantity':name_supplier.quantity,
                            'invoice_no':str(name_supplier.invoice_no or '')+' '+str(name_supplier.invoice_date or ''),
                            'tarrif':str(name_supplier.tarrif or ''),
                            'duty_per_unit':name_supplier.duty_per_unit,
                            'total_duty_amount':name_supplier.total_duty_amount,
                            'new_division': str(name_supplier.division or ''),
                            'range': str(name_supplier.range or ''),
                            'commissionerate': str(name_supplier.commissionerate or ''),
                            'supplier_type': str(name_supplier.type_stage),
                            'supplier_id': name_supplier.new_company_selection,
                            'assessable_value': name_supplier.assessable_value,
                            'rate_bed_amount': name_supplier.rate_bed_amount,
                            'bed_amount': name_supplier.bed_amount,
                            'rate_ed_cess_amount': name_supplier.rate_ed_cess_amount,
                            'ed_cess_amount': name_supplier.ed_cess_amount,
                            'rate_sec_ed_cess_amount': name_supplier.rate_sec_ed_cess_amount,
                            'sec_ed_cess_amount': name_supplier.sec_ed_cess_amount,
                            'comapny_name': str(name_supplier.comapny_name or ''),
                            'company_address': str(name_supplier.addrress or ''),
                            'division': str(name_supplier.division or '') + str(name_supplier.range or '') + str(
                                name_supplier.commissionerate or ''),
                            'invoice_no': str(name_supplier.invoice_no or '') + "/" + str(
                                name_supplier.invoice_date or ''),
                            'seller': name_supplier.seller,

                        })
                        product_tuple+=(manufacturers_dict1,)
        return product_tuple

    def get_product_detail_dealer(self, cr, uid, ids, variable1,invoice_id, origin, context=None):
        product_tuple = ()
        stock_move_obj = self.pool.get("stock.move")
	stock_picking_obj = self.pool.get('stock.picking')
        stock_quant_obj = self.pool.get("stock.quant")
	stock_picking_id = stock_picking_obj.search(cr,uid,[('name','=',origin)])
        
	account_invoice_line_obj = self.pool.get('account.invoice.line')
        invoice_recs=self.pool.get("account.invoice").browse(cr, uid, invoice_id)
	product_list = []
	product_dict = {}
	purchase_stock_list=[]
	for invoice_rec in invoice_recs.invoice_line :
		product_list.append(invoice_rec.product_id.id)
		product_dict.update({invoice_rec.product_id.id:invoice_rec.lot_id.id})

	
        for var1 in variable1:


            new_stock_id_detail = stock_move_obj.browse(cr, uid, var1)
            #print new_stock_id_detail
            manufacturers_dict1={}

#            for lines in new_stock_id_detail.quant_ids:
		#pdb.set_trace()
	    product_id = stock_move_obj.browse(cr,uid,var1).product_id.id
	    lot_id = product_dict[product_id]
	    invoice_line_id = account_invoice_line_obj.search(cr,uid,[('product_id','=',product_id),('lot_id','=',lot_id),('invoice_id','=',invoice_id)])
	    invoice_qty=0.0
	    if invoice_line_id :
			invoice_qty = account_invoice_line_obj.browse(cr,uid,invoice_line_id).quantity
            if len(new_stock_id_detail.new_stock_id)>1:
                for name_supplier in new_stock_id_detail.new_stock_id:
                    if name_supplier.new_company_selection.type=='dealer':
			#pdb.set_trace()
                        manufacturers_dict1.update({

                            'product_name': str(new_stock_id_detail.product_id.name or ''),

                            # 'manufacturer' : manufacturer.comapny_name,
                            # 'product_name':rec.product_id.name,
                            'excise_reg_no': str(name_supplier.reg_num or ''),
			    'quantity':name_supplier.quantity,
                            'invoice_no':str(name_supplier.invoice_no or '')+' '+str(name_supplier.invoice_date or ''),
                            'tarrif':str(name_supplier.tarrif or ''),
                            'duty_per_unit':name_supplier.duty_per_unit,
                            'total_duty_amount':name_supplier.total_duty_amount,
                            'new_division': str(name_supplier.division or ''),
                            'range': str(name_supplier.range or ''),
                            'commissionerate': str(name_supplier.commissionerate or ''),
                            'supplier_type': str(name_supplier.type_stage),
                            'supplier_id': name_supplier.new_company_selection,
                            'assessable_value': (name_supplier.assessable_value/name_supplier.quantity)*invoice_qty,
                            'rate_bed_amount': name_supplier.rate_bed_amount,
                            'bed_amount': (name_supplier.bed_amount/name_supplier.quantity)*invoice_qty,
                            'rate_ed_cess_amount': name_supplier.rate_ed_cess_amount,
                            'ed_cess_amount': (name_supplier.ed_cess_amount/name_supplier.quantity)*invoice_qty,
                            'rate_sec_ed_cess_amount': name_supplier.rate_sec_ed_cess_amount,
                            'sec_ed_cess_amount': (name_supplier.sec_ed_cess_amount/name_supplier.quantity)*invoice_qty,
                            # 'reg_num': manufacturer_row.reg_num,
                            'comapny_name': str(name_supplier.comapny_name or ''),
                            'company_address': str(name_supplier.addrress or ''),

                            'division': str(name_supplier.division or '') + str(name_supplier.range or '') + str(
                                name_supplier.commissionerate or ''),
                            'invoice_no': str(name_supplier.invoice_no or '') + "/" + str(
                                name_supplier.invoice_date or ''),
                            'seller': name_supplier.seller,
                            'invoice_quantity':invoice_qty,

                        })
                        product_tuple += (manufacturers_dict1,)
            elif len(new_stock_id_detail.new_stock_id)==1:
                for name_supplier in new_stock_id_detail.new_stock_id:
                    if name_supplier.new_company_selection.type=='manifacturer':
                        manufacturers_dict1.update({
                            'product_name': str(new_stock_id_detail.product_id.name or ''),

                            # 'manufacturer' : manufacturer.comapny_name,
                            # 'product_name':rec.product_id.name,
                            'excise_reg_no': str(name_supplier.reg_num or ''),
			    'quantity':name_supplier.quantity,
                            'invoice_no':str(name_supplier.invoice_no or '')+' '+str(name_supplier.invoice_date or ''),
                            'tarrif':str(name_supplier.tarrif or ''),
                            'duty_per_unit':name_supplier.duty_per_unit,
                            'total_duty_amount':name_supplier.total_duty_amount,
                            'new_division': str(name_supplier.division or ''),
                            'range': str(name_supplier.range or ''),
                            'commissionerate': str(name_supplier.commissionerate or ''),
                            'supplier_type': str(name_supplier.type_stage),
                            'supplier_id': name_supplier.new_company_selection,
                            'assessable_value': (name_supplier.assessable_value/name_supplier.quantity)*invoice_qty,
                            'rate_bed_amount': name_supplier.rate_bed_amount,
                            'bed_amount': (name_supplier.bed_amount/name_supplier.quantity)*invoice_qty,
                            'rate_ed_cess_amount': name_supplier.rate_ed_cess_amount,
                            'ed_cess_amount': (name_supplier.ed_cess_amount/name_supplier.quantity)*invoice_qty,
                            'rate_sec_ed_cess_amount': name_supplier.rate_sec_ed_cess_amount,
                            'sec_ed_cess_amount': (name_supplier.sec_ed_cess_amount/name_supplier.quantity)*invoice_qty,
                            # 'reg_num': manufacturer_row.reg_num,
                            'comapny_name': str(name_supplier.comapny_name or ''),
                            'company_address': str(name_supplier.addrress or ''),

                            'division': str(name_supplier.division or '') + str(name_supplier.range or '') + str(
                                name_supplier.commissionerate or ''),
                            'invoice_no': str(name_supplier.invoice_no or '') + "/" + str(
                                name_supplier.invoice_date or ''),
                            'seller': name_supplier.seller,
                            'invoice_quantity':invoice_qty,

                        })
                        product_tuple += (manufacturers_dict1,)
                #print product_tuple
        return product_tuple
    def get_warehouse_address(self, cr, uid, variable, context=None):
        manufacturers_info=[]
        val1=self.pool.get("stock.picking").search(cr, uid, [('name','=',variable)])
        val2=self.pool.get('stock.picking').browse(cr, uid, val1, context=context)
        warehouse_name=str(val2.picking_type_id.default_location_src_id.partner_id.name or '')
        street=str(val2.picking_type_id.default_location_src_id.partner_id.street or '')
        street2=str(val2.picking_type_id.default_location_src_id.partner_id.street2 or '')
        city=str(val2.picking_type_id.default_location_src_id.partner_id.city or '')
        state=str(val2.picking_type_id.default_location_src_id.partner_id.state_id.name or '')
        zip_id=str(val2.picking_type_id.default_location_src_id.partner_id.zip or '')
        phone_num=str(val2.picking_type_id.default_location_src_id.partner_id.phone or '')
        county=str(val2.picking_type_id.default_location_src_id.partner_id.country_id.name or'')
        email_id=str(val2.picking_type_id.default_location_src_id.partner_id.email or '')
        manufacturers_info.append(str(warehouse_name))
        manufacturers_info.append(str(street)+" "+str(street2)+" "+str(city)+" "+str(state)+" "+str(zip_id))
        #manufacturers_info.append(str(county)+" "+str(phone_num)+" "+str(email_id))
        manufacturers_info.append(str(county))
        manufacturers_info.append(str(phone_num))
        manufacturers_info.append(str(email_id))
        return manufacturers_info

    def get_consignee_address(self, cr, uid, variable, context=None):
        manufacturers_info=[]
        val1=self.pool.get("stock.picking").search(cr, uid, [('name','=',variable)])
        val2=self.pool.get('stock.picking').browse(cr, uid, val1, context=context)
        if val2.partner_id.parent_id:
            warehouse_name=str(val2.partner_id.parent_id.name)+ ' '+str(val2.partner_id.name or ''),
        else:
            warehouse_name=str(val2.partner_id.name or ''),
        tup=warehouse_name
        warehouse_name=''.join(tup)
        #warehouse_name=val2.partner_id.name
        #tup=warehouse_name
        #warehouse_name=''.join(tup)
        street=val2.partner_id.street
        street2=val2.partner_id.street2
        city=val2.partner_id.city
        state=val2.partner_id.state_id.name
        zip_id=val2.partner_id.zip
        country=val2.partner_id.country_id.name
        vat=str(val2.partner_id.vat_tin or '')
        pan=str(val2.partner_id.pan_no or '')

       
        manufacturers_info.append(str(warehouse_name))
        manufacturers_info.append(str(street)+" "+str(street2))
        manufacturers_info.append(str(state)+" "+str(zip_id)+" "+str(country))
        manufacturers_info.append(str(city))
        manufacturers_info.append(str(vat))
        manufacturers_info.append(str(pan))


            

        #print "-----------------------------------------------------------"
        #print val2
        return manufacturers_info




class sale_order_inherit(osv.osv):
    _inherit="sale.order"
    def amount_to_text(self, cr, uid, doc_ids, currency, sub_currency,context=None):
        total = 0.0
        paylisp_row = self.browse(cr, uid, doc_ids, context=context).amount_untaxed

        #payslip_line_ids = paylisp_row.line_ids
        if paylisp_row:
            total = paylisp_row

        amt_en = amount_to_text_in.amount_to_text(total, 'en', currency, sub_currency)
        #print amt_en
        #print "---------------------------------------------------------------"

        return amt_en

    
    def get_warehouse_address(self, cr, uid, variable, context=None):
        manufacturers_info=[]
        val1=self.pool.get("stock.picking").search(cr, uid, [('name','=',variable)])
        val2=self.pool.get('stock.picking').browse(cr, uid, val1, context=context)
        warehouse_name=val2.picking_type_id.default_location_src_id.partner_id.name
        street=val2.picking_type_id.default_location_src_id.partner_id.street
        street2=val2.picking_type_id.default_location_src_id.partner_id.street2
        city=val2.picking_type_id.default_location_src_id.partner_id.city
        state=val2.picking_type_id.default_location_src_id.partner_id.state_id.name
        zip_id=val2.picking_type_id.default_location_src_id.partner_id.zip
        phone_num=val2.picking_type_id.default_location_src_id.partner_id.phone
        county=val2.picking_type_id.default_location_src_id.partner_id.country_id.name
        email_id=val2.picking_type_id.default_location_src_id.partner_id.email
        manufacturers_info.append(str(warehouse_name))
        manufacturers_info.append(str(street)+" "+str(street2)+" "+str(city)+" "+str(state)+" "+str(zip_id))
        manufacturers_info.append(str(county)+" "+str(phone_num)+" "+str(email_id))
            

        #print "-----------------------------------------------------------"
        #print val2
        return manufacturers_info

class purchase_order_inherit(osv.osv):
    _inherit="purchase.order"
    def amount_to_text(self, cr, uid, doc_ids, currency, sub_currency,context=None):
        total = 0.0
        paylisp_row = self.browse(cr, uid, doc_ids, context=context).amount_untaxed

        #payslip_line_ids = paylisp_row.line_ids
        if paylisp_row:
            total = paylisp_row

        amt_en = amount_to_text_in.amount_to_text(total, 'en', currency, sub_currency)
        #print amt_en
        #print "---------------------------------------------------------------"

        return amt_en

    
    def get_warehouse_address(self, cr, uid, variable, context=None):
        manufacturers_info=[]
        val1=self.pool.get("stock.picking").search(cr, uid, [('name','=',variable)])
        val2=self.pool.get('stock.picking').browse(cr, uid, val1, context=context)
        warehouse_name=val2.picking_type_id.default_location_src_id.partner_id.name
        street=val2.picking_type_id.default_location_src_id.partner_id.street
        street2=val2.picking_type_id.default_location_src_id.partner_id.street2
        city=val2.picking_type_id.default_location_src_id.partner_id.city
        state=val2.picking_type_id.default_location_src_id.partner_id.state_id.name
        zip_id=val2.picking_type_id.default_location_src_id.partner_id.zip
        phone_num=val2.picking_type_id.default_location_src_id.partner_id.phone
        county=val2.picking_type_id.default_location_src_id.partner_id.country_id.name
        email_id=val2.picking_type_id.default_location_src_id.partner_id.email
        manufacturers_info.append(str(warehouse_name))
        manufacturers_info.append(str(street)+" "+str(street2)+" "+str(city)+" "+str(state)+" "+str(zip_id))
        manufacturers_info.append(str(county)+" "+str(phone_num)+" "+str(email_id))
            

        #print "-----------------------------------------------------------"
        #print val2
        return manufacturers_info



class manufacturer(osv.osv):
    _name="manufacturer"
    _columns={
        
        #'description_goods': fields.many2one( 'product.product',string='Description  of Goods'),
        'type_stage':fields.selection([('manifacturer', 'Manufacturer'), ('dealer', 'Dealer')],'Type',required=True),
        "new_company_selection":fields.many2one('dealer.manufacturer','Supplier Selection',required=True),
        'assessable_value':fields.float('Assessable Value',required=True),
        'rate_bed_amount':fields.float('Rate of BED',required=True),
        'bed_amount':fields.float('BED Amount',required=True),
        'rate_ed_cess_amount':fields.float('Rate of Ed Cess',required=True),
        'ed_cess_amount':fields.float('Ed Cess Amount',required=True),
        'rate_sec_ed_cess_amount':fields.float('Rate of Sec Ed Cess',required=True),
        'sec_ed_cess_amount':fields.float('Sec Ed Cess Amount',required=True),
        'comapny_name':fields.char(string='Supplier Name',required=True),
        'reg_num': fields.char('Excise Reg No',required=True),
        'division': fields.char('Division Name',required=True),
        'invoice_no':fields.char("Invoice Number",required=True),
        'invoice_date':fields.date("Date"),
        'tarrif':fields.integer('Tariff Classification',required=True),
        'quantity':fields.integer('Quantity',required=True),
        'addrress':fields.char('Address',required=True),
        'range':fields.char('Range',required=True),
        'commissionerate':fields.char('Commissionerate',required=True),
        'seller':fields.char('Seller RG 23D No. & Supplier RG 23D No.',),  
        'saed':fields.float('SAED',required=True),
        
        
        
        'total_duty_amount': fields.float('Total Duty Amount',required=True),
        'duty_per_unit':fields.float('Duty per Unit',required=True),
        
        
        

        'new_id':fields.many2one('stock.move','Stock'),

    }


    
    def onchange_type(self, cr, uid, ids, type_stage, context=None):
        vals = {}
        dealer_manufacturer_ids = self.pool.get("dealer.manufacturer").search(cr, uid, [('type', '=', type_stage)])
        #pdb.set_trace()
        #vals['new_company_selection']={('id','in',dealer_manufacturer_ids)}
        #val2 = self.pool.get('stock.picking').browse(cr, uid, a, context=context)
        return{'domain':{'new_company_selection':[('id', 'in', dealer_manufacturer_ids)]}}

    def onchange_information(self, cr, uid, ids, new_company_selection, context=None):
        vals={}

        supplier_detail=self.pool.get('dealer.manufacturer').browse(cr,uid,new_company_selection,context=context)
        if new_company_selection:
            for rec in supplier_detail:
                vals={
                    'value':{
                        'comapny_name': rec.name,
                        'reg_num':rec.excise_reg_no,
                        'range':rec.range,
                        'division':rec.division_name,
                        'commissionerate':rec.commissionerate,
                        'addrress':rec.address,


                    }
                }
                print vals
                print "-------------------------------------------------------------"
            return vals




    
    # def supplier_information(self, cr, uid,ids, company_selection, context=None):
    #     vals = {}
    #     a=self.pool.get("res.partner")
    #
    #     if company_selection:
    #         for rec in a.browse(cr,uid,company_selection,context=context):
    #             print rec
    #             vals={
    #             'value':{
    #                         'comapny_name':rec.name,
    #             'reg_num':rec.excise_reg_no,
    #                         'range':rec.range,
    #                         'division':rec.division,
    #                         'commissionerate':rec.commissionerae,
    #                         'addrress':str(rec.street)+" "+str(rec.street2)+" "+str(rec.city)+" "+str(rec.state_id.name)+" "+str(rec.zip)+" "+str(rec.country_id.name),
    #                     }
    #
    #                    }
    #
    #
    #
    #         return vals


class dealer_manufacturer_detail(osv.osv):
    _name="dealer.manufacturer"
    _rec_name="name"
    _columns={
        'type': fields.selection([('manifacturer', 'Manufacturer'), ('dealer', 'Dealer')], 'Type',required=True),
        'name': fields.char('Supplier Name',required=True),
        'address': fields.char('Address',required=True),
        'excise_reg_no':fields.char('Excise Reg No',required=True),
        'range':fields.char('Range',required=True),
        'division_name':fields.char('Division Name',required=True),
        'commissionerate':fields.char('Commissionerate',required=True),

    }

