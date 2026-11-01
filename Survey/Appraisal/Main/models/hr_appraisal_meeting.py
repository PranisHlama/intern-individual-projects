from datetime import timedelta
from odoo import api, fields, models, _

class HrAppraisalMeeting(models.Model):
    _name = 'hr.appraisal.meeting'
    _description = 'Appraisal Review Meeting'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_datetime desc'

    name = fields.Char(string='Meeting Title', required=True, default=lambda self: _('Appraisal Review Session'))
    appraisal_id = fields.Many2one(
        'hr.appraisal', string='Appraisal', required=True, ondelete='cascade', index=True)
    employee_id = fields.Many2one(
        'hr.employee', string='Employee', related='appraisal_id.employee_id', store=True, readonly=True)
    manager_id = fields.Many2one(
        'hr.employee', string='Reviewing Manager', related='appraisal_id.manager_id', store=True, readonly=True)
    calendar_event_id = fields.Many2one(
        'calendar.event', string='Calendar Meeting', ondelete='set null')

    start_datetime = fields.Datetime(string='Scheduled Start', required=True, default=fields.Datetime.now)
    duration = fields.Float(string='Duration (Hours)', default=1.0)
    stop_datetime = fields.Datetime(string='Scheduled End', compute='_compute_stop_datetime', store=True)

    @api.depends('start_datetime', 'duration')
    def _compute_stop_datetime(self):
        for meeting in self:
            if meeting.start_datetime and meeting.duration:
                meeting.stop_datetime = meeting.start_datetime + timedelta(hours=meeting.duration)
            else:
                meeting.stop_datetime = meeting.start_datetime

    location = fields.Char(string='Physical Location / Room')
    video_url = fields.Char(
        string='Video Conference URL',
        help="Meeting link (e.g. Google Meet, Microsoft Teams, Zoom)")

    state = fields.Selection([
        ('scheduled', 'Scheduled'),
        ('held', 'Completed / Held'),
        ('rescheduled', 'Rescheduled'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='scheduled', required=True, tracking=True)

    employee_attended = fields.Boolean(string='Employee Attended', default=False)
    manager_attended = fields.Boolean(string='Manager Attended', default=False)

    agenda = fields.Html(string='Meeting Agenda & Talking Points')
    meeting_notes = fields.Html(string='Session Notes & Agreed Action Items')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if not rec.calendar_event_id and rec.appraisal_id:
                rec._sync_calendar_event()
        return records

    def _sync_calendar_event(self):
        """Create or update linked calendar.event for calendar view integration."""
        self.ensure_one()
        partner_ids = []
        if self.employee_id.user_id.partner_id:
            partner_ids.append(self.employee_id.user_id.partner_id.id)
        if self.manager_id.user_id.partner_id:
            partner_ids.append(self.manager_id.user_id.partner_id.id)

        cal_vals = {
            'name': _("Appraisal Meeting: %s & %s", self.employee_id.name, self.manager_id.name or 'Manager'),
            'start': self.start_datetime,
            'stop': fields.Datetime.add(self.start_datetime, hours=self.duration or 1.0),
            'duration': self.duration or 1.0,
            'description': self.video_url or self.name,
            'partner_ids': [(6, 0, partner_ids)],
            'res_model': 'hr.appraisal',
            'res_id': self.appraisal_id.id,
        }
        if self.calendar_event_id:
            self.calendar_event_id.write(cal_vals)
        else:
            cal_event = self.env['calendar.event'].create(cal_vals)
            self.calendar_event_id = cal_event.id

    def action_mark_held(self):
        self.write({
            'state': 'held',
            'employee_attended': True,
            'manager_attended': True,
        })
        self.message_post(body=_("Appraisal review meeting marked as held and notes documented."))
