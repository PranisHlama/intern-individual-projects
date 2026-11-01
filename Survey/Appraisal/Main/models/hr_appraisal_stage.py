from odoo import api, fields, models, _

class HrAppraisalStage(models.Model):
    _name = 'hr.appraisal.stage'
    _description = 'Appraisal Stage'
    _order = 'sequence, id'

    name = fields.Char(string='Stage Name', required=True, translate=True)
    sequence = fields.Integer(string='Sequence', default=10)
    stage_type = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_self', 'Waiting Self Assessment'),
        ('self_done', 'Self Assessment Submitted'),
        ('waiting_manager', 'Waiting Manager Review'),
        ('manager_done', 'Manager Review Completed'),
        ('waiting_hr', 'Waiting HR Validation'),
        ('done', 'Completed'),
        ('cancel', 'Cancelled'),
    ], string='System Type', required=True, default='draft', index=True,
        help="System classification for workflow automation and permissions.")
    fold = fields.Boolean(
        string='Folded in Kanban', default=False,
        help='This stage is folded in the kanban view when there are no records in that stage.')
    active = fields.Boolean(string='Active', default=True)
    description = fields.Html(string='Stage Guidelines', translate=True)
    requirements = fields.Text(string='Requirements to Complete', translate=True)
    
    mail_template_id = fields.Many2one(
        'mail.template', string='Automated Email Template',
        domain="[('model', '=', 'hr.appraisal')]",
        help="If set, this email template will be automatically dispatched when an appraisal enters this stage.")
    
    auto_activity_type_id = fields.Many2one(
        'mail.activity.type', string='Automated Activity Type')
    auto_activity_summary = fields.Char(string='Activity Summary')
    auto_activity_user = fields.Selection([
        ('employee', 'Target Employee'),
        ('manager', 'Assigned Manager'),
        ('hr', 'HR Officer / Responsible'),
    ], string='Assign Activity To', default='employee')

    appraisal_count = fields.Integer(
        string='Appraisal Count', compute='_compute_appraisal_count')

    def _compute_appraisal_count(self):
        appraisal_data = self.env['hr.appraisal'].read_group(
            [('stage_id', 'in', self.ids)],
            ['stage_id'],
            ['stage_id']
        )
        mapped_data = {data['stage_id'][0]: data['stage_id_count'] for data in appraisal_data}
        for stage in self:
            stage.appraisal_count = mapped_data.get(stage.id, 0)
