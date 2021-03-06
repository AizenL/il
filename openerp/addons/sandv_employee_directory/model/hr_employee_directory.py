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
import re
from openerp import addons
import logging
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import tools
import pdb


class employee_type(osv.osv):
    _name = "employee.type"
    _columns = {
    'name' : fields.char('Employee Type'),
    'probabition_type':fields.boolean('Probation'),
    'perment_type':fields.boolean('Perment Type'),
    }
employee_type()
class hr_holiday_type(osv.osv):
    _inherit = "hr.holidays.status"
    _columns = {
    'sick_leave':fields.boolean('Sick Leave'),
    'casual_leave':fields.boolean('Casual Leave'),
    'prob_leave':fields.boolean('Probation Leave'),
    'earned_leave':fields.boolean('Earned Leave'),
    }
hr_holiday_type()


class hr_employee(osv.osv):
    
    _inherit = 'hr.employee'
    _columns = {
        'address_ids': fields.one2many('hr.address', 'address_id', 'Contact Information'),
        'blood_group': fields.selection([('O-', 'O-'), ('O+', 'O+'), ('A-', 'A-'), ('A+', 'A+'),('B-', 'B-'),('B+', 'B+'),('AB-', 'AB-'),('AB+', 'AB+')], 'Blood Group'),
        'personal_email': fields.char('Personal E-Mail', size=240),
        'personal_phone': fields.char('Personal Phone Number', size=64),
        'education_details_line': fields.one2many('hr.education.details','hr_id','Education Details'),
        'identification_details_lines' : fields.one2many('employee.identification.details','hr_id','Identification Details'),
        'bank_details_line' : fields.one2many('bank.details.line','hr_id','Bank Details'),
        'related_ids' : fields.one2many('hr.employee.related.details', 'employee_id',string='Related'),
        'employee_type' : fields.many2one('employee.type','Employee Type'),
        'joining_date' : fields.date('Joining Date',  size=240),
    }


    def onchange_personal_email(self, cr, uid, ids, personal_email):
        if personal_email :
            if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", personal_email) != None:
                return True
            else:
                raise osv.except_osv('Invalid Personal Email', 'Please enter a valid email address')
            
    def onchange_work_email(self, cr, uid, ids, work_email):
        if work_email :
            if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", work_email) != None:
                return True
            else:
                raise osv.except_osv('Invalid Work Email', 'Please enter a valid email address')
        

hr_employee()

class identification_type(osv.osv):
    _name = "identification.type"
    _columns = {
    'name' : fields.char('Name')
    }
identification_type()

class employee_identification_details(osv.osv):
    _name = "employee.identification.details"
    _columns = {
    'hr_id' : fields.many2one('hr.employee','Employee Reference'),
    'id_type' : fields.many2one('identification.type','ID Types'),
    'id_number' : fields.char('ID Number'),
    'id_issued_date' : fields.date('ID Issue Date'),
    'id_expiry_date' : fields.date('ID Expiry Date'),
    'id_issued_by' : fields.char('Issued By'),
    'upload_id': fields.binary('Upload Document'),
    }
employee_identification_details()


class education_board(osv.osv):
    _name = "education.board"
    _columns = {
    'name' : fields.char('Educational Board'),
    }
education_board()

class highest_qualification(osv.osv):
    _name = "degree.list"
    _columns = {
    'name' : fields.char('Qualification'),
    }
highest_qualification()

class hr_education_details(osv.osv):
    _name = 'hr.education.details'
    _columns = {
    'hr_id':fields.many2one('hr.employee','Educational Reference'),
    'name' : fields.many2one('education.board','Name/Board of University'),
    'highest_qualitfication' : fields.many2one('degree.list','Qualification'),
    'marks_obtained': fields.float('Marks Obtained'),
    'grade': fields.char('Grade'),
    'year_of_passing': fields.char('Year Of Passing'),
    'edu_active': fields.boolean('Active'),
    'upload_edu_docs': fields.binary('Upload Certificates'),
    }

    _defaults = {
	'edu_active':True
	}

hr_education_details()

class address_type(osv.osv):
    _name = "address.type"

    _columns = {
    'name' : fields.char('Name', size=60, required=True),
    'seq' : fields.integer('Sequence'),
    }
address_type()

class hr_address(osv.osv):
    _name = "hr.address"
    _description = "Employee Address"
    _columns = {
        'name': fields.char('Contact Name', size=60),
        'address_info': fields.many2one('address.type', 'Address Type'),  
        'street': fields.char('Street1', size=60),
        'street2': fields.char('Street2', size=60),
        'zip': fields.char('Postal Code', size=24),
        'city': fields.char('City', size=60),
        'state_id': fields.many2one("res.country.state", 'State'),
        'country_id': fields.many2one('res.country', 'Country'),
        'phone': fields.char('Phone'),
        'mobile': fields.char('Mobile'),              
        'address_id':fields.many2one('hr.employee','Employee ID'),
        'status':fields.selection([('active','Active'),('expired','Expired')],'Status'),

        }

hr_address()

class bank_details_line(osv.osv):
    _name = 'bank.details.line'
    _columns = {
    'hr_id' : fields.many2one('hr.employee','HR Reference'),
    'bank_account_id': fields.many2one('res.partner.bank', 'Bank Account Number'),
    'is_salary_account': fields.boolean('Is Salary Account?'),
    }
bank_details_line()

class employee_relation(osv.osv):
	_name = 'employee.relation'
	_columns = {
	'name' : fields.char('Relation'),
	}
employee_relation()

class hr_employee_related_details(osv.osv):
    _name = 'hr.employee.related.details'
    _description = 'Employee related Details'

    _columns = {
    'employee_id' : fields.many2one('hr.employee', string='Employee'),
    'name' : fields.char("First name"),
    'age' : fields.float('Age'),
    'last_name' : fields.char("Last name"),
    'birth_name' : fields.char("Birth name"),
    'gender' : fields.selection([('male', 'Male'), ('female', 'Female')], string='Gender'),
    'relation_id' : fields.many2one('employee.relation','Employee relation'),
    'birth_date' : fields.date(string="Birth date"),
    'telephone' : fields.char("Telephone"),
    'note' : fields.text("Note"),
    'is_dependent' : fields.boolean('Dependent?'),
    'is_salaried' : fields.boolean('Salaried?'),
    'salary_details' : fields.integer('Salary'),
    'is_emergency' : fields.boolean('Emergency Contact'),
    'child_class' : fields.char('Class',size=256),
    }
hr_employee_related_details()
