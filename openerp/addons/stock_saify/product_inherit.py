from datetime import datetime, date
from lxml import etree
import time

from openerp import SUPERUSER_ID
from openerp import tools
from openerp.addons.resource.faces import task as Task
from openerp.osv import fields, osv
from openerp.tools import float_is_zero
from openerp.tools.translate import _
import re


#class product_product(osv.Model):
#	_inherit = 'product.product'

#	def _sales_value(self, cr, uid, ids, field_name, arg, context=None):
#		r = dict.fromkeys(ids, 0)
#		a=self.browse(self,cr,uid,ids,context=None).product_id
#		cr.execute('select sum(product_uom_qty*price_unit) from  sale_order_line where state = 'confirmed' and product_id = '%s'', (a))
		
#		return r

#	def action_view_sales(self, cr, uid, ids, context=None):
#		result = self.pool['ir.model.data'].xmlid_to_res_id(cr, uid, 'sale.action_order_line_product_tree',raise_if_not_found=True)
#		result = self.pool['ir.actions.act_window'].read(cr, uid, [result], context=context)[0]
#		result['domain'] = "[('product_id','in',[" + ','.join(map(str, ids)) + "])]"
#		return result

#	_columns = {
#		'sales_count': fields.function(_sales_value, string='# Sales', type='integer'),
#	}


#class product_template(osv.Model):
#	_inherit = 'product.template'

#	def _sales_count(self, cr, uid, ids, field_name, arg, context=None):
#		res = dict.fromkeys(ids, 0)
#		for template in self.browse(cr, uid, ids, context=context):
#			res[template.id] = sum([p.sales_count for p in template.product_variant_ids])
#		return res

#	def action_view_sales(self, cr, uid, ids, context=None):
#		act_obj = self.pool.get('ir.actions.act_window')
#		mod_obj = self.pool.get('ir.model.data')
#		product_ids = []
#		for template in self.browse(cr, uid, ids, context=context):
#			product_ids += [x.id for x in template.product_variant_ids]
#		result = mod_obj.xmlid_to_res_id(cr, uid, 'sale.action_order_line_product_tree', raise_if_not_found=True)
#		result = act_obj.read(cr, uid, [result], context=context)[0]
#		result['domain'] = "[('product_id','in',[" + ','.join(map(str, product_ids)) + "])]"
#		return result

#	_columns = {
#		'sales_count': fields.function(_sales_count, string='# Sales', type='integer'),

#	}
# class product_product(osv.Model):
# 	_inherit = 'product.product'
#
# 	def _sales_count(self, cr, uid, ids, field_name, arg, context=None):
# 		r = dict.fromkeys(ids, 0)
# 		domain = [
# 			('state', 'in', ['confirmed', 'done']),
# 			('product_id', 'in', ids),
# 		]
# 		for group in self.pool['sale.order.line'].read_group(cr, uid, domain, ['product_id', 'price_subtotal'],
# 														 ['product_id'], context=context):
# 			r[group['product_id'][0]] = group['price_subtotal']
# 		return r
#
# 	def action_view_sales(self, cr, uid, ids, context=None):
# 		result = self.pool['ir.model.data'].xmlid_to_res_id(cr, uid, 'sale.action_order_line_product_tree',
# 															raise_if_not_found=True)
# 		result = self.pool['ir.actions.act_window'].read(cr, uid, [result], context=context)[0]
# 		result['domain'] = "[('product_id','in',[" + ','.join(map(str, ids)) + "])]"
# 		return result
#
# 	_columns = {
# 		'sales_count': fields.function(_sales_count, string='# Sales', type='integer'),
# 	}
#
#
# class product_template(osv.Model):
# 	_inherit = 'product.template'
#
# 	def _sales_count(self, cr, uid, ids, field_name, arg, context=None):
# 		res = dict.fromkeys(ids, 0)
# 		for template in self.browse(cr, uid, ids, context=context):
# 			res[template.id] = sum([p.sales_count for p in template.product_variant_ids])
# 		return res
#
# 	def action_view_sales(self, cr, uid, ids, context=None):
# 		act_obj = self.pool.get('ir.actions.act_window')
# 		mod_obj = self.pool.get('ir.model.data')
# 		product_ids = []
# 		for template in self.browse(cr, uid, ids, context=context):
# 			product_ids += [x.id for x in template.product_variant_ids]
# 		result = mod_obj.xmlid_to_res_id(cr, uid, 'sale.action_order_line_product_tree', raise_if_not_found=True)
# 		result = act_obj.read(cr, uid, [result], context=context)[0]
# 		result['domain'] = "[('product_id','in',[" + ','.join(map(str, product_ids)) + "])]"
# 		return result
#
# 	_columns = {
# 		'sales_count': fields.function(_sales_count, string='# Sales', type='integer'),
#
# 	}
#





class product_inherit(osv.osv):


	_inherit="product.product"
	_description = "Product Inherit"
	_columns={}

	
	def name_get(self, cr, user, ids, context=None):
		if context is None:
			context = {}
		if isinstance(ids, (int, long)):
			ids = [ids]
		if not len(ids):
			return []

		def _name_get(d):
			name = d.get('name', '')

			return (d['id'], name)



		result = []
		for product in self.browse(cr, SUPERUSER_ID, ids, context=context):

				mydict = {
					'id': product.id,
					'name': product.name,
				}
				result.append(_name_get(mydict))
		return result

    	_sql_constraints = [
        ('ilpart_uniq', 'unique(default_code)', 'IL Part No must be unique!'),
    ]


class product_template(osv.Model):
	_inherit = "product.template"
	_columns={
		'new_name':fields.char('Shridhar'),
		'type_quantity1': fields.selection([('Minimum', 'Minimum'),('Multiple', 'Multiple'),],required=True),
		'min_quantity1': fields.float('Min Order Quantity', size=64,required=True,default=1),
		#'parent_category':fields.many2one('product.category','Parent Category',)
		#'parent_category': fields.many2one('product.category',compute='_compute_upper',string="Parent Category"),
	}


class product_supplierinfo(osv.osv):
    _inherit = "product.supplierinfo"
    _description = "Information about a product supplier Inherit"

    _columns = {
        'name' : fields.many2one('res.partner', 'Supplier', required=True,domain = [('supplier','=',True)], ondelete='cascade', help="Supplier of this product"),
        'supplier_price': fields.related('pricelist_ids', 'price', type='float', relation='pricelist.partnerinfo', string="Supplier Price", readonly="1"),

	}

class product_category(osv.osv):
	_inherit="product.category"

	def create(self, cr, uid, vals, context=None):
		if vals.get('name', False):
			lower = vals.get('name', False)
			value = lower.upper()
			vals.update({'name': value})
		return super(product_category, self).create(cr, uid, vals, context=context)
	def write(self, cr,ids, uid, vals, context=None):
		if vals.get('name', False):
			lower = vals.get('name', False)
			value = lower.upper()
			vals.update({'name': value})
		return super(product_category, self).write(cr, ids,uid, vals,)
	_sql_constraints = [
		('productcatg_uniq', 'unique(name)', 'Product Category must be unique!'),
	]

class product_attributes_tree(osv.osv):
	_inherit="product.attribute"

	def create(self, cr, uid, vals, context=None):
		if vals.get('name', False):
			lower = vals.get('name', False)
			value = lower.upper()
			vals.update({'name': value})


		return super(product_attributes_tree, self).create(cr, uid, vals, context=context)
	def write(self, cr,ids, uid, vals, context=None):
		if vals.get('name', False):
			lower = vals.get('name', False)
			value = lower.upper()
			vals.update({'name': value})
		return super(product_attributes_tree, self).write(cr, ids,uid, vals,)

	_sql_constraints = [
		('product_attr_uniq', 'unique(name)', 'Product Attibute must be unique!'),
	]

