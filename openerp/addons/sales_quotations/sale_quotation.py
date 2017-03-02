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
import re
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP
import datetime
import pdb
import openerp.addons.decimal_precision as dp
import time
from datetime import datetime
from datetime import timedelta
from openerp.tools.float_utils import float_compare
import random


class sale_order(osv.osv):
    _inherit = "sale.order"
    _columns = {
		'quotation_id':fields.many2one('sale.quotation', 'Quotation Ref')
	}

    def open_sale_order_view(self, cr, uid, ids, context=None):
	#pdb.set_trace()
        result = self.pool['ir.model.data'].xmlid_to_res_id(cr, uid, 'stock_saify.action_orders_new', raise_if_not_found=True)
        result = self.pool['ir.actions.act_window'].read(cr, uid, [result], context=context)[0]
        result['domain'] = "[('id','in',[" + ','.join(map(str, ids)) + "])]"
        return result


class sale_quotation(osv.osv):

    _name = "sale.quotation"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = "Sales Quotation"


    def _get_default_warehouse(self, cr, uid, context=None):
        company_id = self.pool.get('res.users')._get_company(cr, uid, context=context)
        warehouse_ids = self.pool.get('stock.warehouse').search(cr, uid, [('company_id', '=', company_id)], context=context)
        if not warehouse_ids:
            return False
        return warehouse_ids[0]


    def onchange_warehouse_id(self, cr, uid, ids, warehouse_id, context=None):
        val = {}
        if warehouse_id:
            warehouse = self.pool.get('stock.warehouse').browse(cr, uid, warehouse_id, context=context)
            if warehouse.company_id:
                val['company_id'] = warehouse.company_id.id
        return {'value': val}



    def _get_date_planned(self, cr, uid, order, line, start_date, context=None):
        date_planned = super(sale_order, self)._get_date_planned(cr, uid, order, line, start_date, context=context)
        date_planned = (date_planned - timedelta(days=order.company_id.security_lead)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        return date_planned


    def send_quotation(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'sent'}, context=context)


    def button_dummy(self, cr, uid, ids, context=None):
        return True

    def get_salenote(self, cr, uid, ids, partner_id, context=None):
        if context is None:
            context = {}
        context_lang = context.copy()
        if partner_id:
            partner_lang = self.pool.get('res.partner').browse(cr, uid, partner_id, context=context).lang
            context_lang.update({'lang': partner_lang})
        return self.pool.get('res.users').browse(cr, uid, uid, context=context_lang).company_id.sale_note

    def onchange_pricelist_id(self, cr, uid, ids, pricelist_id, order_lines, context=None):
        context = context or {}
        if not pricelist_id:
            return {}
        value = {
            'currency_id': self.pool.get('product.pricelist').browse(cr, uid, pricelist_id, context=context).currency_id.id
        }
        if not order_lines or order_lines == [(6, 0, [])]:
            return {'value': value}
        warning = {
            'title': _('Pricelist Warning!'),
            'message' : _('If you change the pricelist of this order (and eventually the currency), prices of existing order lines will not be updated.')
        }
        return {'warning': warning, 'value': value}

    def onchange_fiscal_position(self, cr, uid, ids, fiscal_position, order_lines, context=None):
        '''Update taxes of order lines for each line where a product is defined

        :param list ids: not used
        :param int fiscal_position: sale order fiscal position
        :param list order_lines: command list for one2many write method
        '''
        order_line = []
        fiscal_obj = self.pool.get('account.fiscal.position')
        product_obj = self.pool.get('product.product')
        line_obj = self.pool.get('sale.quotation.order.line')

        fpos = False
        if fiscal_position:
            fpos = fiscal_obj.browse(cr, uid, fiscal_position, context=context)
        
        for line in order_lines:
            # create    (0, 0,  { fields })
            # update    (1, ID, { fields })
            if line[0] in [0, 1]:
                prod = None
                if line[2].get('product_id'):
                    prod = product_obj.browse(cr, uid, line[2]['product_id'], context=context)
                elif line[1]:
                    prod =  line_obj.browse(cr, uid, line[1], context=context).product_id
                if prod and prod.taxes_id:
                    line[2]['tax_id'] = [[6, 0, fiscal_obj.map_tax(cr, uid, fpos, prod.taxes_id, context=context)]]
                order_line.append(line)

            # link      (4, ID)
            # link all  (6, 0, IDS)
            elif line[0] in [4, 6]:
                line_ids = line[0] == 4 and [line[1]] or line[2]
                for line_id in line_ids:
                    prod = line_obj.browse(cr, uid, line_id, context=context).product_id
                    if prod and prod.taxes_id:
                        order_line.append([1, line_id, {'tax_id': [[6, 0, fiscal_obj.map_tax(cr, uid, fpos, prod.taxes_id, context=context)]]}])
                    else:
                        order_line.append([4, line_id])
            else:
                order_line.append(line)
        return {'value': {'order_line': order_line, 'amount_untaxed': False, 'amount_tax': False, 'amount_total': False}}


    def _amount_line_tax(self, cr, uid, line, context=None):
        val = 0.0
        line_obj = self.pool['sale.quotation.order.line']
        price = line_obj._calc_line_base_price(cr, uid, line, context=context)
        qty = line_obj._calc_line_quantity(cr, uid, line, context=context)
        for c in self.pool['account.tax'].compute_all(
                cr, uid, line.tax_id, price, qty, line.product_id,
                line.order_id.partner_id)['taxes']:
            val += c.get('amount', 0.0)
        return val

    def _amount_all_wrapper(self, cr, uid, ids, field_name, arg, context=None):
        """ Wrapper because of direct method passing as parameter for function fields """
	#pdb.set_trace()
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
	#pdb.set_trace()
        return res


    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('sale.quotation.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()

    def _get_default_company(self, cr, uid, context=None):
        company_id = self.pool.get('res.users')._get_company(cr, uid, context=context)
        if not company_id:
            raise osv.except_osv(_('Error!'), _('There is no default company for the current user!'))
        return company_id

    def _get_default_section_id(self, cr, uid, context=None):
        """ Gives default section by checking if present in the context """
        section_id = self._resolve_section_id_from_context(cr, uid, context=context) or False
        if not section_id:
            section_id = self.pool.get('res.users').browse(cr, uid, uid, context).default_section_id.id or False
        return section_id

    def _resolve_section_id_from_context(self, cr, uid, context=None):
        """ Returns ID of section based on the value of 'section_id'
            context key, or None if it cannot be resolved to a single
            Sales Team.
        """
        if context is None:
            context = {}
        if type(context.get('default_section_id')) in (int, long):
            return context.get('default_section_id')
        if isinstance(context.get('default_section_id'), basestring):
            section_ids = self.pool.get('crm.case.section').name_search(cr, uid, name=context['default_section_id'],
                                                                        context=context)
            if len(section_ids) == 1:
                return int(section_ids[0][0])
        return None

    _columns = {

        'name': fields.char('Order Reference', required=True, copy=False,
                            readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                            select=True),
        'state': fields.selection([
                    ('draft', 'Draft'),
                    ('sent', 'Quotation Sent'),
                    ('cancel', 'Cancelled'),
                    ('done', 'Done'),
                    ], 'Status', readonly=True, copy=False, select=True),
        'quotation_state': fields.selection([
                    ('awaiting_confirmation', 'Awaiting Confirmation'),
                    ('awaiting_fulfillment', 'Awaiting Fulfillment'),
                    ('order_completed', 'Order Completed'),
                    ('partially_delivered', 'Partially Delivered'),
                    ('cancel', 'Cancelled'),
                    ], 'Status', select=True),
                


        'sale_order_payment_information': fields.many2one('payment.terms', 'Payment Terms'),
        'sale_order_shipping_information': fields.many2one('shipping.terms', 'Shipping Terms'),
        'origin': fields.char('Source Document',
                              help="Reference of the document that generated this sales order request."),
        'client_order_ref': fields.char('Reference/Description', copy=False),

        'date_order': fields.datetime('Date', required=True, readonly=True, select=True,
                                      states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                      copy=False),
        'create_date': fields.datetime('Creation Date', readonly=True, select=True,
                                       help="Date on which sales order is created."),
        'date_confirm': fields.date('Confirmation Date', readonly=True, select=True,
                                    help="Date on which sales order is confirmed.", copy=False),
        'user_id': fields.many2one('res.users', 'Salesperson',
                                   states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, select=True,
                                   track_visibility='onchange'),
        'partner_id': fields.many2one('res.partner', 'Customer', readonly=True,
                                      states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                      required=True, change_default=True, select=True, track_visibility='always'),
        'partner_invoice_id': fields.many2one('res.partner', 'Invoice Address', readonly=True, required=True,
                                              states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                              help="Invoice address for current sales order."),
        'partner_shipping_id': fields.many2one('res.partner', 'Delivery Address', readonly=True, required=True,
                                               states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                               help="Delivery address for current sales order."),
        'pricelist_id': fields.many2one('product.pricelist', 'Pricelist', required=True, readonly=True,
                                        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                        help="Pricelist for current sales order."),
        'currency_id': fields.related('pricelist_id', 'currency_id', type="many2one", relation="res.currency",
                                      string="Currency", readonly=True, required=True),
        'project_id': fields.many2one('account.analytic.account', 'Contract / Analytic', readonly=True,
                                      states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                      help="The analytic account related to a sales order."),

        'order_line': fields.one2many('sale.quotation.order.line', 'order_id', 'Order Lines', readonly=True,
                                      states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                      copy=True),
        'note': fields.text('Terms and conditions'),

        'amount_untaxed': fields.function(_amount_all_wrapper, digits_compute=dp.get_precision('Account'),
                                          string='Untaxed Amount',
                                          store={
                                              'sale.quotation': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                                              'sale.quotation.order.line': (
                                              _get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
                                          },
                                          multi='sums', help="The amount without tax.", track_visibility='always'),
        'amount_tax': fields.function(_amount_all_wrapper, digits_compute=dp.get_precision('Account'), string='Taxes',
                                      store={
                                          'sale.quotation': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                                          'sale.quotation.order.line': (
                                          _get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
                                      },
                                      multi='sums', help="The tax amount."),
        'amount_total': fields.function(_amount_all_wrapper, digits_compute=dp.get_precision('Account'), string='Total',
                                        store={
                                            'sale.quotation': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                                            'sale.quotation.order.line': (
                                            _get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
                                        },
                                        multi='sums', help="The total amount."),

        'payment_term': fields.many2one('account.payment.term', 'Payment Term'),
        'fiscal_position': fields.many2one('account.fiscal.position', 'Fiscal Position'),
        'company_id': fields.many2one('res.company', 'Company'),
        'section_id': fields.many2one('crm.case.section', 'Sales Team'),
        'procurement_group_id': fields.many2one('procurement.group', 'Procurement group', copy=False),
        'product_id': fields.related('order_line', 'product_id', type='many2one', relation='product.product',
                                     string='Product'),
        'sale_orders': fields.one2many('sale.order', 'quotation_id', 'Sale Orders', readonly=True, copy=False),


        'incoterm': fields.many2one('stock.incoterms', 'Incoterm', help="International Commercial Terms are a series of predefined commercial terms used in international transactions."),
        'picking_policy': fields.selection([('direct', 'Deliver each product when available'), ('one', 'Deliver all products at once')],
            'Shipping Policy', required=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
            help="""Pick 'Deliver each product when available' if you allow partial delivery."""),
        'order_policy': fields.selection([
                ('manual', 'On Demand'),
                ('picking', 'On Delivery Order'),
                ('prepaid', 'Before Delivery'),
            ], 'Create Invoice', required=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
            help="""On demand: A draft invoice can be created from the sales order when needed. \nOn delivery order: A draft invoice can be created from the delivery order when the products have been delivered. \nBefore delivery: A draft invoice is created from the sales order and must be paid before the products can be delivered."""),
        'warehouse_id': fields.many2one('stock.warehouse', 'Warehouse', required=True),

    }

    _defaults = {
        'date_order': fields.datetime.now,
        'company_id': _get_default_company,
        'state': 'draft',
        'user_id': lambda obj, cr, uid, context: uid,
        'quotation_state':'awaiting_confirmation',
        'name': lambda obj, cr, uid, context: '/',
        'partner_invoice_id': lambda self, cr, uid, context: context.get('partner_id', False) and
                                                             self.pool.get('res.partner').address_get(cr, uid, [
                                                                 context['partner_id']], ['invoice'])['invoice'],
        'partner_shipping_id': lambda self, cr, uid, context: context.get('partner_id', False) and
                                                              self.pool.get('res.partner').address_get(cr, uid, [
                                                                  context['partner_id']], ['delivery'])['delivery'],
        'note': lambda self, cr, uid, context: self.pool.get('res.users').browse(cr, uid, uid,
                                                                                 context=context).company_id.sale_note,
        'section_id': lambda s, cr, uid, c: s._get_default_section_id(cr, uid, c),
        'warehouse_id': _get_default_warehouse,
        'picking_policy': 'direct',
        'order_policy': 'picking',


    }
    _sql_constraints = [
        ('name_uniq', 'unique(name, company_id)', 'Order Reference must be unique per Company!'),
    ]
    _order = 'date_order desc, id desc'



    def onchange_delivery_id(self, cr, uid, ids, company_id, partner_id, delivery_id, fiscal_position, context=None):
        r = {'value': {}}
        if not company_id:
            company_id = self._get_default_company(cr, uid, context=context)
        fiscal_position = self.pool['account.fiscal.position'].get_fiscal_position(cr, uid, company_id, partner_id,
                                                                                   delivery_id, context=context)
        if fiscal_position:
            r['value']['fiscal_position'] = fiscal_position
        return r

    def onchange_partner_id(self, cr, uid, ids, part, context=None):
        if not part:
            return {'value': {'partner_invoice_id': False, 'partner_shipping_id': False, 'payment_term': False,
                              'fiscal_position': False}}

        part = self.pool.get('res.partner').browse(cr, uid, part, context=context)
        addr = self.pool.get('res.partner').address_get(cr, uid, [part.id], ['delivery', 'invoice', 'contact'])
        pricelist = part.property_product_pricelist and part.property_product_pricelist.id or False
        invoice_part = self.pool.get('res.partner').browse(cr, uid, addr['invoice'], context=context)
        payment_term = invoice_part.property_payment_term and invoice_part.property_payment_term.id or False
        dedicated_salesman = part.user_id and part.user_id.id or uid
        val = {
            #'partner_invoice_id': addr['invoice'],
            #'partner_shipping_id': addr['delivery'],
            'payment_term': payment_term,
            'user_id': dedicated_salesman,
        }
        delivery_onchange = self.onchange_delivery_id(cr, uid, ids, False, part.id, addr['delivery'], False,
                                                      context=context)
        val.update(delivery_onchange['value'])
        if pricelist:
            val['pricelist_id'] = pricelist
        if not self._get_default_section_id(cr, uid, context=context) and part.section_id:
            val['section_id'] = part.section_id.id
        sale_note = self.get_salenote(cr, uid, ids, part.id, context=context)
        if sale_note: val.update({'note': sale_note})
        return {'value': val}

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        if vals.get('name', '/') == '/':
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'sale.quotation', context=context) or '/'
        new_id = super(sale_quotation, self).create(cr, uid, vals, context=context)
        self.message_post(cr, uid, [new_id], body=_("Quotation created"), context=context)
        return new_id


    def test_no_product(self, cr, uid, order, context):
        for line in order.order_line:
            if line.state == 'cancel':
                continue
            if line.product_id and (line.product_id.type <> 'service'):
                return False
        return True


    def action_cancel(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        # sale_order_line_obj = self.pool.get('sale.quotation.order.line')
        # account_invoice_obj = self.pool.get('sale.order')
        # for sale in self.browse(cr, uid, ids, context=context):
        #     for inv in sale.invoice_ids:
        #         if inv.state not in ('draft', 'cancel'):
        #             raise osv.except_osv(
        #                 _('Cannot cancel this sales order!'),
        #                 _('First cancel all invoices attached to this sales order.'))
        #         inv.signal_workflow('invoice_cancel')
        #     line_ids = [l.id for l in sale_quotations.order_line if l.state != 'cancel']
        #     sale_order_line_obj.button_cancel(cr, uid, line_ids, context=context)
        self.write(cr, uid, ids, {'state': 'cancel'})
        self.write(cr,uid,ids,{'quotation_state':'cancel'})
        return True




    def action_done(self, cr, uid, ids, context=None):
        for order in self.browse(cr, uid, ids, context=context):
            self.pool.get('sale.quotation.order.line').write(cr, uid,
                                                   [line.id for line in order.order_line if line.state != 'cancel'],
                                                   {'state': 'done'}, context=context)
        return self.write(cr, uid, ids, {'state': 'done'}, context=context)


class sale_quotation_order_line(osv.osv):
    _name = "sale.quotation.order.line"



    def _amount_line(self, cr, uid, ids, field_name, arg, context=None):
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            price = self._calc_line_base_price(cr, uid, line, context=context)
            qty = self._calc_line_quantity(cr, uid, line, context=context)
            taxes = tax_obj.compute_all(cr, uid, line.tax_id, price, qty,
                                        line.product_id,
                                        line.order_id.partner_id)
            cur = line.order_id.pricelist_id.currency_id
            res[line.id] = cur_obj.round(cr, uid, cur, taxes['total'])
#	pdb.set_trace()
        return res

    def _get_price_reduce(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids, 0.0)
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = line.price_subtotal / line.product_uom_qty
        return res

    def _get_uom_id(self, cr, uid, *args):
        try:
            proxy = self.pool.get('ir.model.data')
            result = proxy.get_object_reference(cr, uid, 'product', 'product_uom_unit')
            return result[1]
        except Exception, ex:
            return False

    def product_uom_change(self, cursor, user, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, context=None):
        context = context or {}
        lang = lang or ('lang' in context and context['lang'])
        if not uom:
            return {'value': {'price_unit': 0.0, 'product_uom' : uom or False}}
        return self.product_id_change(cursor, user, ids, pricelist, product,
                qty=qty, uom=uom, qty_uos=qty_uos, uos=uos, name=name,
                partner_id=partner_id, lang=lang, update_tax=update_tax,
                date_order=date_order, fiscal_position=context.get('fiscal_position', False), context=context)

    def _calc_line_base_price(self, cr, uid, line, context=None):
        return line.price_unit * (1 - (line.discount or 0.0) / 100.0)

    def _calc_line_quantity(self, cr, uid, line, context=None):
        return line.product_uom_qty


    _columns = {
        'order_id': fields.many2one('sale.quotation', 'Quotation Reference', required=True, ondelete='cascade', select=True, readonly=True, states={'draft':[('readonly',False)]}),
        'name': fields.text('Description', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'sequence': fields.integer('Sequence', help="Gives the sequence order when displaying a list of sales order lines."),
        'product_id': fields.many2one('product.product', 'Product', domain=[('sale_ok', '=', True)], change_default=True, readonly=True, states={'draft': [('readonly', False)]}, ondelete='restrict'),
        'price_unit': fields.float('Unit Price', required=True, digits_compute= dp.get_precision('Product Price'), readonly=True, states={'draft': [('readonly', False)]}),
        'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute= dp.get_precision('Account')),
        'price_reduce': fields.function(_get_price_reduce, type='float', string='Price Reduce', digits_compute=dp.get_precision('Product Price')),
        'tax_id': fields.many2many('account.tax', 'sale_quotation_order_tax', 'quotation_order_line_id', 'tax_id', 'Taxes', readonly=True, states={'draft': [('readonly', False)]}),
        'address_allotment_id': fields.many2one('res.partner', 'Allotment Partner',help="A partner to whom the particular product needs to be allotted."),
        'product_uom_qty': fields.float('Quantity', digits_compute= dp.get_precision('Product UoS'), required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'product_uom': fields.many2one('product.uom', 'Unit of Measure ', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'product_uos_qty': fields.float('Quantity (UoS)' ,digits_compute= dp.get_precision('Product UoS'), readonly=True, states={'draft': [('readonly', False)]}),
        'product_uos': fields.many2one('product.uom', 'Product UoS'),
        'discount': fields.float('Discount (%)', digits_compute= dp.get_precision('Discount'), readonly=True, states={'draft': [('readonly', False)]}),
        'th_weight': fields.float('Weight', readonly=True, states={'draft': [('readonly', False)]}, digits_compute=dp.get_precision('Stock Weight')),
        'state': fields.selection(
                [('cancel', 'Cancelled'),('draft', 'Draft'),('sent', 'Quotation Sent'),('cancel', 'Cancel'),('done', 'Done')],
                'Status', required=True, readonly=True, copy=False,
                help='* The \'Draft\' status is set when the related Quotation in draft status. \
                    \n* The \'Confirmed\' status is set when the related Quotation is confirmed. \
                    \n* The \'Exception\' status is set when the related Quotation is set as exception. \
                    \n* The \'Done\' status is set when the Quotation line has been confirmed. \
                    \n* The \'Cancelled\' status is set when a user cancel the Quotation related.'),
        'order_partner_id': fields.related('order_id', 'partner_id', type='many2one', relation='res.partner', store=True, string='Customer'),
        'salesman_id':fields.related('order_id', 'user_id', type='many2one', relation='res.users', store=True, string='Salesperson'),
        'company_id': fields.related('order_id', 'company_id', type='many2one', relation='res.company', string='Company', store=True, readonly=True),
        'delay': fields.float('Delivery Lead Time', required=True, help="Number of days between the order confirmation and the shipping of the products to the customer", readonly=True, states={'draft': [('readonly', False)]}),
        'procurement_ids': fields.one2many('procurement.order', 'sale_line_id', 'Procurements'),

        'brand_name': fields.many2one('product.brand', 'Brand'),
        'il_part_no': fields.char('IL Part No'),
        'full_delivered': fields.boolean("Full Delivered"),
        'actual_qty_in_so': fields.float("Qty Sold"),
        'qty_in_so': fields.float("Qty to Sale"),
        'quotation_amount':fields.float('Quotation Amount'),

    }
    _order = 'order_id desc, sequence, id'
    _defaults = {
        'full_delivered': False,
        'product_uom' : _get_uom_id,
        'discount': 0.0,
        'product_uom_qty': 1,
        'product_uos_qty': 1,
        'sequence': 10,
        'state': 'draft',
        'price_unit': 0.0,
        'delay': 0.0,
    }



    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}

        default.update({

            'actual_qty_in_so': 0.0,
            'qty_in_so': 0.0,
            'full_delivered': False
        })
        res = super(sale_quotation_order_line, self).copy(cr, uid, id, default, context=context)
        return res

    def copy_data(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        default.update({'actual_qty_in_so': 0.0,
                        'qty_in_so': 0.0,
                        'full_delivered': False
                        })
        return super(sale_quotation_order_line, self).copy_data(cr, uid, id, default, context=context)


    def onchange_qty_in_so(self, cr, uid, ids, qty_in_so, context):
        """
        onchange handler of onchange_qty_in_so.
        """

        context = {}

        v = {}
        d = {}
        res = {}
        warning = {}
        msgalert = {}

        if qty_in_so:

            context.update({'qty_in_so': qty_in_so})

            so_lines_brow = self.browse(cr, uid, ids)

            p_qty_in_so = so_lines_brow[0].qty_in_so

            actual_qty_in_so = so_lines_brow[0].actual_qty_in_so
            self.write(cr, 1, ids, {'qty_in_so': qty_in_so})

            remaining_qty = so_lines_brow[0].product_uom_qty - actual_qty_in_so
            if qty_in_so > remaining_qty:

                warning_msg = _(
                    "Quantity to Sale, Cannot exceed Quotation Quantity [(Quantity to Sale) = (Quantity) - (Sale Quantity)] ") + "\n\n"

                if warning_msg:
                    warning = {
                        'title': _('Validation Error!'),
                        'message': warning_msg
                    }

                v['qty_in_so'] = remaining_qty
                self.write(cr, 1, ids, {'qty_in_so': msgalert})


        res = {'value': v, 'domain': d, 'warning': warning}
        return res

    def default_get(self, cr, uid, fields, context=None):
	#pdb.set_trace()
        data = super(sale_quotation_order_line, self).default_get(cr, uid, fields, context=context)

        data.update({'qty_in_so': 1.0})

        return data

    @api.multi
    def action_sale_product_prices(self):
#	pdb.set_trace()
        id2 = self.env.ref(
            'stock_saify.last_sale_product_prices_view')
        sale_lines = self.env['sale.order.line'].search([('order_id', '!=', self.id),('product_id', '=', self.product_id.id),('order_partner_id','=',self.order_partner_id.id),('state','in',('done','confirmed'))],order='sale_data')
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
        #pdb.set_trace()
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

        if update_tax:  # The quantity only have changed
            # The superuser is used by website_sale in order to create a sale order. We need to make
            # sure we only select the taxes related to the company of the partner. This should only
            # apply if the partner is linked to a company.
            if uid == SUPERUSER_ID and context.get('company_id'):
                taxes = product_obj.taxes_id.filtered(lambda r: r.company_id.id == context['company_id'])
            else:
                taxes = product_obj.taxes_id
            result['tax_id'] = self.pool.get('account.fiscal.position').map_tax(cr, uid, fpos, taxes)
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
            self.pool.get('product.pricelist').price_get(cr, uid, [pricelist], product, qty or 1.0, partner_id, ctx)[
                pricelist]
            price_price = self.pool.get('product.pricelist').browse(cr,uid,pricelist)
            print "price_price", ctx,self.pool.get('product.pricelist').price_get(cr, uid, [pricelist], product, qty or 1.0, partner_id, ctx)
            price_item = ctx.get("price_item")            
            if price is False:
#                 warn_msg = _(
#                     "Cannot find a pricelist line matching this product and quantity.\n""You have to change either the product, the quantity or the pricelist.")
#                 warning_msgs += _("No valid pricelist line found ! :") + warn_msg + "\n\n"
                if product:
                    product_obj = self.pool.get('product.product').browse(cr, uid, product)
                    result['price_unit'] = product_obj.list_price        
            else:
                # if update_tax:
                #     price = self.pool['account.tax']._fix_tax_included_price(cr, uid, price, taxes, result['tax_id'])
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
        #pdb.set_trace()
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
#       pdb.set_trace()
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
                       
                        result.update({'product_uom_qty': min_qty})
                        warning = {'title': _('Multiple Quantity Error!'),'message': 'Enter Qty in Multiple of           '+str(min_qty)+'for'+product_name1}
            if qty>min_qty:

                if type_qty=='Multiple':
                    if not (qty%min_qty ==0):
                        result.update({'product_uom_qty': min_qty})
                        warning = {'title': _('Multiple Quantity Error!'),'message': 'Enter Qty in Multiple of           '+str(min_qty)+'          for        '+product_name1}


        return {'value': result, 'domain': domain, 'warning': warning}


class sandv_quotation_lines(osv.osv_memory):
    _name = 'sandv.quotation.lines'

    _columns = {

        'name': fields.many2many('sale.quotation.order.line', "quot_line_and_sandv_quot_lines", 'sandv_ref_id', 'quot_line_id',
                                 "Quotation Lines")

    }
    def sandv_sale_order_create(self, cr, uid, ids, context):
        #pdb.set_trace()
        
        sale_id = False
        if not context:
            context = {}

        quotation_obj = self.pool.get('sale.quotation')
        quotation_line_obj = self.pool.get('sale.quotation.order.line')
        sale_order_obj=self.pool.get('sale.order')
        sale_order_line_obj = self.pool.get('sale.order.line')
        quotation_id = context.get('active_id')
        quotation_data = quotation_obj.copy_data(cr,uid, quotation_id, context=context)

        quotation_browse = quotation_obj.browse(cr, uid, quotation_id, context=context)
        quotation_data.update({'order_line':None, 'quotation_id':quotation_id,'client_order_ref':quotation_browse.client_order_ref})
        sandv_so_lines_brow = self.browse(cr, 1, ids)
        sandv_so_lines_list = sandv_so_lines_brow[0].name
        sale_id =sale_order_obj.create(cr,uid,quotation_data)


        if sale_id:

            for i in sandv_so_lines_list:
                qt_id = i.order_id.id
                qty_in_so = i.qty_in_so
                quotation_line_data = quotation_line_obj.copy_data(cr,uid, i.id, context=context)
                #pdb.set_trace()
                print quotation_line_data
                del quotation_line_data['actual_qty_in_so']
                del quotation_line_data['full_delivered']
                del quotation_line_data['qty_in_so']
                del quotation_line_data['quotation_amount']
                quotation_line_data.update({'order_id': sale_id, 'product_uom_qty': qty_in_so,})
                so_line_id = sale_order_line_obj.create(cr,uid,quotation_line_data)
                actual_qty_in_so = i.actual_qty_in_so + qty_in_so
                if actual_qty_in_so == i.product_uom_qty:
                    quotation_line_obj.write(cr, uid, [i.id],{'full_delivered': True, 'actual_qty_in_so': actual_qty_in_so, 'qty_in_so': 1.0})
                else:
                    quotation_line_obj.write(cr, uid, [i.id], {'actual_qty_in_so': actual_qty_in_so, 'qty_in_so': 1.0})
        all_full_delivered_lines = quotation_line_obj.search(cr,uid,[('full_delivered','=',False),('order_id','=',quotation_id)])
        #pdb.set_trace()
        if len(all_full_delivered_lines) == 0 :
            quotation_obj.write(cr,uid,quotation_id,{'state':'done'})
        if quotation_obj.browse(cr,uid,quotation_id).quotation_state!='partially_delivered':
            quotation_obj.write(cr,uid,quotation_id,{'invoice_state':'awaiting_fulfillment'})
        

        return sale_order_obj.open_sale_order_view(cr, uid, [sale_id], context)



sandv_quotation_lines()



