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

import re
import pdb
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP

class purchase_forecast(osv.osv):
    _name="purchase.forecast"
    _description="Purchase Forecast Qty"
    _columns={
	'il_part':fields.char('IL Part No'),
	'product_id':fields.many2one('product.product', 'Product'),
	'so_date':fields.date("SO Date",readonly=True),
	'order_id':fields.many2one('sale.order','SO Ref'),
	'picking_id':fields.many2one("stock.picking","Outward Ref"),
	'product_uom_qty':fields.float('Qty to Deliver'),
	'qty_to_purchase':fields.float("Qty to Purchase"),
	'qty_in_stock':fields.float("Virtual Qty in Hand"),
        'state': fields.selection([('draft', 'New'),('inprogress', 'RFQ Created'),('pocreated', 'PO Created'),('cancel','Cancelled'),],'Status',readonly=True, copy=False),
	'rfq_ref':fields.many2one('purchase.order', 'RFQ Ref'),
    }

    _defaults = {
        'state': 'draft',
	}

class purchase_forecast_wizard(osv.osv_memory):
    _name="purchase.forecast.wizard"
    _description="Purchase Forecast Qty Wizard"

    STATE_SELECTION = [
        ('draft', 'Draft PO'),
        ('sent', 'RFQ'),
        ('bid', 'Bid Received'),
        ('confirmed', 'Waiting Approval'),
        ('approved', 'Purchase Confirmed'),
        ('except_picking', 'Shipping Exception'),
        ('except_invoice', 'Invoice Exception'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ]


    def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
        """ Change fields position in the view
        """
        if context is None:
            context = {}
        res = super(purchase_forecast_wizard, self).fields_view_get(cr, uid, view_id=view_id,
                                                                view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
		suppliers = []
		doc = etree.XML(res['arch'])
		nodes = doc.xpath("//field[@name='partner_id']")
		planning_ids = context.get('active_ids')
		purchase_planning_rows = self.pool.get('purchase.forecast').browse(cr,uid,planning_ids)
		for purchase_planning_row in purchase_planning_rows :
			vendors = purchase_planning_row.product_id.seller_ids
			if vendors :
				for vendor in vendors : 
					suppliers.append(vendor.name.id)
		actual_vendors = str(suppliers)
		domain = '[("id", "in", '+actual_vendors+')]'
		for node in nodes:
			node.set('domain', domain)
		res['arch'] = etree.tostring(doc)
        return res

    def onchange_partner_id(self, cr, uid, ids, partner_id, context=None):
        partner = self.pool.get('res.partner')
        company_id = self.pool.get('res.users')._get_company(cr, uid, context=context)
        if not company_id:
            raise osv.except_osv(_('Error!'), _('There is no default company for the current user!'))
        supplier = partner.browse(cr, uid, partner_id, context=context)
        return {'value': {
            'pricelist_id': supplier.property_product_pricelist_purchase.id,
            }}

    def _get_journal(self, cr, uid, context=None):
        if context is None:
            context = {}
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        company_id = context.get('company_id', user.company_id.id)
        journal_obj = self.pool.get('account.journal')
        res = journal_obj.search(cr, uid, [('type', '=', 'purchase'),
                                            ('company_id', '=', company_id)],
                                                limit=1)
        return res and res[0] or False  

    def _get_picking_in(self, cr, uid, context=None):
        obj_data = self.pool.get('ir.model.data')
        type_obj = self.pool.get('stock.picking.type')
        user_obj = self.pool.get('res.users')
        company_id = user_obj.browse(cr, uid, uid, context=context).company_id.id
        types = type_obj.search(cr, uid, [('code', '=', 'incoming'), ('warehouse_id.company_id', '=', company_id)], context=context)
        if not types:
            types = type_obj.search(cr, uid, [('code', '=', 'incoming'), ('warehouse_id', '=', False)], context=context)
            if not types:
                raise osv.except_osv(_('Error!'), _("Make sure you have at least an incoming picking type defined"))
        return types[0]


    _columns={
	'partner_id':fields.many2one('res.partner', 'Supplier', domain=[('supplier', '=', True)]),
	'date_order':fields.date("Order Date"),
        'pricelist_id':fields.many2one('product.pricelist', 'Pricelist', required=True),
    }

    _defaults = {
        'date_order': fields.datetime.now,
        'pricelist_id': lambda self, cr, uid, context: context.get('partner_id', False) and self.pool.get('res.partner').browse(cr, uid, context['partner_id']).property_product_pricelist_purchase.id,
    }


    def create_rfq(self, cr, uid, ids, context=None):
	purchase_order_lines = {}
	order_line=[]
	purchase_order = {}
	purchase_order_line_ids=[]
	purchase_forecast_obj = self.pool.get('purchase.forecast')
	purchase_order_obj = self.pool.get('purchase.order')
	purchase_order_line_obj = self.pool.get('purchase.order.line')
	purchase_forecast_ids = context.get('active_ids')
	source_document = ''
	purchase_forecast_wizard_row = self.pool.get('purchase.forecast.wizard').browse(cr,uid,ids)
	pricelist_id = purchase_forecast_wizard_row.pricelist_id
	partner_id = purchase_forecast_wizard_row.partner_id.id
	old_purchase_id = purchase_order_obj.search(cr,uid,[('partner_id','=',partner_id), ('state','=','draft')])
	for purchase_forecast_id in purchase_forecast_ids :

		purchase_forecast_row = purchase_forecast_obj.browse(cr,uid,purchase_forecast_id)
		if purchase_forecast_row.state == 'inprogress' :
                        raise osv.except_osv(_('Error!'),
                                _('RFQ is already created for : "%s"') %(purchase_forecast_row.product_id.name))

		if purchase_forecast_row.product_id.id in purchase_order_lines.keys() :
			old_purchase_qty = purchase_order_lines[purchase_forecast_row.product_id.id]['product_qty']
			qty_to_purchase = old_purchase_qty + purchase_forecast_row.qty_to_purchase
		else :
			qty_to_purchase = purchase_forecast_row.qty_to_purchase
		purchase_order_lines.update({purchase_forecast_row.product_id.id:({
		'product_id':purchase_forecast_row.product_id.id,
		'brand_name':purchase_forecast_row.product_id.product_brand.id,
		'il_part_no':purchase_forecast_row.product_id.default_code,
		'product_qty':qty_to_purchase,
		'product_uom':purchase_forecast_row.product_id.uom_id.id,
		'price_unit':purchase_forecast_row.product_id.standard_price,
		'name':purchase_forecast_row.product_id.name,
		'date_planned':purchase_forecast_wizard_row.date_order,
		})})
		if purchase_forecast_row.order_id.name :
			source_document = source_document + purchase_forecast_row.order_id.name + ', ' 

	for purchase_order_line in purchase_order_lines :
		order_line.append((0,0,purchase_order_lines[purchase_order_line]))
	purchase_order.update({'name':'/','pricelist_id':pricelist_id.id,'location_id':12,'partner_id':purchase_forecast_wizard_row.partner_id.id,'date_order':purchase_forecast_wizard_row.date_order,'order_line':order_line,'origin':source_document})
	if old_purchase_id :
		purchase_list = purchase_order_obj.browse(cr,uid,old_purchase_id[0])
		old_source_document = purchase_list.origin
		if old_source_document :
			new_source_document = old_source_document + source_document
		print old_source_document
		pdb.set_trace()
		purchase_line_list = purchase_order_line_obj.search(cr,uid,[('order_id','=',old_purchase_id[0]),('product_id','=',purchase_forecast_row.product_id.id)])
		
		if purchase_line_list:
			line = purchase_order_line_obj.browse(cr,uid,purchase_line_list[0])
			
			if purchase_forecast_row.product_id.id == line.product_id.id:
				purchase_order_line_obj.write(cr,uid,purchase_line_list[0],{'product_qty':qty_to_purchase+line.product_qty})
			else:
				purchase_order_obj.write(cr,uid,old_purchase_id,{'order_line':order_line,'origin':new_source_document})
		else:		
			purchase_order_obj.write(cr,uid,old_purchase_id,{'order_line':order_line,'origin':new_source_document})
		purchase_forecast_obj.write(cr,uid,purchase_forecast_ids,{'state':'inprogress','rfq_ref':old_purchase_id[0]})
	else :
		purchase_id = purchase_order_obj.create(cr,uid,purchase_order)
		purchase_forecast_obj.write(cr,uid,purchase_forecast_ids,{'state':'inprogress','rfq_ref':purchase_id})

##############################################
#		product = purchase_forecast_row.product_id
#		if pricelist_id:
#			date_order_str = datetime.strptime(date_order, DEFAULT_SERVER_DATETIME_FORMAT).strftime(DEFAULT_SERVER_DATE_FORMAT)
#			price = product_pricelist.price_get(cr, uid, [pricelist_id],
#			product.id, qty or 1.0, partner_id or False, {'uom': uom_id, 'date': date_order_str})[pricelist_id]
#		else:
#			price = product.standard_price
####### how to get the supplier price list unit price
##### how to supply the pricelist, location to create RFQ dynamically
##### how MOQ is managed while creating the RFQ
##############################################

	return True
