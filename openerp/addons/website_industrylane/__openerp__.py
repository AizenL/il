{
    'name': 'Industrylane eCommerce',
    'category': 'Website',
    'summary': 'Website Portal Industrylane',
    'website': 'industrylane.com',
    'version': '1.0',
    'description': """
OpenERP E-Commerce
==================

        """,
    'author': 'OpenERP SA',
    #'depends': ['website', 'sale', 'payment','website_sale','product_pre_module'],
    'depends'    : [ 'product_pre_module' ],
    'data': [
#         'data/data.xml',
#         'views/views.xml',
#         'views/templates.xml',
#         'views/payment.xml',
#         'views/sale_order.xml',
#         'security/ir.model.access.csv',
#         'security/website_sale.xml',
      
          'views/products_template.xml',
          'views/add_to_cart_template_view.xml',    
          'views/custom_template.xml',
          'views/special_order_quotes.xml'
    ],
    'demo': [
#         'data/demo.xml',
    ],
    'qweb': ['static/src/xml/*.xml'],
    'installable': True,
    'application': True,
}
