from openerp.osv import fields,osv
from openerp.tools.translate import _
from lxml import etree
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pdb


   
class sandv_product_template(osv.osv): 
    _inherit = 'product.template'


    _columns={
              
                'moq'  :  fields.float("MOQ", required=True),
                'moq_type':fields.selection([('min_qty','Min Qty'),('multiple_qty','Multiple Qty')],"MOQ Type",required=True),
                
                }
    
    _defaults = {
                 
                 'moq_type':'min_qty',
                 'moq': 1.0,
                 
                 }
    
    
#     def onchange_moq_type(self, cr, uid, ids, moq_type, context):
#         
# #         pdb.set_trace()
#         context = {}
# 
#         v = {}
#         d = {}
#         res = {}
# 
#         if moq_type:
#             
#         res = {'value':v, 'domain':d}
#         return res



sandv_product_template()