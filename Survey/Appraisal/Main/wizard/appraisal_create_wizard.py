from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class HrAppraisalCreateWizard(models.TransientModel):
    _name = 'hr.appraisal.create.wizard'
    _description = 'Batch Appraisal Creation Wizard'

    plan_id = fields.Many2one('hr.appraisal.plan', string='Appraisal Plan')
    review_period = fields.Char(string='Review Period', required=True, default=lambda self: _('Mid-Year / Annual Review'))
    date_start = fields.Date(string='Start Date', default=fields.Date.context_today, required=True)
    date_close = fields.Date(
        string='Deadline', required=True,
        default=lambda self: fields.Date.context_today(self) + relativedelta(days=30))

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    department_ids = fields.Many2many('hr.department', string='Filter by Departments')
    employee_ids = fields.Many2many('hr.employee', string='Select Specific Employees')
    template_id = fields.Many2one('hr.appraisal.template', string='Questionnaire Template')
    rating_scale_id = fields.Many2one('hr.appraisal.rating.scale', string='Rating Scale')
    send_self_immediately = fields.Boolean(string='Immediately Request Self-Assessment', default=True)

    @api.onchange('plan_id')
    def _onchange_plan_id(self):
        if self.plan_id:
            self.template_id = self.plan_id.template_id
            self.rating_scale_id = self.plan_id.rating_scale_id
            self.department_ids = self.plan_id.department_ids
            self.employee_ids = self.plan_id.employee_ids

    def action_create_appraisals(self):
        self.ensure_one()
        domain = [('company_id', '=', self.company_id.id), ('active', '=', True)]
        if self.employee_ids:
            employees = self.employee_ids
        elif self.department_ids:
            domain.append(('department_id', 'in', self.department_ids.ids))
            employees = self.env['hr.employee'].search(domain)
        else:
            employees = self.env['hr.employee'].search(domain)

        if not employees:
            raise UserError(_("No active employees found matching the specified criteria."))

        draft_stage = self.env['hr.appraisal.stage'].search([('stage_type', '=', 'draft')], limit=1)
        created_appraisals = self.env['hr.appraisal']

        for emp in employees:
            appraisal = self.env['hr.appraisal'].create({
                'employee_id': emp.id,
                'manager_id': emp.parent_id.id if emp.parent_id else False,
                'department_id': emp.department_id.id if emp.department_id else False,
                'job_id': emp.job_id.id if emp.job_id else False,
                'company_id': self.company_id.id,
                'plan_id': self.plan_id.id if self.plan_id else False,
                'template_id': self.template_id.id if self.template_id else False,
                'rating_scale_id': self.rating_scale_id.id if self.rating_scale_id else False,
                'review_period': self.review_period,
                'date_start': self.date_start,
                'date_close': self.date_close,
                'stage_id': draft_stage.id if draft_stage else False,
            })
            if self.send_self_immediately:
                appraisal.action_send_self_assessment()
            created_appraisals |= appraisal

        return {
            'type': 'ir.actions.act_window',
            'name': _('Generated Appraisals'),
            'res_model': 'hr.appraisal',
            'view_mode': 'list,kanban,form',
            'domain': [('id', 'in', created_appraisals.ids)],
        }
