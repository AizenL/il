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
    'name': 'Order Lines Extended form view',
    'version': '1.1',
    'category': 'Invoicing',
    'summary': "Order Lines Extended form view",
    'description': """
This module will give the summary of other charges in account invoice. This will change the values of Sale Order based on the taxes and charges in invoice
==========================================================================================================================================================
""",
    'author': 'Hari',
    'website': 'http://www.odoo.com',
    'depends': [
            'product','sale','stock','sale_stock','purchase','account'
            ],
    'data': [
        'data/invoice_line_view.xml',
        ],
    'demo': [ ],
    'test': [ ],
    'installable': True,
    'active': False,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
