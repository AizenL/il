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
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
##### Selection Values Declaration


_EMPLOYEE_STATUS = [('notice_period' , 'Notice Period'),('probation' , 'Probation'),('temporary','Temporary'),('permanent','Permanent'),('terminated','Terminated'),('resigned','Resigned'),('absconded','Absconded')]
################################################################################################

class employee_status(osv.osv_memory):
    _name = "employee.status"
    _columns = {
    'status' : fields.selection(_EMPLOYEE_STATUS, 'Employee Status', required=True),
    'start_date' : fields.date('Start Date', required=True),
    'end_date': fields.date('End Date', required=False),
    }


    def update_status(self, cr, uid, ids, context=None):
        """ Update the employee status in the HR """
        hr_obj = self.pool.get('hr.employee')
        hr_status_obj = self.pool.get('employee.history.lines')
        wizard = self.browse(cr, uid, ids[0], context)
        hr_ids = context.get('active_ids', [])
        status = []
        hr_class = hr_obj.browse(cr, uid, hr_ids, context)
        for obj in hr_class.employee_status_line:
            if obj.status:
                status.append(obj.status)
        if wizard.status not in status:
            # Gets the status of the employee
            hr_id = hr_status_obj.create(cr, uid,{
                'hr_id' : hr_ids[0],
                'status' : wizard.status,
                'start_date' : wizard.start_date,
                'end_date' : wizard.end_date,
                })
        hr_obj.write(cr, uid, hr_ids, {'status':wizard.status})
        if wizard.status == 'probation':
            values ={}
            prob_leave_type_id=self.pool.get('hr.holidays.status').search(cr,uid,[('prob_leave','=',True)],context=context)
            # pdb.set_trace()
            #prob_leave_type_rec=self.pool.get('hr.holidays.status').browse(cr,uid,prob_leave_type)
            prod_obj = self.pool.get('hr.holidays').search(cr, uid, [('employee_id', 'in', hr_ids),('holiday_status_id', '=', prob_leave_type_id[0])], context=context)
            
            if not prod_obj:
                values['name'] = 'Probation Leaves Allocation'
                values['holiday_status_id']=prob_leave_type_id[0]
                values['employee_id']=hr_ids[0]
                values['number_of_days']=6
                values['number_of_days_temp']=6
                values['type']='add'
                values['meeting_id']= False
                values['notes']= False
                values['holiday_type']= 'employee'
                values['parent_id']= False
                values['state']= 'validate'
                values['category_id']= False




                new_id = self.pool.get('hr.holidays').create(cr, uid, values, context=context)
        if wizard.status == 'permanent':
            values ={}
            sick_leave_type_id=self.pool.get('hr.holidays.status').search(cr,uid,[('sick_leave','=',True)],context=context)
            casual_leave_type_id=self.pool.get('hr.holidays.status').search(cr,uid,[('casual_leave','=',True)],context=context)
            # pdb.set_trace()
            #prob_leave_type_rec=self.pool.get('hr.holidays.status').browse(cr,uid,prob_leave_type)
            sick_obj = self.pool.get('hr.holidays').search(cr, uid, [('employee_id', 'in', hr_ids),('holiday_status_id', '=', sick_leave_type_id[0])], context=context)
            casual_obj = self.pool.get('hr.holidays').search(cr, uid, [('employee_id', 'in', hr_ids),('holiday_status_id', '=', casual_leave_type_id[0])], context=context)
            if not sick_obj:
                values['name'] = 'Sick Leaves Allocation'
                values['holiday_status_id']=sick_leave_type_id[0]
                values['employee_id']=hr_ids[0]
                values['number_of_days']=3
                values['number_of_days_temp']=3
                values['type']='add'
                values['meeting_id']= False
                values['notes']= False
                values['holiday_type']= 'employee'
                values['parent_id']= False
                values['state']= 'validate'
                values['category_id']= False
                new_id = self.pool.get('hr.holidays').create(cr, uid, values, context=context)
            if not casual_obj:
                values['name'] = 'Casual Leaves Allocation'
                values['holiday_status_id']=casual_leave_type_id[0]
                values['employee_id']=hr_ids[0]
                values['number_of_days']=3
                values['number_of_days_temp']=3
                values['type']='add'
                values['meeting_id']= False
                values['notes']= False
                values['holiday_type']= 'employee'
                values['parent_id']= False
                values['state']= 'validate'
                values['category_id']= False
                new_id = self.pool.get('hr.holidays').create(cr, uid, values, context=context)


employee_status()
