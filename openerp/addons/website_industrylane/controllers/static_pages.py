# -*- coding: utf-8 -*-
import logging
import werkzeug
import pdb
import json
from openerp import SUPERUSER_ID
from openerp import http
from openerp import tools
from openerp.http import request
from openerp.tools.translate import _
from openerp.addons.website.models.website import slug
from openerp.addons.web.controllers.main import login_redirect
from unicodedata import category
import base64
from openerp.addons.web.http import request
import random



class static_pages(http.Controller):
    
    def _get_search_domain(self, search, category, attrib_values):
        domain = request.website.sale_product_domain()
       
        if search:
            for srch in search.split(" "):
                domain += [
                    '|', '|', '|', ('name', 'ilike', srch), ('description', 'ilike', srch),
                    ('description_sale', 'ilike', srch), ('product_variant_ids.default_code', 'ilike', srch)]

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
                    domain += [('attribute_line_ids.value_ids', 'in', ids)]
                    attrib = value[0]
                    ids = [value[1]]
            if attrib:
                domain += [('attribute_line_ids.value_ids', 'in', ids)]

        return domain
    

     
    @http.route(['/shop/update_get_your_quote'], type='json', auth="public", methods=['POST'], website=True)
    def update_get_your_quote(self,product_id=None, **post):
        cr, uid, context,  registry = request.cr, request.uid, request.context, request.registry
        
        environ = request.httprequest.headers.environ

        get_quote_obj = registry.get('get.your.quote')
        qpl_obj = registry.get('quote.product.list')
        #request.session['get_quote_id'] = None
        random_number = random.randint(0,999999999999)
        #
        get_quote_id = request.session.get('get_quote_id')
        values = {
                  #'product_list': product_id,
                  'identification': random_number
              }
        if not get_quote_id:   
            get_quote_id = get_quote_obj.create(cr, SUPERUSER_ID, values, context=context)
            if get_quote_id:   
                request.session['get_quote_id'] = get_quote_id        
                
        checkDuplicateid = qpl_obj.search(cr, SUPERUSER_ID, [('get_your_quote', '=', get_quote_id),('product_id', '=', product_id)], context=context)
        #pdb.set_trace() 
        if get_quote_id and not checkDuplicateid :
                values = {
                      'product_id': product_id,
                      'get_your_quote': get_quote_id
                  }            
                qpl_obj.create(cr, SUPERUSER_ID, values, context=context)
        
        
        if checkDuplicateid :
            value = "Duplicate"
        else:
            value = 'ok'
        return value    
        
    def get_product_value_ids(self, category):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        template_obj = pool['product.template']
        search=''
        attrib_values=''
        domain = self._get_search_domain(search, category, attrib_values)
        product_ids = template_obj.search(cr, uid, domain, context=context)
        products = template_obj.browse(cr, uid, product_ids, context=context)
        #pdb.set_trace()
        return products
        
    @http.route([
        '/about'
    ], type='http', auth="public", website=True)
    def about_us(self, page=0, category=None, search='', **post):
        
        return request.website.render("website_industrylane.aboutus")
    
    @http.route([
        '/contact_us'
    ], type='http', auth="public", website=True)
    def contact_us(self, page=0, category=None, search='', **post):
        
        return request.website.render("website_industrylane.contact_us")    
    
    @http.route('/home_customer_form', auth="public", methods=['POST'],website=True, type='http')
    def home_customer_form(self, **kwargs):
#         result = {}
#         data = cgi.FieldStorage()
#         output = data.getvalue("email")
#         result['a'] = output
        _TECHNICAL = ['show_info', 'view_from', 'view_callback']  # Only use for behavior, don't stock it
        _BLACKLIST = ['id', 'create_uid', 'create_date', 'write_uid', 'write_date', 'user_id', 'active']  # Allow in description
        _REQUIRED = ['contact_name', 'partner_name','mobile', 'email_from',]  # Could be improved including required from model
        
        post_file = []  # List of file to add to ir_attachment once we have the ID
        post_description = []  # Info to add after the message
        values = {}
        
        values['medium_id'] = request.registry['ir.model.data'].xmlid_to_res_id(request.cr, SUPERUSER_ID, 'crm.crm_medium_website')
        values['section_id'] = request.registry['ir.model.data'].xmlid_to_res_id(request.cr, SUPERUSER_ID, 'website.salesteam_website_sales')        
        
        for field_name, field_value in kwargs.items():
            if hasattr(field_value, 'filename'):
                post_file.append(field_value)
            elif field_name in request.registry['crm.lead']._fields and field_name not in _BLACKLIST:
                values[field_name] = field_value
            elif field_name not in _TECHNICAL:  # allow to add some free fields or blacklisted field like ID
                post_description.append("%s: %s" % (field_name, field_value))
                        
        if "name" not in kwargs and values.get("partner_name"):  # if kwarg.name is empty, it's an error, we cannot copy the contact_name
            values["name"] = values.get("partner_name")
            
        #values["name"] = values.get("partner_name")
        #values["contact_name"] = values.get("name")
        # fields validation : Check that required field from model crm_lead exists
        error = set(field for field in _REQUIRED if not values.get(field))
        
        if error:
            values = dict(values, error=error, kwargs=kwargs.items())
            return values
        
            #description is required, so it is always already initialized
            
            if kwargs.get("show_info"):
                post_description = []
                environ = request.httprequest.headers.environ
                post_description.append("%s: %s" % ("IP", environ.get("REMOTE_ADDR")))
                post_description.append("%s: %s" % ("USER_AGENT", environ.get("HTTP_USER_AGENT")))
                post_description.append("%s: %s" % ("ACCEPT_LANGUAGE", environ.get("HTTP_ACCEPT_LANGUAGE")))
                post_description.append("%s: %s" % ("REFERER", environ.get("HTTP_REFERER")))
                values['description'] += dict_to_str(_("Environ Fields: "), post_description)

        lead_id = self.create_lead(request, dict(values, user_id=False), kwargs)
       
        values.update(lead_id=lead_id)
        if lead_id:
            for field_value in post_file:
                attachment_value = {
                    'name': field_value.filename,
                    'res_name': field_value.filename,
                    'res_model': 'crm.lead',
                    'res_id': lead_id,
                    'datas': base64.encodestring(field_value.read()),
                    'datas_fname': field_value.filename,
                }
                request.registry['ir.attachment'].create(request.cr, SUPERUSER_ID, attachment_value, context=request.context)
        values="Thank You! Your Form Has Been Submitted Successfully.We'll be in touch shortly."
                
        #return self.home_customer_form_response(values, kwargs)
        return values
    
     
    def home_customer_form_response(self, values, kwargs):
        values = self.preRenderThanks(values, kwargs)
        #return request.website.render(kwargs.get("view_callback", "website_industrylane.home_products"), values)
        return request.redirect("/shop/status_msg/1")
                                    
    @http.route([
        '/special_order_quotes'
    ], type='http', auth="public", website=True)
    def special_order_quotes(self, **kwargs):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
       
        #category_obj = pool['product.public.category']
#         category_obj = pool['product.public.category']
#         category_ids = category_obj.search(cr, uid, [('parent_id', '=', False)], context=context)
#         categs = category_obj.browse(cr, uid, category_ids, context=context)
        #pdb.set_trace()
        get_quote_id = request.session.get('get_quote_id')

        get_quote_obj =  pool['get.your.quote']
        gyu_obj_id = get_quote_obj.search(cr, SUPERUSER_ID, [('id', '=',get_quote_id)], context=context)
        products = get_quote_obj.browse(cr, SUPERUSER_ID, gyu_obj_id, context=context)
        #pdb.set_trace()        
        values = {
        'products': products,
        }   
        for field in ['name', 'partner_name','contact_name', 'email_from', 'mobile','description']:
            if kwargs.get(field):
                values[field] = kwargs.pop(field)
        values.update(kwargs=kwargs.items())
        #
      
        #pdb.set_trace()
            
        return request.website.render("website_industrylane.special_order_quotes", values)
    
 
    
    @http.route(['/special_order_quotes_ac'], type='http', auth="public", website=True)
    def special_order_quotes_ac(self, **kwargs):
        
        def dict_to_str(title, dictvar):
            ret = "\n\n%s" % title
            for field in dictvar:
                ret += "\n%s" % field
            return ret
        
        _TECHNICAL = ['show_info', 'view_from', 'view_callback']  # Only use for behavior, don't stock it
        _BLACKLIST = ['id', 'create_uid', 'create_date', 'write_uid', 'write_date', 'user_id', 'active']  # Allow in description
        _REQUIRED = ['name', 'partner_name','contact_name', 'email_from', 'mobile', 'description',]  # Could be improved including required from model

        post_file = []  # List of file to add to ir_attachment once we have the ID
        post_description = []  # Info to add after the message
        values = {}
    
        
                
        values['medium_id'] = request.registry['ir.model.data'].xmlid_to_res_id(request.cr, SUPERUSER_ID, 'crm.crm_medium_website')
        values['section_id'] = request.registry['ir.model.data'].xmlid_to_res_id(request.cr, SUPERUSER_ID, 'website.salesteam_website_sales')

       
        for field_name, field_value in kwargs.items():
            if hasattr(field_value, 'filename'):
                post_file.append(field_value)
            elif field_name in request.registry['crm.lead']._fields and field_name not in _BLACKLIST:
                values[field_name] = field_value
            elif field_name not in _TECHNICAL:  # allow to add some free fields or blacklisted field like ID
                post_description.append("%s: %s" % (field_name, field_value))

       
         
        if "name" not in kwargs and values.get("contact_name"):  # if kwarg.name is empty, it's an error, we cannot copy the contact_name
            values["name"] = values.get("contact_name")

        # fields validation : Check that required field from model crm_lead exists
        error = set(field for field in _REQUIRED if not values.get(field))
        #pdb.set_trace()
        if error:
            values = dict(values, error=error, kwargs=kwargs.items())
            return request.website.render(kwargs.get("view_from", "website_industrylane.error"), values)
        
            #description is required, so it is always already initialized
            if post_description:
                values['description'] += dict_to_str(_("Custom Fields: "), post_description)
            
            if kwargs.get("show_info"):
                post_description = []
                environ = request.httprequest.headers.environ
                post_description.append("%s: %s" % ("IP", environ.get("REMOTE_ADDR")))
                post_description.append("%s: %s" % ("USER_AGENT", environ.get("HTTP_USER_AGENT")))
                post_description.append("%s: %s" % ("ACCEPT_LANGUAGE", environ.get("HTTP_ACCEPT_LANGUAGE")))
                post_description.append("%s: %s" % ("REFERER", environ.get("HTTP_REFERER")))
                values['description'] += dict_to_str(_("Environ Fields: "), post_description)

        lead_id = self.create_lead(request, dict(values, user_id=False), kwargs)
       
        values.update(lead_id=lead_id)
        if lead_id:
            for field_value in post_file:
                attachment_value = {
                    'name': field_value.filename,
                    'res_name': field_value.filename,
                    'res_model': 'crm.lead',
                    'res_id': lead_id,
                    'datas': base64.encodestring(field_value.read()),
                    'datas_fname': field_value.filename,
                }
                request.registry['ir.attachment'].create(request.cr, SUPERUSER_ID, attachment_value, context=request.context)
                
        request.session['get_quote_id'] = None
        return self.get_order_response(values, kwargs)    
    
    def get_order_response(self, values, kwargs):
        values = self.preRenderThanks(values, kwargs)
        return request.website.render(kwargs.get("view_callback", "website_industrylane.order_thanks"), values)
           
    @http.route([
        '/supplier'
    ], type='http', auth="public", website=True)
    def supplier(self, **kwargs):
        values = {}
        for field in ['company_name', 'street', 'zip', 'contact_person','product_category','product_name', 'email', 'nature_of_buisness','mobile']:
            if kwargs.get(field):
                values[field] = kwargs.pop(field)
        values.update(kwargs=kwargs.items())
        return request.website.render("website_industrylane.supplier", values)    
    
    def _get_supplier_files_fields(self):
        return ['ufile']
        
    @http.route(['/supplier_ac'], type='http', auth="public", website=True)
    def supplier_ac(self, **kwargs):
        def dict_to_str(title, dictvar):
            ret = "\n\n%s" % title
            for field in dictvar:
                ret += "\n%s" % field
            return ret
       
        #pdb.set_trace()
                
        _TECHNICAL = ['show_info', 'view_from', 'view_callback']  # Only use for behavior, don't stock it
        _BLACKLIST = ['id', 'create_uid', 'create_date', 'write_uid', 'write_date']  # Allow in description
        _REQUIRED = ['company_name', 'street', 'zip', 'contact_person','nature_of_buisness','email', 'mobile']  # Could be improved including required from model

        post_file = []  # List of file to add to ir_attachment once we have the ID
        post_description = []  # Info to add after the message
        values = {}
        
       # values['medium_id'] = request.registry['ir.model.data'].xmlid_to_res_id(request.cr, SUPERUSER_ID, 'crm.crm_medium_website')
       # values['section_id'] = request.registry['ir.model.data'].xmlid_to_res_id(request.cr, SUPERUSER_ID, 'website.salesteam_website_sales')

        for field_name, field_value in kwargs.items():
            if hasattr(field_value, 'filename'):
                post_file.append(field_value)
            elif field_name in request.registry['potential.supplier']._fields and field_name not in _BLACKLIST:
                values[field_name] = field_value
            elif field_name not in _TECHNICAL:  # allow to add some free fields or blacklisted field like ID
                post_description.append("%s: %s" % (field_name, field_value))

#         if "name" not in kwargs and values.get("company_name"):  # if kwarg.name is empty, it's an error, we cannot copy the contact_name
#             values["name"] = values.get("company_name")
        # fields validation : Check that required field from model crm_lead exists
        error = set(field for field in _REQUIRED if not values.get(field))

        if error:
            values = dict(values, error=error, kwargs=kwargs.items())
            return request.website.render(kwargs.get("view_from", "website_industrylane.error"), values)
        
        
        lead_id = self.create_res_partner(request, dict(values, user_id=False), kwargs)
       
        values.update(lead_id=lead_id)
        if lead_id:
            for field_value in post_file:
                attachment_value = {
                    'name': field_value.filename,
                    'res_name': field_value.filename,
                    'res_model': 'potential.supplier',
                    'res_id': lead_id,
                    'datas': base64.encodestring(field_value.read()),
                    'datas_fname': field_value.filename,
                }
                attach_id = request.registry['ir.attachment'].create(request.cr, SUPERUSER_ID, attachment_value, context=request.context)
#         values['attachments'] = attach_id
        lead_browse = request.registry['potential.supplier'].browse(request.cr, SUPERUSER_ID, lead_id)
       
        lead_browse.write({
                        'attachments': [(6,0,[attach_id])]
                    })
#             for field_value in post_file:
#                 attachment_value = {
#                     'name': field_value.filename,
#                     'res_name': field_value.filename,
#                     'res_model': 'res.partner',
#                     'res_id': lead_id,
#                     'datas': base64.encodestring(field_value.read()),
#                     'datas_fname': field_value.filename,
#                 }
#                 request.registry['ir.attachment'].create(request.cr, SUPERUSER_ID, attachment_value, context=request.context)
        values="Thank You! Your Supplier Registration Form Has Been Submitted Successfully.We'll be in touch shortly."
        return values
        #return self.get_contactus_response(values, kwargs)    
        
    def create_res_partner(self, request, values, kwargs):
        """ Allow to be overrided """
        cr, context = request.cr, request.context
        return request.registry['potential.supplier'].create(cr, SUPERUSER_ID, values, context=dict(context, mail_create_nosubscribe=True))
                           
    def get_contactus_response(self, values, kwargs):
        values = self.preRenderThanks(values, kwargs)
        return request.website.render(kwargs.get("view_callback", "website_industrylane.contactus_thanks"), values)
    
    def preRenderThanks(self, values, kwargs):
        """ Allow to be overrided """
        company = request.website.company_id
        return {
            'google_map_url': self.generate_google_map_url(company.street, company.city, company.zip, company.country_id and company.country_id.name_get()[0][1] or ''),
            '_values': values,
            '_kwargs': kwargs,
        }    
    def create_lead(self, request, values, kwargs):
        """ Allow to be overrided """
        cr, context = request.cr, request.context
        return request.registry['crm.lead'].create(cr, SUPERUSER_ID, values, context=dict(context, mail_create_nosubscribe=True))
            
     
     
    @http.route([
        '/customer'
    ], type='http', auth="public", website=True)
    def customer(self, page=0, category=None, search='', **post):
        
        return request.website.render("website_industrylane.customer")    

    def generate_google_map_url(self, street, city, city_zip, country_name):
        url = "http://maps.googleapis.com/maps/api/staticmap?center=%s&sensor=false&zoom=8&size=298x298" % werkzeug.url_quote_plus(
            '%s, %s %s, %s' % (street, city, city_zip, country_name)
        )
        return url    