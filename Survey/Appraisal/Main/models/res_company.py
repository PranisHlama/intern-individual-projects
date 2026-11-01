from odoo import fields, models

class ResCompany(models.Model):
    _inherit = 'res.company'

    appraisal_plan_frequency = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semiannual', 'Semiannual'),
        ('annual', 'Annual'),
    ], string='Default Appraisal Cadence', default='annual')

    appraisal_default_rating_scale_id = fields.Many2one(
        'hr.appraisal.rating.scale', string='Default Rating Scale')
    appraisal_default_template_id = fields.Many2one(
        'hr.appraisal.template', string='Default Questionnaire Template')
    appraisal_reminder_days = fields.Integer(
        string='Automated Reminder Window (Days)', default=7)
    appraisal_auto_lead_days = fields.Integer(
        string='Plan Generation Lead Time (Days)', default=14)
    appraisal_duration_days = fields.Integer(
        string='Default Cycle Duration (Days)', default=30)
    appraisal_self_assessment_required = fields.Boolean(
        string='Require Employee Self Assessment', default=True)
    appraisal_hr_validation_required = fields.Boolean(
        string='Require HR Committee Sign-Off', default=True)
    appraisal_auto_sync_skills = fields.Boolean(
        string='Auto-Sync Skill Level to Employee Profile', default=True)
