from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
import pdb


class prints_wizard(osv.osv_memory):

	_name="prints.wizard"


	_columns={


	    'selection_item':fields.selection([('Original', 'Original'), ('Duplicate', 'Duplicate'),('Triplicate', 'Triplicate'),('Extra', 'Extra')],'Select',required=True),
	}


	def print_report(self, cr, uid, ids, context=None):
	    datas = {}
	    a=[]
	    print "---------------------------------------------------------------"
	    for phone in self.browse(cr, uid, ids, context=context):
	    	b=phone.selection_item
	    print b
	    if context is None:
	    	context = {}
	    datas['ids'] = context.get('active_ids', [])
	    datas['model'] = context.get('active_model', 'ir.ui.menu')
	    datas['value']=b
	    context.update({'names':b})
	    return {
	    
	    'type': 'ir.actions.report.xml',
        'report_name': 'sales_invoice.report_mom',
        'datas': datas, 
        'context':context}

	def print_report1(self, cr, uid, ids, context=None):
	    datas = {}
	    a=[]
	    print "---------------------------------------------------------------"
	    for phone in self.browse(cr, uid, ids, context=context):
	    	b=phone.selection_item
	    print b
	    if context is None:
	    	context = {}
	    datas['ids'] = context.get('active_ids', [])
	    datas['model'] = context.get('active_model', 'ir.ui.menu')
	    datas['value']=b
	    context.update({'names':b})
	    return {
	    
	    'type': 'ir.actions.report.xml',
        'report_name': 'sales_invoice.report_invoice',
        'datas': datas, 
        'context':context}
	    # return self.pool['report'].get_action(self, 'sales_invoice.report_mom',data=datas)
	    
	    
