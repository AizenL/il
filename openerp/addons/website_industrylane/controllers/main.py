# -*- coding: utf-8 -*-
import logging
import werkzeug
import pdb
from openerp import SUPERUSER_ID
from openerp import http
from openerp import tools
from openerp.http import request
from openerp.tools.translate import _
from openerp.addons.website.models.website import slug
from openerp.addons.web.controllers.main import login_redirect
from openerp.addons.delivery.sale import sale_order
from openerp.addons.lunch.report import order
from datetime import date
import datetime
from dateutil.relativedelta import relativedelta
import json
from time import sleep
from time import strptime
import time
from openerp.addons.test_impex.tests.test_import import values

PPG = 100 # Products Per Page
PPR = 3  # Products Per Row

_logger = logging.getLogger(__name__)

class table_compute(object):
    def __init__(self):
        self.table = {}

    def _check_place(self, posx, posy, sizex, sizey):
        res = True
        for y in range(sizey):
            for x in range(sizex):
                if posx+x>=PPR:
                    res = False
                    break
                row = self.table.setdefault(posy+y, {})
                if row.setdefault(posx+x) is not None:
                    res = False
                    break
            for x in range(PPR):
                self.table[posy+y].setdefault(x, None)
        return res


    
    def process(self, products,PPG,PPR):
        # Compute products positions on the grid
        minpos = 0
        index = 0
        maxy = 0
       
        for p in products:
            x = min(max(p.website_size_x, 1), PPR)
            y = min(max(p.website_size_y, 1), PPR)
            if index>=PPG:
                x = y = 1

            pos = minpos
            while not self._check_place(pos%PPR, pos/PPR, x, y):
                pos += 1
            # if 21st products (index 20) and the last line is full (PPR products in it), break
            # (pos + 1.0) / PPR is the line where the product would be inserted
            # maxy is the number of existing lines
            # + 1.0 is because pos begins at 0, thus pos 20 is actually the 21st block
            # and to force python to not round the division operation
            if index >= PPG and ((pos + 1.0) / PPR) > maxy:
                break

            if x==1 and y==1:   # simple heuristic for CPU optimization
                minpos = pos/PPR

            for y2 in range(y):
                for x2 in range(x):
                    self.table[(pos/PPR)+y2][(pos%PPR)+x2] = False
            self.table[pos/PPR][pos%PPR] = {
                'product': p, 'x':x, 'y': y,
                'class': " ".join(map(lambda x: x.html_class or '', p.website_style_ids))
            }
            if index<=PPG:
                maxy=max(maxy,y+(pos/PPR))
            index += 1

        # Format table according to HTML needs
        rows = self.table.items()
        rows.sort()
        rows = map(lambda x: x[1], rows)
        for col in range(len(rows)):
            cols = rows[col].items()
            cols.sort()
            x += len(cols)
            rows[col] = [c for c in map(lambda x: x[1], cols) if c != False]

       
        return rows
    
    
    def cat_process(self, public_categs,ppg,ppr):
        # Compute products positions on the grid
        minpos = 0
        index = 0
        maxy = 0
       
        for p in public_categs:
            x = min(max(1, 1), PPR)
            y = min(max(1, 1), PPR)
            if index>=PPG:
                x = y = 1

            pos = minpos
            while not self._check_place(pos%PPR, pos/PPR, x, y):
                pos += 1
            # if 21st products (index 20) and the last line is full (PPR products in it), break
            # (pos + 1.0) / PPR is the line where the product would be inserted
            # maxy is the number of existing lines
            # + 1.0 is because pos begins at 0, thus pos 20 is actually the 21st block
            # and to force python to not round the division operation
            if index >= PPG and ((pos + 1.0) / PPR) > maxy:
                break

            if x==1 and y==1:   # simple heuristic for CPU optimization
                minpos = pos/PPR

            for y2 in range(y):
                for x2 in range(x):
                    self.table[(pos/PPR)+y2][(pos%PPR)+x2] = False
            self.table[pos/PPR][pos%PPR] = {
                'product': p, 'x':x, 'y': y,
                'class': " "
            }
            if index<=PPG:
                maxy=max(maxy,y+(pos/PPR))
            index += 1

        # Format table according to HTML needs
        rows = self.table.items()
        rows.sort()
        rows = map(lambda x: x[1], rows)
        for col in range(len(rows)):
            cols = rows[col].items()
            cols.sort()
            x += len(cols)
            rows[col] = [c for c in map(lambda x: x[1], cols) if c != False]

       
        return rows    

        # TODO keep with input type hidden


class QueryURL(object):
    def __init__(self, path='', **args):
        self.path = path
        self.args = args

    def __call__(self, path=None, **kw):
        #pdb.set_trace()
        if not path:
            path = self.path
        for k,v in self.args.items():
            kw.setdefault(k,v)
        l = []
        for k,v in kw.items():
            if v:
                if isinstance(v, list) or isinstance(v, set):
                    l.append(werkzeug.url_encode([(k,i) for i in v]))
                else:
                    l.append(werkzeug.url_encode([(k,v)]))
        if l:
            path += '?' + '&'.join(l)
        return path


def get_pricelist():
    cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
    sale_order = context.get('sale_order')
    if sale_order:
        pricelist = sale_order.pricelist_id
    else:
        partner = pool['res.users'].browse(cr, SUPERUSER_ID, uid, context=context).partner_id
        pricelist = partner.property_product_pricelist
    if not pricelist:
        _logger.error('Fail to find pricelist for partner "%s" (id %s)', partner.name, partner.id)
    return pricelist

class website_sale(http.Controller):

    def get_pricelist(self):
        return get_pricelist()

    def get_attribute_value_ids(self, product):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        currency_obj = pool['res.currency']
        attribute_value_ids = []
        visible_attrs = set(l.attribute_id.id
                                for l in product.attribute_line_ids
                                    if len(l.value_ids) > 1)
        if request.website.pricelist_id.id != context['pricelist']:
            website_currency_id = request.website.currency_id.id
            currency_id = self.get_pricelist().currency_id.id
            for p in product.product_variant_ids:
                price = currency_obj.compute(cr, uid, website_currency_id, currency_id, p.lst_price)
                attribute_value_ids.append([p.id, [v.id for v in p.attribute_value_ids if v.attribute_id.id in visible_attrs], p.price, price])
        else:
            attribute_value_ids = [[p.id, [v.id for v in p.attribute_value_ids if v.attribute_id.id in visible_attrs], p.price, p.lst_price]
                for p in product.product_variant_ids]

        return attribute_value_ids

    def _get_search_order(self, post):
        # OrderBy will be parsed in orm and so no direct sql injection
        return 'website_published desc,%s' % post.get('order', 'website_sequence desc')

    def _get_search_domain(self, search, category, attrib_values):
        domain = request.website.sale_product_domain()
      
        if search:
            for srch in search.split(" "):
#                 domain += [
#                     '|', '|', '|', ('name', 'ilike', srch), ('description', 'ilike', srch),
#                     ('description_sale', 'ilike', srch), ('product_variant_ids.default_code', 'ilike', srch)]
#  
                domain += [
                    '|', ('name', 'ilike', srch),('product_variant_ids.default_code', 'ilike', srch)]
                
        if category:
            domain += [('public_categ_ids', 'child_of', int(category))]

        if attrib_values:
            attrib = None
            ids = []
            for value in attrib_values:
                if not attrib:
                    attrib = value[0]
                    ids.append(value[1])
                elif value[0] == attrib:
                    ids.append(value[1])
                else:
                    domain += [('sandv_attribute_line_ids.value_ids', 'in', ids)]
                    attrib = value[0]
                    ids = [value[1]]
            if attrib:
                domain += [('sandv_attribute_line_ids.value_ids', 'in', ids)]

        return domain
    
    def _get_search_brand(self,brands, attrib_values):
        domain = request.website.sale_product_domain()
                     
        if brands:
            domain += [('product_brand', 'in', brands)]
                                 
        if attrib_values:
            attrib = None
            ids = []
            for value in attrib_values:
                if not attrib:
                    attrib = value[0]
                    ids.append(value[1])
                elif value[0] == attrib:
                    ids.append(value[1])
                else:
                    domain += [('sandv_attribute_line_ids.value_ids', 'in', ids)]
                    attrib = value[0]
                    ids = [value[1]]
            if attrib:
                domain += [('sandv_attribute_line_ids.value_ids', 'in', ids)]

        return domain    


    def ChangeGlobalPPRCatProcess(self,public_categs,ppg,ppr):
        global PPR
        PPR = ppr

        return table_compute().cat_process(public_categs,PPG,PPR)      

    def ChangeGlobalPPRProcess(self,products,ppg,ppr):
        global PPR
        PPR = ppr
       
        return table_compute().process(products,ppg,PPR)  
    
    
    def getQuotation(self, invoice_number):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
         
    
            #sale_quotation_obj = self.env['sale.quotation']
        sale_order_obj = request.registry['sale.order']
        sale_order_ids = sale_order_obj.search(cr, SUPERUSER_ID, [('name', '=', invoice_number)], context=context)            
        sale_orders = sale_order_obj.browse(cr, SUPERUSER_ID, sale_order_ids, context=context)
        
        sale_quotation_obj = request.registry['sale.quotation']
        sale_quotation_ids = sale_quotation_obj.search(cr, SUPERUSER_ID, [('id', '=', sale_orders.quotation_id.id)], context=context)
        sale_quotations = sale_quotation_obj.browse(cr, SUPERUSER_ID, sale_quotation_ids, context=context) 
             
        
        return sale_quotations.name
    
    def getStatus(self, quotation_number,product_id):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
          
        
        values = 0.0
        
        #cr.execute('select sq.name as quotation_number,so.create_date as so_date,sq.state as sq_state,so.state as so_state, sp.state as sp_state,sp.invoice_state as sp_invoice_state from sale_quotation as sq LEFT JOIN sale_order so on sq.id = so.quotation_id LEFT JOIN stock_picking sp on sp.origin = so.name WHERE sq.name = %s ', (quotation_number,))
        cr.execute('select  SM.product_uom_qty as delivered_qty from sale_quotation SQ INNER JOIN sale_order SO on SQ.id = SO.quotation_id INNER JOIN stock_move SM on SM.origin = SO.name WHERE SQ.name = %s AND SM.product_id = %s AND SM.invoice_state=%s', (str(quotation_number),product_id,'invoiced'))
        getQty = cr.fetchall();
        
        if getQty:                     
            values = getQty[0][0]
              
        return values        
        
    @http.route([
       '/shop/order_history',
    ], type='http', auth="user", website=True)
    def order_history(self,category=None, search='', **post):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry

        partner =  pool['res.users'].browse(cr, SUPERUSER_ID, uid, context=context).partner_id
        sale_order_obj = request.registry['sale.order']
        sale_order_ids = sale_order_obj.search(cr, SUPERUSER_ID, [('partner_id', '=', partner.id)], context=context)
        sale_orders = sale_order_obj.browse(cr, SUPERUSER_ID, sale_order_ids, context=context)
        
        sale_quotation_obj = request.registry['sale.quotation']
        sale_quotation_ids = sale_quotation_obj.search(cr, SUPERUSER_ID, [('partner_id', '=', partner.id)], context=context)
        sale_quotations = sale_quotation_obj.browse(cr, SUPERUSER_ID, sale_quotation_ids, context=context)
                
        keep = QueryURL('/shop', category=category and int(category), search=search, attrib="")
        
        values = {
            'sale_orders':sale_orders,
            'sale_quotations':sale_quotations,
            'keep': keep,
            'getQuotation':self.getQuotation,
        }

        return request.website.render("website_industrylane.order_history", values)
     
    
    @http.route([
       '/shop/spend_management',
    ], type='http', auth="user", website=True)
    def spend_management(self,category=None, search='', **post):
        cr, uid, context,  registry = request.cr, request.uid, request.context, request.registry
        
        orm_user = registry.get('res.users')
        partner = orm_user.browse(cr, SUPERUSER_ID, request.uid, context).partner_id
#         today = date.today()
#         lmld = date(today.year, today.month, 1) - relativedelta(days=1)  
#         lmld_format = lmld.strftime('%Y-%m-%d')
        #pdb.set_trace()
        #where so.partner_id = %s GROUP BY pp.id HAVING count(*) > 1', (partner.id,))
        #cr.execute('select pp.product_tmpl_id from sale_order_line sol INNER JOIN sale_order so on so.id = sol.order_id INNER JOIN product_product pp on pp.id = sol.product_id where so.partner_id = %s GROUP BY pp.id HAVING count(*) > 1', (partner.id,))

#         cr.execute("select ai.partner_id,sum(ai.amount_total) as invoice_total,to_char(ai.date_invoice, 'MONTH') as invoice_month from account_invoice ai INNER JOIN account_invoice_line ail on ai.id = ail.invoice_id where ail.partner_id in %s and ai.date_invoice >= date_trunc('month', now()) - interval '1 day' - INTERVAL '3 months' GROUP BY invoice_month,ai.partner_id", (partner.id,))
#         spend_management_obj = cr.fetchall();
        
        #spend_management = spend_management_obj.browse(cr, uid, spend_management_ids, context=context)        
        
       
        return request.website.render("website_industrylane.spend_management")
    
    @http.route(['/shop/get_sm_data'], type='json', auth="public", website=True)
    def get_spend_management_data(self,category=None, search='', **post):
        cr, uid, context,  registry = request.cr, request.uid, request.context, request.registry
        
        orm_user = registry.get('res.users')
        partner = orm_user.browse(cr, SUPERUSER_ID, request.uid, context).partner_id#       
        #pdb.set_trace()
        cr.execute("select ai.partner_id,sum(ail.price_subtotal) as invoice_total,to_char(ai.date_invoice, 'MONTH-YYYY') as invoice_month from account_invoice ai INNER JOIN account_invoice_line ail on ai.id = ail.invoice_id where ail.partner_id = %s and ai.state in %s and ai.date_invoice >= date_trunc('month', now()) - interval '1 day' - INTERVAL '3 months' GROUP BY invoice_month,ai.partner_id ", (partner.id,('open','paid',)))
        spend_management_obj = cr.fetchall();
        data = spend_management_obj
       
        
        alist=[]
        for i,e in enumerate(data):
            adict = {'name':e[2],'y':e[1],'drilldown':e[2]}
            alist.append(adict)
        #pdb.set_trace()             
        return alist
    
    @http.route(['/shop/trand_analysis'], type='json', auth="public", website=True)
    def trand_analysis(self,category=None, search='', **post):
        cr, uid, context,  registry = request.cr, request.uid, request.context, request.registry
        
        orm_user = registry.get('res.users')
        partner = orm_user.browse(cr, SUPERUSER_ID, request.uid, context).partner_id#       
        #pdb.set_trace()
        cr.execute("select pca.name,sum(ail.price_subtotal) as invoice_total from account_invoice ai INNER JOIN account_invoice_line ail on ai.id = ail.invoice_id INNER JOIN product_product pp on pp.id = ail.product_id INNER JOIN product_template pt on pt.id = pp.product_tmpl_id INNER JOIN product_category pc on pc.id = pt.categ_id INNER JOIN product_category pca on pca.id = pc.parent_id where ail.partner_id = %s  and ai.state in %s GROUP BY pca.name", (partner.id,('open','paid',)))
        spend_management_obj = cr.fetchall();
        data = spend_management_obj
       
        
        alist=[]
        for i,e in enumerate(data):
            adict = {'name':e[0],'y':e[1],'drilldown':e[0]}
            alist.append(adict)
        #pdb.set_trace()             
        return alist    
    
    @http.route(['/shop/trand_analysis_line'], type='json', auth="public", website=True)
    def trand_analysis_line(self,category=None, name='', **post):
        cr, uid, context,  registry = request.cr, request.uid, request.context, request.registry
        
        category_obj = registry.get('product.category')
        category_ids = category_obj.search(cr, uid, [('name', '=', name)], context=context)
        
        orm_user = registry.get('res.users')
        partner = orm_user.browse(cr, SUPERUSER_ID, request.uid, context).partner_id#       
        #pdb.set_trace()
        #cr.execute("select to_char(ai.date_invoice, 'MONTH') as invoice_month,sum(ail.price_subtotal) as invoice_total from account_invoice ai INNER JOIN account_invoice_line ail on ai.id = ail.invoice_id INNER JOIN product_product pp on pp.id = ail.product_id INNER JOIN product_template pt on pt.id = pp.product_tmpl_id INNER JOIN product_category pc on pc.id = pt.categ_id INNER JOIN product_category pca on pca.id = pc.parent_id where ail.partner_id = %s and pca.id = %s and ai.state in %s GROUP BY pca.name,invoice_month,ai.date_invoice ORDER BY ai.date_invoice" , (partner.id,category_ids[0],('open','paid',)))
        cr.execute("select to_char(date_trunc('month',ai.date_invoice),'Month-YYYY') as invoice_month,sum(ail.price_subtotal) as invoice_total from account_invoice ai INNER JOIN account_invoice_line ail on ai.id = ail.invoice_id INNER JOIN product_product pp on pp.id = ail.product_id INNER JOIN product_template pt on pt.id = pp.product_tmpl_id INNER JOIN product_category pc on pc.id = pt.categ_id INNER JOIN product_category pca on pca.id = pc.parent_id where ail.partner_id = %s and pca.id = %s and ai.state in %s GROUP BY date_trunc('month',ai.date_invoice) ORDER BY MIN(ai.date_invoice)" , (partner.id,category_ids[0],('open','paid',)))
        spend_management_obj = cr.fetchall();
        data_list = [list(elem) for elem in spend_management_obj]
        series = {'name':'Amount', 'type': 'line', 'id':name,'data':data_list}
        #pdb.set_trace()
#         series = {
# {
#                         name: 'Widget A',
#                         type: 'line',
#                         id: 'CUTTING TOOL',
#                         data: [
#                             {name: 'Qtr 1', y: 5},
#                             {name: 'Qtr 2', y: 25},
#                             {name: 'Qtr 3', y: 25},
#                             {name: 'Qtr 4', y: 20}
#                         ]
#                  }
#                         }          
        return series 
    
    def get_last_day_of_the_month(self,y, m):
        '''
        Returns an integer representing the last day of the month, given
        a year and a month.
        '''
     
        # Algorithm: Take the first day of the next month, then count back
        # ward one day, that will be the last day of a given month. The 
        # advantage of this algorithm is we don't have to determine the 
        # leap year.
        m = strptime(m,'%B').tm_mon
        
        m += 1
        if m == 13:
            m = 1
            y += 1
     
        first_of_next_month = datetime.date(y, m, 1)
        last_of_this_month = first_of_next_month + datetime.timedelta(-1)
        return last_of_this_month.day    

    @http.route(['/shop/get_smdrilldown_data'], type='json', auth="public", website=True)
    def get_spend_management_drilldown_data(self,category=None, name='', **post):
        cr, uid, context,  registry = request.cr, request.uid, request.context, request.registry
        #pdb.set_trace()
        month = name.split('-')[0].strip()
        m = strptime(month,'%B').tm_mon
        year = name.split('-')[1].strip()
        last_date = self.get_last_day_of_the_month(int(year),month)
        
        orm_user = registry.get('res.users')
        partner = orm_user.browse(cr, SUPERUSER_ID, request.uid, context).partner_id#       
        
        start_date = year+'-'+str(m)+'-'+'1'
        end_date = year+'-'+str(m)+'-'+str(last_date)
        #pdb.set_trace()   
        cr.execute("select pca.name,sum(ail.price_subtotal) as invoice_total from account_invoice ai INNER JOIN account_invoice_line ail on ai.id = ail.invoice_id INNER JOIN product_product pp on pp.id = ail.product_id INNER JOIN product_template pt on pt.id = pp.product_tmpl_id INNER JOIN product_category pc on pc.id = pt.categ_id INNER JOIN product_category pca on pca.id = pc.parent_id where ail.partner_id = %s and ai.date_invoice >=%s and ai.date_invoice <=%s and ai.state in %s GROUP BY pca.name", (partner.id,start_date,end_date,('open','paid',)))
        spend_management_obj = cr.fetchall()
        
        data_list = [list(elem) for elem in spend_management_obj]
        series = {'name':'Amount', 'id':name,'data':data_list}
        #pdb.set_trace()
#         series = {
#                'name': 'Cars',
#                 'data': [
#                         ['Toyota', 1],
#                       ['Volkswagen', 2],
#                     ['Opel', 5]
#                             ]
#                         }          
        return series
    
     
     
    """    TO ADD PRODUCT TO MY CART FROM BASKET """
    @http.route(['/shop/move_product_to_cart/product_id'], type='http', auth="public", website=True)
    def cart_update_basket(self, product_id, add_qty=1, set_qty=0, **kw):
        # HANDLING INVALID "add_qty" VALUES
        
        data ={}
        try:
            add_qty = float(add_qty)
        except ValueError:
            #this.do_warn(_t("The following fields are invalid:"), warnings.join(''));
            return None
        
        
        if add_qty <= 0.0:
            return None
        cr, uid, context = request.cr, request.uid, request.context
        sale_order_line = request.website.sale_get_order(force_create=1)._cart_update(product_id=int(product_id), add_qty=add_qty, set_qty=float(set_qty))
        data["message"] = "Added Successfully"
         
        return  json.dumps(data) 
         
    @http.route([
       '/shop/view_order_history', 
    ], type='http', auth="public", website=True)
    def order_history_view(self,soid,category=None, search='', **post):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        

        split_so  = soid.split('-')[0]
        get_first_two_value = split_so[0:2]
        get_soid = soid.split('-')[-1]
        sale_order_id = int(get_soid)         
        order = request.registry['sale.quotation'].browse(cr, SUPERUSER_ID, sale_order_id, context=context)
        keep = QueryURL('/shop', category=category and int(category), search=search, attrib="")        

        values = {
                'order':order,
                'keep': keep,
                'getStatus': self.getStatus,
                'getQuotation':self.getQuotation,
                'getStatus':self.getStatus,
            }         
        return request.website.render("website_industrylane.view_order_history", values) 
    
    
    
       
    @http.route(['/shop/cart/shopping_cart_remove_order_line'], type='http', auth="public", website=True)
    def shopping_cart_remove_order_line(self, line_id, display=True, **post):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        line_id = int(line_id)        
        
        sol = pool.get('sale.quotation.order.line')     
        sol.unlink(cr, SUPERUSER_ID, line_id, context=context)        
        
        if request.httprequest.headers and request.httprequest.headers.get('Referer'):
            return request.redirect(str(request.httprequest.headers.get('Referer')))
        return request.redirect('/shop#portfolio')
        
    
    @http.route([
       '/shop/reorder', 
    ], type='http', auth="public", website=True)
    def reorder(self, soid, **post):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry

        get_soid = soid.split('-')[-1]
        sale_order_id = int(get_soid)      
       
        order = request.registry['sale.quotation'].browse(cr, SUPERUSER_ID, sale_order_id, context=context)     
        
        for so in order:
            order_lines = so.order_line
            for order_line in order_lines:
                
                product_id = order_line.product_id.id
                add_qty = order_line.product_uom_qty
                set_qty = 0
                request.website.sale_get_order(force_create=1)._cart_update(product_id=int(product_id), add_qty=float(add_qty), set_qty=float(set_qty))
                
                

        return request.redirect("/shop/cart")
    
    @http.route([
       '/shop/cancel_order', 
    ], type='http', auth="public", website=True)
    def cancel_order(self, soid, **post):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry

        split_so  = soid.split('-')[0]
        get_first_two_value = split_so[0:2]

        get_soid = soid.split('-')[-1]
        sale_order_id = int(get_soid)  
            
        if get_first_two_value == 'qt':
            values = {
                    'state': 'cancel',  
                    'quotation_state': 'cancel'                     
                }
            request.registry['sale.quotation'].write(cr, SUPERUSER_ID, [sale_order_id], values, context=context)
        else:
            
            values = {
                    'state': 'cancel'                  
                }
            request.registry['sale.order'].write(cr, SUPERUSER_ID, [sale_order_id], values, context=context)

            #Senthil End#        
        return request.redirect("/shop/order_history")
    
    @http.route([
       '/shop_now',
       '/shop-now/page/<int:page>',
       # '/shop/category/<model("product.public.category"):category>',
       # '/shop/category/<model("product.public.category"):category>/page/<int:page>'
    ], type='http', auth="public", website=True)
    def shop_now(self, page=0, category=None, search='', **post):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry

        attrib_list = request.httprequest.args.getlist('attrib')
        attrib_values = [map(int, v.split("-")) for v in attrib_list if v]
        attrib_set = set([v[1] for v in attrib_values])

        domain = self._get_search_domain(search, category, attrib_values)

        keep = QueryURL('/shop', category=category and int(category), search=search, attrib=attrib_list)
        
        if not context.get('pricelist'):
            pricelist = self.get_pricelist()
            context['pricelist'] = int(pricelist)
        else:
            pricelist = pool.get('product.pricelist').browse(cr, uid, context['pricelist'], context)

        product_obj = pool.get('product.template')

        url = "/shop"
        product_count = product_obj.search_count(cr, SUPERUSER_ID, domain, context=context)
        if search:
            post["search"] = search

        if category:
            category = pool['product.public.category'].browse(cr, uid, int(category), context=context)
            url = "/shop/category/%s" % slug(category)
        if attrib_list:
            post['attrib'] = attrib_list
        pager = request.website.pager(url=url, total=product_count, page=page, step=PPG, scope=7, url_args=post)
        product_ids = product_obj.search(cr, uid, domain, limit=PPG, offset=pager['offset'], order=self._get_search_order(post), context=context)
        products = product_obj.browse(cr, uid, product_ids, context=context)


        style_obj = pool['product.style']
        style_ids = style_obj.search(cr, uid, [], context=context)
        styles = style_obj.browse(cr, uid, style_ids, context=context)
        

        category_obj = pool['product.public.category']
        category_ids = category_obj.search(cr, uid, [('parent_id', '=', False)], context=context)
        categs = category_obj.browse(cr, uid, category_ids, context=context)


        cr.execute("select distinct C.parent_id from product_template as A INNER JOIN product_public_category_product_template_rel as B on A.id = B.product_template_id INNER JOIN product_public_category C on B.product_public_category_id = C.id WHERE C.parent_id is not null order by C.parent_id ASC")
        public_category_obj = cr.fetchall();
        public_category_ids = [a[0] for a in public_category_obj]
        public_categs = category_obj.browse(cr, uid, public_category_ids, context=context)
        
        
        
        attributes_obj = request.registry['product.attribute']
        attributes_ids = attributes_obj.search(cr, uid, [], context=context)
        attributes = attributes_obj.browse(cr, uid, attributes_ids, context=context)


        from_currency = pool.get('product.price.type')._get_field_currency(cr, uid, 'list_price', context)
        to_currency = pricelist.currency_id
        compute_currency = lambda price: pool['res.currency']._compute(cr, uid, from_currency, to_currency, price, context=context)

        values = {
            'search': search,
            'category': category,
            'attrib_values': attrib_values,
            'attrib_set': attrib_set,
            'pager': pager,
            'pricelist': pricelist,
            'products': products,
            #'products_categories':table_compute().cat_process(public_categs),   
            #'bins': table_compute().process(products),
            'products_categories':self.ChangeGlobalPPRCatProcess(public_categs,25,4),
            'bins': self.ChangeGlobalPPRProcess(products,20,3),            
            'rows': PPR,
            'styles': styles,
            'categories': categs,
            'attributes': attributes,
            'compute_currency': compute_currency,
            'keep': keep,
            'style_in_product': lambda style, product: style.id in [s.id for s in product.website_style_ids],
            'attrib_encode': lambda attribs: werkzeug.url_encode([('attrib',i) for i in attribs]),
        }
        
        return request.website.render("website_industrylane.shopnow", values)
        
    @http.route([
       '/shop',
       '/shop/status_msg/<int:status_msg>',
       '/shop/page/<int:page>',
       # '/shop/category/<model("product.public.category"):category>',
       # '/shop/category/<model("product.public.category"):category>/page/<int:page>'
    ], type='http', auth="public", website=True)
    def home_shop(self, page=0,status_msg=0 ,category=None, search='', **post):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry

        attrib_list = request.httprequest.args.getlist('attrib')
        attrib_values = [map(int, v.split("-")) for v in attrib_list if v]
        attrib_set = set([v[1] for v in attrib_values])

        domain = self._get_search_domain(search, category, attrib_values)

        keep = QueryURL('/shop', category=category and int(category), search=search, attrib=attrib_list)
        
        
        if status_msg == 1:
            msg = "sucess"
        else:
            msg = "fail"
            
        if not context.get('pricelist'):
            pricelist = self.get_pricelist()
            context['pricelist'] = int(pricelist)
        else:
            pricelist = pool.get('product.pricelist').browse(cr, uid, context['pricelist'], context)

        product_obj = pool.get('product.template')

        url = "/shop"
        product_count = product_obj.search_count(cr, SUPERUSER_ID, domain, context=context)
        if search:
            post["search"] = search
        if category:
            category = pool['product.public.category'].browse(cr, uid, int(category), context=context)
            url = "/shop/category/%s" % slug(category)
        if attrib_list:
            post['attrib'] = attrib_list
        pager = request.website.pager(url=url, total=product_count, page=page, step=PPG, scope=7, url_args=post)
        product_ids = product_obj.search(cr, uid, domain, limit=PPG, offset=pager['offset'], order=self._get_search_order(post), context=context)
        products = product_obj.browse(cr, uid, product_ids, context=context)


        style_obj = pool['product.style']
        style_ids = style_obj.search(cr, uid, [], context=context)
        styles = style_obj.browse(cr, uid, style_ids, context=context)
        

        category_obj = pool['product.public.category']
        category_ids = category_obj.search(cr, uid, [('parent_id', '=', False)], context=context)
        categs = category_obj.browse(cr, uid, category_ids, context=context)


        cr.execute("select distinct C.parent_id from product_template as A INNER JOIN product_public_category_product_template_rel as B on A.id = B.product_template_id INNER JOIN product_public_category C on B.product_public_category_id = C.id WHERE C.parent_id is not null order by C.parent_id ASC")
        public_category_obj = cr.fetchall();
        public_category_ids = [a[0] for a in public_category_obj]
        public_categs = category_obj.browse(cr, uid, public_category_ids, context=context)
        
        
        attributes_obj = request.registry['product.attribute']
        attributes_ids = attributes_obj.search(cr, uid, [], context=context)
        attributes = attributes_obj.browse(cr, uid, attributes_ids, context=context)


        from_currency = pool.get('product.price.type')._get_field_currency(cr, uid, 'list_price', context)
        to_currency = pricelist.currency_id
        compute_currency = lambda price: pool['res.currency']._compute(cr, uid, from_currency, to_currency, price, context=context)
        
        
        
        values = {
            'search': search,
            'category': category,
            'attrib_values': attrib_values,
            'attrib_set': attrib_set,
            'pager': pager,
            'pricelist': pricelist,
            'products': products,
            #'products_categories':table_compute().cat_process(public_categs),   
            #'bins': table_compute().process(products),
            'products_categories':self.ChangeGlobalPPRCatProcess(public_categs,25,4),
            'bins': self.ChangeGlobalPPRProcess(products,20,3),            
            'rows': PPR,
            'styles': styles,
            'status_msg': msg,
            'categories': categs,
            'attributes': attributes,
            'compute_currency': compute_currency,
            'keep': keep,
            'style_in_product': lambda style, product: style.id in [s.id for s in product.website_style_ids],
            'attrib_encode': lambda attribs: werkzeug.url_encode([('attrib',i) for i in attribs]),
        }
        
        return request.website.render("website_industrylane.home_products", values)

    @http.route([
#        '/shop',
#        '/shop/page/<int:page>',
        '/shop/category/<model("product.public.category"):category>',
        '/shop/category/<model("product.public.category"):category>/page/<int:page>'
    ], type='http', auth="public", website=True)
    def shop(self, page=0, category=None, search='', **post):

        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        
        brand_list = request.httprequest.args.getlist('brand')
        brand_set = map(str,brand_list)        
        covert_init = map(int,brand_set)
        brand_set_one = set(covert_init)
        tuple_brand_id=tuple(covert_init)
        
        
        attrib_list = request.httprequest.args.getlist('attrib')
        attrib_values = [map(int, v.split("-")) for v in attrib_list if v]
        attrib_set = set([v[1] for v in attrib_values])

        domain = self._get_search_domain(search, category, attrib_values)

        #keep = QueryURL('/shop', category=category and int(category), search=search, attrib=attrib_list)
        keep = QueryURL('/shop', category=category and int(category), search="", attrib="")

        if not context.get('pricelist'):
            pricelist = self.get_pricelist()
            context['pricelist'] = int(pricelist)
        else:
            pricelist = pool.get('product.pricelist').browse(cr, uid, context['pricelist'], context)
                
        
        product_obj = pool.get('product.template')
        brand_obj = pool.get('product.brand')
        
        url = "/shop"
        product_count = product_obj.search_count(cr, SUPERUSER_ID, domain, context=context)
        if search:
            post["search"] = search
        if category:
            category = pool['product.public.category'].browse(cr, uid, int(category), context=context)
            url = "/shop/category/%s" % slug(category)
            
        if attrib_list:
            post['attrib'] = attrib_list
        pager = request.website.pager(url=url, total=product_count, page=page, step=PPG, scope=7, url_args=post)
        
        
        
        #product_template_id = {} 
        cr.execute('select product_template_id from product_public_category_product_template_rel where product_public_category_id = %s', (category.id,))
        fetch_template_id = cr.fetchall();
        public_products_temp_id = [a[0] for a in fetch_template_id]
        #products_temp_id = product_obj.browse(cr, uid, public_products_temp_id, context=context)           
        tuple_public_products_temp_id=tuple(public_products_temp_id)
               
        if tuple_public_products_temp_id:
#             cr.execute('select distinct categ_id from product_template where id in %s', (tuple_public_products_temp_id,))
#             fetch_categ_id = cr.fetchall();
#             public_products_categ_id = [a[0] for a in fetch_categ_id]
#             categ = product_obj.browse(cr, uid, public_products_categ_id, context=context)
            
            cr.execute('select distinct product_brand from product_template where id in %s', (tuple_public_products_temp_id,))
            fetch_brand_id = cr.fetchall();
            public_products_brand_id = [a[0] for a in fetch_brand_id]            
        else :
            categ = 0
            public_products_brand_id = 0 
            
        
        #pdb.set_trace()
        if brand_list:
            product_ids = product_obj.search(cr, uid, [('product_brand', 'in', tuple_brand_id),('id', 'in', public_products_temp_id)], context=context)
        else:
            product_ids = product_obj.search(cr, uid, domain, limit=PPG, offset=pager['offset'], order=self._get_search_order(post), context=context)        
        
        brands = brand_obj.browse(cr, SUPERUSER_ID, public_products_brand_id, context=context)

        
        products = product_obj.browse(cr, uid, product_ids, context=context)
        #pdb.set_trace()
        style_obj = pool['product.style']
        style_ids = style_obj.search(cr, uid, [], context=context)
        styles = style_obj.browse(cr, uid, style_ids, context=context)
        

        category_obj = pool['product.public.category']
        category_ids = category_obj.search(cr, uid, [('parent_id', '=', False)], context=context)
        categs = category_obj.browse(cr, uid, category_ids, context=context)
        

        cr.execute("select distinct C.parent_id from product_template as A INNER JOIN product_public_category_product_template_rel as B on A.id = B.product_template_id INNER JOIN product_public_category C on B.product_public_category_id = C.id WHERE C.parent_id is not null order by C.parent_id ASC")
        public_category_obj = cr.fetchall();
        public_category_ids = [a[0] for a in public_category_obj]
        public_categs = category_obj.browse(cr, uid, public_category_ids, context=context)
        

        from_currency = pool.get('product.price.type')._get_field_currency(cr, uid, 'list_price', context)
        to_currency = pricelist.currency_id
        compute_currency = lambda price: pool['res.currency']._compute(cr, uid, from_currency, to_currency, price, context=context)
          
        #brand_ids = brands.product_brand 
        
        my_dict = {}
        attrs_lines = {} 
                       
        #for val in product_ids:
        for val in product_ids:

            attrs_lines = request.registry['sandv.product.variant'].search(cr, SUPERUSER_ID, [('product_tmpl_id', '=', val)], context=context)
            
            for each in attrs_lines:
                vals_ids = []
                attrs_line_browse = request.registry['sandv.product.variant'].browse(cr, SUPERUSER_ID, each, context=context)
                for var in attrs_line_browse:
                    if var.attribute_id:
                        for x in var.value_ids:
                            if x.attribute_id.id == var.attribute_id.id:
#                                 
                                if var.attribute_id in my_dict.keys():
                                    vals_ids = my_dict[var.attribute_id]
                                else :
                                    my_dict.update({var.attribute_id:[]})
                                vals_ids.append(x)
                                vals_ids = list(set(vals_ids))
#                                 print var.attribute_id, vals_ids
                                my_dict.update({var.attribute_id:vals_ids})                        
                                #print my_dict
        
        
        values = {
            'search': search,
            'category': category,
            'attrib_values': attrib_values,
            'attrib_set': attrib_set,
            'pager': pager,
            'pricelist': pricelist,
            'products': products,
            #'products_categories':table_compute().cat_process(public_categs),   
            #'bins': table_compute().process(products),
            'products_categories':self.ChangeGlobalPPRCatProcess(public_categs,25,4),
            'bins': self.ChangeGlobalPPRProcess(products,100,3),            
            'rows': PPR,
            'styles': styles,
            'categories': categs,
            'minQty': self.getMimOrderQty,
            'QtyType': self.getOrderType,              
            #'attributes': attributes,
            'brands':brands,
            'brand_set':brand_set_one,
            'custom_attributes': my_dict,            
            'compute_currency': compute_currency,
            'keep': keep,
            'style_in_product': lambda style, product: style.id in [s.id for s in product.website_style_ids],
            'attrib_encode': lambda attribs: werkzeug.url_encode([('attrib',i) for i in attribs]),
        }
        
        return request.website.render("website_industrylane.products", values)
    
    
    
    @http.route([
#        '/shop',
        '/il/category/<model("product.public.category"):category>',
        '/il/category/<model("product.public.category"):category>/page/<int:page>'
    ], type='http', auth="public", website=True)
    def il(self, page=0, category=None, search='', **post):

        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        
        brand_list = request.httprequest.args.getlist('brand')
        brand_set = map(str,brand_list)        
        covert_init = map(int,brand_set)
        brand_set_one = set(covert_init)
        tuple_brand_id=tuple(covert_init)
        
        
        attrib_list = request.httprequest.args.getlist('attrib')
        attrib_values = [map(int, v.split("-")) for v in attrib_list if v]
        attrib_set = set([v[1] for v in attrib_values])

        domain = self._get_search_domain(search, category, attrib_values)

        #keep = QueryURL('/shop', category=category and int(category), search=search, attrib=attrib_list)
        keep = QueryURL('/il', category=category and int(category), search="", attrib="")

        if not context.get('pricelist'):
            pricelist = self.get_pricelist()
            context['pricelist'] = int(pricelist)
        else:
            pricelist = pool.get('product.pricelist').browse(cr, uid, context['pricelist'], context)
                
        
        product_obj = pool.get('product.template')
        brand_obj = pool.get('product.brand')
        
        url = "/il"
        product_count = product_obj.search_count(cr, SUPERUSER_ID, domain, context=context)
        if search:
            post["search"] = search
        if category:
            category = pool['product.public.category'].browse(cr, uid, int(category), context=context)
            url = "/il/category/%s" % slug(category)
            
        if attrib_list:
            post['attrib'] = attrib_list
        pager = request.website.pager(url=url, total=product_count, page=page, step=PPG, scope=7, url_args=post)
        
        
        
        post_value = '%'+search+'%'
        #product_template_id = {} 
        cr.execute('select PCTR.product_template_id from product_public_category_product_template_rel as PCTR INNER JOIN product_template PT on PT.id = PCTR.product_template_id where product_public_category_id = %s and name ilike %s', (category.id,post_value))
        fetch_template_id = cr.fetchall();
        public_products_temp_id = [a[0] for a in fetch_template_id]
        #products_temp_id = product_obj.browse(cr, uid, public_products_temp_id, context=context)           
        tuple_public_products_temp_id=tuple(public_products_temp_id)
               
        if tuple_public_products_temp_id:
            cr.execute('select distinct categ_id from product_template where id in %s', (tuple_public_products_temp_id,))
            fetch_categ_id = cr.fetchall();
            public_products_categ_id = [a[0] for a in fetch_categ_id]
            categ = product_obj.browse(cr, uid, public_products_categ_id, context=context)
            
            cr.execute('select distinct product_brand from product_template where id in %s', (tuple_public_products_temp_id,))
            fetch_brand_id = cr.fetchall();
            public_products_brand_id = [a[0] for a in fetch_brand_id]            
        else :
            categ = 0
            public_products_brand_id = 0 
            
        
        
        if brand_list:
            product_ids = product_obj.search(cr, SUPERUSER_ID, [('product_brand', 'in', tuple_brand_id),('categ_id', '=', categ.id),('name', 'ilike', search)], context=context)
        else:
            product_ids = product_obj.search(cr, SUPERUSER_ID, domain, limit=PPG, offset=pager['offset'], order=self._get_search_order(post), context=context)        
        
        brands = brand_obj.browse(cr, SUPERUSER_ID, public_products_brand_id, context=context)

        
        products = product_obj.browse(cr, uid, product_ids, context=context)
        
        style_obj = pool['product.style']
        style_ids = style_obj.search(cr, uid, [], context=context)
        styles = style_obj.browse(cr, uid, style_ids, context=context)
        

        category_obj = pool['product.public.category']
        category_ids = category_obj.search(cr, uid, [('parent_id', '=', False)], context=context)
        categs = category_obj.browse(cr, uid, category_ids, context=context)
        

        cr.execute("select distinct C.parent_id from product_template as A INNER JOIN product_public_category_product_template_rel as B on A.id = B.product_template_id INNER JOIN product_public_category C on B.product_public_category_id = C.id WHERE C.parent_id is not null order by C.parent_id ASC")
        public_category_obj = cr.fetchall();
        public_category_ids = [a[0] for a in public_category_obj]
        public_categs = category_obj.browse(cr, uid, public_category_ids, context=context)
        

        from_currency = pool.get('product.price.type')._get_field_currency(cr, uid, 'list_price', context)
        to_currency = pricelist.currency_id
        compute_currency = lambda price: pool['res.currency']._compute(cr, uid, from_currency, to_currency, price, context=context)
          
        #brand_ids = brands.product_brand 
        
        my_dict = {}
        attrs_lines = {} 
                       
        #for val in product_ids:
        for val in product_ids:

            attrs_lines = request.registry['sandv.product.variant'].search(cr, SUPERUSER_ID, [('product_tmpl_id', '=', val)], context=context)
            
            for each in attrs_lines:
                vals_ids = []
                attrs_line_browse = request.registry['sandv.product.variant'].browse(cr, SUPERUSER_ID, each, context=context)
                for var in attrs_line_browse:
                    if var.attribute_id:
                        for x in var.value_ids:
                            if x.attribute_id.id == var.attribute_id.id:
#                                 
                                if var.attribute_id in my_dict.keys():
                                    vals_ids = my_dict[var.attribute_id]
                                else :
                                    my_dict.update({var.attribute_id:[]})
                                vals_ids.append(x)
                                vals_ids = list(set(vals_ids))
#                                 print var.attribute_id, vals_ids
                                my_dict.update({var.attribute_id:vals_ids})                        
                                #print my_dict
        
        #pdb.set_trace()
        values = {
            'search': search,
            'category': category,
            'attrib_values': attrib_values,
            'attrib_set': attrib_set,
            'pager': pager,
            'pricelist': pricelist,
            'products': products,
            #'products_categories':table_compute().cat_process(public_categs),   
            #'bins': table_compute().process(products),
            'products_categories':self.ChangeGlobalPPRCatProcess(public_categs,25,4),
            'bins': self.ChangeGlobalPPRProcess(products,100,3),            
            'rows': PPR,
            'styles': styles,
            'categories': categs,
            'minQty': self.getMimOrderQty,
            'QtyType': self.getOrderType,              
            #'attributes': attributes,
            'brands':brands,
            'brand_set':brand_set_one,
            'custom_attributes': my_dict,            
            'compute_currency': compute_currency,
            'keep': keep,
            'style_in_product': lambda style, product: style.id in [s.id for s in product.website_style_ids],
            'attrib_encode': lambda attribs: werkzeug.url_encode([('attrib',i) for i in attribs]),
        }
        
        return request.website.render("website_industrylane.products", values)
    
    @http.route([
#        '/shop',
        '/il/category/all-brands-5002',

    ], type='http', auth="public", website=True)
    def ilsearchby(self, page=0, category=None, search='', **post):

        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        #pdb.set_trace()
        
        brand_list = request.httprequest.args.getlist('brand')
        brand_set = map(str,brand_list)        
        covert_init = map(int,brand_set)
        brand_set_one = set(covert_init)
        tuple_brand_id=tuple(covert_init)
        
        
        attrib_list = request.httprequest.args.getlist('attrib')
        attrib_values = [map(int, v.split("-")) for v in attrib_list if v]
        attrib_set = set([v[1] for v in attrib_values])

        #pdb.set_trace()

        #keep = QueryURL('/shop', category=category and int(category), search=search, attrib=attrib_list)
        keep = QueryURL('/il', category=category and int(category), search="", attrib="")

        if not context.get('pricelist'):
            pricelist = self.get_pricelist()
            context['pricelist'] = int(pricelist)
        else:
            pricelist = pool.get('product.pricelist').browse(cr, uid, context['pricelist'], context)
                
        
        product_obj = pool.get('product.template')
        brand_obj = pool.get('product.brand')
        
        url = "/il"

#         if category:
#             category = pool['product.public.category'].browse(cr, uid, int(category), context=context)
#             url = "/il/category/%s" % slug(category)
            

        
        
        post_value = '%'+search+'%'

        public_products_brand_id = brand_obj.search(cr, uid, [('name', 'ilike', post_value)], context=context)
        
        public_products_temp_id = product_obj.search(cr, SUPERUSER_ID, [('product_brand', 'in', public_products_brand_id)], context=context)

        domain = self._get_search_brand(public_products_brand_id,attrib_values)
        
        product_count = product_obj.search_count(cr, SUPERUSER_ID, domain, context=context)
        if search:
            post["search"] = search    
        
        if attrib_list:
            post['attrib'] = attrib_list
        pager = request.website.pager(url=url, total=product_count, page=page, step=PPG, scope=7, url_args=post)
        
        #pdb.set_trace()         
                
        if brand_list:
            product_ids = product_obj.search(cr, SUPERUSER_ID, [('product_brand', 'in', tuple_brand_id)], context=context)

        elif attrib_list:
            product_ids = product_obj.search(cr, SUPERUSER_ID,domain, limit=PPG, offset=pager['offset'], order=self._get_search_order(post), context=context)
           
        else:
            product_ids = public_products_temp_id        
        
           
        brands = brand_obj.browse(cr, SUPERUSER_ID, public_products_brand_id, context=context)

        
        products = product_obj.browse(cr, SUPERUSER_ID, product_ids, context=context)
        
        style_obj = pool['product.style']
        style_ids = style_obj.search(cr, uid, [], context=context)
        styles = style_obj.browse(cr, uid, style_ids, context=context)
        

        category_obj = pool['product.public.category']
        category_ids = category_obj.search(cr, uid, [('parent_id', '=', False)], context=context)
        categs = category_obj.browse(cr, uid, category_ids, context=context)
        

        cr.execute("select distinct C.parent_id from product_template as A INNER JOIN product_public_category_product_template_rel as B on A.id = B.product_template_id INNER JOIN product_public_category C on B.product_public_category_id = C.id WHERE C.parent_id is not null order by C.parent_id ASC")
        public_category_obj = cr.fetchall();
        public_category_ids = [a[0] for a in public_category_obj]
        public_categs = category_obj.browse(cr, uid, public_category_ids, context=context)
        

        from_currency = pool.get('product.price.type')._get_field_currency(cr, uid, 'list_price', context)
        to_currency = pricelist.currency_id
        compute_currency = lambda price: pool['res.currency']._compute(cr, uid, from_currency, to_currency, price, context=context)
          
        #brand_ids = brands.product_brand 
        
        my_dict = {}
        attrs_lines = {} 
                       
        #for val in product_ids:
        for val in product_ids:

            attrs_lines = request.registry['sandv.product.variant'].search(cr, SUPERUSER_ID, [('product_tmpl_id', '=', val)], context=context)
            
            for each in attrs_lines:
                vals_ids = []
                attrs_line_browse = request.registry['sandv.product.variant'].browse(cr, SUPERUSER_ID, each, context=context)
                for var in attrs_line_browse:
                    if var.attribute_id:
                        for x in var.value_ids:
                            if x.attribute_id.id == var.attribute_id.id:
#                                 
                                if var.attribute_id in my_dict.keys():
                                    vals_ids = my_dict[var.attribute_id]
                                else :
                                    my_dict.update({var.attribute_id:[]})
                                vals_ids.append(x)
                                vals_ids = list(set(vals_ids))
#                                 print var.attribute_id, vals_ids
                                my_dict.update({var.attribute_id:vals_ids})                        
                                #print my_dict
        
        
        values = {
            'search': search,
            'category': category,
            'attrib_values': attrib_values,
            'attrib_set': attrib_set,
            'pager': pager,
            'pricelist': pricelist,
            'products': products,
            #'products_categories':table_compute().cat_process(public_categs),   
            #'bins': table_compute().process(products),
            'products_categories':self.ChangeGlobalPPRCatProcess(public_categs,25,4),
            'bins': self.ChangeGlobalPPRProcess(products,100,3),            
            'rows': PPR,
            'styles': styles,
            'categories': categs,
            'minQty': self.getMimOrderQty,
            'QtyType': self.getOrderType,              
            #'attributes': attributes,
            'brands':brands,
            'brand_set':brand_set_one,
            'custom_attributes': my_dict,            
            'compute_currency': compute_currency,
            'keep': keep,
            'style_in_product': lambda style, product: style.id in [s.id for s in product.website_style_ids],
            'attrib_encode': lambda attribs: werkzeug.url_encode([('attrib',i) for i in attribs]),
        }
        
        return request.website.render("website_industrylane.products", values)
        
    @http.route([
        '/search',
        '/search/page/<int:page>',
    ], type='http', auth="public", website=True)
    def search(self, page=0, category=0, search='', **post):

        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        
        brand_list = request.httprequest.args.getlist('brand')
        brand_set = map(str,brand_list)        
        covert_init = map(int,brand_set)
        brand_set_one = set(covert_init)
        tuple_brand_id=tuple(covert_init)
        
        
        attrib_list = request.httprequest.args.getlist('attrib')
        attrib_values = [map(int, v.split("-")) for v in attrib_list if v]
        attrib_set = set([v[1] for v in attrib_values])

        domain = self._get_search_domain(search, category, attrib_values)

        #keep = QueryURL('/shop', category=category and int(category), search=search, attrib=attrib_list)
        keep = QueryURL('/shop', category=category and int(category), search="", attrib="")

        if not context.get('pricelist'):
            pricelist = self.get_pricelist()
            context['pricelist'] = int(pricelist)
        else:
            pricelist = pool.get('product.pricelist').browse(cr, uid, context['pricelist'], context)
                
        
        product_obj = pool.get('product.template')
        brand_obj = pool.get('product.brand')
        
        url = "/shop"
        product_count = product_obj.search_count(cr, SUPERUSER_ID, domain, context=context)
        if search:
            post["search"] = search
        if category:
            category = pool['product.public.category'].browse(cr, uid, int(category), context=context)
            url = "/shop/category/%s" % slug(category)
            
        if attrib_list:
            post['attrib'] = attrib_list
        pager = request.website.pager(url=url, total=product_count, page=page, step=PPG, scope=7, url_args=post)
        
        
        
        post_value = '%'+search+'%'
        #product_template_id = {} 
        cr.execute('select id from product_template where name ilike %s', (post_value,))
        fetch_template_id = cr.fetchall();
        public_products_temp_id = [a[0] for a in fetch_template_id]
        #products_temp_id = product_obj.browse(cr, uid, public_products_temp_id, context=context)           
        tuple_public_products_temp_id=tuple(public_products_temp_id)
               
        if tuple_public_products_temp_id:
            cr.execute('select distinct categ_id from product_template where id in %s', (tuple_public_products_temp_id,))
            fetch_categ_id = cr.fetchall();
            public_products_categ_id = [a[0] for a in fetch_categ_id]
            categ = product_obj.browse(cr, uid, public_products_categ_id, context=context)
            
            cr.execute('select distinct product_brand from product_template where id in %s', (tuple_public_products_temp_id,))
            fetch_brand_id = cr.fetchall();
            public_products_brand_id = [a[0] for a in fetch_brand_id]            
        else :
            categ = 0
            public_products_brand_id = 0 

        
        
        if brand_list:
            product_ids = product_obj.search(cr, uid, [('product_brand', 'in', tuple_brand_id),('name', 'ilike', search)], context=context)
        else:
            product_ids = product_obj.search(cr, uid, domain, limit=PPG, offset=pager['offset'], order=self._get_search_order(post), context=context)        
        
        
       
        brands = brand_obj.browse(cr, SUPERUSER_ID, public_products_brand_id, context=context)
    
        
        products = product_obj.browse(cr, uid, product_ids, context=context)
        
        style_obj = pool['product.style']
        style_ids = style_obj.search(cr, uid, [], context=context)
        styles = style_obj.browse(cr, uid, style_ids, context=context)
        

        category_obj = pool['product.public.category']
        category_ids = category_obj.search(cr, uid, [('parent_id', '=', False)], context=context)
        categs = category_obj.browse(cr, uid, category_ids, context=context)
        

        

        from_currency = pool.get('product.price.type')._get_field_currency(cr, uid, 'list_price', context)
        to_currency = pricelist.currency_id
        compute_currency = lambda price: pool['res.currency']._compute(cr, uid, from_currency, to_currency, price, context=context)
          
        #brand_ids = brands.product_brand 
        
        my_dict = {}
        attrs_lines = {} 
                       
        #for val in product_ids:
        for val in product_ids:

            attrs_lines = request.registry['sandv.product.variant'].search(cr, SUPERUSER_ID, [('product_tmpl_id', '=', val)], context=context)
            
            for each in attrs_lines:
                vals_ids = []
                attrs_line_browse = request.registry['sandv.product.variant'].browse(cr, SUPERUSER_ID, each, context=context)
                for var in attrs_line_browse:
                    if var.attribute_id:
                        for x in var.value_ids:
                            if x.attribute_id.id == var.attribute_id.id:
#                                 
                                if var.attribute_id in my_dict.keys():
                                    vals_ids = my_dict[var.attribute_id]
                                else :
                                    my_dict.update({var.attribute_id:[]})
                                vals_ids.append(x)
                                vals_ids = list(set(vals_ids))
#                                 print var.attribute_id, vals_ids
                                my_dict.update({var.attribute_id:vals_ids})                        
                                #print my_dict
        
        
        values = {
            'search': search,
            'category': category,
            'attrib_values': attrib_values,
            'attrib_set': attrib_set,
            'pager': pager,
            'pricelist': pricelist,
            'products': products,
            'bins': self.ChangeGlobalPPRProcess(products,100,3),            
            'rows': PPR,
            'styles': styles,
            'categories': categs,
            'minQty': self.getMimOrderQty,
            'QtyType': self.getOrderType,              
            #'attributes': attributes,
            'brands':brands,
            'brand_set':brand_set_one,
            'custom_attributes': my_dict,            
            'compute_currency': compute_currency,
            'keep': keep,
            'style_in_product': lambda style, product: style.id in [s.id for s in product.website_style_ids],
            'attrib_encode': lambda attribs: werkzeug.url_encode([('attrib',i) for i in attribs]),
        }
        #pdb.set_trace()
        return request.website.render("website_industrylane.products", values)  
    

    @http.route([
#        '/shop',
#        '/shop/page/<int:page>',
        '/shop/subcategory/<model("product.public.category"):category>',
        '/shop/subcategory/<model("product.public.category"):category>/page/<int:page>'
    ], type='http', auth="public", website=True)
    def shop_subcategory(self, page=0, category=None, search='', **post):

        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry

        attrib_list = request.httprequest.args.getlist('attrib')
        attrib_values = [map(int, v.split("-")) for v in attrib_list if v]
        attrib_set = set([v[1] for v in attrib_values])

        domain = self._get_search_domain(search, category, attrib_values)
        
        keep = QueryURL('/shop', category=category and int(category), search=search, attrib=attrib_list)

        if not context.get('pricelist'):
            pricelist = self.get_pricelist()
            context['pricelist'] = int(pricelist)
        else:
            pricelist = pool.get('product.pricelist').browse(cr, uid, context['pricelist'], context)
                
       
        product_obj = pool.get('product.template')

        url = "/shop"
        product_count = product_obj.search_count(cr, SUPERUSER_ID, domain, context=context)
        if search:
            post["search"] = search
        if category:
            category = pool['product.public.category'].browse(cr, uid, int(category), context=context)
            url = "/shop/category/%s" % slug(category)
        if attrib_list:
            post['attrib'] = attrib_list
            
            
        pager = request.website.pager(url=url, total=product_count, page=page, step=PPG, scope=7, url_args=post)
        product_ids = product_obj.search(cr, uid, domain, limit=PPG, offset=pager['offset'], order=self._get_search_order(post), context=context)
        products = product_obj.browse(cr, uid, product_ids, context=context)
        
        
        
        style_obj = pool['product.style']
        style_ids = style_obj.search(cr, uid, [], context=context)
        styles = style_obj.browse(cr, uid, style_ids, context=context)
        

        category_obj = pool['product.public.category']
        category_ids = category_obj.search(cr, uid, [('parent_id', '=', False)], context=context)
        categs = category_obj.browse(cr, uid, category_ids, context=context)

        parent_category_id = category.id
        

        #cr.execute("select distinct C.parent_id from product_template as A INNER JOIN product_public_category_product_template_rel as B on A.id = B.product_template_id INNER JOIN product_public_category C on B.product_public_category_id = C.id WHERE C.parent_id = order by C.parent_id ASC")
        cr.execute('select distinct C.id from product_template as A INNER JOIN product_public_category_product_template_rel as B on A.id = B.product_template_id INNER JOIN product_public_category C on B.product_public_category_id = C.id WHERE C.parent_id = %s order by C.id ASC', (parent_category_id,))
        public_category_obj = cr.fetchall();
        public_category_ids = [a[0] for a in public_category_obj]
        public_categs = category_obj.browse(cr, uid, public_category_ids, context=context)
        
       
        
        from_currency = pool.get('product.price.type')._get_field_currency(cr, uid, 'list_price', context)
        to_currency = pricelist.currency_id
        compute_currency = lambda price: pool['res.currency']._compute(cr, uid, from_currency, to_currency, price, context=context)

        my_dict = {}
        attrs_lines = {} 
                       
        for val in product_ids:

            attrs_lines = request.registry['sandv.product.variant'].search(cr, SUPERUSER_ID, [('product_tmpl_id', '=', val)], context=context)
            
            for each in attrs_lines:
                vals_ids = []
                attrs_line_browse = request.registry['sandv.product.variant'].browse(cr, SUPERUSER_ID, each, context=context)
                for var in attrs_line_browse:
                    if var.attribute_id:
                        for x in var.value_ids:
                            if x.attribute_id.id == var.attribute_id.id:
#                                 
                                if var.attribute_id in my_dict.keys():
                                    vals_ids = my_dict[var.attribute_id]
                                else :
                                    my_dict.update({var.attribute_id:[]})
                                vals_ids.append(x)
                                vals_ids = list(set(vals_ids))
#                                 print var.attribute_id, vals_ids
                                my_dict.update({var.attribute_id:vals_ids})                        
                                #print my_dict
        #
        values = {
            'search': search,
            'category': category,
            'attrib_values': attrib_values,
            'attrib_set': attrib_set,
            'pager': pager,
            'pricelist': pricelist,
            'products': products,
            #'products_categories':table_compute().cat_process(public_categs),   
            #'bins': table_compute().process(products),
            'products_categories':self.ChangeGlobalPPRCatProcess(public_categs,25,4),
            'bins': self.ChangeGlobalPPRProcess(products,20,3),            
            'rows': PPR,
            'styles': styles,
            'categories': categs,
            #'attributes': attributes,
            'custom_attributes': my_dict,            
            'compute_currency': compute_currency,
            'keep': keep,
            'style_in_product': lambda style, product: style.id in [s.id for s in product.website_style_ids],
            'attrib_encode': lambda attribs: werkzeug.url_encode([('attrib',i) for i in attribs]),
        }
        
        return request.website.render("website_industrylane.subcategory", values)


    @http.route([
       '/shop/smart_basket',
    ], type='http', auth="user", website=True)
    def smart_basket(self,page=0, category=None, search='', **post):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        
        partner =  pool['res.users'].browse(cr, SUPERUSER_ID, uid, context=context).partner_id
       
        cr.execute('select pp.product_tmpl_id from sale_order_line sol INNER JOIN sale_order so on so.id = sol.order_id INNER JOIN product_product pp on pp.id = sol.product_id where so.partner_id = %s GROUP BY pp.id HAVING count(*) > 1', (partner.id,))
        get_products = cr.fetchall();
        get_products_ids = [a[0] for a in get_products]
        
        product_obj = pool.get('product.template')
        
        products = product_obj.browse(cr, uid, get_products_ids, context=context)
        
        attrib_list = request.httprequest.args.getlist('attrib')
        attrib_values = [map(int, v.split("-")) for v in attrib_list if v]
        attrib_set = set([v[1] for v in attrib_values])

        domain = self._get_search_domain(search, category, attrib_values)
        
        keep = QueryURL('/shop', category=category and int(category), search=search, attrib=attrib_list)
        if not context.get('pricelist'):
            pricelist = self.get_pricelist()
            context['pricelist'] = int(pricelist)
        else:
            pricelist = pool.get('product.pricelist').browse(cr, uid, context['pricelist'], context)
                
       
        

        url = "/shop"
        product_count = product_obj.search_count(cr, SUPERUSER_ID, domain, context=context)
        if search:
            post["search"] = search
        if category:
            category = pool['product.public.category'].browse(cr, uid, int(category), context=context)
            url = "/shop/category/%s" % slug(category)
        if attrib_list:
            post['attrib'] = attrib_list
         
        category_obj = pool['product.public.category']
        category_ids = category_obj.search(cr, uid, [('parent_id', '=', False)], context=context)
        categs = category_obj.browse(cr, uid, category_ids, context=context)            
            
        pager = request.website.pager(url=url, total=product_count, page=page, step=PPG, scope=7, url_args=post)        

        from_currency = pool.get('product.price.type')._get_field_currency(cr, uid, 'list_price', context)
        to_currency = pricelist.currency_id
        compute_currency = lambda price: pool['res.currency']._compute(cr, uid, from_currency, to_currency, price, context=context)

        style_obj = pool['product.style']
        style_ids = style_obj.search(cr, uid, [], context=context)
        styles = style_obj.browse(cr, uid, style_ids, context=context)
        
        #pdb.set_trace()
        values = {
            'search': search,
            'category': category,
            'categories': categs,
            'attrib_values': attrib_values,
            'attrib_set': attrib_set,
            'pager': pager,
            'pricelist': pricelist,
            'products': products,
            'bins': self.ChangeGlobalPPRProcess(products,20,3),            
            'rows': PPR,
            'styles': styles,    
            'compute_currency': compute_currency,
            'keep': keep,
            'style_in_product': lambda style, product: style.id in [s.id for s in product.website_style_ids],
            'attrib_encode': lambda attribs: werkzeug.url_encode([('attrib',i) for i in attribs]),             
        }
              
        #return request.website.render("website_industrylane.smart_basket", values)
        return request.website.render("website_industrylane.smart_basket", values)  
    
        
    def _get_used_attrs(self, category):
        """This method retrieves all ids of the category selected on the
        website.
        """
        cr, uid, context, pool = (request.cr,
                                  request.uid,
                                  request.context,
                                  request.registry)
        attribute_ids = []
        prod_ids = []
        attrs_unknown = {}
        product_obj = pool['product.template']
        if category:
            cond = self._normalize_category(category)
            prod_ids = product_obj.search(
                cr,
                uid,
                [('public_categ_ids', '=', cond)], context=context)
            for product in product_obj.browse(cr, uid, prod_ids,
                                              context=context):
                for line in product.attribute_line_ids:
                    if line.attribute_id.id not in attribute_ids:
                        attribute_ids.append(line.attribute_id.id)
                    if not line.value_ids and line.attribute_id.id in \
                            attribute_ids:
                        attrs_unknown[line.attribute_id.id] = True
        return attribute_ids, attrs_unknown
    
    def _normalize_category(self, category):
        """This method returns a condition value usable on tuples, because
        sometimes category can come from different places, sometimes it
        can be an Odoo object and some others an int or a unicode.
        """
        if isinstance(category, int) or isinstance(category, unicode):
            cond = int(category)
        else:
            cond = category.id
        return cond    

 

    @http.route(['/shop/product/<model("product.template"):product>'], type='http', auth="public", website=True)
    def product(self, product, category='', search='', **post):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        category_obj = pool['product.public.category']
        template_obj = pool['product.template']
        page=0
        context.update(active_id=product.id)

        if category:
            category = category_obj.browse(cr, uid, int(category), context=context)
            category = category if category.exists() else False

        attrib_list = request.httprequest.args.getlist('attrib')
        attrib_values = [map(int,v.split("-")) for v in attrib_list if v]
        attrib_set = set([v[1] for v in attrib_values])
        
        domain = self._get_search_domain(search, category, attrib_values)
       
        keep = QueryURL('/shop', category=category and category.id, search=search, attrib=attrib_list)
        post = ""
        if not context.get('pricelist'):
            pricelist = self.get_pricelist()
            context['pricelist'] = int(pricelist)
        else:
            pricelist = pool.get('product.pricelist').browse(cr, uid, context['pricelist'], context)

        product_obj = pool.get('product.template')
       
        url = "/shop"
        product_count = product_obj.search_count(cr, SUPERUSER_ID, domain, context=context)
        
        
        
#         if search:
#             post["search"] = search
        if category:
            category = pool['product.public.category'].browse(cr, uid, int(category), context=context)
            url = "/shop/category/%s" % slug(category)
        if attrib_list:
            post['attrib'] = attrib_list
            
        pager = request.website.pager(url=url, total=product_count, page=page, step=PPG, scope=7, url_args=post)
        product_ids = product_obj.search(cr, uid, domain, limit=PPG, offset=pager['offset'],  context=context)
        products = product_obj.browse(cr, SUPERUSER_ID, product_ids, context=context)
                

        category_ids = category_obj.search(cr, uid, [], context=context)
        category_list = category_obj.name_get(cr, uid, category_ids, context=context)
        category_list = sorted(category_list, key=lambda category: category[1])

        pricelist = self.get_pricelist()

        from_currency = pool.get('product.price.type')._get_field_currency(cr, uid, 'list_price', context)
        to_currency = pricelist.currency_id
        compute_currency = lambda price: pool['res.currency']._compute(cr, uid, from_currency, to_currency, price, context=context)
       
        if not context.get('pricelist'):
            context['pricelist'] = int(self.get_pricelist())
            product = template_obj.browse(cr, SUPERUSER_ID, int(product), context=context)
       
        count = len(products)
        
        values = {
            'search': search,
            'category': category,
            'pricelist': pricelist,
            'attrib_values': attrib_values,
            'compute_currency': compute_currency,
            'attrib_set': attrib_set,
            'products': products,
            'bins': self.ChangeGlobalPPRProcess(products,count,4),
            'rows': PPR,
            'keep': keep,
            'minQty': self.getMimOrderQty,
            'QtyType': self.getOrderType,              
            'category_list': category_list,
            'main_object': product,
            'product': product,
            'get_attribute_value_ids': self.get_attribute_value_ids
        }
        return request.website.render("website_industrylane.product", values)

    @http.route(['/shop/product/comment/<int:product_template_id>'], type='http', auth="public", website=True)
    def product_comment(self, product_template_id, **post):
        if not request.session.uid:
            return login_redirect()
        cr, uid, context = request.cr, request.uid, request.context
        if post.get('comment'):
            request.registry['product.template'].message_post(
                cr, uid, product_template_id,
                body=post.get('comment'),
                type='comment',
                subtype='mt_comment',
                context=dict(context, mail_create_nosubscribe=True))
        return werkzeug.utils.redirect('/shop/product/%s#comments' % product_template_id)

    @http.route(['/shop/pricelist'], type='http', auth="public", website=True)
    def pricelist(self, promo, **post):
        cr, uid, context = request.cr, request.uid, request.context
        request.website.sale_get_order(code=promo, context=context)
        return request.redirect("/shop/cart")
    
    def getMimOrderQty(self, template_id):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        product_obj = pool.get('product.template')
        product = product_obj.browse(cr, uid, template_id, context=context)
        value = product.min_quantity1
        
        return value
    
    def getOrderType(self, template_id):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        product_obj = pool.get('product.template')
        product = product_obj.browse(cr, uid, template_id, context=context)
        value = product.type_quantity1
        
        return value
        
    @http.route(['/shop/cart'], type='http', auth="public", website=True)
    def cart(self,category='', search='', **post):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        order = request.website.sale_get_order()
        if order:
            from_currency = pool.get('product.price.type')._get_field_currency(cr, uid, 'list_price', context)
            to_currency = order.pricelist_id.currency_id
            compute_currency = lambda price: pool['res.currency']._compute(cr, uid, from_currency, to_currency, price, context=context)
        else:
            compute_currency = lambda price: price
         
          
        category_obj = pool['product.public.category']
        
        
         
        if category:
            category = category_obj.browse(cr, uid, int(category), context=context)
            category = category if category.exists() else False
 
        attrib_list = request.httprequest.args.getlist('attrib')
        attrib_values = [map(int,v.split("-")) for v in attrib_list if v]
        attrib_set = set([v[1] for v in attrib_values])
 
        keep = QueryURL('/shop', category=category and category.id, search=search, attrib=attrib_list)
         
        category_obj = pool['product.public.category']
        category_ids = category_obj.search(cr, uid, [('parent_id', '=', False)], context=context)
        categs = category_obj.browse(cr, uid, category_ids, context=context)
         
        values = {
            'order': order,
            'search': search,
            'category': category,            
            'categories': categs,
            'keep': keep,
            'minQty': self.getMimOrderQty,
            'QtyType': self.getOrderType,                        
            'compute_currency': compute_currency,
            'suggested_products': [],
        }
        if order:
            _order = order
            if not context.get('pricelist'):
                _order = order.with_context(pricelist=order.pricelist_id.id)
            values['suggested_products'] = _order._cart_accessories()
 
        return request.website.render("website_industrylane.cart", values)
        #return request.website.render("website_industrylane.cart", values)

    @http.route(['/shop/cart/update'], type='http', auth="public", methods=['POST'], website=True)
    def cart_update(self, product_id, add_qty=1, set_qty=0, **kw):
        cr, uid, context = request.cr, request.uid, request.context
        
        
        request.website.sale_get_order(force_create=1)._cart_update(product_id=int(product_id), add_qty=float(add_qty), set_qty=float(set_qty))
        
        return request.redirect("/shop/cart")

    @http.route(['/shop/cart/update_json'], type='json', auth="public", methods=['POST'], website=True)
    def cart_update_json(self, product_id, line_id, add_qty=None, set_qty=None, display=True):

        order = request.website.sale_get_order(force_create=1)
        if order.state != 'draft':
            request.website.sale_reset()
            return {}
        
        value = order._cart_update(product_id=product_id, line_id=line_id, add_qty=add_qty, set_qty=set_qty)
        if not order.cart_quantity:
            request.website.sale_reset()
            return {}
        if not display:
            return None
        
        #value['cart_quantity'] = order.cart_quantity
        value['cart_quantity'] = order.cart_quantity
        value['website_sale.total'] = request.website._render("website_sale.total", {
                'website_sale_order': request.website.sale_get_order()
            })
       
        return value
    #------------------------------------------------------
    # Checkout
    #------------------------------------------------------

    def checkout_redirection(self, order):
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry

        # must have a draft sale order with lines at this point, otherwise reset
        if not order or order.state != 'draft':
            request.session['sale_order_id'] = None
            request.session['sale_transaction_id'] = None
            return request.redirect('/shop')

        # if transaction pending / done: redirect to confirmation
        tx = context.get('website_sale_transaction')
        if tx and tx.state != 'draft':
            return request.redirect('/shop/payment/confirmation/%s' % order.id)

    def checkout_values(self, data=None):
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        orm_partner = registry.get('res.partner')
        orm_user = registry.get('res.users')
        orm_country = registry.get('res.country')
        state_orm = registry.get('res.country.state')

        country_ids = orm_country.search(cr, SUPERUSER_ID, [], context=context)
        countries = orm_country.browse(cr, SUPERUSER_ID, country_ids, context)
        states_ids = state_orm.search(cr, SUPERUSER_ID, [], context=context)
        states = state_orm.browse(cr, SUPERUSER_ID, states_ids, context)
        partner = orm_user.browse(cr, SUPERUSER_ID, request.uid, context).partner_id

        order = None

        shipping_id = None
        shipping_ids = []
        checkout = {}
        if not data:
            if request.uid != request.website.user_id.id:
                checkout.update( self.checkout_parse("billing", partner) )
                shipping_ids = orm_partner.search(cr, SUPERUSER_ID, [("parent_id", "=", partner.id), ('type', "=", 'delivery')], context=context)
            else:
                order = request.website.sale_get_order(force_create=1, context=context)
                if order.partner_id:
                    domain = [("partner_id", "=", order.partner_id.id)]
                    user_ids = request.registry['res.users'].search(cr, SUPERUSER_ID, domain, context=dict(context or {}, active_test=False))
                    if not user_ids or request.website.user_id.id not in user_ids:
                        checkout.update( self.checkout_parse("billing", order.partner_id) )
        else:
            checkout = self.checkout_parse('billing', data)
            try: 
                shipping_id = int(data["shipping_id"])
            except ValueError:
                pass
            if shipping_id == -1:
                checkout.update(self.checkout_parse('shipping', data))

        if shipping_id is None:
            if not order:
                order = request.website.sale_get_order(context=context)
            if order and order.partner_shipping_id:
                shipping_id = order.partner_shipping_id.id

        shipping_ids = list(set(shipping_ids) - set([partner.id]))

        if shipping_id == partner.id:
            shipping_id = 0
        elif shipping_id > 0 and shipping_id not in shipping_ids:
            shipping_ids.append(shipping_id)
        elif shipping_id is None and shipping_ids:
            shipping_id = shipping_ids[0]

        ctx = dict(context, show_address=1)
        shippings = []
        if shipping_ids:
            shippings = shipping_ids and orm_partner.browse(cr, SUPERUSER_ID, list(shipping_ids), ctx) or []
        if shipping_id > 0:
            shipping = orm_partner.browse(cr, SUPERUSER_ID, shipping_id, ctx)
            checkout.update( self.checkout_parse("shipping", shipping) )

        checkout['shipping_id'] = shipping_id

        # Default search by user country
        if not checkout.get('country_id'):
            country_code = request.session['geoip'].get('country_code')
            if country_code:
                country_ids = request.registry.get('res.country').search(cr, uid, [('code', '=', country_code)], context=context)
                if country_ids:
                    checkout['country_id'] = country_ids[0]

        values = {
            'countries': countries,
            'states': states,
            'checkout': checkout,
            'shipping_id': partner.id != shipping_id and shipping_id or 0,
            'shippings': shippings,
            'error': {},
            'has_check_vat': hasattr(registry['res.partner'], 'check_vat')
        }

        return values
    
    mandatory_billing_fields = ["name","concern_person", "phone", "email", "street","street2","city", "country_id","state_id"]
    optional_billing_fields = ["street", "state_id", "vat", "vat_subjected", "zip"]
    mandatory_shipping_fields = ["name","concern_person", "phone", "street", "city", "country_id","state_id"]
    optional_shipping_fields = [ "zip"]

    def _get_mandatory_billing_fields(self):
        return self.mandatory_billing_fields

    def _get_optional_billing_fields(self):
        return self.optional_billing_fields

    def _get_mandatory_shipping_fields(self):
        return self.mandatory_shipping_fields

    def _get_optional_shipping_fields(self):
        return self.optional_shipping_fields

    def _post_prepare_query(self, query, data, address_type):
        return query

    def checkout_parse(self, address_type, data, remove_prefix=False):
        """ data is a dict OR a partner browse record
        """
        # set mandatory and optional fields
        assert address_type in ('billing', 'shipping')
        if address_type == 'billing':
            all_fields = self._get_mandatory_billing_fields() + self._get_optional_billing_fields()
            prefix = ''
        else:
            all_fields = self._get_mandatory_shipping_fields() + self._get_optional_shipping_fields()
            prefix = 'shipping_'

        # set data
        if isinstance(data, dict):
            query = dict((prefix + field_name, data[prefix + field_name])
                for field_name in all_fields if prefix + field_name in data)
        else:
            query = dict((prefix + field_name, getattr(data, field_name))
                for field_name in all_fields if getattr(data, field_name))
            if address_type == 'billing' and data.parent_id:
                query[prefix + 'street'] = data.parent_id.name

        if query.get(prefix + 'state_id'):
            query[prefix + 'state_id'] = int(query[prefix + 'state_id'])
        if query.get(prefix + 'country_id'):
            query[prefix + 'country_id'] = int(query[prefix + 'country_id'])

        if query.get(prefix + 'vat'):
            query[prefix + 'vat_subjected'] = True

        query = self._post_prepare_query(query, data, address_type)

        if not remove_prefix:
            return query

        return dict((field_name, data[prefix + field_name]) for field_name in all_fields if prefix + field_name in data)

    def checkout_form_validate(self, data):
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry

        # Validation
        error = dict()
        for field_name in self._get_mandatory_billing_fields():
            if not data.get(field_name):
                error[field_name] = 'missing'

        # email validation
        if data.get('email') and not tools.single_email_re.match(data.get('email')):
            error["email"] = 'error'

        if data.get("vat") and hasattr(registry["res.partner"], "check_vat"):
            if request.website.company_id.vat_check_vies:
                # force full VIES online check
                check_func = registry["res.partner"].vies_vat_check
            else:
                # quick and partial off-line checksum validation
                check_func = registry["res.partner"].simple_vat_check
            vat_country, vat_number = registry["res.partner"]._split_vat(data.get("vat"))
            if not check_func(cr, uid, vat_country, vat_number, context=None): # simple_vat_check
                error["vat"] = 'error'

        if data.get("shipping_id") == -1:
            for field_name in self._get_mandatory_shipping_fields():
                field_name = 'shipping_' + field_name
                if not data.get(field_name):
                    error[field_name] = 'missing'

        return error


    
    def _get_shipping_info(self, checkout):
        shipping_info = {}
        shipping_info.update(self.checkout_parse('shipping', checkout, True))
        shipping_info['type'] = 'delivery'
        return shipping_info

    def checkout_form_save(self, checkout):
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry

        order = request.website.sale_get_order(force_create=1, context=context)

        orm_partner = registry.get('res.partner')
        orm_user = registry.get('res.users')
        order_obj = request.registry.get('sale.quotation')

        partner_lang = request.lang if request.lang in [lang.code for lang in request.website.language_ids] else None

        billing_info = {'customer': True}
        if partner_lang:
            billing_info['lang'] = partner_lang
        billing_info.update(self.checkout_parse('billing', checkout, True))

        # set partner_id
        partner_id = None
        if request.uid != request.website.user_id.id:
            partner_id = orm_user.browse(cr, SUPERUSER_ID, uid, context=context).partner_id.id
        elif order.partner_id:
            user_ids = request.registry['res.users'].search(cr, SUPERUSER_ID,
                [("partner_id", "=", order.partner_id.id)], context=dict(context or {}, active_test=False))
            if not user_ids or request.website.user_id.id not in user_ids:
                partner_id = order.partner_id.id

        # save partner informations
        if partner_id and request.website.partner_id.id != partner_id:
            orm_partner.write(cr, SUPERUSER_ID, [partner_id], billing_info, context=context)
        else:
            # create partner
            partner_id = orm_partner.create(cr, SUPERUSER_ID, billing_info, context=context)

        # create a new shipping partner
        if checkout.get('shipping_id') == -1:
            shipping_info = self._get_shipping_info(checkout)
            if partner_lang:
                shipping_info['lang'] = partner_lang
            shipping_info['parent_id'] = partner_id
            checkout['shipping_id'] = orm_partner.create(cr, SUPERUSER_ID, shipping_info, context)

        order_info = {
            'partner_id': partner_id,
            'message_follower_ids': [(4, partner_id), (3, request.website.partner_id.id)],
            'partner_invoice_id': partner_id,
        }
        order_info.update(order_obj.onchange_partner_id(cr, SUPERUSER_ID, [], partner_id, context=context)['value'])
        address_change = order_obj.onchange_delivery_id(cr, SUPERUSER_ID, [], order.company_id.id, partner_id,
                                                        checkout.get('shipping_id'), None, context=context)['value']
        order_info.update(address_change)
        if address_change.get('fiscal_position'):
            fiscal_update = order_obj.onchange_fiscal_position(cr, SUPERUSER_ID, [], address_change['fiscal_position'],
                                                               [(4, l.id) for l in order.order_line], context=None)['value']
            order_info.update(fiscal_update)

        order_info.pop('user_id')
        order_info.update(partner_shipping_id=checkout.get('shipping_id') or partner_id)

        order_obj.write(cr, SUPERUSER_ID, [order.id], order_info, context=context)

    @http.route(['/shop/checkout'], type='http', auth="public", website=True)
    def checkout(self, **post):
        
        time.sleep(2)
        cr, uid, context = request.cr, request.uid, request.context

        order = request.website.sale_get_order(force_create=1, context=context)

        redirection = self.checkout_redirection(order)
        if redirection:
            return redirection

        values = self.checkout_values()

        return request.website.render("website_industrylane.checkout", values)

    @http.route(['/shop/confirm_order'], type='http', auth="public", website=True)
    def confirm_order(self, **post):
      
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry

        order = request.website.sale_get_order(context=context)
        if not order:
            return request.redirect("/shop")

        redirection = self.checkout_redirection(order)
        if redirection:
            return redirection

        values = self.checkout_values(post)

        values["error"] = self.checkout_form_validate(values["checkout"])
        if values["error"]:
            return request.website.render("website_industrylane.checkout", values)
        
        self.checkout_form_save(values["checkout"])

        request.session['sale_last_order_id'] = order.id

        request.website.sale_get_order(update_pricelist=True, context=context)
        
        return request.redirect("/shop/payment")

    #------------------------------------------------------
    # Payment
    #------------------------------------------------------

    @http.route(['/shop/payment'], type='http', auth="public", website=True)
    def payment(self, **post):
        """ Payment step. This page proposes several payment means based on available
        payment.acquirer. State at this point :

         - a draft sale order with lines; otherwise, clean context / session and
           back to the shop
         - no transaction in context / session, or only a draft one, if the customer
           did go to a payment.acquirer website but closed the tab without
           paying / canceling
        """
        
        cr, uid, context = request.cr, request.uid, request.context
        payment_obj = request.registry.get('payment.acquirer')
        sale_order_obj = request.registry.get('sale.quotation')

        order = request.website.sale_get_order(context=context)

        redirection = self.checkout_redirection(order)
        if redirection:
            return redirection

        shipping_partner_id = False
        if order:
            if order.partner_shipping_id.id:
                shipping_partner_id = order.partner_shipping_id.id
            else:
                shipping_partner_id = order.partner_invoice_id.id

        values = {
            'order': request.registry['sale.quotation'].browse(cr, SUPERUSER_ID, order.id, context=context)
        }
        values['errors'] = sale_order_obj._get_errors(cr, uid, order, context=context)
        values.update(sale_order_obj._get_website_data(cr, uid, order, context))

        if not values['errors']:
            acquirer_ids = payment_obj.search(cr, SUPERUSER_ID, [('website_published', '=', True), ('company_id', '=', order.company_id.id)], context=context)
            values['acquirers'] = list(payment_obj.browse(cr, uid, acquirer_ids, context=context))
            render_ctx = dict(context, submit_class='btn btn-primary', submit_txt=_('Confirm Order'))
            for acquirer in values['acquirers']:
                acquirer.button = payment_obj.render(
                    cr, SUPERUSER_ID, acquirer.id,
                    '/',
                    order.amount_total,
                    order.pricelist_id.currency_id.id,
                    partner_id=shipping_partner_id,
                    tx_values={
                        'return_url': '/shop/payment/validate',
                    },
                    context=render_ctx)

        return request.website.render("website_industrylane.payment", values)

    @http.route(['/shop/payment/transaction/<int:acquirer_id>'], type='json', auth="public", website=True)
    def payment_transaction(self, acquirer_id):
        """ Json method that creates a payment.transaction, used to create a
        transaction when the user clicks on 'pay now' button. After having
        created the transaction, the event continues and the user is redirected
        to the acquirer website.

        :param int acquirer_id: id of a payment.acquirer record. If not set the
                                user is redirected to the checkout page
        """
       
        cr, uid, context = request.cr, request.uid, request.context
        payment_obj = request.registry.get('payment.acquirer')
        transaction_obj = request.registry.get('payment.transaction')
        order = request.website.sale_get_order(context=context)

        if not order or not order.order_line or acquirer_id is None:
            return request.redirect("/shop/checkout")

        assert order.partner_id.id != request.website.partner_id.id

        # find an already existing transaction
        tx = request.website.sale_get_transaction()
        if tx:
            tx_id = tx.id
            if tx.sale_order_id.id != order.id or tx.state in ['error', 'cancel'] or tx.acquirer_id.id != acquirer_id:
                tx = False
                tx_id = False
            elif tx.state == 'draft':  # button cliked but no more info -> rewrite on tx or create a new one ?
                tx.write(dict(transaction_obj.on_change_partner_id(cr, SUPERUSER_ID, None, order.partner_id.id, context=context).get('values', {}), amount=order.amount_total))
        if not tx:
            tx_id = transaction_obj.create(cr, SUPERUSER_ID, {
                'acquirer_id': acquirer_id,
                'type': 'form',
                'amount': order.amount_total,
                'currency_id': order.pricelist_id.currency_id.id,
                'partner_id': order.partner_id.id,
                'partner_country_id': order.partner_id.country_id.id,
                'reference': request.env['payment.transaction'].get_next_reference(order.name),
                'quotation_id': order.id,
            }, context=context)
            request.session['sale_transaction_id'] = tx_id
            tx = transaction_obj.browse(cr, SUPERUSER_ID, tx_id, context=context)

        # update quotation
        request.registry['sale.quotation'].write(
            cr, SUPERUSER_ID, [order.id], {
                'payment_acquirer_id': acquirer_id,
                'payment_tx_id': request.session['sale_transaction_id']
            }, context=context)

        return payment_obj.render(
            cr, SUPERUSER_ID, tx.acquirer_id.id,
            tx.reference,
            order.amount_total,
            order.pricelist_id.currency_id.id,
            partner_id=order.partner_shipping_id.id or order.partner_invoice_id.id,
            tx_values={
                'return_url': '/shop/payment/validate',
            },
            context=dict(context, submit_class='btn btn-primary', submit_txt=_('Confirm Order')))

    @http.route('/shop/payment/get_status/<int:sale_order_id>', type='json', auth="public", website=True)
    def payment_get_status(self, sale_order_id, **post):
        cr, uid, context = request.cr, request.uid, request.context

        order = request.registry['sale.quotation'].browse(cr, SUPERUSER_ID, sale_order_id, context=context)
        assert order.id == request.session.get('sale_last_order_id')

        if not order:
            return {
                'state': 'error',
                'message': '<p>%s</p>' % _('There seems to be an error with your request.'),
            }

        tx_ids = request.registry['payment.transaction'].search(
            cr, SUPERUSER_ID, [
                '|', ('sale_order_id', '=', order.id), ('reference', '=', order.name)
            ], context=context)

        state = 'done'
        message = ""
        validation = None

        if not tx_ids:
            if order.amount_total:
                state = 'error'
                message = '<p>%s</p>' % _('There seems to be an error with your request.')
        else:
            tx = request.registry['payment.transaction'].browse(cr, SUPERUSER_ID, tx_ids[0], context=context)
            state = tx.state
            if state == 'done':
                message = '<p>%s</p>' % _('Your payment has been received.')
            elif state == 'cancel':
                message = '<p>%s</p>' % _('The payment seems to have been canceled.')
            elif state == 'pending' and tx.acquirer_id.validation == 'manual':
                message = '<p>%s</p>' % _('Our Team will be get back to you soon.')
                if tx.acquirer_id.post_msg:
                    message += tx.acquirer_id.post_msg
            elif state == 'error':
                message = '<p>%s</p>' % _('An error occurred during the transaction.')
            validation = tx.acquirer_id.validation

        return {
            'state': state,
            'message': message,
            'validation': validation
        }

    @http.route('/shop/payment/validate', type='http', auth="public", website=True)
    def payment_validate(self, transaction_id=None, sale_order_id=None, **post):
        """ Method that should be called by the server when receiving an update
        for a transaction. State at this point :

         - UDPATE ME
        """
        cr, uid, context = request.cr, request.uid, request.context
        email_act = None
        sale_order_obj = request.registry['sale.quotation']

        if transaction_id is None:
            tx = request.website.sale_get_transaction()
        else:
            tx = request.registry['payment.transaction'].browse(cr, uid, transaction_id, context=context)

        if sale_order_id is None:
            order = request.website.sale_get_order(context=context)
        else:
            order = request.registry['sale.quotation'].browse(cr, SUPERUSER_ID, sale_order_id, context=context)
            assert order.id == request.session.get('sale_last_order_id')

        if not order or (order.amount_total and not tx):
            return request.redirect('/shop')

        if (not order.amount_total and not tx) or tx.state in ['pending', 'done']:
            if (not order.amount_total and not tx):
                # Orders are confirmed by payment transactions, but there is none for free orders,
                # (e.g. free events), so confirm immediately
                order.with_context(dict(context, send_email=True)).action_button_confirm()
        elif tx and tx.state == 'cancel':
            # cancel the quotation
            sale_order_obj.action_cancel(cr, SUPERUSER_ID, [order.id], context=request.context)

        # clean context and session, then redirect to the confirmation page
        request.website.sale_reset(context=context)
        if tx and tx.state == 'draft':
            return request.redirect('/shop')

        return request.redirect('/shop/confirmation')

    @http.route(['/shop/confirmation'], type='http', auth="public", website=True)
    def payment_confirmation(self, **post):
        """ End of checkout process controller. Confirmation is basically seing
        the status of a sale.quotation. State at this point :

         - should not have any context / session info: clean them
         - take a sale.quotation id, because we request a sale.quotation and are not
           session dependant anymore
        """
        cr, uid, context = request.cr, request.uid, request.context
        
        
        sale_order_id = request.session.get('sale_last_order_id')
        
        if sale_order_id:
            #senthil Start
            values = {
                    'state': 'sent'                  
                }
            request.registry['sale.quotation'].write(cr, SUPERUSER_ID, [sale_order_id], values, context=context)
            #Senthil End#
            order = request.registry['sale.quotation'].browse(cr, SUPERUSER_ID, sale_order_id, context=context)
        else:
            return request.redirect('/shop')
        
        
       
        return request.website.render("website_industrylane.confirmation", {'order': order})
    

    #------------------------------------------------------
    # Edit
    #------------------------------------------------------

    @http.route(['/shop/add_product'], type='http', auth="user", methods=['POST'], website=True)
    def add_product(self, name=None, category=0, **post):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        if not name:
            name = _("New Product")
        product_obj = request.registry.get('product.product')
        product_id = product_obj.create(cr, uid, { 'name': name, 'public_categ_ids': category }, context=context)
        product = product_obj.browse(cr, uid, product_id, context=context)

        return request.redirect("/shop/product/%s?enable_editor=1" % slug(product.product_tmpl_id))

    @http.route(['/shop/change_styles'], type='json', auth="public")
    def change_styles(self, id, style_id):
        product_obj = request.registry.get('product.template')
        product = product_obj.browse(request.cr, request.uid, id, context=request.context)

        remove = []
        active = False
        for style in product.website_style_ids:
            if style.id == style_id:
                remove.append(style.id)
                active = True
                break

        style = request.registry.get('product.style').browse(request.cr, request.uid, style_id, context=request.context)

        if remove:
            product.write({'website_style_ids': [(3, rid) for rid in remove]})
        if not active:
            product.write({'website_style_ids': [(4, style.id)]})

        return not active

    @http.route(['/shop/change_sequence'], type='json', auth="public")
    def change_sequence(self, id, sequence):
        product_obj = request.registry.get('product.template')
        if sequence == "top":
            product_obj.set_sequence_top(request.cr, request.uid, [id], context=request.context)
        elif sequence == "bottom":
            product_obj.set_sequence_bottom(request.cr, request.uid, [id], context=request.context)
        elif sequence == "up":
            product_obj.set_sequence_up(request.cr, request.uid, [id], context=request.context)
        elif sequence == "down":
            product_obj.set_sequence_down(request.cr, request.uid, [id], context=request.context)

    @http.route(['/shop/change_size'], type='json', auth="public")
    def change_size(self, id, x, y):
        product_obj = request.registry.get('product.template')
        product = product_obj.browse(request.cr, request.uid, id, context=request.context)
        return product.write({'website_size_x': x, 'website_size_y': y})

    def order_lines_2_google_api(self, order_lines):
        """ Transforms a list of order lines into a dict for google analytics """
        ret = []
        for line in order_lines:
            product = line.product_id
            ret.append({
                'id': line.order_id and line.order_id.id,
                'sku': product.ean13 or product.id,
                'name': product.name or '-',
                'category': product.categ_id and product.categ_id.name or '-',
                'price': line.price_unit,
                'quantity': line.product_uom_qty,
            })
        return ret

    def order_2_return_dict(self, order):
        """ Returns the tracking_cart dict of the order for Google analytics basically defined to be inherited """
        return {
            'transaction': {
                'id': order.id,
                'affiliation': order.company_id.name,
                'revenue': order.amount_total,
                'tax': order.amount_tax,
                'currency': order.currency_id.name
            },
            'lines': self.order_lines_2_google_api(order.order_line)
        }

    @http.route(['/shop/tracking_last_order'], type='json', auth="public")
    def tracking_cart(self, **post):
        """ return data about order in JSON needed for google analytics"""
        cr, context = request.cr, request.context
        ret = {}
        sale_order_id = request.session.get('sale_last_order_id')
        if sale_order_id:
            order = request.registry['sale.quotation'].browse(cr, SUPERUSER_ID, sale_order_id, context=context)
            ret = self.order_2_return_dict(order)
        return ret

    @http.route(['/shop/get_unit_price'], type='json', auth="public", methods=['POST'], website=True)
    def get_unit_price(self, product_ids, add_qty, use_order_pricelist=False, **kw):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        products = pool['product.product'].browse(cr, uid, product_ids, context=context)
        partner = pool['res.users'].browse(cr, uid, uid, context=context).partner_id
        
        if use_order_pricelist:
            pricelist_id = request.session.get('sale_order_code_pricelist_id') or partner.property_product_pricelist.id
        else:
            pricelist_id = partner.property_product_pricelist.id
        prices = pool['product.pricelist'].price_rule_get_multi(cr, uid, [pricelist_id], [(product, add_qty, partner) for product in products], context=context)
        return {product_id: prices[product_id][pricelist_id][0] for product_id in product_ids}
    



# vim:expandtab:tabstop=4:softtabstop=4:shiftwidth=4:
