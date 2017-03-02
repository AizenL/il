##############################################################################
import time
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools.float_utils import float_compare
import pdb



class stock_picking_invoice(osv.osv):

    _inherit = "stock.picking"
   
    _columns = {


           }



    def _invoice_create_line(self, cr, uid, moves, journal_id, inv_type='out_invoice', context=None):


        res = super(stock_picking_invoice,self)._invoice_create_line(cr, uid, moves, journal_id, inv_type, context=context)    
        for mv in moves:
            for m1 in mv :
                move = mv[m1]
    #        for move in moves:
                picking_type = move.picking_id.picking_type_id
                if picking_type.id == 1 :
                    location = move.location_dest_id
                    complete_name = location.complete_name
                elif picking_type.id == 2 :
                    location = move.location_id
                    complete_name = location.complete_name
                owner = location.partner_id
                
                if picking_type.id == 2 or picking_type.id == 1 : 
                    if not owner :
                        raise osv.except_osv(_('Warning!'), _('Please define the Owner for the Stock location: %s' % (complete_name)))

                    from_loc = location.partner_id.state_id
                    if not from_loc:
                        raise osv.except_osv(_('Warning!'), _('Please define the State for the Partner: %s' % (owner.name)))

                    cust_loc = move.picking_id.partner_id.state_id
                    if not cust_loc:
                        raise osv.except_osv(_('Warning!'), _('Please define the State for the Customer: %s' % (move.picking_id.partner_id.name)))

                    
                    loc_tax_search = self.pool.get('delivery.location.tax').search(cr, uid, [('name', '=', from_loc.id),('to_state', '=', cust_loc.id)], limit=1)
                    invoice = self.pool.get('account.invoice').browse(cr, uid,res)
                    inv_line = invoice.invoice_line
                    for inv in inv_line:
                        if loc_tax_search:
                            categ = inv.product_id.categ_id.id
                            categ_tax_search = self.pool.get('tax.category').search(cr, uid, [('tax_id', 'in', loc_tax_search),('name', '=', categ)], limit=1)
                            if categ_tax_search:
                                tax = self.pool.get('tax.category').browse(cr, uid,categ_tax_search).account_tax
                            	if tax:
                                	inv.write({'invoice_line_tax_id': [(4, [tax.id])]})				
            return res

    def _invoice_create_line_new(self, cr, uid, moves, journal_id, inv_type='out_invoice', context=None):
        res = super(stock_picking_invoice,self)._invoice_create_line_new(cr, uid, moves, journal_id, inv_type, context=context)    

        for mv in moves:
            for m1 in mv :
                move = mv[m1]
                picking_type = move.picking_id.picking_type_id
                if picking_type.id == 1 :
                    location = move.location_dest_id
                    complete_name = location.complete_name
                elif picking_type.id == 2 :
                    location = move.location_id
                    complete_name = location.complete_name
                owner = location.partner_id

                if picking_type.id == 2 or picking_type.id == 1 : 
                    if not owner :
                        raise osv.except_osv(_('Warning!'), _('Please define the Owner for the Stock location: %s' % (complete_name)))

                from_loc = location.partner_id.state_id
                if not from_loc:
                    raise osv.except_osv(_('Warning!'), _('Please define the State for the Partner: %s' % (owner.name)))

                cust_loc = move.picking_id.partner_id.state_id
                if not cust_loc:
                    raise osv.except_osv(_('Warning!'), _('Please define the State for the Customer: %s' % (move.picking_id.partner_id.name)))

                loc_tax_search = self.pool.get('delivery.location.tax').search(cr, uid, [('name', '=', from_loc.id),('to_state', '=', cust_loc.id)], limit=1)
                invoice = self.pool.get('account.invoice').browse(cr, uid,res)
                inv_line = invoice.invoice_line
                for inv in inv_line:
                    if loc_tax_search:
                        categ = inv.product_id.categ_id.id
                        categ_tax_search = self.pool.get('tax.category').search(cr, uid, [('tax_id', 'in', loc_tax_search),('name', '=', categ)], limit=1)
                        if categ_tax_search:
                            tax = self.pool.get('tax.category').browse(cr, uid,categ_tax_search).account_tax
                            if tax:
                                inv.write({'invoice_line_tax_id': [(4, [tax.id])]})				
        return res

    def _invoice_create_line_other(self, cr, uid, moves, journal_id, inv_type='out_invoice', context=None):
        res = super(stock_picking_invoice,self)._invoice_create_line_other(cr, uid, moves, journal_id, inv_type, context=context)    

        for move in moves:
#             for m1 in mv :
#                 move = mv[m1]
                picking_type = move.picking_id.picking_type_id


                if picking_type.id == 1 : 
                    location = move.location_dest_id
                    complete_name = location.complete_name
                    owner = location.partner_id
                    if not owner :
                        raise osv.except_osv(_('Warning!'), _('Please define the Owner for the Stock location: %s' % (complete_name)))

                    from_loc = location.partner_id.state_id
                    if not from_loc:
                        raise osv.except_osv(_('Warning!'), _('Please define the State for the Partner: %s' % (owner.name)))

                    cust_loc = move.picking_id.partner_id.state_id
                    if not cust_loc:
                        raise osv.except_osv(_('Warning!'), _('Please define the State for the Customer: %s' % (move.picking_id.partner_id.name)))

                    loc_tax_search = self.pool.get('delivery.location.tax').search(cr, uid, [('name', '=', from_loc.id),('to_state', '=', cust_loc.id)], limit=1)
                    invoice = self.pool.get('account.invoice').browse(cr, uid,res)
                    inv_line = invoice.invoice_line
                    for inv in inv_line:
                        if loc_tax_search:
                            categ = inv.product_id.categ_id.id
                            categ_tax_search = self.pool.get('tax.category').search(cr, uid, [('tax_id', 'in', loc_tax_search),('name', '=', categ)], limit=1)
                            if categ_tax_search:
                                tax = self.pool.get('tax.category').browse(cr, uid,categ_tax_search).account_tax_input
                                if tax:
                                    inv.write({'invoice_line_tax_id': [(4, [tax.id])]})                
        return res

class delivery_tax_location(osv.osv):
    _name = "delivery.location.tax"
    _description = "Delivery location tax"
    _order = "name"
    _columns = {
        'name': fields.many2one('res.country.state', 'Ship From',required=True),
        'to_state': fields.many2one('res.country.state', 'Ship To',required=True),
        'bill_to': fields.many2one('res.country.state', 'Bill To'),
        'tax_category': fields.one2many('tax.category', 'tax_id', 'Taxes To Apply'),
        'active': fields.boolean('Active'),
    }
    _defaults = {
        'active': True,
    }

class Delivery_tax_location_category(osv.osv):
    _name = "tax.category"
    _description = "Tax Category"
    _order = "name"

    def create(self, cr, uid, vals, context=None):
        if 'amount_per' in vals:
	    amount_per = vals['amount_per']
	    round_value = round(amount_per,2)
	    per = ((amount_per or 0.0) / 100.0)
	    tax_name = 'Tax @ ' +str(round_value)+ '%'
            account_tax = self.pool.get('account.tax').search(cr, uid, [('name', '=', tax_name),('type', '=', 'percent')])
	    if not account_tax:
            	self.pool.get('account.tax').create(cr, uid, {'name': tax_name,'type': 'percent','amount': per})		

        return super(Delivery_tax_location_category, self).create(cr, uid, vals, context)


    _columns = {
        'name': fields.many2one('product.category', 'Category',required=True),
        'tax_id': fields.many2one('delivery.location.tax', 'Delivery Tax',required=True),
        'account_tax': fields.many2one('account.tax', 'Output Tax',required=True),
        'account_tax_input': fields.many2one('account.tax', 'Input Tax',required=True),       
    }
