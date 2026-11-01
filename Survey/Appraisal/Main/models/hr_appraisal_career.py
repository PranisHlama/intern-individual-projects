from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class HrAppraisalCareerPlan(models.Model):
    _name = 'hr.appraisal.career.plan'
    _description = 'Career Development Plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Career Plan Title', required=True, tracking=True)
    employee_id = fields.Many2one(
        'hr.employee', string='Employee', required=True, tracking=True, index=True)
    manager_id = fields.Many2one(
        'hr.employee', string='Manager / Mentor', related='employee_id.parent_id', store=True, readonly=True)
    appraisal_id = fields.Many2one(
        'hr.appraisal', string='Source Appraisal', ondelete='set null')
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company, required=True)

    career_objective = fields.Text(
        string='Career Aspirations & Target Role', required=True,
        help="Target position, responsibilities, or professional milestone.")
    timeline = fields.Selection([
        ('short_term', 'Short-Term (3-6 Months)'),
        ('mid_term', 'Mid-Term (1-2 Years)'),
        ('long_term', 'Long-Term (3-5 Years)'),
    ], string='Target Horizon', default='mid_term', required=True, tracking=True)

    required_skills = fields.Text(string='Required Skills & Knowledge to Acquire')
    suggested_training = fields.Html(string='Recommended Courses, Mentorship & Certifications')

    state = fields.Selection([
        ('draft', 'Drafting'),
        ('in_progress', 'In Progress'),
        ('achieved', 'Achieved'),
        ('deferred', 'Deferred / On Hold'),
    ], string='Plan Status', default='draft', required=True, tracking=True)

    manager_approval = fields.Selection([
        ('draft', 'Not Submitted'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved by Manager'),
        ('revision', 'Revision Requested'),
    ], string='Manager Endorsement', default='draft', tracking=True)
    manager_notes = fields.Text(string='Manager Feedback & Endorsement Notes')

    progress = fields.Integer(string='Milestone Progress (%)', default=0, tracking=True)

    @api.constrains('progress')
    def _check_progress(self):
        for plan in self:
            if not (0 <= plan.progress <= 100):
                raise ValidationError(_("Progress must be between 0% and 100%."))

    def action_submit_for_approval(self):
        for plan in self:
            plan.write({'manager_approval': 'pending', 'state': 'draft'})
            plan.message_post(body=_("Career development plan submitted to manager for endorsement."))

    def action_approve(self):
        for plan in self:
            plan.write({'manager_approval': 'approved', 'state': 'in_progress'})
            plan.message_post(body=_("Career development plan approved by %s.", self.env.user.name))

    def action_mark_achieved(self):
        for plan in self:
            plan.write({'state': 'achieved', 'progress': 100})
            plan.message_post(body=_("Career development plan marked as Achieved!"))
