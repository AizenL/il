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
from openerp import models, fields, api, _
from _dbus_bindings import String
import random
from openerp.exceptions import ValidationError
from twisted.application.strports import _DEFAULT
from pygooglechart import QRChart
from qrtools import QR
import base64
import tempfile
from PIL import Image
import qrtools
import cStringIO
import json
import ast
from ast import literal_eval
from collections import MutableMapping
# import demjson
# from matplotlib.mathtext import Char
from openerp.exceptions import except_orm, Warning, RedirectWarning
import pdb
import sys, qrcode
import random

class product_master(models.Model):
    _name = "product.master"

    @api.model
    def create(self,vals):
        material_number = vals.get('material_number')
        material_name = vals.get('name')
        if material_number and material_name:
            vals['ref'] = self.env['ir.sequence'].next_by_code('product')
        return super(product_master, self).create(vals)

    def action_generate_qr(self, cr, uid, ids, context=None):
        """ generate QR Code """
        for val in self.browse(cr, uid, ids, context=context):
            val.qr_data = ''
    	    code = {}
            code['name'] = val.name
            code['material_number'] = val.material_number
            code['unit_price'] = val.unit_price
            code['id'] = val.id
            view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'sandv_qr_code', 'product_master_form_view')
            view_id = view_ref and view_ref[1] or False
            code['view_id'] = view_id
    	    qrCode = QR(data=str(code))
    	    qrCode.encode()
            val.qr_file = qrCode.filename
    	    val.qr_code = open(qrCode.filename, 'rb').read().encode('base64')
            val.qr_data = qrCode.data_to_string()
            val.image_name = str(val.material_number) + str(val.name)
	    self.write(cr,uid,ids,{'is_qr_generated':True})

    def action_generate_qr(self, cr, uid, ids, context=None):
        """ generate QR Code """
        for val in self.browse(cr, uid, ids, context=context):
            val.qr_data = ''
    	    code = {}
            code['name'] = val.name
            code['material_number'] = val.material_number
            code['unit_price'] = val.unit_price
            code['id'] = val.id
            view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'sandv_qr_code', 'product_master_form_view')
            view_id = view_ref and view_ref[1] or False
            code['view_id'] = view_id
    	    qrCode = QR(data=str(code))
    	    qrCode.encode()
            val.qr_file = qrCode.filename
    	    val.qr_code = open(qrCode.filename, 'rb').read().encode('base64')
            val.qr_data = qrCode.data_to_string()
            val.image_name = str(val.material_number) + str(val.name)
	    self.write(cr,uid,ids,{'is_qr_generated':True})

    def receive_material(self, cr, uid, ids, context=None):
        """ generate QR Code """
        for val in self.browse(cr, uid, ids, context=context):
	    self.write(cr,uid,ids,{'state':'received'})

    qr_code = fields.Binary('QR Code')
    qr_data = fields.Char('Data')
    name = fields.Char('PO Number')
    image_name = fields.Char('Image Name')
    line_item = fields.Integer('Line Item')
    material_number = fields.Char('Material Number')
    material_desc = fields.Char('Material Description')
    uom = fields.Char('UOM',size=256)
    qty = fields.Float('PO Qty')
    unit_price = fields.Float('Unit Price')
    total = fields.Float('Total')
    currency = fields.Char('Currency')
    qr_file = fields.Char('QR Code')
    received_qty = fields.Float('Recd Qty')
    is_qr_generated = fields.Boolean('QR Generated')
    state = fields.Selection([('draft', 'Draft'),('received', 'Received')], string='State')

    _defaults = {
        'state': 'draft'
	    }


class product_scan(models.Model):
    _name = 'product.scan'

    def action_view_form(self, cr, uid, ids, context=None):
        """ Open Respective form view """
        res_id = 0
        view_id = 0
        for val in self.browse(cr, uid, ids, context=context):
            mydict = {}
            if val.qr_code:
                res_id = random.sample(range(1, 50), 1)
                view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'sandv_qr_code', 'product_master_form_view')
                view_id = view_ref and view_ref[1] or False,

        return {
            'type': 'ir.actions.act_window',
            'name': _('PO'),
            'res_model': 'product.master',
            'res_id': res_id[0],
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'current',
            'nodestroy': True,
        }
                

    qr_code = fields.Binary('QR Code')
    qr_data = fields.Char('Data')
