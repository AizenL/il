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
    'name': 'Stock Saify',
    'version': '1.1',
    'author': 'OpenERP SA',
    
    'category': 'All Operation',
    'sequence': 8,
    'summary': 'Projects,',
    'depends': [
        'base_setup',
        
        'stock',
        'mail',
        'purchase',
        'account',
        'sale',

        
        'web_kanban'
    ],
    'description': """

    """,
    'data': [
        
        'stock_picking_inherit_view.xml',
       'res_partner_inherit_view.xml',
        'so_po_account_menuitem.xml',

         'security/ir.model.access.csv',
        'product_inherit_view.xml',
       'purchase_order_inherit_view.xml',
        'sale_order_inherit_view.xml',
        'stock_landed_inherit_view.xml',
        'crons_schedular_view.xml',
        'ir_sequence_inherit_view.xml',
        'purchase_forecast_view.xml',
        'account_invoice.xml',
        'wizard/bank_statement_view.xml',
        'account_bank_statement_line_view.xml',
        
        ],
   
    # 'test': [
    
    'installable': True,
    'auto_install': False,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
