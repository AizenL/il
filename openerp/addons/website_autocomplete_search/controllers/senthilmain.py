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
        #pdb.set_trace()
#         product_ids = product_obj.search(cr, uid, domain, order='website_published desc, website_sequence desc', context=context)
#         products = [x.name for x in product_obj.browse(cr, uid, product_ids, context=context)]
#         print products
        domain +=[('name','ilike',post['key_in_data'])]
        #print domain
        product_ids = product_obj.search(cr, uid, domain, order='website_published desc, website_sequence desc', context=context)

        products = [{'label':x.name, 'category':x.categ_id.name} for x in product_obj.browse(cr, uid, product_ids, context=context)]
        return products


# vim:expandtab:tabstop=4:softtabstop=4:shiftwidth=4:

