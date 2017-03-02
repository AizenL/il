from openerp.osv import fields,osv
from openerp.tools.translate import _
from lxml import etree
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp import tools
from openerp import SUPERUSER_ID
from datetime import timedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
import openerp.addons.decimal_precision as dp
from openerp import workflow
from openerp.tools.float_utils import float_compare


import pdb








class sandv_product_product(osv.osv): 
    _inherit = 'product.product'


    _columns={
              
                'out_of_stock_qty'  :  fields.boolean("Out of Qty"),
                
                }
    
    _defaults = {
                 
                 'out_of_stock_qty':False,
                 
                 }
    

sandv_product_product()

# planning view for products management----------------start



class sandv_stock_product_qty(osv.osv):
    _name = "sandv.stock.product.qty"
    _description = "View DO stock and Actual Stock Qty"
    _auto = False
    _log_access = False
    
    
    
    #code for checking quantity available on hand is zero or not
    def _actual_stock_qty_in_hand(self, cr, uid, ids, field_name, arg, context):
        res = {}
        product_obj=self.pool.get('product.product')
        stock_obj = self.pool.get('stock.move')
        
        stock_ids = stock_obj.search(cr,1,[('state','not in',['done','cancel']),('picking_id.picking_type_id','=',2)])
        stock_brow = stock_obj.browse(cr, uid, stock_ids, context=context)
        
#         pdb.set_trace()
        if ids:
            for i in self.browse(cr, uid, ids, context=context):
#             for i in stock_brow:
            #line = stock_obj.browse(cr, uid, int(i), context=context)
                line = i
                prod_id = line.product_id.id
                
                qty_on_hand = line.product_id.qty_available


                qty_to_deliver = line.tot_do_qty
                qty_on_hand = line.product_id.qty_available
    
                if qty_on_hand <= qty_to_deliver:
                    #pdb.set_trace()
                    product_obj.write(cr,uid,[prod_id],{'out_of_stock_qty':True})
                else:
                    product_obj.write(cr,uid,[prod_id],{'out_of_stock_qty':False})
                
                res[line.id] = qty_on_hand
                 
        ###pdb.set_trace()
        return res
     


    #code for checking quantity available on hand is out of stock or not
    def _zero_qty_available(self, cr, uid, ids, field_name, arg, context):
        res = {}
        
        #pdb.set_trace()
#         if not context:
#             context = {}
            
        product_obj=self.pool.get('product.product')
        for i in self.browse(cr, uid, ids, context=context):
            line = i
            qty_to_deliver = line.tot_do_qty
            qty_on_hand = line.product_id.qty_available

            if qty_on_hand <= qty_to_deliver:
                res[line.id] = True
            else:
                res[line.id] = False
             
        
        return res
     
    def _zero_qty_search(self, cr, uid, obj, name, args, context=None):
        res = []
        kk = []
        
        #pdb.set_trace()
        product_obj = self.pool.get('product.product')
        out_of_qty_product_ids = product_obj.search(cr,uid,[('out_of_stock_qty','=',True)])
        product_ids = product_obj.search(cr,uid,[('out_of_stock_qty','=',False)])
        
        if args[0][2] == True:
            return [('product_id', 'in', out_of_qty_product_ids)]
        else:
            return [('product_id', 'in', product_ids)]




    
    _columns = {
              
#               'stock_id':fields.many2one("stock.move","Stock", readonly=True),
              'product_id':fields.many2one('product.product', 'Product', readonly=True),
              'product_uom_qty':fields.float('Qty to Deliver', readonly=True),
              'prod_name':fields.char('Description', size=256, readonly=True),
              'date_expected':fields.date("Scheduled Date",readonly=True),
              'origin':fields.char('Source', size=256, readonly=True),
              
#               'qty_available':fields.float("Quantity in Stock",readonly=True),
             
              'picking_id':fields.many2one("stock.picking","Ref",readonly=True),
              
              'stock_qty':fields.function(_actual_stock_qty_in_hand, string='Qty in Stock', type = 'float', help=""),
            
              'tot_do_qty':fields.float("Total Qty"),
               
                'out_of_stock_qty':fields.function(_zero_qty_available,fnct_search=_zero_qty_search, string='Qty Out of Stock',type = 'boolean', help="If the product having 'Quantity on hand Qty Out of Stock' then True else False."),

               }   
    


#     def init(self, cr):
#         tools.sql.drop_view_if_exists(cr, 'sandv_stock_product_qty')
#         cr.execute("""create or replace view sandv_stock_product_qty as (
#         select ROW_NUMBER() OVER (ORDER BY i.id) AS id,
#         
#            i.product_id product_id,
#            i.name prod_name,
#            i.product_uom_qty product_uom_qty,
#            i.date_expected date_expected,
#            i.origin origin,
#            i.picking_id picking_id
#            
#            from stock_move i
#     
#            where picking_id in (select id from stock_picking where state not in ('done','cancel') and picking_type_id = 2)
#        
# 
# 
#         )""")        


    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, 'sandv_stock_product_qty')
        cr.execute("""create or replace view sandv_stock_product_qty as (
        select ROW_NUMBER() OVER (ORDER BY i.id) AS id,
         
           i.product_id product_id,
           i.name prod_name,
           i.product_uom_qty product_uom_qty,
           i.date_expected date_expected,
           i.origin origin,
            
           (select sum(product_uom_qty) from stock_move where product_id = i.product_id and picking_id = i.picking_id) tot_do_qty,
            
           i.picking_id picking_id
            
           from stock_move i
     
           where picking_id in (select id from stock_picking where state not in ('done','cancel') and picking_type_id = 2)
        
 
 
        )""")        



#     def init(self, cr):
#         tools.sql.drop_view_if_exists(cr, 'sandv_stock_product_qty')
#         cr.execute("""create or replace view sandv_stock_product_qty as (
#         
#         select ROW_NUMBER() OVER (ORDER BY j.id) as id,
#             
#            j.product_id product_id,
#            j.prod_name prod_name,
#            j.product_uom_qty product_uom_qty,
#            j.date_expected date_expected,
#            j.origin origin,
#            j.tot_do_qty tot_do_qty,
#         
#            j.picking_id picking_id
#            
#         from 
#         (
#         select ROW_NUMBER() OVER (ORDER BY i.id) AS id,
#         
#            i.product_id product_id,
#            i.name prod_name,
#            i.product_uom_qty product_uom_qty,
#            i.date_expected date_expected,
#            i.origin origin,
#            
#            
#            (select sum(product_uom_qty) from stock_move where product_id = i.product_id and state not in ('done','cancel')) tot_do_qty,
#            
#            i.picking_id picking_id
#            
#            from stock_move i
#     
#            where picking_id in (select id from stock_picking where state not in ('done','cancel') and picking_type_id = 2)
#            
#         ) j
#         
#         where j.tot_do_qty <= j.stock_qty
#        
# 
# 
#         )""")        


# (select id from stock_picking where state not in ('done','cancel') and picking_type_id = 2)
        

sandv_stock_product_qty()










