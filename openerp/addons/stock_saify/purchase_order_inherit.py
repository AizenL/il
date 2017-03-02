from datetime import datetime, date
from lxml import etree
import time

from openerp import SUPERUSER_ID
from openerp import tools
from openerp.addons.resource.faces import task as Task
from openerp.osv import fields, osv
from openerp.tools import float_is_zero
from openerp.tools.translate import _
from openerp.tools.float_utils import float_compare
import openerp.addons.decimal_precision as dp
import re
import pdb
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP

class purchase_shipping_terms(osv.osv):
    _name="purchase.shipping"
    _rec_name="purchase_shipping_information"
    _columns={
        'purchase_shipping_information':fields.char('Shipping Charges'),
        'terms' : fields.char('Terms'),

    }


class purchase_order_line_inherit(osv.osv):
    _inherit="purchase.order.line"
    _columns={
    'brand_name':fields.many2one('product.brand','Brand'),
    'il_part_no':fields.char('IL Part No'),

}


    def onchange_product_id(self, cr, uid, ids, pricelist_id,product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, state='draft', context=None):
        """
        onchange handler of product_id.
        """
        if context is None:
            context = {}
#	pdb.set_trace()
        il_part=self.pool.get('product.product').browse(cr,uid,product_id).default_code
        brand=self.pool.get('product.product').browse(cr,uid,product_id).product_brand
#        pdb.set_trace()

        res = {'value': {'price_unit': price_unit or 0.0, 'name': name or '', 'product_uom' : uom_id or False}}
        if not product_id:
            if not uom_id:
                uom_id = self.default_get(cr, uid, ['product_uom'], context=context).get('product_uom', False)
                res['value']['product_uom'] = uom_id
            return res

        product_product = self.pool.get('product.product')
        product_uom = self.pool.get('product.uom')
        res_partner = self.pool.get('res.partner')
        product_pricelist = self.pool.get('product.pricelist')
        account_fiscal_position = self.pool.get('account.fiscal.position')
        account_tax = self.pool.get('account.tax')
        res['value']['il_part_no'] = il_part
        res['value']['brand_name'] = brand



        # - check for the presence of partner_id and pricelist_id
        #if not partner_id:
        #    raise osv.except_osv(_('No Partner!'), _('Select a partner in purchase order to choose a product.'))
        #if not pricelist_id:
        #    raise osv.except_osv(_('No Pricelist !'), _('Select a price list in the purchase order form before choosing a product.'))

        # - determine name and notes based on product in partner lang.
        context_partner = context.copy()
        if partner_id:

            lang = res_partner.browse(cr, uid, partner_id).lang
            context_partner.update( {'lang': lang, 'partner_id': partner_id} )
        product = product_product.browse(cr, uid, product_id, context=context_partner)
        #call name_get() with partner in the context to eventually match name and description in the seller_ids field
        if not name or not uom_id:
            # The 'or not uom_id' part of the above condition can be removed in master. See commit message of the rev. introducing this line.
            dummy, name = product_product.name_get(cr, uid, product_id, context=context_partner)[0]
            if product.description_purchase:
                name += '\n' + product.description_purchase
            res['value'].update({'name': name})

        # - set a domain on product_uom
        res['domain'] = {'product_uom': [('category_id','=',product.uom_id.category_id.id)]}

        # - check that uom and product uom belong to the same category
        product_uom_po_id = product.uom_po_id.id
        if not uom_id:
            uom_id = product_uom_po_id

        if product.uom_id.category_id.id != product_uom.browse(cr, uid, uom_id, context=context).category_id.id:
            if context.get('purchase_uom_check') and self._check_product_uom_group(cr, uid, context=context):
                res['warning'] = {'title': _('Warning!'), 'message': _('Selected Unit of Measure does not belong to the same category as the product Unit of Measure.')}
            uom_id = product_uom_po_id

        res['value'].update({'product_uom': uom_id})

        # - determine product_qty and date_planned based on seller info
        if not date_order:
            date_order = fields.datetime.now()


        supplierinfo = False
        precision = self.pool.get('decimal.precision').precision_get(cr, uid, 'Product Unit of Measure')
        for supplier in product.seller_ids:
            if partner_id and (supplier.name.id == partner_id):
                supplierinfo = supplier
                if supplierinfo.product_uom.id != uom_id:
                    res['warning'] = {'title': _('Warning!'), 'message': _('The selected supplier only sells this product by %s') % supplierinfo.product_uom.name }
                min_qty = product_uom._compute_qty(cr, uid, supplierinfo.product_uom.id, supplierinfo.min_qty, to_uom_id=uom_id)
                if float_compare(min_qty , qty, precision_digits=precision) == 1: # If the supplier quantity is greater than entered from user, set minimal.
                    if qty:
                        res['warning'] = {'title': _('Warning!'), 'message': _('The selected supplier has a minimal quantity set to %s %s, you should not purchase less.') % (supplierinfo.min_qty, supplierinfo.product_uom.name)}
                    qty = min_qty
        dt = self._get_date_planned(cr, uid, supplierinfo, date_order, context=context).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        qty = qty or 1.0
        res['value'].update({'date_planned': date_planned or dt})
        if qty:
            res['value'].update({'product_qty': qty})

        price = price_unit
        if price_unit is False or price_unit is None:
            # - determine price_unit and taxes_id
            if pricelist_id:
                date_order_str = datetime.strptime(date_order, DEFAULT_SERVER_DATETIME_FORMAT).strftime(DEFAULT_SERVER_DATE_FORMAT)
                price = product_pricelist.price_get(cr, uid, [pricelist_id],
                        product.id, qty or 1.0, partner_id or False, {'uom': uom_id, 'date': date_order_str})[pricelist_id]
            else:
                price = product.standard_price

        taxes = account_tax.browse(cr, uid, map(lambda x: x.id, product.supplier_taxes_id))
        fpos = fiscal_position_id and account_fiscal_position.browse(cr, uid, fiscal_position_id, context=context) or False
        #taxes_ids = account_fiscal_position.map_tax(cr, uid, fpos, taxes, context=context)
        taxes_ids = 0
        price = self.pool['account.tax']._fix_tax_included_price(cr, uid, price, product.supplier_taxes_id, taxes_ids)
        res['value'].update({'price_unit': price, 'taxes_id': taxes_ids})
        #pdb.set_trace()
        from_loc = res_partner.browse(cr, uid, partner_id).state_id
        owner = res_partner.browse(cr, uid, partner_id)
        if not from_loc:
            raise osv.except_osv(_('Warning!'), _('Please define the State for the Partner: %s' % (owner.name)))

        cust_loc = res_partner.browse(cr, uid, partner_id).state_id
        categ = product_product.browse(cr, uid, product_id).categ_id.id
        loc_tax_search = self.pool.get('delivery.location.tax').search(cr, uid, [('name', '=', from_loc.id),('to_state', '=', cust_loc.id)], limit=1)
        categ_tax_search = self.pool.get('tax.category').search(cr, uid, [('tax_id', 'in', loc_tax_search),('name', '=', categ)], limit=1)
        if categ_tax_search:
            tax = self.pool.get('tax.category').browse(cr, uid,categ_tax_search).account_tax_input
            if tax:
                res['value'].update({'taxes_id': [(6,0, [tax.id])]})


        supplier_records = self.pool.get('product.product').browse(cr, uid, product_id).seller_ids
        purchase_supplier_name = res_partner.browse(cr, uid, partner_id).name
	supplier_matched = False
	if supplier_records :
		for supplier in supplier_records :
			if supplier.name.id == partner_id :
				supplier_matched = True
				break
	if supplier_matched == False:
	    res['warning'] = {'title': _('Warning!'),
	                      'message': _('Selected Product is not supplying by %s supplier') % purchase_supplier_name}
	if product_id:
		product_obj = product_product.browse(cr, uid, product_id)
		product_name1=product_obj.name
		min_qty=product_obj.min_quantity1
		type_qty=product_obj.type_quantity1
		if qty<min_qty:
			res['value'].update({'product_qty': min_qty})
			if type_qty=='Minimum':
				res['warning'] = {'title': _('Minimum Quantity Error!'), 'message': 'Minimum order Qty is   '+str(min_qty)+'     for     '+product_name1}
			else:
				if not (qty%min_qty ==0):
					res['value'].update({'product_qty': min_qty})
					res['warning'] = {'title': _('Multiple Quantity Error!'),'message': 'Enter Qty in Multiple of           '+str(min_qty)+'for'+product_name1}
		if qty>min_qty:
			if type_qty=='Multiple':
				if not (qty%min_qty ==0):
					res['value'].update({'product_qty': min_qty})
					res['warning'] = {'title': _('Multiple Quantity Error!'),'message': 'Enter Qty in Multiple of           '+str(min_qty)+'          for        '+product_name1}







        return res

class purchase_order(osv.osv):

    _inherit="purchase.order"

    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('purchase.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()

    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        res = super(purchase_order, self)._amount_all(cr, uid, ids, field_name, arg, context=context)
        #pdb.set_trace()
        # result=super(purchase_order,self)._amount_all(res)

        cur_obj=self.pool.get('res.currency')
        line_obj = self.pool['purchase.order.line']
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
            res[order.id]['amount_total']=res[order.id]['amount_untaxed']
            
        return res

    STATE_SELECTION = [
        ('draft', 'Draft'),
        ('sent', 'RFQ'),
        ('bid', 'Quotation Received'),
        ('confirmed', 'Waiting Approval'),
        ('approved', 'Purchase Confirmed'),
        ('except_picking', 'Shipping Exception'),
        ('except_invoice', 'Invoice Exception'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')

    ]
    _columns={
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

        'purchase_payment':fields.many2one('purchase.payment','Payment Terms'),
        'purchase_shipping': fields.many2one('purchase.shipping', 'Shipping Terms'),
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

    }
    # def create(self, cr, uid, vals, context=None):
    #     if vals.get('name', '/') == '/':
    #         pad_s = self.pool.get('ir.sequence').get(cr, uid, 'purchase.order')  # get seq. like : 'SO111'

    #         pad_s = pad_s.replace('PO', '')  # remove the 'PO' from the seq number
    #         val = fields.date.today()

    #         your_new_so_name = 'PO/' + '%(year)s' + '/2' + str(pad_s)



    #         vals.update({'name': your_new_so_name})

      #  return super(purchase_order, self).create(cr, uid, vals, context=context)

    # def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
    #     #pdb.set_trace()
    #     res = {}
    #     cur_obj=self.pool.get('res.currency')
    #     line_obj = self.pool['purchase.order.line']
    #     for order in self.browse(cr, uid, ids, context=context):
    #         res[order.id] = {
    #             'amount_untaxed': 0.0,
    #             'amount_tax': 0.0,
    #             'amount_total': 0.0,
    #         }
    #         val = val1 = 0.0
    #         cur = order.pricelist_id.currency_id
    #         for line in order.order_line:
    #             val1 += line.price_subtotal
    #             line_price = line_obj._calc_line_base_price(cr, uid, line,
    #                                                         context=context)
    #             line_qty = line_obj._calc_line_quantity(cr, uid, line,
    #                                                     context=context)
    #             for c in self.pool['account.tax'].compute_all(
    #                     cr, uid, line.taxes_id, line_price, line_qty,
    #                     line.product_id, order.partner_id)['taxes']:
    #                 val += c.get('amount', 0.0)
    #         #res[order.id]['amount_tax']=cur_obj.round(cr, uid, cur, val)
    #         res[order.id]['amount_tax']=0.0
    #         res[order.id]['amount_untaxed']=cur_obj.round(cr, uid, cur, val1)
    #         #res[order.id]['amount_total']=res[order.id]['amount_untaxed'] + res[order.id]['amount_tax']
    #         res[order.id]['amount_total']=res[order.id]['amount_untaxed']
    #     return res

    def print_quotation(self, cr, uid, ids, context=None):
        '''This function prints the request for quotation and mark it as sent, so that we can see more easily the next step of the workflow'''
        assert len(ids) == 1, 'This option should only be used for a single id at a time'
        self.signal_workflow(cr, uid, ids, 'send_rfq')

#####inherit PO confim function to change the forecast state as PO Created
    def wkf_confirm_order(self, cr, uid, ids, context=None):
	purchase_forecast_obj = self.pool.get('purchase.forecast')
	purchase_forecast_ids = purchase_forecast_obj.search(cr,uid,[('rfq_ref','in',ids)])
	if purchase_forecast_ids : 
		purchase_forecast_obj.write(cr,uid,purchase_forecast_ids,{'state':'pocreated'})
	return super(purchase_order, self).wkf_confirm_order(cr, uid, ids,context=context)
    def action_picking_create(self, cr, uid, ids, context=None):
        for order in self.browse(cr, uid, ids):
            picking_vals = {
                'picking_type_id': order.picking_type_id.id,
                'partner_id': order.partner_id.id,
                'date': order.date_order,
                'origin': order.name,
                'referance':order.partner_ref,
            }
            picking_id = self.pool.get('stock.picking').create(cr, uid, picking_vals, context=context)
            self._create_stock_moves(cr, uid, order, order.order_line, picking_id, context=context)
        return picking_id


class purchase_payment_terms(osv.osv):
    _name="purchase.payment"
    _rec_name="purchase_payment_information"
    _columns={
        'purchase_payment_information':fields.char('Payment Terms'),


    }


        

