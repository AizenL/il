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

from datetime import datetime, timedelta
import time
from openerp import SUPERUSER_ID
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
import openerp.addons.decimal_precision as dp
from openerp import workflow

class sandv_hr_payroll_variables(osv.Model):
    _name = "sandv.hr.payroll.variables"
    _columns = {
    'variable_pay_rating':fields.float('Variable Pay'),
	'name':fields.many2one('hr.employee',string='Employee'),
	'start_date': fields.date('Start Date'),
	'end_date': fields.date('End Date'),
	# 'tds':fields.float('TDS'),
	# 'leave_deductions':fields.float('Leave Deductions'),
	# 'advance_deductions':fields.float('Advance Deductions'),
	'other_allowances' : fields.float('Other Allowances'),
	'other_deductions' : fields.float('Other Deductions'),
	# 'journal_entry_date': fields.date('Journal Entry Date'),
	# 'journal_id': fields.many2one('account.journal', 'Expense Journal',states={'draft': [('readonly', False)]}, readonly=True, required=False),
	# 'move_id': fields.many2one('account.move', 'Accounting Entry', readonly=True),       
	'state': fields.selection([
	('draft', 'New'),
	('done', 'Done'),
	('cancelled', 'Cancel')],
	'State', readonly=True),

	}

    _defaults = {
	'state':'draft'  ,
    }

    def hr_verify_sheet(self, cr, uid, ids, context=None):
    	pdb.set_trace()
    	emp_type_obj = self.pool.get('sandv.hr.payroll.variables')
    	for rec in self.browse(cr, uid, ids, context=context):
    		emp_search = emp_type_obj.search(cr,uid,[('name','=',rec.employee_id.id),('start_date','>=',rec.date_from),('end_date','<=',rec.date_to)])
    		# print "\n\n\n\n\n+++++",emp_search
    		if emp_search:	
    			emp_type_obj.write(cr, uid, emp_search, {'state': 'done'}, context=context)
    	self.write(cr, uid, ids, {'state': 'verify'}, context=context)
        return  True
