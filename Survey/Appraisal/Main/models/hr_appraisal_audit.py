from odoo import api, fields, models, _

class HrAppraisalAuditLog(models.Model):
    _name = 'hr.appraisal.audit.log'
    _description = 'Appraisal Audit Trail'
    _order = 'timestamp desc, id desc'

    appraisal_id = fields.Many2one(
        'hr.appraisal', string='Appraisal', required=True, ondelete='cascade', index=True)
    user_id = fields.Many2one(
        'res.users', string='Triggered By', required=True, default=lambda self: self.env.user)
    timestamp = fields.Datetime(
        string='Timestamp', default=fields.Datetime.now, required=True, readonly=True)
    
    action_type = fields.Selection([
        ('stage_change', 'Stage Transition'),
        ('score_change', 'Score Adjustment / Override'),
        ('manager_change', 'Reviewer / Manager Reassigned'),
        ('deadline_change', 'Deadline Adjusted'),
        ('validation', 'HR Approval / Sign-Off'),
        ('reset', 'Workflow Reopened'),
        ('cancellation', 'Appraisal Cancelled'),
    ], string='Action Event', required=True)

    old_value = fields.Char(string='Previous Value')
    new_value = fields.Char(string='New Value')
    notes = fields.Text(string='Operational Notes / Reason')
