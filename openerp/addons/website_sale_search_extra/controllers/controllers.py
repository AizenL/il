# -*- coding: utf-8 -*-
from openerp import http
from openerp.http import request
#import redis

#r = redis.StrictRedis(host='localhost', port=6379, db=0)

class WebsiteSaleSearchExtra(http.Controller):

    def _get_search_domain(self, search):
        # TODO: add category and attributes
        domain = request.website.sale_product_domain()
        if search:
            for srch in search.split(" "):
                domain += [
                    '|', '|', '|', '|', ('name', 'ilike', srch), ('description', 'ilike', srch),
                    ('description_sale', 'ilike', srch), ('product_variant_ids.default_code', 'ilike', srch),
                    ('website_description', 'ilike', srch),
                ]
        return domain

    @http.route('/shop/search', auth='public',search='', type='json', website=True)
    def search(self, **post):
        context = request.context
        search = post['search']
        domain = self._get_search_domain(search)

        product_obj = http.request.env['product.template']
        product_count = product_obj.with_context(context).search_count(domain)
        products = product_obj.with_context(context).search(domain)

        data = []
        for product in products:
            data.append({
                'name': product.name,
                'description': product.description_sale,
                'image': product.image_medium,
                'url': product.website_url
            })

        return {
            'status': 'ok',
            'data': data
        }