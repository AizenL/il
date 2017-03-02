##############################################################################
import time
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools.float_utils import float_compare
import pdb
import psycopg2
from openerp import api, tools, SUPERUSER_ID


class res_partner(osv.osv):
    _inherit="res.partner"
    def open_res_partner_view(self, cr, uid, ids, context=None):
        #pdb.set_trace()
        result = self.pool['ir.model.data'].xmlid_to_res_id(cr, uid, 'base.action_partner_form', raise_if_not_found=True)
        result = self.pool['ir.actions.act_window'].read(cr, uid, [result], context=context)[0]
        result['domain'] = "[('id','in',[" + ','.join(map(str, ids)) + "])]"
        return result


class crm_lead(osv.osv):

    _inherit = "crm.lead"
   
    _columns = {
        'customer_designation':fields.char('Designation',),
    }


    def case_mark_won(self, cr, uid, ids, context=None):
        """ Mark the case as won: state=done and probability=100
        """
        #pdb.set_trace()
        rec_ids=context and context.get('active_ids',[])
        customer_obj=self.pool.get("res.partner")
        customer_list=customer_obj.browse(cr, uid, ids)
        #customer_name=self.browse(cr,uid,ids).partner_name
        street=self.browse(cr,uid,ids).street or False
        street1=self.browse(cr,uid,ids).street2 or False
        #customer_name=self.browse(cr,uid,ids).street1
        city=self.browse(cr,uid,ids).city or False
        state_id=self.browse(cr,uid,ids).state_id.id or False
        zip_code=self.browse(cr,uid,ids).zip or False
        country_id=self.browse(cr,uid,ids).country_id.id or False

        email_form=self.browse(cr,uid,ids).email_from
        user_name=self.browse(cr,uid,ids).user_id or False
        partner_name=self.browse(cr,uid,ids).partner_name or False
        customer=1
        contact_name=self.browse(cr,uid,ids).contact_name
        


        cur_id=customer_obj.create(cr,uid,{'name':partner_name,'is_company':True,'concern_person':contact_name,'email':email_form,'user_id':user_name.id,'street':street,'street2':street1,'city':city,'state_id':state_id,'zip':zip_code,'country_id':country_id,'customer':True})

        stages_leads = {}
        for lead in self.browse(cr, uid, ids, context=context):
            stage_id = self.stage_find(cr, uid, [lead], lead.section_id.id or False, [('probability', '=', 100.0), ('on_change', '=', True)], context=context)
            if stage_id:
                if stages_leads.get(stage_id):
                    stages_leads[stage_id].append(lead.id)
                else:
                    stages_leads[stage_id] = [lead.id]
            else:
                raise osv.except_osv(_('Warning!'),
                    _('To relieve your sales pipe and group all Won opportunities, configure one of your sales stage as follow:\n'
                        'probability = 100 % and select "Change Probability Automatically".\n'
                        'Create a specific stage or edit an existing one by editing columns of your opportunity pipe.'))
        for stage_id, lead_ids in stages_leads.items():
            self.write(cr, uid, lead_ids, {'stage_id': stage_id}, context=context)
        return customer_obj.open_res_partner_view(cr, uid, [cur_id], context)


