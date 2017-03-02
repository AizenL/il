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
import itertools
from lxml import etree

from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools import float_compare
import openerp.addons.decimal_precision as dp






############################################ Accounting ##############################################################

class account_invoice(models.Model):
    _inherit = 'account.invoice'

    ########################## sandv function to make the sale order gets added with taxes and other other costs while valididating invoice ###########

    @api.multi
    def action_move_create(self):
        """ Creates invoice related analytics and financial move lines """
        account_invoice_tax = self.env['account.invoice.tax']
        account_move = self.env['account.move']
        sale_order = self.env['sale.order']
        sale_order_line = self.env['sale.order.line']
        purchase_order = self.env['purchase.order']
        purchase_order_line = self.env['purchase.order.line']
        #tax_config = self.env['invoice.tax.config']
        other_charges = 0.00 
        additional = [] 
        tax_search = []
        pick_ids = []
        pack_operations_ids = []

        for inv in self:            
            if not inv.journal_id.sequence_id:
                raise except_orm(_('Error!'), _('Please define sequence on the journal related to this invoice.'))
            if not inv.invoice_line:
                raise except_orm(_('No Invoice Lines!'), _('Please create some invoice lines.'))
            if inv.move_id:
                continue

            ctx = dict(self._context, lang=inv.partner_id.lang)

            if not inv.date_invoice:
                inv.with_context(ctx).write({'date_invoice': fields.Date.context_today(self)})
            date_invoice = inv.date_invoice

            company_currency = inv.company_id.currency_id
            # create the analytical lines, one move line per invoice line
            iml = inv._get_analytic_lines()
            # check if taxes are all computed
            compute_taxes = account_invoice_tax.compute(inv.with_context(lang=inv.partner_id.lang))
            inv.check_tax_lines(compute_taxes)

            # I disabled the check_total feature
            if self.env.user.has_group('account.group_supplier_inv_check_total'):
                if inv.type in ('in_invoice', 'in_refund') and abs(inv.check_total - inv.amount_total) >= (inv.currency_id.rounding / 2.0):
                    raise except_orm(_('Bad Total!'), _('Please verify the price of the invoice!\nThe encoded total does not match the computed total.'))          
          
            if inv.payment_term:
                total_fixed = total_percent = 0
                for line in inv.payment_term.line_ids:
                    if line.value == 'fixed':
                        total_fixed += line.value_amount
                    if line.value == 'procent':
                        total_percent += line.value_amount
                total_fixed = (total_fixed * 100) / (inv.amount_total or 1.0)
                if (total_fixed + total_percent) > 100:
                    raise except_orm(_('Error!'), _("Cannot create the invoice.\nThe related payment term is probably misconfigured as it gives a computed amount greater than the total invoiced amount. In order to avoid rounding issues, the latest line of your payment term must be of type 'balance'."))

            # one move line per tax line
            iml += account_invoice_tax.move_line_get(inv.id)

            if inv.type in ('in_invoice', 'in_refund'):
                ref = inv.reference
            else:
                ref = inv.number

            diff_currency = inv.currency_id != company_currency
            # create one move line for the total and possibly adjust the other lines amount
            total, total_currency, iml = inv.with_context(ctx).compute_invoice_totals(company_currency, ref, iml)

            name = inv.supplier_invoice_number or inv.name or '/'
            totlines = []
            if inv.payment_term:
                totlines = inv.with_context(ctx).payment_term.compute(total, date_invoice)[0]
            if totlines:
                res_amount_currency = total_currency
                ctx['date'] = date_invoice
                for i, t in enumerate(totlines):
                    if inv.currency_id != company_currency:
                        amount_currency = company_currency.with_context(ctx).compute(t[1], inv.currency_id)
                    else:
                        amount_currency = False

                    # last line: add the diff
                    res_amount_currency -= amount_currency or 0
                    if i + 1 == len(totlines):
                        amount_currency += res_amount_currency
                    iml.append({
                        'type': 'dest',
                        'name': name,
                        'price': t[1],
                        'account_id': inv.account_id.id,
                        'date_maturity': t[0],
                        'amount_currency': diff_currency and amount_currency,
                        'currency_id': diff_currency and inv.currency_id.id,
                        'ref': ref,
                    })
            else:
                iml.append({
                    'type': 'dest',
                    'name': name,
                    'price': total,
                    'account_id': inv.account_id.id,
                    'date_maturity': inv.date_due,
                    'amount_currency': diff_currency and total_currency,
                    'currency_id': diff_currency and inv.currency_id.id,
                    'ref': ref
                })

            date = date_invoice

            part = self.env['res.partner']._find_accounting_partner(inv.partner_id)


################################sandv code for creating a new entry line in journal entries for other charges ##########################

            for inv_line in inv.invoice_line:
                if inv.type in ('out_invoice','in_refund'):
                    if inv.other_charges != 0.00:
	                    tmp = (0,0,{
	                        'partner_id' : inv.partner_id.id,
	                        'account_id' : 10,
	                        'date_maturity' : inv.date_due,
	                        'debit' : False,
	                        'credit' : inv.other_charges,
	                        'name' : u'Other Charges',
	                        'ref' : ref or False,

	                        })
	                    break
                if inv.type in ('in_invoice','out_refund'):
                    if inv.other_charges != 0.00:
	                    tmp = (0,0,{
	                        'partner_id' : inv.partner_id.id,
	                        'account_id' : 10,
	                        'date_maturity' : inv.date_due,
	                        'debit' : inv.other_charges,
	                        'credit' : False,
	                        'name' : u'Other Charges',
	                        'ref' : ref or False,

	                        })
	                    break
########################################################################################################################################
            line = [(0, 0, self.line_get_convert(l, part.id, date)) for l in iml]
            print "\n\n\n\n\n----------->line",line
################################sandv code for creating a new entry line in journal entries for other charges ##########################
            if inv.other_charges!= 0.00:
                line.append(tmp)
#######################################################################################################################################          	

################################sandv code for adding other charges to the partner ##########################
            if inv.type in ('out_invoice'):
                for i,ml in enumerate(line):
                    if ml[2]['debit'] and ml[2]['account_id'] == inv.account_id.id:
                        ml[2]['debit'] = ml[2]['debit'] + inv.other_charges
            if inv.type in ('out_refund'):
                for i,ml in enumerate(line):
                    if ml[2]['credit']  and ml[2]['account_id'] == inv.account_id.id:
                        ml[2]['credit'] = ml[2]['credit'] + inv.other_charges
            if inv.type in ('in_invoice','in_refund'):
                for i,ml in enumerate(line):
                    if ml[2]['debit']  and ml[2]['account_id'] == inv.account_id.id:
                        ml[2]['debit'] = ml[2]['debit'] + inv.other_charges 
                    if ml[2]['credit']  and ml[2]['account_id'] == inv.account_id.id :
                        ml[2]['credit'] = ml[2]['credit'] + inv.other_charges

    		
            if inv.type in ('in_invoice'):
            	for val in inv.purchase_ids:
        	        pick_ids += [picking.id for picking in val.picking_ids]
                	if pick_ids:
        	    		for obj in pick_ids:
        	    		    pack_operations_ids = self.env['stock.pack.operation'].search([('picking_id','=',obj)])
        	    	if pack_operations_ids:
        	    		for var in pack_operations_ids:
        	    			var.write({'invoice_id':inv.id,'purchase_id': val.id})
            if inv.type in ('out_invoice'):
                for var in inv.sale_ids:
                    pick_ids += [picking.id for picking in var.picking_ids]
                    if pick_ids:
                        for ids in pick_ids:
                            pack_operations_ids = self.env['stock.move'].search([('picking_id','=',ids)])
                        if pack_operations_ids:
                            for variable in pack_operations_ids:
                                for quant in variable.quant_ids:
                                    pack_ids = self.env['stock.pack.operation'].search([('lot_id','=',quant.lot_id.id),('invoice_id','!=',False)])
                                    print "\n\n\n\n\n____>",pack_ids
                                    for each in pack_ids:
	                                    for invoice in each.invoice_id:
	                                    	for inv_line in inv.invoice_line:
					    	    if invoice.sale_ids:
						        for order in invoice.sale_ids:
						            for line in order.order_line:
						                                                
				                                cr = self.env.cr
				                                uid = self.env.uid
				                                context = self.env.context
				                                line.write({'excise_amount': invoice.tax_amount})
				                                field_name = [invoice.amount_tax, invoice.other_charges, invoice.amount_total, invoice.amount_untaxed]
				                                arg = None                            
				                                result = order._amount_all(field_name, arg, context=context)
				                                tax_update = order.button_dummy()
	                                    	# for inv_lines in invoice.tax_line:
	                                    	# print"\n\n\n\n\n\n\n\n\n\n******",inv.amount_tax
            # print aaaa


###############################################################################################################
            line = inv.group_lines(iml, line)


            journal = inv.journal_id.with_context(ctx)
            if journal.centralisation:
                raise except_orm(_('User Error!'),
                        _('You cannot create an invoice on a centralized journal. Uncheck the centralized counterpart box in the related journal from the configuration menu.'))

            line = inv.finalize_invoice_move_lines(line)

            move_vals = {
                'ref': inv.reference or inv.name,
                'line_id': line,
                'journal_id': journal.id,
                'date': inv.date_invoice,
                'narration': inv.comment,
                'company_id': inv.company_id.id,
            }
            ctx['company_id'] = inv.company_id.id
            period = inv.period_id
            if not period:
                period = period.with_context(ctx).find(date_invoice)[:1]
            if period:
                move_vals['period_id'] = period.id
                for i in line:
                    i[2]['period_id'] = period.id

            ctx['invoice'] = inv
            ctx_nolang = ctx.copy()
            ctx_nolang.pop('lang', None)
            move = account_move.with_context(ctx_nolang).create(move_vals)

            # make the invoice point to that move
            vals = {
                'move_id': move.id,
                'period_id': period.id,
                'move_name': move.name,
            }
            inv.with_context(ctx).write(vals)
            # Pass invoice in context in method post: used if you want to get the same
            # account move reference when creating the same invoice after a cancelled one: 


################################sandv code for adding other charges to the sale order/Purchase for so corections ##########################
            for inv_line in inv.invoice_line:
            	if inv.sale_ids:
	                for order in inv.sale_ids:
	                    for line in order.order_line:
	                        if inv.amount_total != order.amount_total:
	                            if inv_line.product_id.id == line.product_id.id:                                
	                                cr = self.env.cr
	                                uid = self.env.uid
	                                context = self.env.context
	                                line.write({'pandf_value': inv_line.pandf_value,'freight_value': inv_line.freight_value,
	                                    'insurance_value':inv_line.insurance_value,'tax_id': [(6, 0, [x.id for x in inv_line.invoice_line_tax_id])]})                                 
	                                field_name = [inv.amount_tax, inv.other_charges, inv.amount_total, inv.amount_untaxed]
	                                arg = None                            
	                                result = order._amount_all(field_name, arg, context=context)
	                                tax_update = order.button_dummy()
                if inv.purchase_ids:
                    for po_order in inv.purchase_ids:
	                    for po_line in po_order.order_line:
	                        if inv.amount_total != po_order.amount_total:
	                            if inv_line.product_id.id == po_line.product_id.id:
	                                cr = self.env.cr
	                                uid = self.env.uid
	                                context = self.env.context
	                                po_line.write({'pandf_value': inv_line.pandf_value,'freight_value': inv_line.freight_value,
	                                    'insurance_value':inv_line.insurance_value,'taxes_id': [(6, 0, [x.id for x in inv_line.invoice_line_tax_id])]})                                 
	                                field_name = [inv.amount_tax, inv.other_charges, inv.amount_total, inv.amount_untaxed]
	                                arg = None                            
	                                result = po_order._amount_all(field_name, arg, context=context)
	                                tax_update = po_order.button_dummy()
###############################################################################################################
            move.post()       
          
        self._log_event()
        return True


    @api.model
    def line_get_convert(self, line, part, date):
        return {
            'date_maturity': line.get('date_maturity', False),
            'partner_id': part,
            'name': line['name'][:64],
            'date': date,
            'debit': line['price']>0 and line['price'],
            'credit': line['price']<0 and -line['price'],
            'account_id': line['account_id'],
            'analytic_lines': line.get('analytic_lines', []),
            'amount_currency': line['price']>0 and abs(line.get('amount_currency', False)) or -abs(line.get('amount_currency', False)),
            'currency_id': line.get('currency_id', False),
            'tax_code_id': line.get('tax_code_id', False),
            'tax_amount': line.get('tax_amount', False),
            'ref': line.get('ref', False),
            'quantity': line.get('quantity',1.00),
            'product_id': line.get('product_id', False),
            'product_uom_id': line.get('uos_id', False),
            'analytic_account_id': line.get('account_analytic_id', False),
        }


    ################# sandv function to make the invoice calculation addition with other charges ###########
    @api.one
    @api.depends('invoice_line.price_subtotal', 'tax_line.amount')
    def _compute_amount(self):
    	packing_charges = 0.00
    	freight_charges = 0.00
    	insurance_charges = 0.00
    	other_charges = 0.00
        self.amount_untaxed = sum(line.price_subtotal for line in self.invoice_line)
        self.amount_tax = sum(line.amount for line in self.tax_line)        
        packing_charges = self.packing_charges
        freight_charges = self.freight_charges
        insurance_charges = self.insurance_charges
        other_charges = packing_charges + freight_charges + insurance_charges
        self.other_charges = other_charges
        self.amount_total = self.amount_untaxed + self.amount_tax + self.other_charges

    ################# sandv function to make the other charges calculation###########

    amount_untaxed = fields.Float(string='Subtotal', digits=dp.get_precision('Account'),store=True,readonly=True,compute='_compute_amount', track_visibility='always')
    amount_tax = fields.Float(string='Tax', digits=dp.get_precision('Account'), store=True, readonly=True, compute='_compute_amount')
    amount_total = fields.Float(string='Total', digits=dp.get_precision('Account'),store=True, readonly=True, compute='_compute_amount')
    other_charges = fields.Float(string='Other Charges', digits=dp.get_precision('Account'),store=True, readonly=True, compute='_compute_amount')
    sale_ids = fields.Many2many('sale.order', 'sale_order_invoice_rel', 'invoice_id', 'order_id', 'Sale Orders', readonly=True, help="This is the list of sale orders related to this invoice.")
    purchase_ids = fields.Many2many('purchase.order', 'purchase_order_invoice_rel', 'invoice_id', 'order_id', 'Purchase Orders', readonly=True, help="This is the list of purchase orders related to this invoice.")
    packing_charges = fields.Float(string='Packing Charges', digits=dp.get_precision('Account'),readonly=False)
    freight_charges = fields.Float(string='Freight Charges', digits=dp.get_precision('Account'),readonly=False)
    insurance_charges = fields.Float(string='Insurance Charges', digits=dp.get_precision('Account'), readonly=False)

    _defaults = {
    'packing_charges' : 0.00,
    'freight_charges' : 0.00,
    'insurance_charges' : 0.00,
    }



class stock_pack_operation(models.Model):
    _inherit = 'stock.pack.operation'

    invoice_id = fields.Many2one('account.invoice','Invoice Reference')
    purchase_id = fields.Many2one('purchase.order','Purchase Reference')
    sale_id = fields.Many2one('sale.order','Sale Reference')
    
