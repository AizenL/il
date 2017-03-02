from openerp.osv import fields, osv
 
class QueueResetter(osv.osv):
    _name = "seq.resetter"
 
    def reset_queue(self, cr, uid, ids=False, context={}):
        # Membuat variabel object sequence
        obj_sequence = self.pool.get('ir.sequence')
         
        # Mencari id object yang sequencenya ingin kita reset 
        seq_id = obj_sequence.search(cr, uid, [('reset_required', '=', True)]) 
         
        # Reset sequence berdasarkan id diatas
        obj_sequence.write(cr, uid, seq_id, {'number_next_actual': 1})
        return True
     
QueueResetter()