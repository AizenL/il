from openerp.osv import fields,osv
from openerp.tools.translate import _
from lxml import etree
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp import tools
from openerp import SUPERUSER_ID,api
from datetime import timedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
import openerp.addons.decimal_precision as dp
from openerp import workflow
from openerp.tools.float_utils import float_compare
from itertools import chain

import pdb

class product_pricelist_version(osv.osv):
    _inherit="product.pricelist.version"
    _columns={
            'customer_pricelist_id':fields.many2one('sandv.customer.pricelist'),
    }
class product_pricelist_item(osv.osv):
    _inherit="product.pricelist.item"
    _columns={
            'customer_code':fields.char('Customer Part No'),
    }
class sandv_customer_pricelist(osv.osv):
    
    _name = 'sandv.customer.pricelist'
    
    _columns = {
                
                'name' :fields.char("Name" , size=256),
                'pricelist':fields.many2one("product.pricelist","Pricelist"),
                'start_date':fields.date("Start Date",required=True),
                'end_date':fields.date("End Date",required=True),
                
                'item_list':fields.one2many("item.list","pricelist_id","Item List",copy=True,),
                
                
                }
    @api.one
    def update_pricelist(self):
        list_product_id=[]
        
        odoo_items_obj = self.env['product.pricelist.item']
        odoo_version_obj=self.env['product.pricelist.version']
        pricelist_name=self.pricelist
        sandv_version_id = self.id
        odoo_version_id = odoo_version_obj.search([('customer_pricelist_id','=',sandv_version_id)])
                
            
        date_start=self.start_date
        date_end=self.end_date
        version_name=self.name
        item_list=self.item_list
        
        
        if not odoo_version_id:
            
            new_version_id=odoo_version_obj.create({'name':version_name,'date_start':date_start,'date_end':date_end,'pricelist_id':pricelist_name.id,'customer_pricelist_id':self.id})
            for line in self.item_list:
                sale_price=line.sale_price
                il_no=line.product_id
                item=odoo_items_obj.create({'base':1, 'product_id':il_no.id,'name':version_name,'price_surcharge':sale_price,'price_discount':'-1','price_version_id':new_version_id.id,'customer_code':line.customer_code})
                list_product_id.append(item.id)
            new_version_id.write({'items_id':[(4,0,list_product_id)]})
        else:
            
                odoo_version_id.write({'name':version_name,'date_start':date_start,'date_end':date_end,'pricelist_id':pricelist_name.id,'customer_pricelist_id':self.id})
                
                for item_id in odoo_version_id.items_id.ids :
                    odoo_version_id.write({'items_id':[(3,item_id)]})

                for line in self.item_list:
                    sale_price=line.sale_price
                    il_no=line.product_id
                    item=odoo_items_obj.create({'base':1,'product_id':il_no.id,'name':version_name,'price_surcharge':sale_price,'price_discount':'-1','price_version_id':odoo_version_id.id,'customer_code':line.customer_code})
                    list_product_id.append(item.id)
                odoo_version_id.write({'items_id':[(4,0,list_product_id)]})

          

        return True

    
     
    
    
sandv_customer_pricelist()

class sandv_item_list(osv.osv):
    
    _name = 'item.list'
    
    
    
    def _compute_all_value(self, cr, uid, ids, field_name, arg, context=None):
       
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'net_price': 0.0,
                'cst_vat': 0.0,
                'il_landed_price': 0.0,
                'entry_tax':0.0,
                'final_il_landed_price':0.0,
                'sale_price':0.0
               
            }
	    param_obj = self.pool.get("ir.config_parameter")
	    cst_vat_percent1 = param_obj.get_param(cr, uid, "cst_vat")
	    entry_tax_percent1 = param_obj.get_param(cr, uid, "entry_tax")
            cst_vat_percent = float(cst_vat_percent1 or 0.00) 
            entry_tax_percent = float(entry_tax_percent1  or 0.00)

           
            mrp = order.mrp
            discount = order.discount/100
            cst_vat_percent = cst_vat_percent / 100
            cst_vat_selection=order.cst_vat_selection
            ed = order.ed
            margin = order.margin / 100
            entry_tax_percent = entry_tax_percent / 100
           
           
           
            res[order.id]['net_price'] = mrp - (mrp * discount)
           
            
           
            if cst_vat_selection == 'Yes':
               
                res[order.id]['il_landed_price'] = res[order.id]['net_price'] + (res[order.id]['net_price'] * cst_vat_percent )
		res[order.id]['entry_tax'] = res[order.id]['il_landed_price'] * entry_tax_percent
		res[order.id]['final_il_landed_price'] = res[order.id]['il_landed_price'] + res[order.id]['entry_tax']
		res[order.id]['cst_vat'] = res[order.id]['net_price'] * cst_vat_percent
               
            else:
               
                res[order.id]['il_landed_price'] = res[order.id]['net_price']
		res[order.id]['final_il_landed_price'] = res[order.id]['il_landed_price']
           
           
            
           
#             pdb.set_trace()
            
           
            res[order.id]['sale_price'] = res[order.id]['final_il_landed_price'] + (res[order.id]['final_il_landed_price'] * margin)
           
           
           

        return res

    _columns = {
                'pricelist_version':fields.many2one('product.pricelist.version'),
		'cst_vat_selection': fields.selection([('Yes', 'Yes'),('No', 'No'),],),
                'sequence' :fields.char("Sequence" , size=256),
                'product_id':fields.many2one("product.product","Product Name"),
                'il_part_no':fields.char("IL Part NO"),

                'product_brand':fields.many2one("product.brand","Brand"),
                'name':fields.char("Product Name" , size=256),
                
                'customer_code':fields.char("Customer Code" , size=256),
                'mrp':fields.float("MRP"),
                'discount':fields.float("Discount"),
                'ed':fields.boolean("ED",),
                'cst_vat_percent':fields.float("CST/VAT %"),
                'margin':fields.float("Margin %"),
                'entry_tax_percent':fields.float("Entry Tax %"),
                'no_cst_vat_percent':fields.float("CST/VAT %"),
                'no_entry_tax_percent':fields.float("Entry Tax %"),
                
                'net_price':fields.function(_compute_all_value,  string='Net Price (Inclusive of ED)',
                    store={
                        
                        'item.list':(lambda self, cr, uid, ids, c={}: ids, ['mrp','discount','cst_vat_selection'], 10),
                            
                    }, multi="item_list_val", track_visibility='always'),
                   
                
                
                'cst_vat':fields.function(_compute_all_value,  string='CST/VAT',
                    store={
                        
                        'item.list':(lambda self, cr, uid, ids, c={}: ids, ['net_price','cst_vat_percent','cst_vat_selection'], 10),
                            
                    }, multi="item_list_val", track_visibility='always'),
                
                
                
                
                'il_landed_price':fields.function(_compute_all_value,  string='IL Landed Price',
                    store={
                        
                        'item.list':(lambda self, cr, uid, ids, c={}: ids, ['cst_vat_selection','net_price','cst_vat_percent'], 10),
                            
                    }, multi="item_list_val", track_visibility='always'),
                
                
                
                'entry_tax':fields.function(_compute_all_value,  string='Entry Tax Amount',
                    store={
                        
                        'item.list':(lambda self, cr, uid, ids, c={}: ids, ['il_landed_price','entry_tax_percent','cst_vat_selection'], 10),
                            
                    }, multi="item_list_val", track_visibility='always'),
                
                
                
                
                'final_il_landed_price':fields.function(_compute_all_value,  string='Final IL Landed Price',
                    store={
                        
                        'item.list':(lambda self, cr, uid, ids, c={}: ids, ['cst_vat_selection','net_price','cst_vat_percent','il_landed_price','entry_tax_percent'], 10),
                            
                    }, multi="item_list_val", track_visibility='always'),
                
                
                
                
                'sale_price':fields.function(_compute_all_value,  string='Sale Price',
                    store={
                        
                        'item.list':(lambda self, cr, uid, ids, c={}: ids, ['final_il_landed_price','margin','cst_vat_selection'], 10),
                            
                    }, multi="item_list_val", track_visibility='always'),
                
                
                
                
                'pricelist_id':fields.many2one("sandv.customer.pricelist","Pricelist"),
                
                
                }
    _defaults = {
        "cst_vat_selection": "No",
        }


    def onchange_product_id(self,cr,uid,ids,product_id):
        
        v = {}
        v['name'] = ' '
        
        v['product_brand'] = False
        
        if product_id:
            product_obj = self.pool.get("product.product")
            product_brow = product_obj.browse(cr,1,product_id)
            
            prod_name = product_brow.name
            
            if product_brow.product_brand:
                prod_brand = product_brow.product_brand.id
		il_part_no=product_brow.default_code
                v['product_brand'] = prod_brand
		
		v['il_part_no'] = il_part_no
        
            v['name'] = prod_name

        
        
        return {'value':v}




    def onchange_item_list_value(self,cr,uid,ids,discount,cst_vat_percent,margin,cst_vat_selection,mrp,entry_tax_percent):
        
        v = {}
        res = {}
        if cst_vat_selection == 'Yes':
		param_obj = self.pool.get("ir.config_parameter")
		cst_vat_percent1 = param_obj.get_param(cr, uid, "cst_vat")
		entry_tax_percent1 = param_obj.get_param(cr, uid, "entry_tax")
        	cst_vat_percent = float(cst_vat_percent1 or 0.00) 
        	entry_tax_percent = float(entry_tax_percent1  or 0.00)
	    	res['cst_vat_percent'] = cst_vat_percent
		res['entry_tax_percent'] = entry_tax_percent  
      
        cst_vat_percent = cst_vat_percent / 100
        margin = margin / 100
        entry_tax_percent = entry_tax_percent / 100
        discount=discount/100
        #pdb.set_trace()
  
        
        
        res['net_price'] = mrp - (mrp * discount)
        
        
        
        if cst_vat_selection == 'Yes':
            
            res['il_landed_price'] = res['net_price'] + (res['net_price'] * cst_vat_percent )
	    res['entry_tax'] = res['il_landed_price'] * entry_tax_percent
	    res['final_il_landed_price'] = res['il_landed_price'] + res['entry_tax']
	    res['cst_vat'] = res['net_price'] * cst_vat_percent

            
        else:
            
            res['il_landed_price'] = res['net_price']
	    res['final_il_landed_price'] = res['il_landed_price']
        
        
        
        
#             pdb.set_trace()
        
        
        res['sale_price'] = res['final_il_landed_price'] + (res['final_il_landed_price'] * margin )

     
        
        
        
        return {'value':res}
    
    
sandv_item_list()

class product_pricelist(osv.osv):
    _inherit = "product.pricelist"

    def _price_rule_get_multi(self, cr, uid, pricelist, products_by_qty_by_partner, context=None):
        context = context or {}
        date = context.get('date') or time.strftime('%Y-%m-%d')
        date = date[0:10]

        products = map(lambda x: x[0], products_by_qty_by_partner)
        currency_obj = self.pool.get('res.currency')
        product_obj = self.pool.get('product.template')
        product_uom_obj = self.pool.get('product.uom')
        price_type_obj = self.pool.get('product.price.type')

        if not products:
            return {}

        version = False
        for v in pricelist.version_id:
            if ((v.date_start is False) or (v.date_start <= date)) and ((v.date_end is False) or (v.date_end >= date)):
                version = v
                break
        if not version:
            raise osv.except_osv(_('Warning!'), _("At least one pricelist has no active version !\nPlease create or activate one."))
        categ_ids = {}
        for p in products:
            categ = p.categ_id
            while categ:
                categ_ids[categ.id] = True
                categ = categ.parent_id
        categ_ids = categ_ids.keys()

        is_product_template = products[0]._name == "product.template"
        if is_product_template:
            prod_tmpl_ids = [tmpl.id for tmpl in products]
            # all variants of all products
            prod_ids = [p.id for p in
                        list(chain.from_iterable([t.product_variant_ids for t in products]))]
        else:
            prod_ids = [product.id for product in products]
            prod_tmpl_ids = [product.product_tmpl_id.id for product in products]

        # Load all rules
        cr.execute(
            'SELECT i.id '
            'FROM product_pricelist_item AS i '
            'WHERE (product_tmpl_id IS NULL OR product_tmpl_id = any(%s)) '
                'AND (product_id IS NULL OR (product_id = any(%s))) '
                'AND ((categ_id IS NULL) OR (categ_id = any(%s))) '
                'AND (price_version_id = %s) '
            'ORDER BY sequence, min_quantity desc',
            (prod_tmpl_ids, prod_ids, categ_ids, version.id))
        
        item_ids = [x[0] for x in cr.fetchall()]
        items = self.pool.get('product.pricelist.item').browse(cr, uid, item_ids, context=context)
        #context.update({"price_item":items})
        price_types = {}

        results = {}
        for product, qty, partner in products_by_qty_by_partner:
            results[product.id] = 0.0
            rule_id = False
            price = False

            # Final unit price is computed according to `qty` in the `qty_uom_id` UoM.
            # An intermediary unit price may be computed according to a different UoM, in
            # which case the price_uom_id contains that UoM.
            # The final price will be converted to match `qty_uom_id`.
            qty_uom_id = context.get('uom') or product.uom_id.id
            price_uom_id = product.uom_id.id
            qty_in_product_uom = qty
            if qty_uom_id != product.uom_id.id:
                try:
                    qty_in_product_uom = product_uom_obj._compute_qty(
                        cr, uid, context['uom'], qty, product.uom_id.id or product.uos_id.id)
                except except_orm:
                    # Ignored - incompatible UoM in context, use default product UoM
                    pass

            for rule in items:
                if rule.min_quantity and qty_in_product_uom < rule.min_quantity:
                    continue
                if is_product_template:
                    if rule.product_tmpl_id and product.id != rule.product_tmpl_id.id:
                        continue
                    if rule.product_id and not (product.product_variant_count == 1 and product.product_variant_ids[0].id == rule.product_id.id):
                        # product rule acceptable on template if has only one variant
                        continue
                else:
                    if rule.product_tmpl_id and product.product_tmpl_id.id != rule.product_tmpl_id.id:
                        continue
                    if rule.product_id and product.id != rule.product_id.id:
                        continue

                if rule.categ_id:
                    cat = product.categ_id
                    while cat:
                        if cat.id == rule.categ_id.id:
                            break
                        cat = cat.parent_id
                    if not cat:
                        continue

                if rule.base == -1:
                    if rule.base_pricelist_id:
                        price_tmp = self._price_get_multi(cr, uid,
                                rule.base_pricelist_id, [(product,
                                qty, partner)], context=context)[product.id]
                        ptype_src = rule.base_pricelist_id.currency_id.id
                        price_uom_id = qty_uom_id
                        price = currency_obj.compute(cr, uid,
                                ptype_src, pricelist.currency_id.id,
                                price_tmp, round=False,
                                context=context)
                elif rule.base == -2:
                    seller = False
                    for seller_id in product.seller_ids:
                        if (not partner) or (seller_id.name.id != partner):
                            continue
                        seller = seller_id
                    if not seller and product.seller_ids:
                        seller = product.seller_ids[0]
                    if seller:
                        qty_in_seller_uom = qty
                        seller_uom = seller.product_uom.id
                        if qty_uom_id != seller_uom:
                            qty_in_seller_uom = product_uom_obj._compute_qty(cr, uid, qty_uom_id, qty, to_uom_id=seller_uom)
                        price_uom_id = seller_uom
                        for line in seller.pricelist_ids:
                            if line.min_quantity <= qty_in_seller_uom:
                                price = line.price

                else:
                    if rule.base not in price_types:
                        price_types[rule.base] = price_type_obj.browse(cr, uid, int(rule.base))
                    price_type = price_types[rule.base]

                    # price_get returns the price in the context UoM, i.e. qty_uom_id
                    price_uom_id = qty_uom_id
                    price = currency_obj.compute(
                            cr, uid,
                            price_type.currency_id.id, pricelist.currency_id.id,
                            product_obj._price_get(cr, uid, [product], price_type.field, context=context)[product.id],
                            round=False, context=context)

                if price is not False:
                    price_limit = price
                    price = price * (1.0+(rule.price_discount or 0.0))
                    if rule.price_round:
                        price = tools.float_round(price, precision_rounding=rule.price_round)

                    convert_to_price_uom = (lambda price: product_uom_obj._compute_price(
                                                cr, uid, product.uom_id.id,
                                                price, price_uom_id))
                    if rule.price_surcharge:
                        price_surcharge = convert_to_price_uom(rule.price_surcharge)
                        price += price_surcharge

                    if rule.price_min_margin:
                        price_min_margin = convert_to_price_uom(rule.price_min_margin)
                        price = max(price, price_limit + price_min_margin)

                    if rule.price_max_margin:
                        price_max_margin = convert_to_price_uom(rule.price_max_margin)
                        price = min(price, price_limit + price_max_margin)

                    rule_id = rule.id
                break

            # Final price conversion to target UoM
            price = product_uom_obj._compute_price(cr, uid, price_uom_id, price, qty_uom_id)

            results[product.id] = (price, rule_id)
        return results

















