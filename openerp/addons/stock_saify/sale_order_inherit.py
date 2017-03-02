from datetime import datetime, date
from lxml import etree
import time

from openerp import SUPERUSER_ID
from openerp import tools,api
from openerp import models, api, fields
from openerp.addons.resource.faces import task as Task
from openerp.osv import fields, osv
from openerp.tools import float_is_zero
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
import re
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP
import datetime
import pdb


class sale_order(osv.osv):
    _inherit = "sale.order"
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
            }
            val = val1 = 0.0
            cur = order.pricelist_id.currency_id
            for line in order.order_line:
                val1 += line.price_subtotal
                val += self._amount_line_tax(cr, uid, line, context=context)
            res[order.id]['amount_tax'] = cur_obj.round(cr, uid, cur, val)
            res[order.id]['amount_untaxed'] = cur_obj.round(cr, uid, cur, val1)
            res[order.id]['amount_total'] = res[order.id]['amount_untaxed']
        return res
    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('sale.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()


    _columns = {
        'state': fields.selection([
            ('draft', 'Draft'),
            ('sent', 'Quotation Sent'),
            ('cancel', 'Cancelled'),
            ('waiting_date', 'Waiting Schedule'),
            ('progress', 'Sales Order'),
            ('manual', 'Sale to Invoice'),
            ('shipping_except', 'Shipping Exception'),
            ('invoice_except', 'Invoice Exception'),
            ('done', 'Done'),
        ], 'Status', readonly=True, copy=False, help="Gives the status of the quotation or sales order.\
                  \nThe exception status is automatically set when a cancel operation occurs \
                  in the invoice validation (Invoice Exception) or in the picking list process (Shipping Exception).\nThe 'Waiting Schedule' status is set when the invoice is confirmed\
                   but waiting for the scheduler to run on the order date.", select=True),

        'sale_order_payment_information': fields.many2one('payment.terms', 'Payment Terms'),
        'sale_order_shipping_information': fields.many2one('shipping.terms', 'Shipping Terms'),
        'amount_untaxed': fields.function(_amount_all_wrapper, digits_compute=dp.get_precision('Account'), string='Untaxed Amount',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The amount without tax.", track_visibility='always'),
        'amount_tax': fields.function(_amount_all_wrapper, digits_compute=dp.get_precision('Account'), string='Taxes',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The tax amount."),
        'amount_total': fields.function(_amount_all_wrapper, digits_compute=dp.get_precision('Account'), string='Total',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The total amount."),


         }
    def _prepare_order_line_procurement(self, cr, uid, order, line, group_id=False, context=None):
        vals = super(sale_order, self)._prepare_order_line_procurement(cr, uid, order, line, group_id=group_id,context=context)
        # print "____________________________________________________________________"
        # print vals
        location_id = order.partner_shipping_id.property_stock_customer.id
        vals['location_id'] = location_id
        routes = line.route_id and [(4, line.route_id.id)] or []
        vals['route_ids'] = routes
        vals['warehouse_id'] = order.warehouse_id and order.warehouse_id.id or False
        vals['partner_dest_id'] = order.partner_shipping_id.id
        vals['unit_price'] = line.price_unit
        print vals['unit_price']
        return vals

    # def create(self, cr, uid, vals, context=None):
    #     if vals.get('name', '/') == '/':
    #         pad_s = self.pool.get('ir.sequence').get(cr, uid, 'sale.order')  # get seq. like : 'SO111'

    #         pad_s = pad_s.replace('SO', '')  # remove the 'SO' from the seq number
    #         print "\n\n\n\n++++date",fields.date.today()
    #         val = fields.date.today()
    #         print "\n\n\n\n++++val",val
    #         your_new_so_name = 'SO/' + str(date.today().year) + '/1' + str(pad_s)
    #         print your_new_so_name

    #         # >target is 'SO'SO14/06/17-001
    #         vals.update({'name': your_new_so_name})

    #     return super(sale_order, self).create(cr, uid, vals, context=context)

    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        """Prepare the dict of values to create the new invoice for a
           sales order. This method may be overridden to implement custom
           invoice generation (making sure to call super() to establish
           a clean extension chain).

           :param browse_record order: sale.order record to invoice
           :param list(int) line: list of invoice line IDs that must be
                                  attached to the invoice
           :return: dict of value to create() the invoice
        """
        if context is None:
            context = {}
        journal_id = self.pool['account.invoice'].default_get(cr, uid, ['journal_id'], context=context)['journal_id']
        if not journal_id:
            raise osv.except_osv(_('Error!'),
                                 _('Please define sales journal for this company: "%s" (id:%d).') % (
                                 order.company_id.name, order.company_id.id))
        invoice_vals = {
            'name': order.client_order_ref or '',
            'origin': order.name,
            'type': 'out_invoice',
            'reference': order.client_order_ref or order.name,
            'account_id': order.partner_invoice_id.property_account_receivable.id,
            'partner_id': order.partner_invoice_id.id,
            'journal_id': journal_id,
            'invoice_line': [(6, 0, lines)],
            'currency_id': order.pricelist_id.currency_id.id,
            'comment': order.note,
            'payment_term': order.payment_term and order.payment_term.id or 0,
            'fiscal_position': order.fiscal_position.id or order.partner_invoice_id.property_account_position.id,
            'date_invoice': context.get('date_invoice', False),
            'company_id': order.company_id.id,
            'user_id': order.user_id and order.user_id.id or False,
            'section_id': order.section_id.id,
            'pay_term':order.sale_order_payment_information.payment_information or False,
            'ship_term': order.sale_order_shipping_information.shipping_information or False,
        }

        # Care for deprecated _inv_get() hook - FIXME: to be removed after 6.1
        invoice_vals.update(self._inv_get(cr, uid, order, context=context))
        return invoice_vals

    def print_quotation(self, cr, uid, ids, context=None):
        ''' This function prints the sales order and mark it as sent, so that we can see more easily the next step of the workflow'''
        assert len(ids) == 1, 'This option should only be used for a single id at a time'
        self.signal_workflow(cr, uid, ids, 'quotation_sent')


class sales_order_line_inherit(osv.osv):
    _inherit = "sale.order.line"
    _order = 'sale_data desc, order_id desc, sequence, id'
    _columns = {
        'brand_name': fields.many2one('product.brand', 'Brand'),
        'il_part_no': fields.char('IL Part No'),
	'customer_code': fields.char('Customer Code',),
        'quotation_amount':fields.float('Quotation Amount'),
        'sale_data': fields.datetime(
        comodel_name='sale.order', string='Sale Date',
        related='order_id.date_order', store=True)
    }

##############Inherit sale order line confirm button to create the purchase planning view records
    def button_confirm(self, cr, uid, ids, context=None):
        purchase_forecast_obj = self.pool.get('purchase.forecast')
        sale_order_lines = self.browse(cr,uid,ids)
        for sale_order_line in sale_order_lines :
            forecast_qty = sale_order_line.product_id.virtual_available
            actual_qty_in_stock = forecast_qty-sale_order_line.product_id.qty_available
            if actual_qty_in_stock > 0 :
                qty_in_stock = actual_qty_in_stock
            else : 
                qty_in_stock = 0
            if forecast_qty < 0 :
                vals=({'qty_to_purchase':sale_order_line.product_uom_qty,
	                'il_part':sale_order_line.product_id.default_code,
	                'product_id':sale_order_line.product_id.id,
	                'so_date':sale_order_line.order_id.date_order,
	                'order_id':sale_order_line.order_id.id,
	                'picking_id':False,
	                'product_uom_qty':sale_order_line.product_uom_qty,
	                'qty_to_purchase':sale_order_line.product_uom_qty,
	                'qty_in_stock':qty_in_stock,
                })
                purchase_forecast_obj.create(cr,uid,vals)
            elif sale_order_line.product_uom_qty > forecast_qty :
                if forecast_qty > 0 :
                    qty_in_stock = forecast_qty
                else : 
                    qty_in_stock = 0

                qty_to_purchase = sale_order_line.product_uom_qty - forecast_qty
                vals=({'qty_to_purchase':sale_order_line.product_uom_qty,
	                'il_part':sale_order_line.product_id.default_code,
	                'product_id':sale_order_line.product_id.id,
	                'so_date':sale_order_line.order_id.date_order,
	                'order_id':sale_order_line.order_id.id,
	                'picking_id':False,
	                'product_uom_qty':sale_order_line.product_uom_qty,
	                'qty_to_purchase':qty_to_purchase,
	                'qty_in_stock':qty_in_stock,
                })

                purchase_forecast_obj.create(cr,uid,vals)
	return super(sales_order_line_inherit, self).button_confirm(cr, uid, ids,context=context)

    def button_cancel(self, cr, uid, ids, context=None):
        purchase_forecast_obj = self.pool.get('purchase.forecast')
        for so_id in self.browse(cr, uid, ids, context=context):
            pf_search = purchase_forecast_obj.search(cr, uid, [('order_id', '=', so_id.order_id.id)], context=context)
            #pf_browse = purchase_forecast_obj.browse(cr, uid, pf_search, context=context)
            purchase_forecast_obj.write(cr, uid, pf_search, {'state': 'cancel'}, context=context)
        return super(sales_order_line_inherit, self).button_cancel(cr, uid, ids, context=context)


    @api.multi
    def action_sale_product_prices(self):
        #pdb.set_trace()
        id2 = self.env.ref(
            'stock_saify.last_sale_product_prices_view')
        sale_lines = self.search(
            [('order_id', '!=', self.id),
             ('product_id', '=', self.product_id.id),
             ('order_partner_id','=',self.order_partner_id.id),
             ('state','in',('done','confirmed'))],
            order='sale_data')
        return {
            'view_type': 'tree',
            'view_mode': 'tree',
            'res_model': 'sale.order.line',
            'views': [(id2.id, 'tree')],
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'domain': "[('id','in',[" + ','.join(map(str, sale_lines.ids)) + "])]",
        }

    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0, uom=False, qty_uos=0, uos=False, name='',
                          partner_id=False, lang=False, update_tax=True, date_order=False, packaging=False,
                          fiscal_position=False, flag=False, context=None):
        context = context or {}
        lang = lang or context.get('lang', False)
        if not partner_id:
            raise osv.except_osv(_('No Customer Defined!'),
                                 _('Before choosing a product,\n select a customer in the sales form.'))
        warning = False
        product_uom_obj = self.pool.get('product.uom')
        partner_obj = self.pool.get('res.partner')
        product_obj = self.pool.get('product.product')

        #qty_type=self.pool.get('product.template').browse(cr,uid,product).min_quantity1
        #print "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++",qty_type
        #print aaaa
        # brand=self.pool.get('product.template').browse(cr,uid,product).product_brand
        # print "-------------------------------------------------------------------------------------------"
        # print il_part
        # print brand
        # print "-------------------------------------------------------------------------------------------"
        partner = partner_obj.browse(cr, uid, partner_id)
        lang = partner.lang
        context_partner = context.copy()
        context_partner.update({'lang': lang, 'partner_id': partner_id})
        if not product:
            return {'value': {'th_weight': 0, 'product_uos_qty': qty}, 'domain': {'product_uom': [], 'product_uos': []}}
        if not date_order:
            date_order = time.strftime(DEFAULT_SERVER_DATE_FORMAT)
        result = {}
        warning_msgs = ''
        product_obj = product_obj.browse(cr, uid, product, context=context_partner)
        il_part = product_obj.default_code
        brand = product_obj.product_brand.id

        uom2 = False
        if uom:
            uom2 = product_uom_obj.browse(cr, uid, uom)
            if product_obj.uom_id.category_id.id != uom2.category_id.id:
                uom = False
        if uos:
            if product_obj.uos_id:
                uos2 = product_uom_obj.browse(cr, uid, uos)
                if product_obj.uos_id.category_id.id != uos2.category_id.id:
                    uos = False
            else:
                uos = False
        fpos = False
        result['il_part_no'] = il_part
        result['brand_name'] = brand
        if not fiscal_position:
            fpos = partner.property_account_position or False
        else:
            fpos = self.pool.get('account.fiscal.position').browse(cr, uid, fiscal_position)

        # if update_tax:  # The quantity only have changed
        #     # The superuser is used by website_sale in order to create a sale order. We need to make
        #     # sure we only select the taxes related to the company of the partner. This should only
        #     # apply if the partner is linked to a company.
        #     if uid == SUPERUSER_ID and context.get('company_id'):
        #         taxes = product_obj.taxes_id.filtered(lambda r: r.company_id.id == context['company_id'])
        #     else:
        #         taxes = product_obj.taxes_id
        #     result['tax_id'] = self.pool.get('account.fiscal.position').map_tax(cr, uid, fpos, taxes)
        if not flag:
            result['name'] = \
            self.pool.get('product.product').name_get(cr, uid, [product_obj.id], context=context_partner)[0][1]
            if product_obj.description_sale:
                result['name'] += '\n' + product_obj.description_sale
        domain = {}
        if (not uom) and (not uos):
            result['product_uom'] = product_obj.uom_id.id
            if product_obj.uos_id:
                result['product_uos'] = product_obj.uos_id.id
                result['product_uos_qty'] = qty * product_obj.uos_coeff
                uos_category_id = product_obj.uos_id.category_id.id
            else:
                result['product_uos'] = False
                result['product_uos_qty'] = qty
                uos_category_id = False
            result['th_weight'] = qty * product_obj.weight
            domain = {'product_uom': [('category_id', '=', product_obj.uom_id.category_id.id)],
                      'product_uos': [('category_id', '=', uos_category_id)]}
        elif uos and not uom:  # only happens if uom is False
            result['product_uom'] = product_obj.uom_id and product_obj.uom_id.id
            result['product_uom_qty'] = qty_uos / product_obj.uos_coeff
            result['th_weight'] = result['product_uom_qty'] * product_obj.weight
        elif uom:  # whether uos is set or not
            default_uom = product_obj.uom_id and product_obj.uom_id.id
            q = product_uom_obj._compute_qty(cr, uid, uom, qty, default_uom)
            if product_obj.uos_id:
                result['product_uos'] = product_obj.uos_id.id
                result['product_uos_qty'] = qty * product_obj.uos_coeff
            else:
                result['product_uos'] = False
                result['product_uos_qty'] = qty
            result['th_weight'] = q * product_obj.weight  # Round the quantity up
        if not uom2:
            uom2 = product_obj.uom_id
            # get unit price
        if not pricelist:
            warn_msg = _(
                'You have to select a pricelist or a customer in the sales form !\n''Please set one before choosing a product.')
            warning_msgs += _("No Pricelist ! : ") + warn_msg + "\n\n"
        else:
            ctx = dict(context, uom=uom or result.get('product_uom'), date=date_order, )
            price = \
            self.pool.get('product.pricelist').price_get(cr, uid, [pricelist], product, qty or 1.0, partner_id, ctx)[
                pricelist]
	    price_price = self.pool.get('product.pricelist').browse(cr,uid,pricelist)
	    price_item = ctx.get("price_item")
	    result['customer_code'] = price_item.customer_code
            if price is False:
                if product:
                    product_obj = self.pool.get('product.product').browse(cr, uid, product)
                    result['price_unit'] = product_obj.list_price

            #if price is False:
             #   warn_msg = _(
              #      "Cannot find a pricelist line matching this product and quantity.\n""You have to change either the product, the quantity or the pricelist.")
               # warning_msgs += _("No valid pricelist line found ! :") + warn_msg + "\n\n"
            else:
                #if update_tax:
                    #price = self.pool['account.tax']._fix_tax_included_price(cr, uid, price, taxes, result['tax_id'])
                result.update({'price_unit': price})
                if context.get('uom_qty_change', False):
                    values = {'price_unit': price}
                    if result.get('product_uos_qty'):
                        values['product_uos_qty'] = result['product_uos_qty']
                    return {'value': values, 'domain': {}, 'warning': False}
        from_loc = partner.state_id
        cust_loc = partner.state_id
        if not from_loc:
            raise osv.except_osv(_('Warning!'), _('Please define the State for the Customer: %s' % (partner.name)))
        #pdb.set_trace()
        categ = product_obj.categ_id.id
        loc_tax_search = self.pool.get('delivery.location.tax').search(cr, uid, [('name', '=', from_loc.id),('to_state', '=', cust_loc.id)], limit=1)
        categ_tax_search = self.pool.get('tax.category').search(cr, uid, [('tax_id', 'in', loc_tax_search),('name', '=', categ)], limit=1)
        if categ_tax_search:
            tax = self.pool.get('tax.category').browse(cr, uid,categ_tax_search).account_tax
            if tax:
                result.update({'tax_id': [(6,0, [tax.id])]})
        if warning_msgs:
            warning = {'title': _('Configuration Error!'), 'message': warning_msgs}
        if product:
            product_obj = self.pool.get('product.product').browse(cr, uid, product)
            product_name1=product_obj.name
            #line_min = product

            min_qty=product_obj.min_quantity1
            type_qty=product_obj.type_quantity1
#	    pdb.set_trace()
            print "++++++++++++++++++++++++++++++++++"
#            print product_name1
            print type_qty
            if qty<min_qty:
                print"+++++++++++++++++++++++++++++++++++++++++++++++++"
                print"HEllo"
#                raise osv.except_osv(_('Warning!'), _(
#                    "Quantity is less than"+str(type_qty)+"  of  "+str(min_qty)+" !\nPlease Re-enter Quantity"))
                #print aaa
                result.update({'product_uom_qty': min_qty})
                if type_qty=='Minimum':
                    warning = {'title': _('Minimum Quantity Error!'), 'message': 'Minimum order Qty is   '+str(min_qty)+'     for     '+product_name1}
                else:
                    
                    if not (qty%min_qty ==0):
                        warning = {'title': _('Multiple Quantity Error!'),'message': 'Enter Qty in Multiple of           '+str(min_qty)+'          for        '+product_name1}
            if qty>min_qty:

                if type_qty=='Multiple':
                    if not (qty%min_qty ==0):
                        result.update({'product_uom_qty': min_qty})
                        warning = {'title': _('Multiple Quantity Error!'),'message': 'Enter Qty in Multiple of           '+str(min_qty)+'          for        '+product_name1}



        return {'value': result, 'domain': domain, 'warning': warning}

    def onchange_il_partno(self,cr,uid,ids,il_part_no,product,context=None):
        #print "\n\n\n\n\n\+++++++",product_id
        #print "\n\n\n\n\n++++++",il_part_no
#       pdb.set_trace()
        result={}
        if il_part_no and product:
             product_obj = self.pool.get('product.product')
             old_il_part_no=product_obj.browse(cr, uid, product, context=context).default_code

             if old_il_part_no :
                if il_part_no != old_il_part_no :
                    result.update({'il_part_no': old_il_part_no})
                    warning = {'title': _('IL Part No Error!'), 'message': 'Dont Change IL PART No'}
                    return{'warning':warning,'value':result}


#     def onchange_qty(self,cr,uid,ids,qty,product,context=None):
#         #print "\n\n\n\n\n\+++++++",product_id
#         #print "\n\n\n\n\n++++++",il_part_no
# #       pdb.set_trace()
#         result={}
#         if qty and product:
#              product_obj = self.pool.get('product.product')
#              min_qty=product_obj.min_quantity1
#              product_name1=product_obj.name
#              result.update({'product_uom_qty': min_qty})
#              if not (qty%min_qty ==0):
#                 warning = {'title': _('Multiple Quantity Error!'),'message': 'Enter Qty in Multiple of'+str(min_qty)+'for'+product_name1}

             
#              return{'warning':warning,'value':result}

    def onchange_brand_name(self,cr,uid,ids,brand_name,product,context=None):
        #pdb.set_trace()
        result={}
        if brand_name and product:
             product_obj = self.pool.get('product.product')


             old_brand=product_obj.browse(cr, uid, product, context=context).product_brand.id
             print old_brand,brand_name
             #  print a

             if old_brand :
                if brand_name != old_brand :
                    result.update({'brand_name': old_brand})
                    warning = {'title': _('Brand Error!'), 'message': 'Dont Change Brand'}
                    return{'warning':warning,'value':result}

    

class product_product(osv.Model):
    _inherit = 'product.product'

    def _sales_count(self, cr, uid, ids, field_name, arg, context=None):
        r = dict.fromkeys(ids, 0)
        domain = [
            ('state', 'in', ['confirmed', 'done']),
            ('product_id', 'in', ids),
        ]
        for group in self.pool['sale.report'].read_group(cr, uid, domain, ['product_id', 'product_uom_qty'],
                                                         ['product_id'], context=context):
            r[group['product_id'][0]] = group['product_uom_qty']
        return r

    def action_view_sales(self, cr, uid, ids, context=None):
        result = self.pool['ir.model.data'].xmlid_to_res_id(cr, uid, 'sale.action_order_line_product_tree',
                                                            raise_if_not_found=True)
        result = self.pool['ir.actions.act_window'].read(cr, uid, [result], context=context)[0]
        result['domain'] = "[('product_id','in',[" + ','.join(map(str, ids)) + "])]"
        return result

    _columns = {
        'sales_count': fields.function(_sales_count, string='# Sales', type='integer'),
    }


class product_template(osv.Model):
    _inherit = 'product.template'

    def _sales_count(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids, 0)
        for template in self.browse(cr, uid, ids, context=context):
            product_search = self.pool.get('product.product').search(cr, uid, [('product_tmpl_id', '=', template.id)],
                                                                     context=context)
	    if product_search :
		    cr.execute(
		        "SELECT sum(product_uom_qty*price_unit) FROM sale_order_line WHERE state in ('confirmed','done') and product_id in %s",
		        (tuple(product_search),))
		    sum_sale = cr.fetchone()[0]
		    res[template.id] = sum_sale
        return res

    def action_view_sales(self, cr, uid, ids, context=None):
        act_obj = self.pool.get('ir.actions.act_window')
        mod_obj = self.pool.get('ir.model.data')
        product_ids = []
        for template in self.browse(cr, uid, ids, context=context):
            product_ids += [x.id for x in template.product_variant_ids]
        result = mod_obj.xmlid_to_res_id(cr, uid, 'sale.action_order_line_product_tree', raise_if_not_found=True)
        result = act_obj.read(cr, uid, [result], context=context)[0]
        result['domain'] = "[('product_id','in',[" + ','.join(map(str, product_ids)) + "])]"
        return result

    _columns = {
        'sales_count': fields.function(_sales_count, string='# Sales', type='integer'),


    }


class payment_terms(osv.osv):
    _name = "payment.terms"
    _rec_name = "payment_information"
    _discription = "Sale-Payment terms information "
    _columns = {
        'payment_information': fields.char('Payment Terms'),

    }


class shipping_terms(osv.osv):
    _name = "shipping.terms"
    _rec_name = "shipping_information"
    _discription = "Sale-Shipping Charges information "
    _columns = {
        'shipping_information': fields.char('Shipping Charges'),

    }



