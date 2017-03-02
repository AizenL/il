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


class res_partner_inherit(osv.osv):


	_inherit="res.partner"
	_description = "stock move"
	_columns={
		'vat_tin':fields.char('VAT TIN / CST NO.'),
		'excise_reg_no':fields.char('Excise Reg NO.'),
		'cts_no':fields.char('CST NO.'),
		'range':fields.char('Range'),
		'division':fields.char('Division'),
		'commissionerae':fields.char('Commissionerate'),
		'pan_no':fields.char('PAN Card NO'),
		'ecc':fields.char('ECC'),
		'tin':fields.char('TIN'),
		'cin':fields.char('CIN'),
		'concern_person':fields.char('Concerned Person'),

		'attachments': fields.many2many('ir.attachment', 'partner_attachment_rel', 'partner_id', 'attachment_id', string="Attachments"),
	}
   

	def is_phone(self, cr, uid, ids, context=None):
		record = self.browse(cr, uid, ids)
		pattern ="^[0-9]{10}$"
		for data in record:
			if data.mobile != False:
				if not re.match(pattern, data.mobile):
					return False
			# else:
			# 	return False

		return True
	# def is_phone(self, cr, uid, ids, context=None):
	# 	pattern ="^[0-9]{10}$"
 #    	for obj in self.browse(cr, uid, ids, context=context):
 #    		if obj.mobile != False :
 #    			if not re.match(pattern, data.mobile):
 #    				return False
 #    	return True
	# _constraints = [(is_phone, 'Invalid Phone Number  ', ['mobile']),]
	def is_zip(self, cr, uid, ids, context=None):
		record = self.browse(cr, uid, ids)
		pattern ="^[0-9]{1,8}$"
		for data in record:
			if data.zip != False:
				if not re.match(pattern, data.zip):
					return False

			
		return True

	

	def is_phone1(self, cr, uid, ids, context=None):
		record = self.browse(cr, uid, ids)
		#pattern ="[0-9]{1,5}[-][0-9]{6,8}"
		pattern ="[0-9]{11}"
		for data in record:
			if data.phone != False:
				if not re.match(pattern, data.phone):
					return False
			
		return True

	def is_email(self, cr, uid, ids, context=None):
		record = self.browse(cr, uid, ids)
		pattern ="^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
		for data in record:
			if data.email != False:
				if not re.match(pattern, data.email):
					return False
		return True
	def is_vat_tin(self, cr, uid, ids, context=None):
		record = self.browse(cr, uid, ids)
		pattern ="^[0-9]$"
		for data in record:
			if data.vat_tin != False:
				if not (data.vat_tin).isdigit():
					return False
		return True

	_constraints = [(is_phone1, 'Invalid Phone Number  ', ['phone']),(is_zip, 'Invalid Zip Code  ', ['zip']),(is_phone, 'Invalid Mobile Number  ', ['mobile']),(is_email, 'Invalid Email ID  ', ['email']),]

	# (is_vat_tin, 'Invalid VAT TIN  ', ['vat_tin']),]



class res_company_inherit(osv.osv):


	_inherit="res.company"
	_description = "Company Detail"
	_columns={
		
		'ecc':fields.char('ECC'),
		'tin':fields.char('TIN'),
		'cin':fields.char('CIN'),
		
	}
