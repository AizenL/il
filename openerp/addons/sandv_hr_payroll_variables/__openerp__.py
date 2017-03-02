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

{
    'name': 'SandV HR Payroll Variables',
    'version': '1.0',
    'category': 'HR',
    'sequence': 14,
    'summary': 'SandV HR Payroll Variables',
    'description': """
    Used to import or create the monthly salary variables amounts
    """,
    'author': 'Khalid Ahmed',
    'website': 'https://www.sandv.biz',
    'depends': ['hr_payroll'],
    'data': [
        'security/ir.model.access.csv',
        'sandv_hr_payroll_variables_view.xml',
        # 'security/payroll_security.xml',
    ],
    'demo': [],
    'test': [
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
