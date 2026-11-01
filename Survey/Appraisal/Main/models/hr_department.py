from odoo import api, fields, models, _

class HrDepartment(models.Model):
    _inherit = 'hr.department'

    appraisal_count = fields.Integer(
        string='Total Appraisals', compute='_compute_department_appraisal_counts')
    pending_appraisal_count = fields.Integer(
        string='Pending Appraisals', compute='_compute_department_appraisal_counts')
    overdue_appraisal_count = fields.Integer(
        string='Overdue Appraisals', compute='_compute_department_appraisal_counts')

    def _compute_department_appraisal_counts(self):
        Appraisal = self.env['hr.appraisal']
        today = fields.Date.context_today(self)
        for dept in self:
            dept.appraisal_count = Appraisal.search_count([('department_id', '=', dept.id)])
            dept.pending_appraisal_count = Appraisal.search_count([
                ('department_id', '=', dept.id),
                ('state', 'in', ['waiting_self', 'waiting_manager', 'waiting_hr']),
            ])
            dept.overdue_appraisal_count = Appraisal.search_count([
                ('department_id', '=', dept.id),
                ('state', 'not in', ['done', 'cancel']),
                ('date_close', '<', today),
            ])

    def action_open_department_appraisals(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Appraisals for %s Department", self.name),
            'res_model': 'hr.appraisal',
            'view_mode': 'list,kanban,form,pivot,graph',
            'domain': [('department_id', '=', self.id)],
            'context': {'default_department_id': self.id},
        }
