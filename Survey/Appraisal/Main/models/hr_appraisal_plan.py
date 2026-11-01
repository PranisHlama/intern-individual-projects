from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class HrAppraisalPlan(models.Model):
    _name = 'hr.appraisal.plan'
    _description = 'Recurring Appraisal Plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='Plan Name', required=True, translate=True, tracking=True)
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company, required=True)
    active = fields.Boolean(string='Active', default=True, tracking=True)

    start_date = fields.Date(
        string='Plan Start Date', default=fields.Date.context_today, required=True)
    end_date = fields.Date(string='Plan Expiration Date')
    
    frequency = fields.Selection([
        ('one_time', 'One-Time Cycle'),
        ('monthly', 'Monthly Cycle'),
        ('quarterly', 'Quarterly (Every 3 Months)'),
        ('semiannual', 'Semiannual (Every 6 Months)'),
        ('annual', 'Annual Review (Every 12 Months)'),
        ('custom', 'Custom Interval in Days'),
    ], string='Frequency', default='annual', required=True, tracking=True)

    custom_interval_days = fields.Integer(string='Custom Interval (Days)', default=90)
    lead_days = fields.Integer(
        string='Generation Lead Time (Days)', default=14,
        help="Number of days prior to review period start when appraisals will be generated automatically.")
    duration_days = fields.Integer(
        string='Completion Window (Days)', default=30,
        help="Number of days allocated from appraisal start date until deadline.")

    next_generation_date = fields.Date(
        string='Next Execution Date', default=fields.Date.context_today, tracking=True)
    last_generation_date = fields.Date(string='Last Generated Date', readonly=True)

    department_ids = fields.Many2many(
        'hr.department', 'hr_appraisal_plan_department_rel',
        'plan_id', 'department_id', string='Target Departments')
    job_ids = fields.Many2many(
        'hr.job', 'hr_appraisal_plan_job_rel',
        'plan_id', 'job_id', string='Target Job Positions')
    employee_ids = fields.Many2many(
        'hr.employee', 'hr_appraisal_plan_employee_rel',
        'plan_id', 'employee_id', string='Specific Employees Included')
    category_ids = fields.Many2many(
        'hr.employee.category', 'hr_appraisal_plan_category_rel',
        'plan_id', 'category_id', string='Employee Tags')

    hr_responsible_id = fields.Many2one(
        'res.users', string='Responsible HR Officer', default=lambda self: self.env.user, required=True)
    manager_required = fields.Boolean(
        string='Manager Evaluation Required', default=True)
    self_assessment_required = fields.Boolean(
        string='Self Assessment Required', default=True)
    final_approval_required = fields.Boolean(
        string='HR Final Sign-off Required', default=True)

    template_id = fields.Many2one(
        'hr.appraisal.template', string='Default Questionnaire Template')
    rating_scale_id = fields.Many2one(
        'hr.appraisal.rating.scale', string='Rating Scale')

    appraisal_ids = fields.One2many(
        'hr.appraisal', 'plan_id', string='Generated Appraisals')
    appraisal_count = fields.Integer(
        string='Total Appraisals', compute='_compute_appraisal_count')

    @api.depends('appraisal_ids')
    def _compute_appraisal_count(self):
        for plan in self:
            plan.appraisal_count = len(plan.appraisal_ids)

    def _get_target_employees(self):
        """Determine eligible active employees for this plan based on filters."""
        self.ensure_one()
        domain = [('company_id', '=', self.company_id.id), ('active', '=', True)]
        if self.employee_ids:
            return self.employee_ids.filtered(lambda e: e.active and e.company_id == self.company_id)
        if self.department_ids:
            domain.append(('department_id', 'in', self.department_ids.ids))
        if self.job_ids:
            domain.append(('job_id', 'in', self.job_ids.ids))
        if self.category_ids:
            domain.append(('category_ids', 'in', self.category_ids.ids))
        return self.env['hr.employee'].search(domain)

    def _calculate_next_date(self, base_date):
        """Calculate next scheduled cycle date depending on frequency setting."""
        if self.frequency == 'monthly':
            return base_date + relativedelta(months=1)
        elif self.frequency == 'quarterly':
            return base_date + relativedelta(months=3)
        elif self.frequency == 'semiannual':
            return base_date + relativedelta(months=6)
        elif self.frequency == 'annual':
            return base_date + relativedelta(years=1)
        elif self.frequency == 'custom':
            return base_date + relativedelta(days=self.custom_interval_days or 30)
        return False

    def action_generate_appraisals(self):
        """Manually or automatically generate appraisals for all eligible employees."""
        self.ensure_one()
        employees = self._get_target_employees()
        if not employees:
            raise UserError(_("No active employees found matching the filters for plan '%s'.", self.name))

        created_appraisals = self.env['hr.appraisal']
        today = fields.Date.context_today(self)
        deadline = today + relativedelta(days=self.duration_days or 30)

        draft_stage = self.env['hr.appraisal.stage'].search([('stage_type', '=', 'draft')], limit=1)

        for emp in employees:
            existing = self.env['hr.appraisal'].search([
                ('employee_id', '=', emp.id),
                ('plan_id', '=', self.id),
                ('state', 'not in', ['done', 'cancel']),
            ], limit=1)
            if existing:
                continue

            review_period_str = _("%s - Cycle %s", self.name, today.strftime('%b %Y'))
            vals = {
                'employee_id': emp.id,
                'manager_id': emp.parent_id.id if emp.parent_id else False,
                'department_id': emp.department_id.id if emp.department_id else False,
                'job_id': emp.job_id.id if emp.job_id else False,
                'company_id': self.company_id.id,
                'plan_id': self.id,
                'template_id': self.template_id.id if self.template_id else False,
                'rating_scale_id': self.rating_scale_id.id if self.rating_scale_id else False,
                'hr_responsible_id': self.hr_responsible_id.id if self.hr_responsible_id else self.env.uid,
                'review_period': review_period_str,
                'date_start': today,
                'date_close': deadline,
                'stage_id': draft_stage.id if draft_stage else False,
            }
            appraisal = self.env['hr.appraisal'].create(vals)
            appraisal._populate_template_questions()
            appraisal._populate_standard_competencies()
            created_appraisals |= appraisal

        self.last_generation_date = today
        if self.frequency != 'one_time':
            next_date = self._calculate_next_date(self.next_generation_date or today)
            if self.end_date and next_date and next_date > self.end_date:
                self.active = False
            else:
                self.next_generation_date = next_date

        self.message_post(body=_("Generated %d appraisal record(s) for plan '%s'.", len(created_appraisals), self.name))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Generated Appraisals'),
            'res_model': 'hr.appraisal',
            'view_mode': 'list,kanban,form',
            'domain': [('id', 'in', created_appraisals.ids)],
        }

    @api.model
    def cron_generate_recurring_appraisals(self):
        """Cron execution: checks all active recurring plans due for generation."""
        today = fields.Date.context_today(self)
        plans = self.search([
            ('active', '=', True),
            ('frequency', '!=', 'one_time'),
            ('next_generation_date', '<=', today + relativedelta(days=1)),
        ])
        for plan in plans:
            try:
                plan.action_generate_appraisals()
            except Exception as e:
                plan.message_post(body=_("Automated recurring appraisal generation failed: %s", str(e)))
