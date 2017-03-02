# -*- coding: utf-8 -*-
import werkzeug

from openerp import SUPERUSER_ID
from openerp import http
from openerp.http import request
from openerp.tools.translate import _
from openerp.addons.website.models.website import slug
from openerp.addons.web.controllers.main import login_redirect
import pdb
class website_sale(http.Controller):

    @http.route(['/shop/get_products'], type='json', auth="public", website=True)
    def get_products(self, page=0, category=None, search='', **post):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        domain = request.website.sale_product_domain()
        
        if search:
            for srch in search.split(" "):
                domain += ['|', '|', '|', ('name', 'ilike', srch), ('description', 'ilike', srch),
                    ('description_sale', 'ilike', srch), ('product_variant_ids.default_code', 'ilike', srch)]
        if category:
            domain += [('public_categ_ids', 'child_of', int(category))]
        
        attrib_list = request.httprequest.args.getlist('attrib')
        attrib_values = [map(int,v.split("-")) for v in attrib_list if v]
        attrib_set = set([v[1] for v in attrib_values])
        
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
                    domain += [('attribute_line_ids.value_ids', 'in', ids)]
                    attrib = value[0]
                    ids = [value[1]]
            if attrib:
                domain += [('attribute_line_ids.value_ids', 'in', ids)]
        product_obj = pool.get('product.template')
        product_cat_obj = pool.get('product.public.category')
        key_in_value = post['key_in_data']
        domain +=[('name','ilike',key_in_value)]

        product_ids = product_obj.search(cr, uid, domain, order='website_published desc, website_sequence desc', context=context)

#        products = [{'label':x.name, 'category':x.categ_id.name} for x in product_obj.browse(cr, uid, product_ids, context=context)]

        pub_cat_ids = set([x.public_categ_ids.id for x in product_obj.browse(cr, uid, product_ids, context=context)])
        cat_ids = filter(None,pub_cat_ids)
        products = [{'category':x.id,'label': key_in_value + ' in '+ x.name,'parent_name':x.parent_id.name} for  x in product_cat_obj.browse(cr,uid,cat_ids)]
        #pdb.set_trace()
        #products.append({'category': 5001, 'parent_name': 'All', 'label': 'search in Categories'})
        products.append({'category': 5002, 'parent_name': 'All', 'label': 'search in Brands'})
        #products.append({'category': 5003, 'parent_name': 'All', 'label': 'search in Products'})
        return products


# vim:expandtab:tabstop=4:softtabstop=4:shiftwidth=4:

