from openerp.osv import fields,osv
from openerp.tools.translate import _
from lxml import etree
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp import tools
from openerp import SUPERUSER_ID
from datetime import timedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
import openerp.addons.decimal_precision as dp
from openerp import workflow
from openerp.tools.float_utils import float_compare


import pdb
   
class sale_order(osv.osv): 
    
    _inherit = 'sale.order'
    _columns={
                'quotation_done'    :   fields.boolean("Approved"),
                'sale_quotation'    :   fields.boolean("Approved"),
                'quotation_id'      :   fields.many2one('sale.order','Quotation'),
                'sale_name'           :   fields.char('SO Number'),
                'state': fields.selection([ 
                    ('draft', 'Draft'),('approve', 'Waiting Approval'),
                    ('sent', 'Quotation Sent'),
                    ('cancel', 'Cancelled'),
                    ('waiting_date', 'Waiting Schedule'),
                    ('progress', 'Sales Confirmed'),
                    ('manual', 'Sale to Invoice'),
                    ('shipping_except', 'Shipping Exception'),
                    ('invoice_except', 'Invoice Exception'),
                    ('done', 'Done'),
                    ], 'Status', readonly=True, copy=False, help="Gives the status of the quotation or sales order.\
                      \nThe exception status is automatically set when a cancel operation occurs \
                      in the invoice validation (Invoice Exception) or in the picking list process (Shipping Exception).\nThe 'Waiting Schedule' status is set when the invoice is confirmed\
                       but waiting for the scheduler to run on the order date.", select=True),                
                   
                   
                   'parent_seq':fields.char("Parent Seq",size=256),
                   'parent_suffix':fields.char("Parent Suffix",size=256),
                   'child_next_no':fields.integer("child Next Number"),
                   
                   'lead_time':fields.date("Lead Time"),
                   
                   
                      
                      }
    
    
            
    _defaults = {'quotation_done':False,'sale_quotation':  True}
    
    def send_so_mail(self,cr,uid,ids,context=None):
        res={}
        if not context:
            context = {}
        state = context.get('state',False)
        print 'context',context
        type = context.get('type','')
        partners = ''
        user_obj = self.pool.get('res.users')
        user_id = user_obj.browse(cr,uid,uid) 
        mail_obj = self.pool.get('mail.mail')
        partner_obj = self.pool.get('res.partner')
        email_obj = self.pool.get('email.template')
        send_mail = False
        to_update = context.get('to_update',False)
        template = self.pool.get('ir.model.data').get_object(cr, uid,'bemco', 'bemco_customer_send_mail')
                         
        if template:    
            for case in self.browse(cr,uid,ids):        
                assert template._name == 'email.template'
                
                for case in self.browse(cr,uid,ids):
                    email_obj.write(cr, uid, [template.id], {'email_to':case.partner_id.email})
                                
                    mail_id = self.pool.get('email.template').send_mail(cr, uid, template.id, case.id, True, context=context)
                    mail_state = mail_obj.read(cr, uid, mail_id, ['state'], context=context)
                    if mail_state and mail_state['state'] == 'exception':
                        raise osv.except_osv(_("Cannot send email(SO): no outgoing email server configured.\nYou can configure it under Settings/General Settings."), case.partner_id.name)

        return True
    
#     def sale_approve(self,cr,uid,ids,context):
#         self.write(cr,uid,ids,{'state':'approve'})
#         return True  
           
#     def action_button_confirm(self, cr, uid, ids, context=None):
#         res = super(sale_order,self).action_button_confirm(cr, uid, ids, context)
# #         self.send_so_mail(cr,uid,ids,context) 
#         return res
    
    
    def vendor_portal_user(self,cr,uid,ids,context):
        portal_wizard = self.pool.get('portal.wizard')
        res_users = self.pool.get('res.users')
        portal_ids = self.pool.get('res.groups').search(cr, uid, [('is_portal', '=', True)])
        portal_id = portal_ids and portal_ids[0] or False
        val=[]
        vals={}
        portal_val = {}
        #############pdb.set_trace()
        po_brow = self.browse(cr,uid,ids)
#         delivery_dates_list = po_brow[0].delivery_dates_list
#         if len(delivery_dates_list.ids) > 1:
#             vals = {}
#             wiz_id = portal_wizard.create(cr,uid,vals,context)
#             portal_wizard.action_apply(cr,uid,[wiz_id],context)
# 
#             
#             
#         
#         else:
        for case in self.browse(cr,uid,ids):
#                 context.update({'active_id':case.partner_id.id,'active_ids':[case.partner_id.id]})
            portal_val.update({'in_portal':True,'partner_id': case.partner_id.id, 'email': case.partner_id.email})
        wiz_data = portal_wizard.onchange_portal_id(cr,uid,[],portal_id,context)
        if wiz_data:
           val = wiz_data.values()
        if val:
            vals.update(val[0])
            print vals
        vals.update({'portal_id':portal_id,'user_ids':[(0,0,portal_val)]})
        wiz_id = portal_wizard.create(cr,uid,vals,context)
        portal_wizard.action_apply(cr,uid,[wiz_id],context)
        user_id = res_users.search(cr,uid,[('partner_id','=',case.partner_id.id)])
#             context.update({'group_name':'vendor'})
        group_obj = self.pool.get("res.groups")
        
        #######pdb.set_trace()
        group_id = group_obj.search(cr,1,[('name','=','Sale for Portal Users'),('category_id.name','=','Sales')])
        users = user_id
        if group_id:
            group_obj.write(cr, 1, group_id, {'users': [(4, user) for user in users]}, context=context)

        res_users.write(cr,1,user_id,{},context)
        
        return 


    def action_button_confirm(self, cr, uid, ids, context=None):
        if not context:
            context = {}
#         assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        self.signal_workflow(cr, uid, ids, 'order_confirm')
#         if context.get('send_email'):
#             self.force_quotation_send(cr, uid, ids, context=context)
            
        for id in ids:
        #######pdb.set_trace()

            so_obj = self.pool.get("sale.order")
            so_obj.vendor_portal_user(cr,uid,ids,context) 
#             self.write(cr, uid, [id], {'state' : 'progress', 'validator' : uid})
            
        compose_ctx = dict(context,active_ids=ids)
        # Set your template search domain
        search_domain = [('name', '=', 'Sales Order - Send by Email (Portal)')]
        # Get template id
        template_id = self.pool['email.template'].search(cr, uid, search_domain, context=context)[0]
        # Compose email
        po_brow = self.browse(cr,uid,ids)
        
        kk =  self.pool['email.template'].send_mail(cr, uid, template_id, ids[0], force_send=True,raise_exception=False, context=compose_ctx)


        return True


    def sale_approve(self,cr,uid,ids,context = None):
        res = True
        self.write(cr,uid,ids,{'state':'approve'},context)
        return res
   
    def sale_order_create_old(self,cr,uid,ids,context = None):
        sale_id=False
        if not context:
            context = {}
        picking_obj = self.pool.get('stock.picking')
        sale_name = ''
        for case in self.browse(cr,uid,ids):         
            sale_name = str(case.sale_name or '')
            sale_id = self.search(cr,uid,[('quotation_id','=',case.id)])
#                 if not context.get('so_diplicate',''):
            if sale_id:
                raise osv.except_osv(_('Warning'),_('Access Denied! Sale Order Created for the quotation'))            
#             if case.partner_id.status != 'approved':
#                 raise osv.except_osv(_('Warning'),_('Access Denied! Customer is not Approved'))              
            if case.quotation_done and case.state=='draft':
                raise osv.except_osv(_('Warning'),_('Access Denied! Quotation Approved'))   
        context.update({'copy_sale':'copy sale','sale_name':sale_name})                         
        sale_id = self.copy(cr, uid, ids[0], {}, context=context)
        if sale_id:
#             super(sale_order,self).action_button_confirm(cr, uid, [sale_id], context)
            self.write(cr,uid,ids,{'quotation_done':True,'quotation_id':False})
            self.write(cr,uid,[sale_id],{'quotation_id':ids[0],'name':sale_name,'sale_name':case.name,'sale_quotation':False}) 
#             self.send_so_mail(cr,uid,[sale_id],context) 
            
#             result = self.bemco_sale_order_action(cr,uid,[sale_id],context)
            
        return self.bemco_sale_order_action(cr,uid,[sale_id],context)
    
    
    def sale_order_create(self,cr,uid,ids,context = None):
        sale_id=False
        if not context:
            context = {}
            
        picking_obj = self.pool.get('stock.picking')
        parent_so_brow = self.browse(cr,1,ids)
        parent_seq = parent_so_brow[0].parent_seq
        parent_suffix = parent_so_brow[0].parent_suffix
        child_next_no = parent_so_brow[0].child_next_no
        parent_so_id = ids[0]
        
        context.update({'parent_seq':parent_seq,'parent_suffix':parent_suffix,'child_next_no':child_next_no,'parent_so_id':parent_so_id})
                            
        sale_id = self.copy(cr, uid, ids[0], {}, context=context)
        
        if sale_id:
#             super(sale_order,self).action_button_confirm(cr, uid, [sale_id], context)
            self.write(cr,uid,ids,{'quotation_done':True,'quotation_id':False})
            self.write(cr,uid,[sale_id],{'quotation_id':ids[0],'sale_quotation':False}) 

        return self.bemco_sale_order_action(cr,uid,[sale_id],context)

    def return_form(self, cr, uid, ids, model, form, target, context=None):
        """ Depend on res_id record will be opened, else new form"""
        res= {}
        ir_model_data = self.pool.get('ir.model.data')
        try:
            compose_form_id = ir_model_data.get_object_reference(cr, uid, 'sale', form)[1]
        except ValueError:
            compose_form_id = False
        ctx = dict(context)
        res.update({
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': model,
            'view_type': 'form',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target'   : target,
            'context'  : ctx,
            'tag': 'reload',
           
        })
    
    
    def bemco_sale_order_action(self, cr, uid, ids, context=None):
#     def action_view_sales(self, cr, uid, ids, context=None):
        result = self.pool['ir.model.data'].xmlid_to_res_id(cr, uid, 'sale.action_orders', raise_if_not_found=True)
        result = self.pool['ir.actions.act_window'].read(cr, uid, [result], context=context)[0]
        result['domain'] = "[('id','in',[" + ','.join(map(str, ids)) + "])]"
        return result 
           
    def generate_sequence(self, cr, uid, today, case, context):
        year=False
        user_obj = self.pool.get('res.users')
        user = user_obj.browse(cr, uid, [uid])[0]
        
        context.update({'month':1})
        month = self.get_month(cr,uid,[],today,context)
        if len(month)<2:
            month = '0'+str(month)
        l=0
        cr.execute("select code from account_fiscalyear where date_start <= '" + today + "' and date_stop >='" + today + "'")
        code = cr.fetchone()
        if code:
            year = code[0]
        if not year:
            raise osv.except_osv(_('Warning!'), _('Please Create Fiscal Year For "%s"')%(today))
        
        format = str(year)+str(month)
     
        cr.execute("select sale_name from sale_order where sale_name like '" + format + "'|| '%' order by to_number(substr(sale_name,(length('" + format + "')+1)),'99999') desc limit 1")
        prev_format = cr.fetchone()
        
        if not prev_format:
            number = format + '0001' + "-SO"
        else:
            print "auto_gen",prev_format
            print prev_format[0][6:len(prev_format)-4]
            auto_gen = prev_format[0][6:len(prev_format)-4]
            number = format + str(int(auto_gen) + 1).zfill(4)+str('-SO')
        return number

    def get_month(self,cr,uid,ids,from_date,context):
        res=''
        f_month='' 
        f_month = datetime.fromtimestamp(time.mktime(time.strptime(from_date, "%Y-%m-%d")))
        res = tools.ustr(f_month.strftime('%B-%Y'))
        if context.get('month','')==1:
            res = tools.ustr(f_month.strftime('%m'))
        if context.get('year','')==1:
            res = tools.ustr(f_month.strftime('%Y'))
        if context.get('day','')==1:
            res = tools.ustr(f_month.strftime('%d'))            
        return res
        
    def create_old(self, cr, uid, vals, context=None):
        if not context:
            context={}
        today = time.strftime('%Y-%m-%d')
        res = super(sale_order,self).create(cr, uid, vals, context)
        vals.update({'quotation_done':False})
        copy_sale = context.get('copy_sale','')
#         sale_id = self.browse(cr,uid,res)
        context.update({"month":1})
        for case in self.browse(cr,uid,[res],context):
            sale_num = self.generate_sequence(cr, uid, today, case, context)
            sale = str(sale_num).replace('SO','BP')
            context.update({'so_diplicate':"duplicate"})
            vals['name'] = sale
            vals['sale_name'] = sale_num
            if copy_sale:
               vals['name'] = context.get('sale_name',False)
            self.write(cr,uid,[res],{'name':sale,'sale_name':sale_num},context)
#         res = super(sale_order,self).create(cr, uid, vals, context)
#         self.write(cr,uid,[res],{'name':sale,'sale_name':sale_num},context)
        return res
    
    def create(self, cr, uid, vals, context=None):
        if not context:
            context={}
        vals.update({'quotation_done':False})
        
        #####pdb.set_trace()
        
        if 'parent_so_id' not in context:
            seq_obj = self.pool.get('ir.sequence')
            sale_quotation_seq_id = seq_obj.get(cr,uid,'sandv.quotation')
            
            vals.update({'name': sale_quotation_seq_id})
        
        else:
            seq_obj = self.pool.get('ir.sequence')
            sale_order_seq_id = seq_obj.get(cr,uid,'sale.order')
            
            vals.update({'name': sale_order_seq_id})
        

            
            
        
#         if 'parent_seq' not in context:
#             seq_obj = self.pool.get('ir.sequence')
#             sale_order_seq_id = seq_obj.get(cr,uid,'sale.order')
#             seq_id = seq_obj.search(cr,uid,[('code','=','sale.order')])
#             if seq_id:
#                 seq_brow = seq_obj.browse(cr,uid,seq_id[0])
#                 
#                 so_suffix = seq_brow.suffix
#                 full_so_seq = sale_order_seq_id
#                 
#                 only_parent_seq = sale_order_seq_id.replace(so_suffix,'')
#                 child_next_no = 1
#                 
#                 vals.update({'parent_seq':only_parent_seq,'parent_suffix':so_suffix,'child_next_no':child_next_no,'name':full_so_seq})
#                 
#         else:
#             if 'parent_seq' in context and 'child_next_no' in context and 'parent_suffix' in context:
#                 parent_seq = context['parent_seq'] 
#                 child_next_no = context['child_next_no']
#                 parent_suffix = context['parent_suffix']
#                 
#                 child_seq = parent_seq + 'R' + str(child_next_no) + parent_suffix
#                 
#                 vals.update({'name':child_seq}) 
#                 
#                 if 'parent_so_id' in context:
#                     child_next_no_1 = child_next_no + 1
#                     parent_so = context['parent_so_id']
#                     self.write(cr,1,[parent_so],{'child_next_no':child_next_no_1 })
             
        
        ######pdb.set_trace()      
        res = super(sale_order,self).create(cr, uid, vals, context)

        
        return res

    
#     def write(self, cr, uid, ids, vals, context=None):
#         if not context:
#             context={}
#         picking_obj = self.pool.get('stock.picking')
#         for case in self.browse(cr,uid,ids):
# #             if case.quotation_done and case.state=='draft':
# #                 sale_id = self.search(cr,uid,[('quotation_id','=',case.id)])
# # #                 if not context.get('so_diplicate',''):
# #                 if sale_id:
# #                     raise osv.except_osv(_('Warning'),_('Access Denied! Sale Order Created for the quotation'))
#                    
# #             if vals.get('state','')!='draft':
# #                 sale_num = "QT"+str(int(case.name[2:]) + 1)
# #                 picking_id = picking_obj.search(cr,uid,[('origin','=',sale_num)])
# #                 if picking_id:
# #                    picking_obj.write(cr,uid,picking_id,{'origin':case.sale_name},context)   
#                                           
#         res = super(sale_order,self).write(cr, uid, ids,vals, context)
#         
#         return res
    
sale_order()



class sale_order_line(osv.osv): 
    
    _inherit = 'sale.order.line'
    _columns={
              
               
               'so_created':fields.boolean("SO created"),
               
#                'parent_qt_id':fields.related('order_id','quotation_id',type='many2one',relation='sale.order','Quotation'),
               
               'actual_qty_in_so':fields.float("Qty Sold"),
               'qty_in_so':fields.float("Qty to Sale"),
               
                      
                      }
    
    _defaults = {
                 
                 'so_created':False
                 }
    
    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        
        default.update({
                        
                        'actual_qty_in_so':0.0,
                        'qty_in_so':0.0,
                        'so_created' : False
                        })
        res = super(sale_order_line, self).copy(cr, uid, id, default, context=context) 
        return res

    

    def copy_data(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
#         bom_data = self.read(cr, uid, id, [], context=context)
        default.update({'actual_qty_in_so':0.0,
                        'qty_in_so':0.0,
                        'so_created' : False
                        })
        return super(sale_order_line, self).copy_data(cr, uid, id, default, context=context)


    def product_id_change_with_wh(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, warehouse_id=False, context=None):
        context = context or {}
        product_uom_obj = self.pool.get('product.uom')
        product_obj = self.pool.get('product.product')
        warning = {}
        #UoM False due to hack which makes sure uom changes price, ... in product_id_change
        res = self.product_id_change(cr, uid, ids, pricelist, product, qty=qty,
            uom=False, qty_uos=qty_uos, uos=uos, name=name, partner_id=partner_id,
            lang=lang, update_tax=update_tax, date_order=date_order, packaging=packaging, fiscal_position=fiscal_position, flag=flag, context=context)

        if not product:
            res['value'].update({'product_packaging': False})
            return res

        # set product uom in context to get virtual stock in current uom
        if 'product_uom' in res.get('value', {}):
            # use the uom changed by super call
            context = dict(context, uom=res['value']['product_uom'])
        elif uom:
            # fallback on selected
            context = dict(context, uom=uom)

        #update of result obtained in super function
        product_obj = product_obj.browse(cr, uid, product, context=context)
        res['value'].update({'product_tmpl_id': product_obj.product_tmpl_id.id, 'delay': (product_obj.sale_delay or 0.0)})


# MOQ code --------------------start

        if qty :
            browsed_rec = self.browse(cr,uid,ids)
            browsed_qty = browsed_rec.product_uom_qty
            browsed_product = browsed_rec.product_id
            
            if qty == browsed_qty or browsed_qty == False or (qty == 1.0 and browsed_qty == False ):
                res['value'].update({'product_uom_qty':product_obj.moq})
            
            
            else:
                res['value'].update({'product_uom_qty': qty})
        
            
#             pdb.set_trace()
            if qty != 1.0 and not browsed_rec:
                if product_obj.moq_type == 'multiple_qty':
                    if (qty % product_obj.moq) != 0:
                        warning_msg = _("Quantity should be multiple of Product MOQ") + "\n\n"
                
                        if warning_msg:
                            warning = {
                                       'title': _('Validation Error!'),
                                       'message' : warning_msg
                                    }
                            
                            
                    else:
                        res['value'].update({'product_uom_qty': qty})
                                
                    
                if product_obj.moq_type == 'min_qty' and qty < product_obj.moq:
                    warning_msg = _("Quantity should be more than minimun Product MOQ") + "\n\n"
            
                    if warning_msg:
                        warning = {
                                   'title': _('Validation Error!'),
                                   'message' : warning_msg
                                }
                        
                else:
                    res['value'].update({'product_uom_qty': qty})

                        
                
            



#             pdb.set_trace()
#             if product_obj.moq != 0.0 and ('product_uom_qty' in res['value'] and res['value']['product_uom_qty'] != product_obj.moq) and product_obj.moq_type == 'multiple_qty':
            if product_obj.moq != 0.0 and  product_obj.moq_type == 'multiple_qty':

                if (res['value']['product_uom_qty'] % product_obj.moq) != 0:
                    
                    if product_obj.moq != res['value']['product_uom_qty']:
                        warning_msg = _("Quantity should be multiple of Product MOQ") + "\n\n"
            
                        if warning_msg:
                            warning = {
                                       'title': _('Validation Error!'),
                                       'message' : warning_msg
                                    }
                            
                    res['value'].update({'product_uom_qty':product_obj.moq})
                    
                
                
                   
#                 else:
#                     
#                         
#                         res['value'].update({'product_uom_qty':qty})
#                         
                        
            elif product_obj.moq_type == 'min_qty' and res['value']['product_uom_qty'] < product_obj.moq:
                
                    warning_msg = _("Quantity should be more than minimun Product MOQ") + "\n\n"
            
                    if warning_msg:
                        warning = {
                                   'title': _('Validation Error!'),
                                   'message' : warning_msg
                                }

                    res['value'].update({'product_uom_qty':product_obj.moq})
                    
#             else:
#                  
#                 res['value'].update({'product_uom_qty':qty})
#                 
                
                    
    
# MOQ code --------------------end


        # Calling product_packaging_change function after updating UoM
        res_packing = self.product_packaging_change(cr, uid, ids, pricelist, product, qty, uom, partner_id, packaging, context=context)
        res['value'].update(res_packing.get('value', {}))
        warning_msgs = res_packing.get('warning') and res_packing['warning']['message'] or ''

        if product_obj.type == 'product':
            #determine if the product needs further check for stock availibility
            is_available = self._check_routing(cr, uid, ids, product_obj, warehouse_id, context=context)

            #check if product is available, and if not: raise a warning, but do this only for products that aren't processed in MTO
            if not is_available:
                uom_record = False
                if uom:
                    uom_record = product_uom_obj.browse(cr, uid, uom, context=context)
                    if product_obj.uom_id.category_id.id != uom_record.category_id.id:
                        uom_record = False
                if not uom_record:
                    uom_record = product_obj.uom_id
                compare_qty = float_compare(product_obj.virtual_available, qty, precision_rounding=uom_record.rounding)
                if compare_qty == -1:
                    warn_msg = _('You plan to sell %.2f %s but you only have %.2f %s available !\nThe real stock is %.2f %s. (without reservations)') % \
                        (qty, uom_record.name,
                         max(0,product_obj.virtual_available), uom_record.name,
                         max(0,product_obj.qty_available), uom_record.name)
                    warning_msgs += _("Not enough stock ! : ") + warn_msg + "\n\n"

        #update of warning messages
        if warning_msgs:
            warning = {
                       'title': _('Configuration Error!'),
                       'message' : warning_msgs
                    }
        res.update({'warning': warning})
        return res

    
    
    
    
    
    
    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context=None):
        context = context or {}
        lang = lang or context.get('lang', False)
        if not partner_id:
            raise osv.except_osv(_('No Customer Defined!'), _('Before choosing a product,\n select a customer in the sales form.'))
        warning = False
        product_uom_obj = self.pool.get('product.uom')
        partner_obj = self.pool.get('res.partner')
        product_obj = self.pool.get('product.product')
        partner = partner_obj.browse(cr, uid, partner_id)
        lang = partner.lang
        context_partner = context.copy()
        context_partner.update({'lang': lang, 'partner_id': partner_id})

        if not product:
            return {'value': {'th_weight': 0,
                'product_uos_qty': qty}, 'domain': {'product_uom': [],
                   'product_uos': []}}
        if not date_order:
            date_order = time.strftime(DEFAULT_SERVER_DATE_FORMAT)

        result = {}
        warning_msgs = ''
        product_obj = product_obj.browse(cr, uid, product, context=context_partner)


# MOQ code --------------------start
        
        if qty :
            browsed_rec = self.browse(cr,uid,ids)
            browsed_qty = browsed_rec.product_uom_qty
            browsed_product = browsed_rec.product_id
            
            if qty == browsed_qty or browsed_qty == False or (qty == 1.0 and browsed_qty == False ):
                result.update({'product_uom_qty':product_obj.moq})
            
            
            else:
                result.update({'product_uom_qty': qty})
        
            
#             pdb.set_trace()
            if qty != 1.0 and not browsed_rec:
                if product_obj.moq_type == 'multiple_qty':
                    if (qty % product_obj.moq) != 0:
                        warning_msg = _("Quantity should be multiple of Product MOQ") + "\n\n"
                
                        if warning_msg:
                            warning = {
                                       'title': _('Validation Error!'),
                                       'message' : warning_msg
                                    }
                            
                            
                    else:
                        result.update({'product_uom_qty': qty})
                                
                    
                if product_obj.moq_type == 'min_qty' and qty < product_obj.moq:
                    warning_msg = _("Quantity should be more than minimun Product MOQ") + "\n\n"
            
                    if warning_msg:
                        warning = {
                                   'title': _('Validation Error!'),
                                   'message' : warning_msg
                                }
                        
                else:
                    result.update({'product_uom_qty': qty})

        
            
#             #pdb.set_trace()
#             if product_obj.moq != 0.0 and ('product_uom_qty' in res['value'] and res['value']['product_uom_qty'] != product_obj.moq) and product_obj.moq_type == 'multiple_qty':
            if product_obj.moq != 0.0 and  product_obj.moq_type == 'multiple_qty':

                if (result['product_uom_qty'] % product_obj.moq) != 0:
                    
                    if product_obj.moq != result['product_uom_qty']:
                        warning_msg = _("Quantity should be multiple of Product MOQ") + "\n\n"
            
                        if warning_msg:
                            warning = {
                                       'title': _('Validation Error!'),
                                       'message' : warning_msg
                                    }
                            
                    result.update({'product_uom_qty':product_obj.moq})
                    
                
                
                   
#                 else:
#                     
#                         
#                         result.update({'product_uom_qty':qty})
#                         
                        
            elif product_obj.moq_type == 'min_qty' and result['product_uom_qty'] < product_obj.moq:
                
                    warning_msg = _("Quantity should be more than minimun Product MOQ") + "\n\n"
            
                    if warning_msg:
                        warning = {
                                   'title': _('Validation Error!'),
                                   'message' : warning_msg
                                }

                    result.update({'product_uom_qty':product_obj.moq})
                    
#             else:
#                  
#                 res['value'].update({'product_uom_qty':qty})
#                 


# MOQ code --------------------end





        uom2 = False
        if uom:
            uom2 = product_uom_obj.browse(cr, uid, uom)
            if product_obj.uom_id.category_id.id != uom2.category_id.id:
                uom = False
        if uos:
            if product_obj.uos_id:
                uos2 = product_uom_obj.browse(cr, uid, uos)
                if product_obj.uos_id.category_id.id != uos2.category_id.id:
                    uos = False
            else:
                uos = False

        fpos = False
        if not fiscal_position:
            fpos = partner.property_account_position or False
        else:
            fpos = self.pool.get('account.fiscal.position').browse(cr, uid, fiscal_position)

        if uid == SUPERUSER_ID and context.get('company_id'):
            taxes = product_obj.taxes_id.filtered(lambda r: r.company_id.id == context['company_id'])
        else:
            taxes = product_obj.taxes_id
        result['tax_id'] = self.pool.get('account.fiscal.position').map_tax(cr, uid, fpos, taxes, context=context)

        if not flag:
            result['name'] = self.pool.get('product.product').name_get(cr, uid, [product_obj.id], context=context_partner)[0][1]
            if product_obj.description_sale:
                result['name'] += '\n'+product_obj.description_sale
        domain = {}
        if (not uom) and (not uos):
            result['product_uom'] = product_obj.uom_id.id
            if product_obj.uos_id:
                result['product_uos'] = product_obj.uos_id.id
                result['product_uos_qty'] = qty * product_obj.uos_coeff
                uos_category_id = product_obj.uos_id.category_id.id
            else:
                result['product_uos'] = False
                result['product_uos_qty'] = qty
                uos_category_id = False
            result['th_weight'] = qty * product_obj.weight
            domain = {'product_uom':
                        [('category_id', '=', product_obj.uom_id.category_id.id)],
                        'product_uos':
                        [('category_id', '=', uos_category_id)]}
        elif uos and not uom: # only happens if uom is False
            result['product_uom'] = product_obj.uom_id and product_obj.uom_id.id
            result['product_uom_qty'] = qty_uos / product_obj.uos_coeff
            result['th_weight'] = result['product_uom_qty'] * product_obj.weight
        elif uom: # whether uos is set or not
            default_uom = product_obj.uom_id and product_obj.uom_id.id
            q = product_uom_obj._compute_qty(cr, uid, uom, qty, default_uom)
            if product_obj.uos_id:
                result['product_uos'] = product_obj.uos_id.id
                result['product_uos_qty'] = qty * product_obj.uos_coeff
            else:
                result['product_uos'] = False
                result['product_uos_qty'] = qty
            result['th_weight'] = q * product_obj.weight        # Round the quantity up

        if not uom2:
            uom2 = product_obj.uom_id
        # get unit price

        if not pricelist:
            warn_msg = _('You have to select a pricelist or a customer in the sales form !\n'
                    'Please set one before choosing a product.')
            warning_msgs += _("No Pricelist ! : ") + warn_msg +"\n\n"
        else:
            ctx = dict(
                context,
                uom=uom or result.get('product_uom'),
                date=date_order,
            )
            price = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist],
                    product, qty or 1.0, partner_id, ctx)[pricelist]
            if price is False:
                warn_msg = _("Cannot find a pricelist line matching this product and quantity.\n"
                        "You have to change either the product, the quantity or the pricelist.")

                warning_msgs += _("No valid pricelist line found ! :") + warn_msg +"\n\n"
            else:
                price = self.pool['account.tax']._fix_tax_included_price(cr, uid, price, taxes, result['tax_id'])
                result.update({'price_unit': price})
                if context.get('uom_qty_change', False):
                    values = {'price_unit': price}
                    if result.get('product_uos_qty'):
                        values['product_uos_qty'] = result['product_uos_qty']
                    return {'value': values, 'domain': {}, 'warning': False}
        if warning_msgs:
            warning = {
                       'title': _('Configuration Error!'),
                       'message' : warning_msgs
                    }
        return {'value': result, 'domain': domain, 'warning': warning}

    
    
    
    
    def onchange_qty_in_so(self, cr, uid, ids, qty_in_so, context):
        """
        onchange handler of onchange_qty_in_so.
        """
        
        ###pdb.set_trace()
        context = {}

        v = {}
        d = {}
        res = {}
        warning = {}
        msgalert = {}

        if qty_in_so:
        
        
            context.update({'qty_in_so':qty_in_so})
            
            so_lines_brow = self.browse(cr,uid,ids)
            
            p_qty_in_so = so_lines_brow[0].qty_in_so
            
    #             p_qty_in_so = p_qty_in_so + qty_in_so
            
            
# MOQ code --------------------start
            #pdb.set_trace()
            
            product_obj = self.pool.get("product.product")
            product_id = so_lines_brow[0].product_id.id
            product_obj = product_obj.browse(cr, uid, product_id)
            
            qty = qty_in_so
            
#             ####pdb.set_trace()
            if product_obj.moq != 0.0 and qty_in_so != product_obj.moq and product_obj.moq_type == 'multiple_qty':
                if (qty % product_obj.moq) != 0:
                    v['qty_in_so'] = 0.0
                    
#                     msgalert = {'title' : 'Warning', 'message': ('Quantity should be multiple of Product MOQ')}
                    
                    warning_msg = _("Quantity should be multiple of Product MOQ") + "\n\n"
                     
                    if warning_msg:
                        warning = {
                                   'title': _('Validation Error!'),
                                   'message' : warning_msg
                                }
                        
                        
                     
                        

# MOQ code --------------------end
            

            actual_qty_in_so = so_lines_brow[0].actual_qty_in_so
            self.write(cr, 1 , ids, {'qty_in_so':qty_in_so})
            
            remaining_qty = so_lines_brow[0].product_uom_qty - actual_qty_in_so
            if qty_in_so > remaining_qty:
                
#                 msgalert = {'title' : 'Warning', 'message': ("Quantity to Sale, Cannot exceed Quotation Quantity [(Quantity to Sale) = (Quantity) - (Sale Quantity)] ")}
                warning_msg = _("Quantity to Sale, Cannot exceed Quotation Quantity [(Quantity to Sale) = (Quantity) - (Sale Quantity)] ") + "\n\n"
              
                if warning_msg:
                    warning = {
                               'title': _('Validation Error!'),
                               'message' : warning_msg
                            }
      
        
                
                v['qty_in_so'] = remaining_qty
                self.write(cr, 1 , ids, {'qty_in_so':msgalert})
        
            
#             warning_msgs += _("Not enough stock ! : ") + warn_msg + "\n\n"
        
        #pdb.set_trace()
        res = {'value':v, 'domain':d, 'warning' : warning}
        return res

    
    
    def default_get(self, cr, uid, fields, context=None):
        data = super(sale_order_line, self).default_get(cr, uid, fields, context=context)
            
        data.update({'qty_in_so':1.0})

        return data

    
sale_order_line()    





 
class sandv_so_lines_ids(osv.osv): 
     
    _name = 'sandv.so.lines'
    
    
    def sandv_sale_order_create(self,cr,uid,ids,context):
        #####pdb.set_trace()
        
#         ##pdb.set_trace()
        
        sale_id=False
        if not context:
            context = {}
            
        
            
        so_obj = self.pool.get('sale.order')
        so_line_obj = self.pool.get('sale.order.line')
        
        sandv_so_lines_brow = self.browse(cr,1,ids)
        sandv_so_lines_list = sandv_so_lines_brow[0].name
        parent_so_id = None
        
        if 'active_ids' in context:
            parent_so_id = context['active_ids']
            if parent_so_id:
#                 if type(parent_so_id) == 'list':
                    parent_so_id = parent_so_id[0]
        
            
            
        context.update({'parent_so_id':parent_so_id})
                            
        sale_id = so_obj.copy(cr, uid, parent_so_id, {'order_line':None }, context=context)
        
        if sale_id:
            
            for i in sandv_so_lines_list:
                qt_id = i.order_id.id
                
                parent_so_id = qt_id
                
                ###pdb.set_trace()
                qty_in_so = i.qty_in_so
#                 parent_qty_in_so = 
                
                so_line_id = so_line_obj.copy(cr, uid, i.id, {'order_id': sale_id, 'product_uom_qty':qty_in_so }, context=context)
                
                actual_qty_in_so = i.actual_qty_in_so + qty_in_so
                
                
                if actual_qty_in_so == i.product_uom_qty:
                    so_line_obj.write(cr,uid,[i.id],{'so_created':True,'actual_qty_in_so':actual_qty_in_so,'qty_in_so':1.0})
        
                else:
                    so_line_obj.write(cr,uid,[i.id],{'actual_qty_in_so':actual_qty_in_so,'qty_in_so':1.0})
                
                

            so_obj.write(cr,uid,[parent_so_id],{'quotation_done':True,'quotation_id':False})
            so_obj.write(cr,uid,[sale_id],{'quotation_id':parent_so_id,'sale_quotation':False}) 


        return so_obj.bemco_sale_order_action(cr,uid,[sale_id],context)
#         return {'type': 'ir.actions.act_window_close'}


    
    
    _columns = {
               
               
               'name':fields.many2many('sale.order.line',"sandv_so_line_ids_rel",'sandv_ref_id','so_line_id', "Quotation Lines")
               
                
                       
                      }
    
    
     
sandv_so_lines_ids()    









class sandv_po_order_line(osv.osv): 
    
    _inherit = 'purchase.order.line'



    def onchange_product_uom(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, state='draft', context=None):
        """
        onchange handler of product_uom.
        """
        if context is None:
            context = {}
        if not uom_id:
            return {'value': {'price_unit': price_unit or 0.0, 'name': name or '', 'product_uom' : uom_id or False}}
        context = dict(context, purchase_uom_check=True)
        return self.onchange_product_id(cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=date_order, fiscal_position_id=fiscal_position_id, date_planned=date_planned,
            name=name, price_unit=price_unit, state=state, context=context)

    def _get_date_planned(self, cr, uid, supplier_info, date_order_str, context=None):
        """Return the datetime value to use as Schedule Date (``date_planned``) for
           PO Lines that correspond to the given product.supplierinfo,
           when ordered at `date_order_str`.

           :param browse_record | False supplier_info: product.supplierinfo, used to
               determine delivery delay (if False, default delay = 0)
           :param str date_order_str: date of order field, as a string in
               DEFAULT_SERVER_DATETIME_FORMAT
           :rtype: datetime
           :return: desired Schedule Date for the PO line
        """
        supplier_delay = int(supplier_info.delay) if supplier_info else 0
        return datetime.strptime(date_order_str, DEFAULT_SERVER_DATETIME_FORMAT) + relativedelta(days=supplier_delay)

    def action_cancel(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'cancel'}, context=context)
        # We will group by PO first, so we do the check only once for each PO
        purchase_orders = list(set([x.order_id for x in self.browse(cr, uid, ids, context=context)]))
        for purchase in purchase_orders:
            if all([l.state == 'cancel' for l in purchase.order_line]):
                self.pool.get('purchase.order').action_cancel(cr, uid, [purchase.id], context=context)

    def _check_product_uom_group(self, cr, uid, context=None):
        group_uom = self.pool.get('ir.model.data').get_object(cr, uid, 'product', 'group_uom')
        res = [user for user in group_uom.users if user.id == uid]
        return len(res) and True or False


    def onchange_product_id(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, state='draft', context=None):
        """
        onchange handler of product_id.
        """
        if context is None:
            context = {}

        res = {'value': {'price_unit': price_unit or 0.0, 'name': name or '', 'product_uom' : uom_id or False}}
        if not product_id:
            if not uom_id:
                uom_id = self.default_get(cr, uid, ['product_uom'], context=context).get('product_uom', False)
                res['value']['product_uom'] = uom_id
            return res

        product_product = self.pool.get('product.product')
        product_uom = self.pool.get('product.uom')
        res_partner = self.pool.get('res.partner')
        product_pricelist = self.pool.get('product.pricelist')
        account_fiscal_position = self.pool.get('account.fiscal.position')
        account_tax = self.pool.get('account.tax')

        # - check for the presence of partner_id and pricelist_id
        #if not partner_id:
        #    raise osv.except_osv(_('No Partner!'), _('Select a partner in purchase order to choose a product.'))
        #if not pricelist_id:
        #    raise osv.except_osv(_('No Pricelist !'), _('Select a price list in the purchase order form before choosing a product.'))

        # - determine name and notes based on product in partner lang.
        context_partner = context.copy()
        if partner_id:
            lang = res_partner.browse(cr, uid, partner_id).lang
            context_partner.update( {'lang': lang, 'partner_id': partner_id} )
        product = product_product.browse(cr, uid, product_id, context=context_partner)
        #call name_get() with partner in the context to eventually match name and description in the seller_ids field
        if not name or not uom_id:
            # The 'or not uom_id' part of the above condition can be removed in master. See commit message of the rev. introducing this line.
            dummy, name = product_product.name_get(cr, uid, product_id, context=context_partner)[0]
            if product.description_purchase:
                name += '\n' + product.description_purchase
            res['value'].update({'name': name})

        # - set a domain on product_uom
        res['domain'] = {'product_uom': [('category_id','=',product.uom_id.category_id.id)]}




        # - check that uom and product uom belong to the same category
        product_uom_po_id = product.uom_po_id.id
        if not uom_id:
            uom_id = product_uom_po_id

        if product.uom_id.category_id.id != product_uom.browse(cr, uid, uom_id, context=context).category_id.id:
            if context.get('purchase_uom_check') and self._check_product_uom_group(cr, uid, context=context):
                res['warning'] = {'title': _('Warning!'), 'message': _('Selected Unit of Measure does not belong to the same category as the product Unit of Measure.')}
            uom_id = product_uom_po_id

        res['value'].update({'product_uom': uom_id})

        # - determine product_qty and date_planned based on seller info
        if not date_order:
            date_order = fields.datetime.now()


        supplierinfo = False
        precision = self.pool.get('decimal.precision').precision_get(cr, uid, 'Product Unit of Measure')
        for supplier in product.seller_ids:
            if partner_id and (supplier.name.id == partner_id):
                supplierinfo = supplier
                if supplierinfo.product_uom.id != uom_id:
                    res['warning'] = {'title': _('Warning!'), 'message': _('The selected supplier only sells this product by %s') % supplierinfo.product_uom.name }
                min_qty = product_uom._compute_qty(cr, uid, supplierinfo.product_uom.id, supplierinfo.min_qty, to_uom_id=uom_id)
                if float_compare(min_qty , qty, precision_digits=precision) == 1: # If the supplier quantity is greater than entered from user, set minimal.
                    if qty:
                        res['warning'] = {'title': _('Warning!'), 'message': _('The selected supplier has a minimal quantity set to %s %s, you should not purchase less.') % (supplierinfo.min_qty, supplierinfo.product_uom.name)}
                    qty = min_qty
        dt = self._get_date_planned(cr, uid, supplierinfo, date_order, context=context).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        qty = qty or 1.0
        res['value'].update({'date_planned': date_planned or dt})
        if qty:
            res['value'].update({'product_qty': qty})


# MOQ code --------------------start




        if qty :
            browsed_rec = self.browse(cr,uid,ids)
            browsed_qty = browsed_rec.product_qty
            browsed_product = browsed_rec.product_id
            
            if qty == browsed_qty or browsed_qty == False or (qty == 1.0 and browsed_qty == False ):
                res['value'].update({'product_qty':product.moq})
            
            
            else:
                res['value'].update({'product_qty': qty})
        
            
#             pdb.set_trace()
            if qty != 1.0 and not browsed_rec:
                if product.moq_type == 'multiple_qty':
                    if (qty % product.moq) != 0:
                        warning_msg = _("Quantity should be multiple of Product MOQ") + "\n\n"
                
                        if warning_msg:
                            warning = {
                                       'title': _('Validation Error!'),
                                       'message' : warning_msg
                                    }
                        
                            res['warning'] = warning
                            
                            
                    else:
                        res['value'].update({'product_qty': qty})
                           
                    
                if product.moq_type == 'min_qty' and qty < product.moq:
                    warning_msg = _("Quantity should be more than minimun Product MOQ") + "\n\n"
            
                    if warning_msg:
                        warning = {
                                   'title': _('Validation Error!'),
                                   'message' : warning_msg
                                }
                        res['warning'] = warning
                        
                else:
                    res['value'].update({'product_qty': qty})

        
            
#             #pdb.set_trace()
            if product.moq != 0.0 and  product.moq_type == 'multiple_qty':

                if (res['value']['product_qty'] % product.moq) != 0:
                    
                    if product.moq != res['value']['product_qty']:
                        warning_msg = _("Quantity should be multiple of Product MOQ") + "\n\n"
            
                        if warning_msg:
                            warning = {
                                       'title': _('Validation Error!'),
                                       'message' : warning_msg
                                    }
                            res['warning'] = warning
                            
                    res['value'].update({'product_qty':product.moq})
                    
                
                
                   
#                 else:
#                     
#                         
#                         res['value'].update({'product_qty':qty})
#                         
                        
            elif product.moq_type == 'min_qty' and res['value']['product_qty'] < product.moq:
                
                    warning_msg = _("Quantity should be more than minimun Product MOQ") + "\n\n"
            
                    if warning_msg:
                        warning = {
                                   'title': _('Validation Error!'),
                                   'message' : warning_msg
                                }
                        res['warning'] = warning

                    res['value'].update({'product_qty':product.moq})
                    
#             else:
#                  
#                 res['value'].update({'product_uom_qty':qty})
#                 
                    
                    

# MOQ code --------------------end




        price = price_unit
        if price_unit is False or price_unit is None:
            # - determine price_unit and taxes_id
            if pricelist_id:
                date_order_str = datetime.strptime(date_order, DEFAULT_SERVER_DATETIME_FORMAT).strftime(DEFAULT_SERVER_DATE_FORMAT)
                price = product_pricelist.price_get(cr, uid, [pricelist_id],
                        product.id, qty or 1.0, partner_id or False, {'uom': uom_id, 'date': date_order_str})[pricelist_id]
            else:
                price = product.standard_price

        if uid == SUPERUSER_ID:
            company_id = self.pool['res.users'].browse(cr, uid, [uid]).company_id.id
            taxes = product.supplier_taxes_id.filtered(lambda r: r.company_id.id == company_id)
        else:
            taxes = product.supplier_taxes_id
        fpos = fiscal_position_id and account_fiscal_position.browse(cr, uid, fiscal_position_id, context=context) or False
        taxes_ids = account_fiscal_position.map_tax(cr, uid, fpos, taxes, context=context)
        price = self.pool['account.tax']._fix_tax_included_price(cr, uid, price, product.supplier_taxes_id, taxes_ids)
        res['value'].update({'price_unit': price, 'taxes_id': taxes_ids})

        return res

    product_id_change = onchange_product_id
    product_uom_change = onchange_product_uom 



sandv_po_order_line()





# 
# class sandv_stock_move_line(osv.osv): 
#     
#     _inherit = 'stock.move'
# 
# 
# 
#     def onchange_product_id(self, cr, uid, ids, prod_id=False, loc_id=False, loc_dest_id=False, partner_id=False):
#         """ On change of product id, if finds UoM, UoS, quantity and UoS quantity.
#         @param prod_id: Changed Product id
#         @param loc_id: Source location id
#         @param loc_dest_id: Destination location id
#         @param partner_id: Address id of partner
#         @return: Dictionary of values
#         """
#         if not prod_id:
#             return {}
#         user = self.pool.get('res.users').browse(cr, uid, uid)
#         lang = user and user.lang or False
#         if partner_id:
#             addr_rec = self.pool.get('res.partner').browse(cr, uid, partner_id)
#             if addr_rec:
#                 lang = addr_rec and addr_rec.lang or False
#         ctx = {'lang': lang}
# 
#         product = self.pool.get('product.product').browse(cr, uid, [prod_id], context=ctx)[0]
#         uos_id = product.uos_id and product.uos_id.id or False
#         result = {
#             'name': product.partner_ref,
#             'product_uom': product.uom_id.id,
#             'product_uos': uos_id,
#             'product_uom_qty': 1.00,
#             'product_uos_qty': self.pool.get('stock.move').onchange_quantity(cr, uid, ids, prod_id, 1.00, product.uom_id.id, uos_id)['value']['product_uos_qty'],
#         }
#         if loc_id:
#             result['location_id'] = loc_id
#         if loc_dest_id:
#             result['location_dest_id'] = loc_dest_id
#             
#             
#             
# # MOQ code --------------------start
#         
#         result.update({'product_uom_qty':product.moq})
#     
#             
# 
# # MOQ code --------------------end
# 
#         return {'value': result}
# 
# 
# 
# 
#     def onchange_quantity(self, cr, uid, ids, product_id, product_qty, product_uom, product_uos):
#         """ On change of product quantity finds UoM and UoS quantities
#         @param product_id: Product id
#         @param product_qty: Changed Quantity of product
#         @param product_uom: Unit of measure of product
#         @param product_uos: Unit of sale of product
#         @return: Dictionary of values
#         """
#         result = {
#             'product_uos_qty': 0.00
#         }
#         warning = {}
# 
#         if (not product_id) or (product_qty <= 0.0):
#             result['product_qty'] = 0.0
#             return {'value': result}
# 
#         product_obj = self.pool.get('product.product')
#         uos_coeff = product_obj.read(cr, uid, product_id, ['uos_coeff'])
#         
# 
# 
# 
# 
# # MOQ code --------------------start
#         ####pdb.set_trace()
#         qty = product_qty
#         product_obj = product_obj.browse(cr, uid, product_id)
#         if qty :
# #             if qty == 1.0:
# #                 result.update({'product_uom_qty':product_obj.moq})
# #         
# #             else:
#             result.update({'product_uom_qty':qty})
#         
#                 
# #             ####pdb.set_trace()
#             if product_obj.moq != 0.0 and ('product_uom_qty' in result and result['product_uom_qty'] != product_obj.moq) and product_obj.moq_type == 'multiple_qty':
#                 if (qty % product_obj.moq) != 0:
#                     result.update({'product_uom_qty':product_obj.moq})
#                     
#                     if product_obj.moq != result['product_uom_qty']:
#                         warning_msg = _("Quantity should be multiple of Product MOQ") + "\n\n"
#             
#                         if warning_msg:
#                             warning = {
#                                        'title': _('Validation Error!'),
#                                        'message' : warning_msg
#                                     }
#                             
#                 else:
#                     
#                     result.update({'product_uom_qty':qty})
#                         
#                         
#             elif product_obj.moq_type == 'min_qty' and qty < product_obj.moq:
#                     result.update({'product_uom_qty':product_obj.moq})
#                     
#             else:
#                 
#                 result.update({'product_uom_qty':qty})
# 
#                         
# 
# # MOQ code --------------------end
# 
# 
# 
# 
# 
# 
# 
#         # Warn if the quantity was decreased
#         if ids:
#             for move in self.read(cr, uid, ids, ['product_qty']):
#                 if product_qty < move['product_qty']:
#                     warning.update({
#                         'title': _('Information'),
#                         'message': _("By changing this quantity here, you accept the "
#                                 "new quantity as complete: Odoo will not "
#                                 "automatically generate a back order.")})
#                 break
# 
#         if product_uos and product_uom and (product_uom != product_uos):
#             precision = self.pool.get('decimal.precision').precision_get(cr, uid, 'Product UoS')
#             result['product_uos_qty'] = float_round(product_qty * uos_coeff['uos_coeff'], precision_digits=precision)
#         else:
#             result['product_uos_qty'] = product_qty
#             
#             
#     
# 
#         return {'value': result, 'warning': warning}
# 
# 
# 
# 
#     def onchange_uos_quantity(self, cr, uid, ids, product_id, product_uos_qty,
#                           product_uos, product_uom):
#         """ On change of product quantity finds UoM and UoS quantities
#         @param product_id: Product id
#         @param product_uos_qty: Changed UoS Quantity of product
#         @param product_uom: Unit of measure of product
#         @param product_uos: Unit of sale of product
#         @return: Dictionary of values
#         """
#         result = {
#             'product_uom_qty': 0.00
#         }
# 
#         if (not product_id) or (product_uos_qty <= 0.0):
#             result['product_uos_qty'] = 0.0
#             return {'value': result}
# 
#         product_obj = self.pool.get('product.product')
#         uos_coeff = product_obj.read(cr, uid, product_id, ['uos_coeff'])
# 
#         # No warning if the quantity was decreased to avoid double warnings:
#         # The clients should call onchange_quantity too anyway
# 
#         if product_uos and product_uom and (product_uom != product_uos):
#             precision = self.pool.get('decimal.precision').precision_get(cr, uid, 'Product Unit of Measure')
#             result['product_uom_qty'] = float_round(product_uos_qty / uos_coeff['uos_coeff'], precision_digits=precision)
#         else:
#             result['product_uom_qty'] = product_uos_qty
#             
#             
#             
# # MOQ code --------------------start
#         ####pdb.set_trace()
#         qty = result['product_uom_qty']
#         product_obj = product_obj.browse(cr, uid, product_id)
#         if qty :
# #             if qty == 1.0:
# #                 result.update({'product_uom_qty':product_obj.moq})
# #         
# #             else:
#             result.update({'product_uom_qty':qty})
#         
#                 
# #             ####pdb.set_trace()
#             if product_obj.moq != 0.0 and ('product_uom_qty' in result and result['product_uom_qty'] != product_obj.moq):
#                 if (qty % product_obj.moq) != 0:
#                     result.update({'product_uom_qty':product_obj.moq})
#                     
#                     if product_obj.moq != result['product_uom_qty']:
#                         warning_msg = _("Quantity should be multiple of Product MOQ") + "\n\n"
#             
#                         if warning_msg:
#                             warning = {
#                                        'title': _('Validation Error!'),
#                                        'message' : warning_msg
#                                     }
#                             
#                 else:
#                     
#                     result.update({'product_uom_qty':qty})
#                         
#                         
# 
# # MOQ code --------------------end
# 
#         return {'value': result}
# 
# 
# 
# 
# 
# sandv_stock_move_line()



# planning view for products management----------------start



class sandv_stock_product_qty(osv.osv):
    _name = "sandv.stock.product.qty"
    _description = "View DO stock and Actual Stock Qty"
    _auto = False
    _log_access = False
    
    
    
    #code for checking quantity available on hand is zero or not
    def _actual_stock_qty_in_hand(self, cr, uid, ids, field_name, arg, context):
        res = {}
        product_obj=self.pool.get('product.product')
        stock_obj = self.pool.get('stock.move')
    ##pdb.set_trace()
        if ids:
            for i in self.browse(cr, uid, ids, context=context):
            #line = stock_obj.browse(cr, uid, int(i), context=context)
                line = i
                prod_id = line.product_id.id
                #             product_brow = product_obj.browse(cr,uid,line.id)
                qty_on_hand = line.product_id.qty_available
                #             if qty_on_hand == 0.0:
                #                 res[line.id] = False
                #             else:
                #                 res[line.id] = True
        
                res[line.id] = qty_on_hand
                 
        ##pdb.set_trace()
        return res
     
#     def _qty_stock_in_search(self, cr, uid, obj, name, args, context=None):
#         res = []
#         kk = []
#         
#         product_obj = self.pool.get('product.product')
#         product_ids = product_obj.search(cr,uid,[])
#         for line in product_obj.browse(cr, uid, product_ids, context=context):
#             qty_on_hand = line.qty_available
#             if qty_on_hand == 0.0:
#                 res.append(line.id)
#             else:
#                 kk.append(line.id)
#  
# # if False then selected option in Product Without zero qty is NO else YES
#         if args[0][2] == False:
#             return [('id', 'in', res)]
#         else:
#             return [('id', 'in', kk)]

    
    _columns = {
              
#               'stock_id':fields.many2one("stock.move","Stock", readonly=True),
              'product_id':fields.many2one('product.product', 'Product', readonly=True),
              'product_uom_qty':fields.float('Qty to Deliver', readonly=True),
              'prod_name':fields.char('Description', size=256, readonly=True),
              'date_expected':fields.date("Scheduled Date",readonly=True),
              'origin':fields.char('Source', size=256, readonly=True),
              
#               'qty_available':fields.float("Quantity in Stock",readonly=True),
             
              'picking_id':fields.many2one("stock.picking","Ref",readonly=True),
              
              'stock_qty':fields.function(_actual_stock_qty_in_hand, string='Qty in Stock', type = 'float', help=""),
            
            
               }   



    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, 'sandv_stock_product_qty')
        cr.execute("""create or replace view sandv_stock_product_qty as (
        select ROW_NUMBER() OVER (ORDER BY i.id) AS id,
        
           i.product_id product_id,
           i.name prod_name,
           i.product_uom_qty product_uom_qty,
           i.date_expected date_expected,
           i.origin origin,
           i.picking_id picking_id
           
           from stock_move i
    
           where picking_id in (select id from stock_picking where state not in ('done','cancel') and picking_type_id = 2)
       


        )""")        
        

sandv_stock_product_qty()



 
class sandv_stock_transfer_details_line(osv.osv): 
     
    _inherit = 'stock.transfer_details_items'



    def onchange_quantity(self, cr, uid, ids, qty_in_so, context):
        """
        onchange handler of onchange_qty_in_so.
        """
        

        v = {}
        d = {}
        res = {}
        warning = {}
        msgalert = {}

        if qty_in_so:
        
        
            so_lines_brow = self.browse(cr,uid,ids)
            
            
    #             p_qty_in_so = p_qty_in_so + qty_in_so
            
            
# MOQ code --------------------start
            #pdb.set_trace()
            
            product_obj = self.pool.get("product.product")
            product_id = so_lines_brow[0].product_id.id
            product_obj = product_obj.browse(cr, uid, product_id)
            
            qty = qty_in_so
            
#             ####pdb.set_trace()
            if product_obj.moq != 0.0 and qty_in_so != product_obj.moq and product_obj.moq_type == 'multiple_qty':
                if (qty % product_obj.moq) != 0:
                    v['qty_in_so'] = 0.0
                    
#                     msgalert = {'title' : 'Warning', 'message': ('Quantity should be multiple of Product MOQ')}
                    
                    warning_msg = _("Quantity should be multiple of Product MOQ") + "\n\n"
                     
                    if warning_msg:
                        warning = {
                                   'title': _('Validation Error!'),
                                   'message' : warning_msg
                                }
                    
                    v['quantity'] = so_lines_brow[0].quantity
                        
                        
                     
                        

# MOQ code --------------------end
            

        res = {'value':v, 'domain':d, 'warning' : warning}
        return res


sandv_stock_transfer_details_line()















    