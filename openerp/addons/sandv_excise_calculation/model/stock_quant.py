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
import itertools
from lxml import etree

from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools import float_compare
import openerp.addons.decimal_precision as dp






############################################ Stock Quant ##############################################################

class stock_quant(models.Model):
    _inherit = 'stock.quant'



    amount_untaxed = fields.Float(string='Subtotal', digits=dp.get_precision('Account'),store=True,readonly=True,compute='_compute_amount', track_visibility='always')
    amount_tax = fields.Float(string='Tax', digits=dp.get_precision('Account'), store=True, readonly=True, compute='_compute_amount')
    amount_total = fields.Float(string='Total', digits=dp.get_precision('Account'),store=True, readonly=True, compute='_compute_amount')
    other_charges = fields.Float(string='Other Charges', digits=dp.get_precision('Account'),store=True, readonly=True, compute='_compute_amount')
    sale_ids = fields.Many2many('sale.order', 'sale_order_invoice_rel', 'invoice_id', 'order_id', 'Sale Orders', readonly=True, help="This is the list of sale orders related to this invoice.")
    purchase_ids = fields.Many2many('purchase.order', 'purchase_order_invoice_rel', 'invoice_id', 'order_id', 'Purchase Orders', readonly=True, help="This is the list of purchase orders related to this invoice.")
    packing_charges = fields.Float(string='Packing Charges', digits=dp.get_precision('Account'),store=True, readonly=True, compute='_compute_other_charges')
    freight_charges = fields.Float(string='Freight Charges', digits=dp.get_precision('Account'),store=True, readonly=True, compute='_compute_other_charges')
    insurance_charges = fields.Float(string='Insurance Charges', digits=dp.get_precision('Account'),store=True, readonly=True, compute='_compute_other_charges')

