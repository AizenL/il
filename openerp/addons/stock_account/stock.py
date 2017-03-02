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

from openerp.osv import fields, osv
import pdb
from openerp import SUPERUSER_ID

class stock_location_path(osv.osv):
    _inherit = "stock.location.path"
    _columns = {
        'invoice_state': fields.selection([
            ("invoiced", "Invoiced"),
            ("2binvoiced", "To Be Invoiced"),
            ("none", "Not Applicable")], "Invoice Status",),
    }
    _defaults = {
        'invoice_state': '',
    }

    def _prepare_push_apply(self, cr, uid, rule, move, context=None):
        res = super(stock_location_path, self)._prepare_push_apply(cr, uid, rule, move, context=context)
        res['invoice_state'] = rule.invoice_state or 'none'
        return res

#----------------------------------------------------------
# Procurement Rule
#----------------------------------------------------------
class procurement_rule(osv.osv):
    _inherit = 'procurement.rule'
    _columns = {
        'invoice_state': fields.selection([
            ("invoiced", "Invoiced"),
            ("2binvoiced", "To Be Invoiced"),
            ("none", "Not Applicable")], "Invoice Status",),
        }
    _defaults = {
        'invoice_state': '',
    }

#----------------------------------------------------------
# Procurement Order
#----------------------------------------------------------


class procurement_order(osv.osv):
    _inherit = "procurement.order"
    _columns = {
        'invoice_state': fields.selection([("invoiced", "Invoiced"),
            ("2binvoiced", "To Be Invoiced"),
            ("none", "Not Applicable")
         ], "Invoice Control"),
        }

    def _run_move_create(self, cr, uid, procurement, context=None):
        res = super(procurement_order, self)._run_move_create(cr, uid, procurement, context=context)
        res.update({'invoice_state': procurement.rule_id.invoice_state or procurement.invoice_state or 'none'})
        return res

    _defaults = {
        'invoice_state': ''
        }


#----------------------------------------------------------
# Move
#----------------------------------------------------------

class stock_move(osv.osv):
    _inherit = "stock.move"
    _columns = {
        'invoice_state': fields.selection([("invoiced", "Invoiced"),
            ("2binvoiced", "To Be Invoiced"),
            ("none", "Not Applicable")], "Invoice Control",
            select=True, required=True, track_visibility='onchange',
            states={'draft': [('readonly', False)]}),
        }
    _defaults = {
        'invoice_state': lambda *args, **argv: 'none'
    }

    def _get_master_data(self, cr, uid, move, company, context=None):
        ''' returns a tuple (browse_record(res.partner), ID(res.users), ID(res.currency)'''
        currency = company.currency_id.id
        partner = move.picking_id and move.picking_id.partner_id
        if partner:
            code = self.get_code_from_locs(cr, uid, move, context=context)
            if partner.property_product_pricelist and code == 'outgoing':
                currency = partner.property_product_pricelist.currency_id.id
        return partner, uid, currency

    def _create_invoice_line_from_vals(self, cr, uid, move, invoice_line_vals, context=None):
        return self.pool.get('account.invoice.line').create(cr, uid, invoice_line_vals, context=context)

    def _get_price_unit_invoice(self, cr, uid, move_line, type, context=None):
        """ Gets price unit for invoice
        @param move_line: Stock move lines
        @param type: Type of invoice
        @return: The price unit for the move line
        """
        if context is None:
            context = {}
        if type in ('in_invoice', 'in_refund'):
            return move_line.price_unit
        else:
            # If partner given, search price in its sale pricelist
            if move_line.partner_id and move_line.partner_id.property_product_pricelist:
                pricelist_obj = self.pool.get("product.pricelist")
                pricelist = move_line.partner_id.property_product_pricelist.id
                price = pricelist_obj.price_get(cr, uid, [pricelist],
                        move_line.product_id.id, move_line.product_uom_qty, move_line.partner_id.id, {
                            'uom': move_line.product_uom.id,
                            'date': move_line.date,
                            })[pricelist]
                if price:
                    return price
        return move_line.product_id.lst_price

    def _get_invoice_line_vals(self, cr, uid, move, partner, inv_type, context=None):
        fp_obj = self.pool.get('account.fiscal.position')
        # Get account_id
        fp = fp_obj.browse(cr, uid, context.get('fp_id')) if context.get('fp_id') else False
        name = False
        if inv_type in ('out_invoice', 'out_refund'):
            account_id = move.product_id.property_account_income.id
            if not account_id:
                account_id = move.product_id.categ_id.property_account_income_categ.id
            if move.procurement_id and move.procurement_id.sale_line_id:
                name = move.procurement_id.sale_line_id.name
        else:
            account_id = move.product_id.property_account_expense.id
            if not account_id:
                account_id = move.product_id.categ_id.property_account_expense_categ.id
        fiscal_position = fp or partner.property_account_position
        account_id = fp_obj.map_account(cr, uid, fiscal_position, account_id)

        # set UoS if it's a sale and the picking doesn't have one
        uos_id = move.product_uom.id
        quantity = move.product_uom_qty
        if move.product_uos:
            uos_id = move.product_uos.id
            quantity = move.product_uos_qty

        taxes_ids = self._get_taxes(cr, uid, move, context=context)

        return {
            'name': name or move.name,
            'account_id': account_id,
            'product_id': move.product_id.id,
            'uos_id': uos_id,
            'quantity': quantity,
            'price_unit': self._get_price_unit_invoice(cr, uid, move, inv_type),
            'invoice_line_tax_id': [(6, 0, taxes_ids)],
            'discount': 0.0,
            'account_analytic_id': False,
        }

    def _get_moves_taxes(self, cr, uid, moves, inv_type, context=None):
        #extra moves with the same picking_id and product_id of a move have the same taxes
        extra_move_tax = {}
        is_extra_move = {}
        for move in moves:
            if move.picking_id:
                is_extra_move[move.id] = True
                if not (move.picking_id, move.product_id) in extra_move_tax:
                    extra_move_tax[move.picking_id, move.product_id] = 0
            else:
                is_extra_move[move.id] = False
        return (is_extra_move, extra_move_tax)

    def action_cancel(self, cr, uid, ids, context=None):
        res = super(stock_move, self).action_cancel(cr, uid, ids, context=context)
        self.write(cr, uid, ids, {'invoice_state': 'none'}, context=context)
        return res

#----------------------------------------------------------
# Picking
#----------------------------------------------------------

class stock_picking(osv.osv):
    _inherit = 'stock.picking'
    def __get_invoice_state(self, cr, uid, ids, name, arg, context=None):
        result = {}
        for pick in self.browse(cr, uid, ids, context=context):
            result[pick.id] = 'none'
            for move in pick.move_lines:
                if move.invoice_state == 'invoiced':
                    result[pick.id] = 'invoiced'
                elif move.invoice_state == '2binvoiced':
                    result[pick.id] = '2binvoiced'
                    break
        return result

    def __get_picking_move(self, cr, uid, ids, context={}):
        res = []
        for move in self.pool.get('stock.move').browse(cr, uid, ids, context=context):
            if move.picking_id and move.invoice_state != move.picking_id.invoice_state:
                res.append(move.picking_id.id)
        return res

    def _set_inv_state(self, cr, uid, picking_id, name, value, arg, context=None):
        pick = self.browse(cr, uid, picking_id, context=context)
        moves = [x.id for x in pick.move_lines]
        move_obj= self.pool.get("stock.move")
        move_obj.write(cr, uid, moves, {'invoice_state': value}, context=context)

    _columns = {
        'invoice_state': fields.function(__get_invoice_state, type='selection', selection=[
            ("invoiced", "Invoiced"),
            ("2binvoiced", "To Be Invoiced"),
            ("none", "Not Applicable")
          ], string="Invoice Control", required=True,
        fnct_inv = _set_inv_state,
        store={
            'stock.picking': (lambda self, cr, uid, ids, c={}: ids, ['state'], 10),
            'stock.move': (__get_picking_move, ['picking_id', 'invoice_state'], 10),
        },
        ),
    }
    _defaults = {
        'invoice_state': lambda *args, **argv: 'none'
    }

    def _create_invoice_from_picking(self, cr, uid, picking, vals, context=None):
        ''' This function simply creates the invoice from the given values. It is overriden in delivery module to add the delivery costs.
        '''
        invoice_obj = self.pool.get('account.invoice')
        return invoice_obj.create(cr, uid, vals, context=context)

    def _get_partner_to_invoice(self, cr, uid, picking, context=None):
        """ Gets the partner that will be invoiced
            Note that this function is inherited in the sale and purchase modules
            @param picking: object of the picking for which we are selecting the partner to invoice
            @return: object of the partner to invoice
        """
        return picking.partner_id and picking.partner_id.id

#    def action_invoice_create(self, cr, uid, ids, journal_id, group=False, type='out_invoice', context=None):
#        """ Creates invoice based on the invoice state selected for picking.
#        @param journal_id: Id of journal
#        @param group: Whether to create a group invoice or not
#        @param type: Type invoice to be created
#        @return: Ids of created invoices for the pickings
#        """
#        context = context or {}
#        todo = {}
#        for picking in self.browse(cr, uid, ids, context=context):
#            partner = self._get_partner_to_invoice(cr, uid, picking, dict(context, type=type))
            #grouping is based on the invoiced partner
#            if group:
#                key = partner
#            else:
#                key = picking.id
#            for move in picking.move_lines:
#                if move.invoice_state == '2binvoiced':
#                    if (move.state != 'cancel') and not move.scrapped:
#                        todo.setdefault(key, [])
#                        todo[key].append(move)
#        invoices = []
#        for moves in todo.values():
#            invoices += self._invoice_create_line(cr, uid, moves, journal_id, type, context=context)
#        return invoices

    def action_invoice_create(self, cr, uid, ids, journal_id, group=False, type='out_invoice', context=None):
        """ Creates invoice based on the invoice state selected for picking.
        @param journal_id: Id of journal
        @param group: Whether to create a group invoice or not
        @param type: Type invoice to be created
        @return: Ids of created invoices for the pickings

        """
	#pdb.set_trace()
	if self.browse(cr,uid,ids).invoice_state=='2binvoiced':
		#pdb.set_trace()
		source_document=self.browse(cr,SUPERUSER_ID,ids,context=context).origin
		sale_order_obj=self.pool.get("sale.order")
		search_so=sale_order_obj.search(cr,uid,[('name','=',source_document),])
		serch_quotation=sale_order_obj.browse(cr,SUPERUSER_ID,search_so[0]).quotation_id
		#sale_quotation_obj=self.pool.get("sale.quotation")
		#quotation_search=sale_quotation_obj.search(cr,uid,[('name','=',serch_quotation),])
		if serch_quotation:
			if serch_quotation.state=='done':
				serch_quotation.write({'quotation_state':'order_completed'})
			if serch_quotation.state=='sent':
				serch_quotation.write({'quotation_state':'partially_delivered'})
		
        context = context or {}
        todo_commercial_other = {}
        todo_commercial = {}
        todo_excise_moves = {}
	todo_excise_mirinda= {}
	dealer_manu_dict= {ids[0]:[]}
	dealer_manu_list=[]
	todo_excise = {}
	stock_quant_obj = self.pool.get("stock.quant")
	stock_move_obj = self.pool.get("stock.move")
        for picking in self.browse(cr, uid, ids, context=context):
            partner = self._get_partner_to_invoice(cr, uid, picking, dict(context, type=type))
            if group:
                key = partner
            else:
                key = picking.id
            for move in picking.move_lines:
		stock_move_products = {}
		print move
                if move.invoice_state == '2binvoiced':
                    if (move.state != 'cancel') and not move.scrapped:
			    if picking.return_voucher == False and picking.picking_type_id.id == 2:
				quant_ids=[]
				for lines in move.quant_ids:
					#if one product is delivered in 2 lots then don't process the quant 2 times
					if move.product_id.id not in stock_move_products :
						stock_move_products.update({lines.id:move.product_id.id})
						if lines.lot_id.id not in quant_ids :
							quant_ids.append(lines.lot_id.id)
							print "Quant ID=====", lines
							purchase_quant=stock_quant_obj.search(cr,uid,[('lot_id','=',lines.lot_id.id)])
							purchase_stock_move_id = stock_move_obj.search(cr,uid,[('quant_ids','in',purchase_quant), ('picking_id.picking_type_id','=',1),('picking_id.return_voucher','=',False)])
							purchase_stock_move = stock_move_obj.browse(cr,uid,purchase_stock_move_id)
							if purchase_stock_move :
								for pur_stock_move in purchase_stock_move :
									excise_info = pur_stock_move.new_stock_id
									if excise_info :
										if len(excise_info) == 2 :
											dealer1 = excise_info[0].new_company_selection.id
											dealer2 = excise_info[1].new_company_selection.id
											if excise_info[0].type_stage == 'dealer' :
												no_dealer = False
												for x in dealer_manu_list :
													if dealer1 == x.keys()[0] and x.values()[0] == dealer2:
														no_dealer = True
														todo_excise_moves.setdefault(str(dealer1) + ':'+str(dealer2), [])
														todo_excise_moves[str(dealer1) + ':'+str(dealer2)].append({lines.lot_id.id:move})


														break
												if no_dealer == False : 
													dealer_manu_list.append({dealer1 : dealer2})
													todo_excise_moves.setdefault(str(dealer1) + ':'+str(dealer2), [])
													todo_excise_moves.update({str(dealer1) + ':'+str(dealer2):[{lines.lot_id.id:move}]})
											elif excise_info[1].type_stage == 'dealer' :
												no_dealer = False
												for x in dealer_manu_list :
													if dealer2 == x.keys()[0] and x.values()[0] == dealer1:
														no_dealer = True
														todo_excise_moves.setdefault(str(dealer2) + ':'+str(dealer1), [])
														todo_excise_moves[str(dealer2) + ':'+str(dealer1)].append({lines.lot_id.id:move})
														print "====3", todo_excise_moves
														print str(dealer2) + ':'+str(dealer1)
														break
												if no_dealer == False : 
													dealer_manu_list.append({dealer2 : dealer1})
													todo_excise_moves.setdefault(str(dealer2) + ':'+str(dealer1), [])
													todo_excise_moves.update({str(dealer2) + ':'+str(dealer1):[{lines.lot_id.id:move}]})
										if len(excise_info) == 1 :
											dealer1 = excise_info[0].new_company_selection.id
											if excise_info[0].type_stage == 'manifacturer' :
												no_dealer = False
												for x in dealer_manu_list :
													if dealer1 == x.keys()[0] and x.values()[0] == dealer1:
														no_dealer = True
														todo_excise_moves.setdefault(str(dealer1) + ':'+str(dealer1), [])
														todo_excise_moves[str(dealer1) + ':'+str(dealer1)].append({lines.lot_id.id:move})

														break
												if no_dealer == False : 
													dealer_manu_list.append({dealer1 : dealer1})
													todo_excise_moves.setdefault(str(dealer1) + ':'+str(dealer1), [])
													todo_excise_moves.update({str(dealer1) + ':'+str(dealer1):[{lines.lot_id.id:move}]})

									else :
										todo_commercial.setdefault(key, [])
										#todo_commercial[key].append(move)
										todo_commercial[key].append({lines.lot_id.id:move})

							else :
								todo_commercial.setdefault(key, [])
								#todo_commercial[key].append(move)
								todo_commercial[key].append({lines.lot_id.id:move})

			    else :
					pdb.set_trace()
					todo_commercial_other.setdefault(key, [])
					todo_commercial_other[key].append(move)
					#todo_commercial[key].append({lines.lot_id.id:move})

        invoices = []
	if todo_excise_moves :
		for single_excise_invoice in todo_excise_moves : 
			moves = todo_excise_moves[single_excise_invoice]
			context.update({'is_excise':True})
			if type=='out_invoice' :
				journal_id = 1
			invoices += self._invoice_create_line_new(cr, uid, moves, journal_id, type, context=context)

	if todo_commercial :
		for single_commercial_invoice in todo_commercial : 
			moves = todo_commercial[single_commercial_invoice]
			if type=='out_invoice' :
				journal_id = 11
			invoices += self._invoice_create_line(cr, uid, moves, journal_id, type, context=context)

        for moves in todo_commercial_other.values():
	    context.update({'is_excise':False})
            invoices += self._invoice_create_line_other(cr, uid, moves, journal_id, type, context=context)

#        for moves in todo_commercial.values():
#	    context.update({'is_excise':False})
#	    if type=='out_invoice' :
#		journal_id = 11
#            invoices += self._invoice_create_line(cr, uid, moves, journal_id, type, context=context)
        return invoices

    def _get_invoice_vals(self, cr, uid, key, inv_type, journal_id, move, context=None):
        if context is None:
            context = {}
        partner, currency_id, company_id, user_id = key
        if inv_type in ('out_invoice', 'out_refund'):
            account_id = partner.property_account_receivable.id
            payment_term = partner.property_payment_term.id or False
        else:
            account_id = partner.property_account_payable.id
            payment_term = partner.property_supplier_payment_term.id or False
        return {
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
        }

    def _invoice_create_line_new(self, cr, uid, moves, journal_id, inv_type='out_invoice', context=None):
        invoice_obj = self.pool.get('account.invoice')
        move_obj = self.pool.get('stock.move')
	stock_quant_obj = self.pool.get("stock.quant")
#	pdb.set_trace()
        invoices = {}
	new_moves = []
	for move in moves : 
		new_moves.append(move.values()[0])

        is_extra_move, extra_move_tax = move_obj._get_moves_taxes(cr, uid, new_moves, inv_type, context=context)
        product_price_unit = {}

        for mv in moves:
		for m1 in mv :
		    move = mv[m1]
		    company = move.company_id
		    origin = move.picking_id.name
		    partner, user_id, currency_id = move_obj._get_master_data(cr, uid, move, company, context=context)

		    key = (partner, currency_id, company.id, user_id)
		    invoice_vals = self._get_invoice_vals(cr, uid, key, inv_type, journal_id, move, context=context)
		    invoice_vals.update({'is_excise':context.get('is_excise')})
#		    pdb.set_trace()
		    if key not in invoices:
		        # Get account and payment terms
		        invoice_id = self._create_invoice_from_picking(cr, uid, move.picking_id, invoice_vals, context=context)
		        invoices[key] = invoice_id
		    else:
		        invoice = invoice_obj.browse(cr, uid, invoices[key], context=context)
		        merge_vals = {}
		        if not invoice.origin or invoice_vals['origin'] not in invoice.origin.split(', '):
		            invoice_origin = filter(None, [invoice.origin, invoice_vals['origin']])
		            merge_vals['origin'] = ', '.join(invoice_origin)
		        if invoice_vals.get('name', False) and (not invoice.name or invoice_vals['name'] not in invoice.name.split(', ')):
		            invoice_name = filter(None, [invoice.name, invoice_vals['name']])
		            merge_vals['name'] = ', '.join(invoice_name)
		        if merge_vals:
		            invoice.write(merge_vals)
		    invoice_line_vals = move_obj._get_invoice_line_vals(cr, uid, move, partner, inv_type, context=dict(context, fp_id=invoice_vals.get('fiscal_position', False)))
		    invoice_line_vals['invoice_id'] = invoices[key]
		    invoice_line_vals['origin'] = origin
		    if not is_extra_move[move.id]:
		        product_price_unit[invoice_line_vals['product_id'], invoice_line_vals['uos_id']] = invoice_line_vals['price_unit']
		    if is_extra_move[move.id] and (invoice_line_vals['product_id'], invoice_line_vals['uos_id']) in product_price_unit:
		        invoice_line_vals['price_unit'] = product_price_unit[invoice_line_vals['product_id'], invoice_line_vals['uos_id']]
		    if is_extra_move[move.id]:
		        desc = (inv_type in ('out_invoice', 'out_refund') and move.product_id.product_tmpl_id.description_sale) or \
		            (inv_type in ('in_invoice','in_refund') and move.product_id.product_tmpl_id.description_purchase)
		        invoice_line_vals['name'] += ' ' + desc if desc else ''
		        if extra_move_tax[move.picking_id, move.product_id]:
		            invoice_line_vals['invoice_line_tax_id'] = extra_move_tax[move.picking_id, move.product_id]
		        #the default product taxes
		        elif (0, move.product_id) in extra_move_tax:
		            invoice_line_vals['invoice_line_tax_id'] = extra_move_tax[0, move.product_id]
		    duty_per_unit_amount=0.0
#		    for lines in move.quant_ids:
		    purchase_quant = stock_quant_obj.search(cr, uid, [('lot_id', '=', m1)])
		    purchase_stock_move_id = move_obj.search(cr, uid,
										    [('quant_ids', 'in', purchase_quant),
										     ('picking_id.picking_type_id', '=', 1),
										     ('picking_id.return_voucher', '=', False),
										     ])
#		    pdb.set_trace()
		    purchase_stock_move_rec = move_obj.browse(cr, uid, purchase_stock_move_id)
		    if len(purchase_stock_move_rec.new_stock_id) > 1 :
			for manufacturer in purchase_stock_move_rec.new_stock_id :
				
				if manufacturer.type_stage == 'dealer' :
					duty_per_unit_amount=0.0
					duty_per_unit_amount = manufacturer.duty_per_unit
#					continue
		    else :
			for manufacturer in purchase_stock_move_rec.new_stock_id :
				if manufacturer.type_stage == 'manifacturer' :
					duty_per_unit_amount=0.0
					duty_per_unit_amount = manufacturer.duty_per_unit
#					continue
#		    pdb.set_trace()
		    stock_pack_opr_id = self.pool.get('stock.pack.operation').search(cr,uid,[('lot_id','=',m1),('picking_id','=',move.picking_id.id)])
		    new_qty = self.pool.get('stock.pack.operation').browse(cr,uid,stock_pack_opr_id).product_qty
		    invoice_line_vals.update({'price_unit':invoice_line_vals['price_unit'] + duty_per_unit_amount,'quantity':new_qty,'lot_id':m1})
#		    pdb.set_trace()
		    move_obj._create_invoice_line_from_vals(cr, uid, move, invoice_line_vals, context=context)
		    move_obj.write(cr, uid, move.id, {'invoice_state': 'invoiced'}, context=context)
	
        invoice_obj.button_compute(cr, uid, invoices.values(), context=context, set_total=(inv_type in ('in_invoice', 'in_refund')))
        return invoices.values()

    def _invoice_create_line(self, cr, uid, moves, journal_id, inv_type='out_invoice', context=None):
        invoice_obj = self.pool.get('account.invoice')
        move_obj = self.pool.get('stock.move')
    	stock_quant_obj = self.pool.get("stock.quant")
        invoices = {}
    	new_moves = []
    	for move in moves :
        	new_moves.append(move.values()[0])
        is_extra_move, extra_move_tax = move_obj._get_moves_taxes(cr, uid, new_moves, inv_type, context=context)
        product_price_unit = {}
    	stock_move_ids = []#################
    	for mv in moves :#################
        	for m1 in mv :#################
            		stock_move_ids.append(mv[m1])#################

#        for mv in moves:#################

    	for m1 in set(stock_move_ids) :#################
            move = m1#################

#        for move in moves:
            company = move.company_id
            origin = move.picking_id.name
            partner, user_id, currency_id = move_obj._get_master_data(cr, uid, move, company, context=context)

            key = (partner, currency_id, company.id, user_id)
            invoice_vals = self._get_invoice_vals(cr, uid, key, inv_type, journal_id, move, context=context)
            if key not in invoices:
                # Get account and payment terms
                invoice_id = self._create_invoice_from_picking(cr, uid, move.picking_id, invoice_vals, context=context)
                invoices[key] = invoice_id
            else:
                invoice = invoice_obj.browse(cr, uid, invoices[key], context=context)
                merge_vals = {}
                if not invoice.origin or invoice_vals['origin'] not in invoice.origin.split(', '):
                    invoice_origin = filter(None, [invoice.origin, invoice_vals['origin']])
                    merge_vals['origin'] = ', '.join(invoice_origin)
                if invoice_vals.get('name', False) and (not invoice.name or invoice_vals['name'] not in invoice.name.split(', ')):
                    invoice_name = filter(None, [invoice.name, invoice_vals['name']])
                    merge_vals['name'] = ', '.join(invoice_name)
                if merge_vals:
                    invoice.write(merge_vals)
            invoice_line_vals = move_obj._get_invoice_line_vals(cr, uid, move, partner, inv_type, context=dict(context, fp_id=invoice_vals.get('fiscal_position', False)))
            invoice_line_vals['invoice_id'] = invoices[key]
            invoice_line_vals['origin'] = origin
            if not is_extra_move[move.id]:
                product_price_unit[invoice_line_vals['product_id'], invoice_line_vals['uos_id']] = invoice_line_vals['price_unit']
            if is_extra_move[move.id] and (invoice_line_vals['product_id'], invoice_line_vals['uos_id']) in product_price_unit:
                invoice_line_vals['price_unit'] = product_price_unit[invoice_line_vals['product_id'], invoice_line_vals['uos_id']]
            if is_extra_move[move.id]:
                desc = (inv_type in ('out_invoice', 'out_refund') and move.product_id.product_tmpl_id.description_sale) or \
                    (inv_type in ('in_invoice','in_refund') and move.product_id.product_tmpl_id.description_purchase)
                invoice_line_vals['name'] += ' ' + desc if desc else ''
                if extra_move_tax[move.picking_id, move.product_id]:
                    invoice_line_vals['invoice_line_tax_id'] = extra_move_tax[move.picking_id, move.product_id]
                #the default product taxes
                elif (0, move.product_id) in extra_move_tax:
                    invoice_line_vals['invoice_line_tax_id'] = extra_move_tax[0, move.product_id]
#            stock_pack_opr_id = self.pool.get('stock.pack.operation').search(cr,uid,[('lot_id','=',m1),('picking_id','=',move.picking_id.id)])#################
#            new_qty = self.pool.get('stock.pack.operation').browse(cr,uid,stock_pack_opr_id).product_qty
#            pdb.set_trace()#################
#            invoice_line_vals.update({'quantity':new_qty,'lot_id':m1})#################

            move_obj._create_invoice_line_from_vals(cr, uid, move, invoice_line_vals, context=context)
            move_obj.write(cr, uid, move.id, {'invoice_state': 'invoiced'}, context=context)

        invoice_obj.button_compute(cr, uid, invoices.values(), context=context, set_total=(inv_type in ('in_invoice', 'in_refund')))
        return invoices.values()

    def _invoice_create_line_other(self, cr, uid, moves, journal_id, inv_type='out_invoice', context=None):
        invoice_obj = self.pool.get('account.invoice')
        move_obj = self.pool.get('stock.move')
	stock_quant_obj = self.pool.get("stock.quant")

        invoices = {}
        is_extra_move, extra_move_tax = move_obj._get_moves_taxes(cr, uid, moves, inv_type, context=context)
        product_price_unit = {}
        for move in moves:
#        for move in moves:
		    company = move.company_id
		    origin = move.picking_id.name
		    partner, user_id, currency_id = move_obj._get_master_data(cr, uid, move, company, context=context)

		    key = (partner, currency_id, company.id, user_id)
		    invoice_vals = self._get_invoice_vals(cr, uid, key, inv_type, journal_id, move, context=context)
		    if key not in invoices:
		        # Get account and payment terms
		        invoice_id = self._create_invoice_from_picking(cr, uid, move.picking_id, invoice_vals, context=context)
		        invoices[key] = invoice_id
		    else:
		        invoice = invoice_obj.browse(cr, uid, invoices[key], context=context)
		        merge_vals = {}
		        if not invoice.origin or invoice_vals['origin'] not in invoice.origin.split(', '):
		            invoice_origin = filter(None, [invoice.origin, invoice_vals['origin']])
		            merge_vals['origin'] = ', '.join(invoice_origin)
		        if invoice_vals.get('name', False) and (not invoice.name or invoice_vals['name'] not in invoice.name.split(', ')):
		            invoice_name = filter(None, [invoice.name, invoice_vals['name']])
		            merge_vals['name'] = ', '.join(invoice_name)
		        if merge_vals:
		            invoice.write(merge_vals)
		    invoice_line_vals = move_obj._get_invoice_line_vals(cr, uid, move, partner, inv_type, context=dict(context, fp_id=invoice_vals.get('fiscal_position', False)))
		    invoice_line_vals['invoice_id'] = invoices[key]
		    invoice_line_vals['origin'] = origin
		    if not is_extra_move[move.id]:
		        product_price_unit[invoice_line_vals['product_id'], invoice_line_vals['uos_id']] = invoice_line_vals['price_unit']
		    if is_extra_move[move.id] and (invoice_line_vals['product_id'], invoice_line_vals['uos_id']) in product_price_unit:
		        invoice_line_vals['price_unit'] = product_price_unit[invoice_line_vals['product_id'], invoice_line_vals['uos_id']]
		    if is_extra_move[move.id]:
		        desc = (inv_type in ('out_invoice', 'out_refund') and move.product_id.product_tmpl_id.description_sale) or \
		            (inv_type in ('in_invoice','in_refund') and move.product_id.product_tmpl_id.description_purchase)
		        invoice_line_vals['name'] += ' ' + desc if desc else ''
		        if extra_move_tax[move.picking_id, move.product_id]:
		            invoice_line_vals['invoice_line_tax_id'] = extra_move_tax[move.picking_id, move.product_id]
		        #the default product taxes
		        elif (0, move.product_id) in extra_move_tax:
		            invoice_line_vals['invoice_line_tax_id'] = extra_move_tax[0, move.product_id]
		    move_obj._create_invoice_line_from_vals(cr, uid, move, invoice_line_vals, context=context)
		    move_obj.write(cr, uid, move.id, {'invoice_state': 'invoiced'}, context=context)

        invoice_obj.button_compute(cr, uid, invoices.values(), context=context, set_total=(inv_type in ('in_invoice', 'in_refund')))
        return invoices.values()

    def _prepare_values_extra_move(self, cr, uid, op, product, remaining_qty, context=None):
        """
        Need to pass invoice_state of picking when an extra move is created which is not a copy of a previous
        """
        res = super(stock_picking, self)._prepare_values_extra_move(cr, uid, op, product, remaining_qty, context=context)
        res.update({'invoice_state': op.picking_id.invoice_state})
        if op.linked_move_operation_ids:
            res.update({'price_unit': op.linked_move_operation_ids[-1].move_id.price_unit})
        return res
