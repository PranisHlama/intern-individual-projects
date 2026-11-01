from odoo import api, fields, models, _
from odoo.exceptions import UserError

class HrAppraisalBulkManagerWizard(models.TransientModel):
    _name = 'hr.appraisal.bulk.manager.wizard'
    _description = 'Bulk Reassign Reviewing Manager'

    manager_id = fields.Many2one(
        'hr.employee', string='New Reviewing Manager', required=True)
    reason = fields.Char(
        string='Reason for Reassignment', required=True,
        default=lambda self: _('Organizational restructuring / Manager rotation'))

    def action_apply_manager(self):
        self.ensure_one()
        appraisal_ids = self.env.context.get('active_ids', [])
        appraisals = self.env['hr.appraisal'].browse(appraisal_ids)
        if not appraisals:
            raise UserError(_("No appraisal records selected."))

        for app in appraisals:
            app.write({
                'manager_id': self.manager_id.id,
            })
            app.message_post(body=_("Manager reassigned to %s. Reason: %s", self.manager_id.name, self.reason))

        return {'type': 'ir.actions.act_window_close'}
