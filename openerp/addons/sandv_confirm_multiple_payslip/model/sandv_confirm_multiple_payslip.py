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

class hr_payslip_run(osv.osv):
    _inherit = "hr.payslip.run"
    
    def confirm_multiple_payslip(self, cr, uid, ids, context=None):
            # hr_type_obj = self.pool.get('hr.payslip.run')
            slip_type_obj = self.pool.get('hr.payslip')
            for rec in self.browse(cr, uid, ids, context=context):
                slip_ids = rec.slip_ids
                if slip_ids :
                    for slip_id in slip_ids :
                        # pdb.set_trace()
                        print "\n\n\n\n\n+++++",slip_id
                        slip_type_obj.signal_workflow(cr, uid, [slip_id.id], 'hr_verify_sheet')
                self.write(cr, uid, rec.id, {'state': 'close'}, context=context)                  
            return  True
