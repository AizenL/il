import time
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools.float_utils import float_compare
import pdb



class stock_landed_cost_inherit(osv.osv):
    _inherit = "stock.landed.cost"

    _columns = {
        'note': fields.text('Note'),
    }



