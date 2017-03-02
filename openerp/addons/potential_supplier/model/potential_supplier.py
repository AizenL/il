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

class potential_supllier(osv.osv):
    _name = 'potential.supplier'

    def convert_sup(self, cr, uid, ids, context=None):
        # pdb.set_trace()
        context = context or {}
        self.write(cr, uid, ids, {'state': 'draft'})
        
        return True

    def inprogress(self, cr, uid, ids, context=None):
        # pdb.set_trace()
        context = context or {}
        self.write(cr, uid, ids, {'state': 'inprogress'})
        
        return True

    def cancel_supl(self, cr, uid, ids, context=None):
        # pdb.set_trace()
        context = context or {}
        self.write(cr, uid, ids, {'state': 'cancel'})
        
        return True

    def reset_new(self, cr, uid, ids, context=None):
        # pdb.set_trace()
        context = context or {}
        self.write(cr, uid, ids, {'state': 'new'})
        
        return True


    def create_res_partener(self, cr, uid, ids, context=None):

            res_partner_obj = self.pool.get('res.partner')
            potential_supplier = self.browse(cr, uid, ids, context=context)
            ctx = context.copy()
            ctx.update()
            res_country_id=potential_supplier.country_id.id
            res_country_state=potential_supplier.state_id.id
            nature_of_buisness_id=potential_supplier.nature_of_buisness
            obj={
                'name': potential_supplier.company_name,
                'street':potential_supplier.street,
                'street2':potential_supplier.street2,
                'city':potential_supplier.city,
                'state_id':res_country_state,
                'zip': potential_supplier.zip,
                'email':potential_supplier.email,
                'country_id':res_country_id,
                'mobile':potential_supplier.mobile,
                'division':potential_supplier.product_name,
                'commissionerae':nature_of_buisness_id,
                'concern_person':potential_supplier.contact_person,
                'attachments':potential_supplier.attachments,
                'customer':False,
                'is_company':True,
                'supplier':True,
                }
            new_partner_id=res_partner_obj.create(cr,uid,obj,context=context)
            #res_partner_obj.create(cr,uid,{'parent_id':new_partner_id ,'name':potential_supplier.contact_person},context=context)
            
            self.write(cr, uid, ids, {'state': 'done'})
            return True

    _columns = {
        'company_name': fields.char('Name of the company'),
        'adress':fields.char('Corporate head office adress'),
        'street': fields.char('Street'),
        'street2': fields.char('Street2'),
        'city': fields.char('City'),
        'state_id': fields.many2one("res.country.state", 'State', ondelete='restrict'),
        'zip': fields.char('Zip', size=24, change_default=True),
        'country_id': fields.many2one('res.country', 'Country'),
        'email': fields.char('Email'),
        'contact_person': fields.char('Contact Person'),
        'mobile': fields.char('Mobile'),
        'product_category': fields.char('Product Category'),
        'product_name':fields.char('Product Name'),
        'nature_of_buisness': fields.selection([('manufacturer', 'Manufacturer'),('dealer', 'Dealer'), ('distributor', 'Distributor')], "Nature of buisness", required=True),
        'supplier_id':fields.many2one('res.partner','Potential Supplier',readonly=1),
        'state': fields.selection([('new', 'New'),
                                   ('inprogress', 'In progress'),
                                   ('done', 'Done'),
                                   ('cancel', 'Cancelled'),], string='State'),

        'attachments': fields.many2many('ir.attachment', string="Attachments")
    }    

    _defaults = {
       'state': 'new',
    }













