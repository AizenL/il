##############################################################################
import time
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools.float_utils import float_compare
import pdb


class product_brand(osv.osv):

    _name = "product.brand"
   
    _columns = {
        'name': fields.char(string='Name'),
       
    }
    def create(self, cr, uid, vals, context=None):
        if vals.get('name', False):
            lower = vals.get('name', False)
            value = lower.upper()
            vals.update({'name': value})
        return super(product_brand, self).create(cr, uid, vals, context=context)
    def write(self, cr,ids, uid, vals, context=None):
        if vals.get('name', False):
            lower = vals.get('name', False)
            value = lower.upper()
            vals.update({'name': value})
        return super(product_brand, self).write(cr, ids,uid, vals,)
    _sql_constraints = [
        ('brand_uniq', 'unique(name)', 'Brand Name must be unique!'),]


class product_type(osv.osv):

    _name = "product.type"
   
    _columns = {
        'name': fields.char(string='Name'),
       
    }


class product_material(osv.osv):

    _name = "product.material"
   
    _columns = {
        'name': fields.char(string='Name'),
       
    }


class sandv_product(osv.osv):

    _inherit = "product.template"
   
    _columns = {
        'customer_part_noo': fields.char(string='Customer Part No'),
        'product_description': fields.char(string='Product Description'),
        'product_brand': fields.many2one('product.brand', 'Brand',required=True),
        'manufacturer_part_no': fields.char(string='Manufacturer Part No',required=False),
        'product_type': fields.many2one('product.type', 'Product Type'),
        'product_material': fields.many2one('product.material', 'Product Material'),
        'sandv_attribute_line_ids': fields.one2many('sandv.product.variant', 'product_tmpl_id', 'Product Attributes'),
    }

class sandv_product_variant(osv.osv):
    _name="sandv.product.variant"

    _columns={
    'product_tmpl_id': fields.many2one('product.template', 'Product Template', required=True, ondelete='cascade'),
    'attribute_id': fields.many2one('sandv_product.attribute', 'Attribute', required=True, ),
    'value_ids': fields.many2many('sandv_product.attribute.value', id1='line_id', id2='val_id', string='Product Attribute Value'),
    }
    # def _check_valid_attribute(self, cr, uid, ids, context=None):
    #     obj_pal = self.browse(cr, uid, ids[0], context=context)
    #     return obj_pal.value_ids <= obj_pal.attribute_id.value_ids

    # _constraints = [
    #     (_check_valid_attribute, 'Error ! You cannot use this attribute with the following value.', ['attribute_id'])
    # ]


class sandv_product_attribute(osv.osv):
    _name = "sandv_product.attribute"
    _description = "Product Attribute"
    _order = 'name'
    _columns = {
        'name': fields.char('Name', translate=True, required=True),
        'sandv_value_ids': fields.one2many('sandv_product.attribute.value', 'attribute_id', 'Values', copy=True),
    }
    def create(self, cr, uid, vals, context=None):
        if vals.get('name', False):
            lower = vals.get('name', False)
            value = lower.upper()
            vals.update({'name': value})


        return super(sandv_product_attribute, self).create(cr, uid, vals, context=context)
    def write(self, cr,ids, uid, vals, context=None):
        if vals.get('name', False):
            lower = vals.get('name', False)
            value = lower.upper()
            vals.update({'name': value})
        return super(sandv_product_attribute, self).write(cr, ids,uid, vals,)

    _sql_constraints = [
        ('sandv_product_attr_uniq', 'unique(name)', 'Product Attibute must be unique!'),
    ]


class sandv_product_attribute_value(osv.osv):
    _name = "sandv_product.attribute.value"
    _order = 'sequence'
    def name_get(self, cr, uid, ids, context=None):
        if context and not context.get('show_attribute', True):
            return super(sandv_product_attribute_value, self).name_get(cr, uid, ids, context=context)
        res = []
        for value in self.browse(cr, uid, ids, context=context):
            res.append([value.id, "%s: %s" % (value.attribute_id.name, value.name)])
        return res

    _columns = {
        'sequence': fields.integer('Sequence', help="Determine the display order"),
        'name': fields.char('Value', translate=True, required=True),
        'attribute_id': fields.many2one('sandv_product.attribute', 'Attribute', required=True, ondelete='cascade'),
        #'product_ids': fields.many2many('product.product', id1='att_id', id2='prod_id', string='Variants', readonly=True),
        #'price_extra': fields.function(_get_price_extra, type='float', string='Attribute Price Extra',
         #   fnct_inv=_set_price_extra,
          #  digits_compute=dp.get_precision('Product Price'),
           # help="Price Extra: Extra price for the variant with this attribute value on sale price. eg. 200 price extra, 1000 + 200 = 1200."),
        #'price_ids': fields.one2many('product.attribute.price', 'value_id', string='Attribute Prices', readonly=True),
    }
    
    def unlink(self, cr, uid, ids, context=None):
        ctx = dict(context or {}, active_test=False)
        product_ids = self.pool['product.product'].search(cr, uid, [('attribute_value_ids', 'in', ids)], context=ctx)
        if product_ids:
            raise osv.except_osv(_('Integrity Error!'), _('The operation cannot be completed:\nYou trying to delete an attribute value with a reference on a product variant.'))
        return super(sandv_product_attribute_value, self).unlink(cr, uid, ids, context=context)

    # def _check_suppliers_ids(self, cr, uid, ids, context=None):
    #     seller_ids1 = self.browse(cr, uid, ids)
    #     print "----------------------------------------------------------"
    #     print seller_ids1.seller_ids

    #     if not(seller_ids1.seller_ids):
    #         return False
    #     return True

    # _constraints = [
    #     (_check_suppliers_ids, 'Please add atlease one Supplier Details',
    #     ['seller_ids']),
    # ]



    # def _check_varient_ids(self, cr, uid, ids, context=None):
    #     seller_ids1 = self.browse(cr, uid, ids)
    #     print "----------------------------------------------------------"
    #     print seller_ids1.attribute_line_ids

    #     if not(seller_ids1.attribute_line_ids):
    #         return False
    #     return True

    # _constraints = [
    #     (_check_suppliers_ids, 'Please add atleast one Supplier Details',
    #     ['seller_ids']),
    #     (_check_varient_ids, 'Please add atleast one Varient Details',
    #     ['attribute_line_ids']),
    # ]


