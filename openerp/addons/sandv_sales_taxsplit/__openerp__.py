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
    'name': 'Tax Summary In Sale Order',
    'version': '1.1',
    'category': 'Sales Management',
    'summary': "Tax Summary in sale order",
    'description': """
This module will give the detailed summary of taxes in the sale order form view. In addition,it will show the splitups in other charges
========================================================================================================================================
""",
    'author': 'Hari',
    'website': 'http://www.odoo.com',
    'depends': [
            'sale','account','base'
            ],
    'data': [
        'data/sale_order_view.xml',
        ],
    'demo': [ ],
    'test': [ ],
    'installable': True,
    'active': False,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
