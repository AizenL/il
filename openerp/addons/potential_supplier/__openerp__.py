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
    'name': 'Potential Supplier',
    'version': '1.1',
    'author': 'sanju',
    'category': 'purchase',
    'sequence': 21,
    'website': 'http://www.openerp.com',
    'summary': 'potential supplier form',
    'description': """

==========================

This application enables you to potential supplier data form...



    """,
    'author': 'sanju',
    'website': 'http://www.openerp.com',
    'images': [

    ],
    'depends': ['base','purchase'],
    'data': [
        'data/potential_supplier.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [],
    'test': [


    ],
    'installable': True,
    'application': True,
    'active': False,
    'auto_install': False,

}
