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
from openerp import models, fields, api
from _dbus_bindings import String
import random
from openerp.exceptions import ValidationError
from twisted.application.strports import _DEFAULT
from matplotlib.mathtext import Char
from openerp.exceptions import except_orm, Warning, RedirectWarning

################## link tax and state #######################
class state_tax_config(models.Model):
    _name = 'state.tax.config'
    _rec_name = 'state_id'

    state_id = fields.Many2one('res.country.state',string='State',copy=False)
    tax_lines = fields.One2many('tax.list', 'state_tax_id', 'Related Tax', copy=False)


class tax_list(models.Model):
    _name = 'tax.list'

    state_tax_id = fields.Many2one('state.tax.config',string='State Reference',copy = False)
    tax_id = fields.Many2one('account.tax',String='Tax',copy=False)

########################################################################


############################ link state matrix configuration with tax ################################
class invoice_tax_config(models.Model):
    _name= 'invoice.tax.config'

    order_state_id = fields.Many2one('res.country.state',string='Order State',copy=False)
    delivery_state_id = fields.Many2one('res.country.state',string='Dispatch State',copy=False)
    material_state_id = fields.Many2one('res.country.state',string='Material State',copy=False)
    tax_lines = fields.One2many('invoice.tax.list', 'invoice_tax_list_id', 'Related Tax', copy=False)


class invoice_tax_list(models.Model):
    _name = 'invoice.tax.list'

    invoice_tax_list_id = fields.Many2one('invoice.tax.config', 'Invoice Reference',copy = False)
    state_id = fields.Many2one('res.country.state',string='State Tax of',required=True,copy=False)
    tax_id = fields.Many2one('account.tax',String='Tax',required=True,copy=False,widget="selection")

    @api.multi
    def onchange_state_id(self, state_id = False,tax_id =False):
        context = self._context
        state_tax_browse = self.env['state.tax.config']
        var_list = []
        if state_id:
            state_wise_tax = state_tax_browse.search([('state_id', '=', state_id)])
            if not state_wise_tax.id:
                raise except_orm(('Warning!'),
                                    ("You didn't mapped tax for its respective state"))
            if state_wise_tax.id:
                state_config_browse = state_tax_browse.browse(state_wise_tax.id)
                for obj in state_config_browse:
                    for line in obj.tax_lines:
                        var_list.append(line.tax_id.id)
                return {'domain':{'tax_id':[('id','in',var_list)]}}

######################################################################################


class account_invoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def button_reset_taxes(self):
        account_invoice_tax = self.env['account.invoice.tax']
        invoice_tax_config = self.env['invoice.tax.config']
        warehouse = self.env['stock.warehouse']
        tax_search = 0
        cr = self.env.cr
        uid = self.env.uid
        context = self.env.context
        ctx = dict(self._context)
        for invoice in self:
            #########                 Sandv code for creating tax matrix and automatically update in tax  ##############
            for inv_line in invoice.invoice_line:
                for sale in invoice.sale_ids:
                    for pick in invoice.picking_ids:
                        if (sale.partner_id.id != sale.partner_invoice_id.id) or (sale.partner_id.id != sale.partner_shipping_id.id):
                            part = self.pool.get('res.partner').browse(cr, uid, sale.partner_id.id, context=context)
                            addr = self.pool.get('res.partner').address_get(cr, uid, [part.id], ['delivery', 'invoice', 'contact'])
                            if not sale.partner_id.state_id or not pick.partner_id.state_id or not sale.warehouse_id.partner_id.state_id:
                                raise except_orm(('Warning!'),
                                            ("You have different invoice address and delivery address for this Customer. Kindly map the State for all different address."))
                            tax = cr.execute("select id from invoice_tax_config "
                            "where order_state_id =%s and delivery_state_id = %s and material_state_id = %s", (sale.partner_id.state_id.id,
                            pick.partner_id.state_id.id,sale.warehouse_id.partner_id.state_id.id,))
                            tax_search = cr.fetchone()
                            if not tax_search:
                                raise except_orm(('Error!'),
                                                    ("You didn't created the matrix configuration for these state taxes('%s' as Order State, '%s' as Despatch State, '%s' as Material State)")% 
                                                    (sale.partner_id.state_id.name,pick.partner_id.state_id.name,sale.warehouse_id.partner_id.state_id.name,))
                            if tax_search:
                                for obj in invoice_tax_config.browse(tax_search):
                                    inv_line.write({'invoice_line_tax_id': [(6, 0, [x.tax_id.id for x in obj.tax_lines])]})
            #########                 Sandv code for creating tax matrix and automatically update in tax  ##############
            self._cr.execute("DELETE FROM account_invoice_tax WHERE invoice_id=%s AND manual is False", (invoice.id,))
            self.invalidate_cache()
            partner = invoice.partner_id
            if partner.lang:
                ctx['lang'] = partner.lang
            for taxe in account_invoice_tax.compute(invoice.with_context(ctx)).values():
                account_invoice_tax.create(taxe)

        # dummy write on self to trigger recomputations
        return self.with_context(ctx).write({'invoice_line': []})


    @api.multi
    def button_compute(self, set_total=False):
        self.button_reset_taxes()
        for invoice in self:
            if set_total:
                invoice.check_total = invoice.amount_total
        return True