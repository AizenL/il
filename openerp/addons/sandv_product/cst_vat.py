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

class cst_vat(osv.osv):
	_name="cst.vat"
	_columns={
			'cst' :fields.float("CST/VAT %"),
            'entery_tax':fields.float("Entery Tax %"),
            'cuurent_tax':fields.float('Active'),


	}