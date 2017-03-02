from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
import pdb
import base64
import csv
import logging
import StringIO

def process_csv_data(csv_data):

    datafile = StringIO.StringIO(base64.decodestring(csv_data))
    csvReader = csv.reader(datafile, dialect='excel')

    cline = []
    for row in csvReader:
        cline.append(row)
    return cline
class import_product(osv.osv_memory):

	_name="import.product"


	_columns={


	    'selection_item':fields.binary('CSV File',filters="*.csv"),
	}
	def get_csv(self,cr,uid,ids,context=None):
		
		if context is None:
			context={}
		data=self.read(cr,uid,ids)[0]
		data1=self.browse(cr,uid,ids)[0]
		rec_ids=context and context.get('active_ids',[])
		if data and data1:
			data_list=process_csv_data(data['selection_item'])

			index = {}
        	for x in data_list[0]:
           		index[x]=data_list[0].index(x)
	        unavailable_product_names = []
	        lines = 0
	        prod_obj = self.pool.get('product.product')
	        for data in data_list[1:]:
	        	values ={}
	        	lines += 1
	        	
	        	product_code = data[index['IL Part No']]
	        	product_id = prod_obj.search(cr, uid, [('default_code', '=', product_code)], context=context)
	        	if product_id:
	        		
	        		product_rec = prod_obj.browse(cr, uid, product_id[0], context=context)
	        		values['il_part_no'] = product_code
	        		values['product_id'] = product_rec.id
	        		values['name'] = product_rec.name
	        		#pdb.set_trace()
	        		values['product_brand'] = product_rec.product_brand.id
	        		values['mrp'] = data[index['MRP']]
	        		values['discount'] = data[index['Discount']]
	        		values['cst_vat_selection'] =data[index['CST / VAT Selection']]
	        		values['no_cst_vat_percent'] = data[index['CST/VAT']]
	        		#pdb.set_trace()
	        		values['no_entry_tax_percent'] = data[index['Entery Tax']]
	        		values['margin'] = data[index['Margin']]
	        		values['customer_code'] = data[index['Customer Code']]
	        		values['pricelist_id'] = context.get('active_id')
	        		
	        		new_id = self.pool.get('item.list').create(cr, uid, values, context=context)	
	        		# pdb.set_trace()


	# def print_report(self, cr, uid, ids, context=None):
	#     datas = {}
	#     a=[]
	#     print "---------------------------------------------------------------"
	#     for phone in self.browse(cr, uid, ids, context=context):
	#     	b=phone.selection_item
	#     print b
	#     if context is None:
	#     	context = {}
	#     datas['ids'] = context.get('active_ids', [])
	#     datas['model'] = context.get('active_model', 'ir.ui.menu')
	#     datas['value']=b
	#     context.update({'names':b})
	#     return {
	    
	#     'type': 'ir.actions.report.xml',
 #        'report_name': 'sales_invoice.report_mom',
 #        'datas': datas, 
 #        'context':context}

	# def print_report1(self, cr, uid, ids, context=None):
	#     datas = {}
	#     a=[]
	#     print "---------------------------------------------------------------"
	#     for phone in self.browse(cr, uid, ids, context=context):
	#     	b=phone.selection_item
	#     print b
	#     if context is None:
	#     	context = {}
	#     datas['ids'] = context.get('active_ids', [])
	#     datas['model'] = context.get('active_model', 'ir.ui.menu')
	#     datas['value']=b
	#     context.update({'names':b})
	#     return {
	    
	#     'type': 'ir.actions.report.xml',
 #        'report_name': 'sales_invoice.report_invoice',
 #        'datas': datas, 
 #        'context':context}
	#     # return self.pool['report'].get_action(self, 'sales_invoice.report_mom',data=datas)
	    
	    
