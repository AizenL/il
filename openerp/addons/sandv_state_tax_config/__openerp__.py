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
    'name': 'Tax Configuration',
    'version': '1.1',
    'category': 'Invoicing',
    'summary': "Tax Configuration based on state",
    'description': """
This module captures the taxation details with respect to the State.
=======================================================================
""",
    'author': 'Hari',
    'website': 'http://www.odoo.com',
    'depends': [
            'account','base','sale'
            ],
    'data': [
        'data/tax_configuration_view.xml',
        ],
    'demo': [ ],
    'test': [ ],
    'installable': True,
    'active': False,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
