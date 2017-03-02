# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields, api
from _dbus_bindings import String
import random
from openerp.exceptions import ValidationError
from twisted.application.strports import _DEFAULT
from matplotlib.mathtext import Char



class product_template(models.Model):
	_inherit = 'product.template'



	pandf_value = fields.Float(string = 'Packing and Forwarding')
	freight_value = fields.Float(string = 'Freight')
	insurance_value = fields.Float(string = 'Insurance')
	excise_value = fields.Float(string = 'Excise Value')
	vat_value = fields.Float(string = 'VAT Value')




