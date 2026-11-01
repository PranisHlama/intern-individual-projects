from odoo import api, fields, models, _

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    appraisal_ids = fields.One2many(
        'hr.appraisal', 'employee_id', string='Appraisals')
    appraisal_count = fields.Integer(
        string='Appraisals Count', compute='_compute_appraisal_data', store=True, compute_sudo=True)
    last_appraisal_date = fields.Date(
        string='Last Appraisal Date', compute='_compute_appraisal_data', store=True, compute_sudo=True)
    last_appraisal_score = fields.Float(
        string='Last Performance Score', compute='_compute_appraisal_data', store=True, compute_sudo=True)
    next_appraisal_date = fields.Date(
        string='Next Scheduled Appraisal', compute='_compute_appraisal_data', store=True, compute_sudo=True)
    ongoing_appraisal_id = fields.Many2one(
        'hr.appraisal', string='Ongoing Appraisal', compute='_compute_appraisal_data', store=True, compute_sudo=True)
    goal_count = fields.Integer(
        string='Active Goals', compute='_compute_goal_count')
    goal_progress = fields.Float(
        string='Goals Average Progress (%)', compute='_compute_goal_count')

    @api.depends('appraisal_ids.state', 'appraisal_ids.date_completed', 'appraisal_ids.final_score', 'appraisal_ids.date_close')
    def _compute_appraisal_data(self):
        for emp in self:
            emp.appraisal_count = len(emp.appraisal_ids)
            completed = emp.appraisal_ids.filtered(lambda a: a.state == 'done').sorted('date_completed', reverse=True)
            if completed:
                emp.last_appraisal_date = completed[0].date_completed
                emp.last_appraisal_score = completed[0].final_score
            else:
                emp.last_appraisal_date = False
                emp.last_appraisal_score = 0.0

            ongoing = emp.appraisal_ids.filtered(lambda a: a.state not in ['done', 'cancel']).sorted('date_close')
            if ongoing:
                emp.ongoing_appraisal_id = ongoing[0].id
                emp.next_appraisal_date = ongoing[0].date_close
            else:
                emp.ongoing_appraisal_id = False
                emp.next_appraisal_date = False

    def _compute_goal_count(self):
        Goal = self.env['hr.appraisal.goal']
        for emp in self:
            all_goals = Goal.search([
                ('employee_id', '=', emp.id),
                ('status', '!=', 'cancelled'),
            ])
            active_goals = all_goals.filtered(lambda g: g.status in ['not_started', 'in_progress', 'blocked'])
            emp.goal_count = len(active_goals)
            if all_goals:
                emp.goal_progress = round(sum(all_goals.mapped('progress')) / len(all_goals), 1)
            else:
                emp.goal_progress = 0.0

    def action_open_appraisals(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Appraisals for %s", self.name),
            'res_model': 'hr.appraisal',
            'view_mode': 'list,kanban,form,pivot,graph',
            'domain': [('employee_id', '=', self.id)],
            'context': {'default_employee_id': self.id},
        }

    def action_open_goals(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Performance Goals for %s", self.name),
            'res_model': 'hr.appraisal.goal',
            'view_mode': 'list,kanban,form',
            'domain': [('employee_id', '=', self.id)],
            'context': {'default_employee_id': self.id},
        }
