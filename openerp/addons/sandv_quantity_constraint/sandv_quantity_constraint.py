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

class sandv_quantity_constraint(osv.osv):
    _inherit = "stock.transfer_details_items"
    def onchange_lot_id(self, cr, uid, ids,quantity, lot_id,context=None):
        # pdb.set_trace()
        transfer_details_brow = self.browse(cr, uid, ids, context=context)
        if transfer_details_brow.transfer_id.picking_id.picking_type_id.id == 2:

            Quantity = transfer_details_brow.quantity
            production_lot_obj = self.pool.get('stock.production.lot')
            lot_id = production_lot_obj.browse(cr, uid, lot_id, context=context)
            serial_Number = lot_id.name
            on_hand = lot_id.qty_available
            if Quantity > on_hand :
                raise osv.except_osv(_('Warning!'),_('Selected Lot Number not have required Quantity of Product,Please select other Lot Number '))

    def write(self, cr, uid, ids,vals, context=None):
        # pdb.set_trace()
        transfer_details_brow = self.browse(cr, uid, ids, context=context)
        if transfer_details_brow.transfer_id.picking_id.picking_type_id.id == 2:
            Quantity = transfer_details_brow.quantity
            if vals['lot_id']:
                lot_obj = self.pool.get('stock.production.lot').browse(cr, uid, vals['lot_id'], context=context)
                serial_number = lot_obj.name
                on_hand = lot_obj.qty_available
            if Quantity > on_hand :
                raise osv.except_osv(_('Warning!'),_('Selected Lot Number not have required Quantity of Product,Please select other Lot Number '))
        res = super(sandv_quantity_constraint, self).write(cr, uid, ids,vals, context=None)
        return res        
sandv_quantity_constraint()

