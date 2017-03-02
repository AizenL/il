# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

#-------------------------------------------------------------
#ENGLISH
#-------------------------------------------------------------
#from tools.translate import _
from openerp.tools.translate import _
import pdb

ones = {
   0: '', 1:'One', 2:'Two', 3:'Three', 4:'Four', 5:'Five', 6:'Six', 7:'Seven', 8:'Eight', 9:'Nine',
   10:'Ten', 11:'Eleven', 12:'Twelve', 13:'Thirteen', 14:'Fourteen', 15:'Fifteen', 16:'Sixteen',
   17:'Seventeen', 18:'Eighteen', 19:'Nineteen', 20:'Twenty',
}

tens = {
   1: 'Ten', 2:'Twenty', 3:'Thirty',4:'Forty', 5:'Fifty', 6:'Sixty', 7:'Seventy', 8:'Eighty', 9:'Ninety'
}

def _100_to_text_in(chiffre):
   if chiffre in ones:
      return ones[chiffre]
   else:
      if chiffre%10>0:
         return tens[chiffre / 10]+'-'+ones[chiffre % 10]
      else:
         return tens[chiffre / 10]


def _1000_to_text_in(chiffre):
   d = _100_to_text_in(chiffre % 100)
   d2 = chiffre/100
   if d2>0:
      return ones[d2]+' Hundred '+d
   else:
      return d

def _10000_to_text_in(chiffre):
   if chiffre==0:
      return 'Zero'
   part1 = _1000_to_text_in(chiffre % 1000)
   part2 = (int(str(chiffre/1000)[-2:])>0 and _1000_to_text_in(int(str(chiffre/1000)[-2:]))+' Thousand') or ''
   part3 = ((int(str(chiffre/100000)[-2:]))>1 and _1000_to_text_in(int(str(chiffre/100000)[-2:]))+' Lakhs') or ((int(str(chiffre/100000)[-2:]))>0 and _1000_to_text_in(int(str(chiffre/100000)[-2:]))+' Lakh') or ''
   part4 = ((int(str(chiffre/10000000)[-2:]))>1 and _1000_to_text_in(int(str(chiffre/10000000)[-2:]))+' Crores') or ((int(str(chiffre/10000000)[-2:]))>0 and _1000_to_text_in(int(str(chiffre/10000000)[-2:]))+' Crore') or ''
   if (part2 or part3 or part4) and part1:
      part1 = ' '+part1
   if (part3 or part4) and part2:
      part2 = ' '+part2
   if part4 and part3:
      part3 = ' '+part3
   return part4+part3+part2+part1


def amount_to_text(number, currency,sub_currency):
#   pdb.set_trace()
   units_number = int(number)
   units_name = currency
#   if units_number > 1:
#      units_name += '.'
   units = _10000_to_text_in(units_number)
   units = units_number and '%s %s' % (units_name, units) or ''
   
   
   cents_number = int(number * 100) % 100
#   cents_name = (cents_number > 1) and '& Paise' or '& Paisa'
   cents_name = ' and ' 
   cents = _100_to_text_in(cents_number)
   cents = cents_number and '%s %s' % (cents_name, cents + ' ' + sub_currency) or '' 
   
   if units and cents:
      cents = ' '+cents
      
   return units + cents+' only.'


#-------------------------------------------------------------
# Generic functions
#-------------------------------------------------------------

_translate_funcs = {'en' : amount_to_text}
    
#TODO: we should use the country AND language (ex: septante VS soixante dix)
#TODO: we should use en by default, but the translation func is yet to be implemented
def amount_to_text(nbr, lang='en', currency='euro', sub_currency='cents'):
    """
    Converts an integer to its textual representation, using the language set in the context if any.
    Example:
        1654: thousands six cent cinquante-quatre.
    """
    from openerp import netsvc
#    if nbr > 10000000:
#        netsvc.Logger().notifyChannel('translate', netsvc.LOG_WARNING, _("Number too large '%d', can not translate it"))
#        return str(nbr)
    
    if not _translate_funcs.has_key(lang):
        netsvc.Logger().notifyChannel('translate', netsvc.LOG_WARNING, _("no translation function found for lang: '%s'" % (lang,)))
        #TODO: (default should be en) same as above
        lang = 'en'
    return _translate_funcs[lang](abs(nbr), currency, sub_currency)

if __name__=='__main__':
    from sys import argv
    
    lang = 'nl'
    if len(argv) < 2:
        for i in range(1,200):
            print i, ">>", int_to_text(i, lang)
        for i in range(200,999999,139):
            print i, ">>", int_to_text(i, lang)
    else:
        print int_to_text(int(argv[1]), lang)

