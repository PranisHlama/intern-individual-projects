from odoo import api, fields, models, _
from odoo.exceptions import UserError

class HrAppraisalReminderWizard(models.TransientModel):
    _name = 'hr.appraisal.reminder.wizard'
    _description = 'Send On-Demand Appraisal Reminders'

    target_recipient = fields.Selection([
        ('employee', 'Employee (Self-Assessment)'),
        ('manager', 'Manager (Review &amp; Rating)'),
        ('both', 'Both Employee and Manager'),
    ], string='Send Reminder To', default='both', required=True)

    subject = fields.Char(
        string='Email Subject', required=True,
        default=lambda self: _('Reminder: Pending Action on Performance Appraisal'))
    message = fields.Html(
        string='Custom Reminder Message', required=True,
        default=lambda self: _('<p>Please be advised that your performance appraisal review requires your prompt attention. Please submit outstanding sections before the impending deadline.</p>'))

    def action_send_reminders(self):
        self.ensure_one()
        appraisal_ids = self.env.context.get('active_ids', [])
        appraisals = self.env['hr.appraisal'].browse(appraisal_ids)
        if not appraisals:
            raise UserError(_("No appraisal records selected."))

        for app in appraisals:
            partners = []
            if self.target_recipient in ['employee', 'both'] and app.employee_user_id.partner_id:
                partners.append(app.employee_user_id.partner_id.id)
            if self.target_recipient in ['manager', 'both'] and app.manager_user_id.partner_id:
                partners.append(app.manager_user_id.partner_id.id)

            if partners:
                app.message_post(
                    body=self.message,
                    subject=self.subject,
                    partner_ids=partners,
                    message_type='comment',
                    subtype_xmlid='mail.mt_comment',
                )

        return {'type': 'ir.actions.act_window_close'}
