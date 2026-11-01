from odoo import api, fields, models, _
from odoo.exceptions import UserError

class HrAppraisalBulkDeadlineWizard(models.TransientModel):
    _name = 'hr.appraisal.bulk.deadline.wizard'
    _description = 'Bulk Update Appraisal Deadlines'

    new_deadline = fields.Date(
        string='New Submission Deadline', required=True, default=fields.Date.context_today)
    reason = fields.Char(
        string='Extension Reason', required=True,
        default=lambda self: _('Company-wide schedule adjustment / Deadline extension'))

    def action_apply_deadline(self):
        self.ensure_one()
        appraisal_ids = self.env.context.get('active_ids', [])
        appraisals = self.env['hr.appraisal'].browse(appraisal_ids)
        if not appraisals:
            raise UserError(_("No appraisal records selected."))

        for app in appraisals:
            if app.state not in ['done', 'cancel']:
                app.write({'date_close': self.new_deadline})
                app.message_post(body=_("Deadline adjusted to %s. Reason: %s", self.new_deadline, self.reason))

        return {'type': 'ir.actions.act_window_close'}
