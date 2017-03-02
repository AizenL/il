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
from openerp import api, models
from openerp.tools import amount_to_text
from openerp.tools import amount_to_text_en

import time
from openerp.osv import osv
from openerp.report import report_sxw


class sandv_batch_payslip(osv.osv):
	_inherit = 'hr.payslip.run'

	def get_total_deduction(self,cr,uid,payslip_id):
		#pdb.set_trace()
		total_deduction = 0.0
		paylisp_row = self.pool.get('hr.payslip').browse(cr,uid,payslip_id)
		payslip_line_ids = paylisp_row.line_ids
		if payslip_line_ids :
			for payslip_line_id in payslip_line_ids :
				if payslip_line_id.category_id.name == 'Deduction' :
					total_deduction = total_deduction + payslip_line_id.total
		return total_deduction
