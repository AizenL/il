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
    'name': 'Purchase Amendment',
    'version': '1.1',
    'category': 'Purchase Management',
    'summary': "Order Amendment",
    'description': """
This module can be used to amend the Purchase Order.
=====================================================
""",
    'author': 'Hariharan',
    'website': 'http://www.itarait.com',
    'depends': [
            'purchase',
            'stock',
            'itara_purchase_approval',
            ],
    'data': [
        'security/purchase_amendment.xml',
        'security/ir.model.access.csv',
        'data/purchase_workflow.xml',
        'data/purchase_amendment_view.xml',
        'data/purchase_view.xml',
        ],
    'demo': [ ],
    'test': [ ],
    'installable': True,
    'active': False,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
