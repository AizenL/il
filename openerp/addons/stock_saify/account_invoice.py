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

from openerp.osv import osv
from openerp.tools.translate import _

class account_invoice_cancel_reset(osv.osv_memory):
    """
    This wizard will cancel and reset the all the selected invoices.
    If in the journal, the option allow cancelling entry is not selected then it will give warning message.
    """

    _name = "account.invoice.cancel.reset"
    _description = "Cancel and Reset the Selected Invoices"

    def invoice_cancel_reset(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        proxy = self.pool['account.invoice']
        active_ids = context.get('active_ids', []) or []

        for record in proxy.browse(cr, uid, active_ids, context=context):
            if record.state in ('cancel','paid'):
                raise osv.except_osv(_('Warning!'), _("Selected invoice(s) cannot be cancelled as they are already in 'Cancelled' or 'Done' state."))
            record.signal_workflow('invoice_cancel')
            record.write({'state': 'draft'})
            record.delete_workflow()
            record.create_workflow()
            record.button_reset_taxes()
            record.signal_workflow('invoice_open')
            print "Invoice ID ====", record

        return {'type': 'ir.actions.act_window_close'}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
