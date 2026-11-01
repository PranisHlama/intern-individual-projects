from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    appraisal_plan_frequency = fields.Selection(
        related='company_id.appraisal_plan_frequency', readonly=False,
        string='Default Appraisal Cadence')
    appraisal_default_rating_scale_id = fields.Many2one(
        related='company_id.appraisal_default_rating_scale_id', readonly=False,
        string='Default Rating Scale')
    appraisal_default_template_id = fields.Many2one(
        related='company_id.appraisal_default_template_id', readonly=False,
        string='Default Questionnaire Template')
    appraisal_reminder_days = fields.Integer(
        related='company_id.appraisal_reminder_days', readonly=False,
        string='Automated Reminder Window (Days)')
    appraisal_auto_lead_days = fields.Integer(
        related='company_id.appraisal_auto_lead_days', readonly=False,
        string='Plan Generation Lead Time (Days)')
    appraisal_duration_days = fields.Integer(
        related='company_id.appraisal_duration_days', readonly=False,
        string='Default Cycle Duration (Days)')
    appraisal_self_assessment_required = fields.Boolean(
        related='company_id.appraisal_self_assessment_required', readonly=False,
        string='Require Employee Self Assessment')
    appraisal_hr_validation_required = fields.Boolean(
        related='company_id.appraisal_hr_validation_required', readonly=False,
        string='Require HR Committee Sign-Off')
    appraisal_auto_sync_skills = fields.Boolean(
        related='company_id.appraisal_auto_sync_skills', readonly=False,
        string='Auto-Sync Skill Level to Employee Profile')
