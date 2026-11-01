from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

def _get_progression_from_progress(progress_val):
    val = int(progress_val or 0)
    if val >= 88:
        return '100'
    elif val >= 63:
        return '75'
    elif val >= 38:
        return '50'
    elif val >= 13:
        return '25'
    else:
        return '0'

class HrAppraisalGoal(models.Model):
    _name = 'hr.appraisal.goal'
    _description = 'Performance Objective / Goal'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'due_date asc, id desc'

    name = fields.Char(string='Goal Title', required=True, tracking=True)
    template_id = fields.Many2one(
        'hr.appraisal.goal.template', string='Goal Template', tracking=True)
    description = fields.Html(string='Success Criteria / Key Results')
    employee_id = fields.Many2one(
        'hr.employee', string='Employee (Owner)', required=True, tracking=True, index=True)
    manager_id = fields.Many2one(
        'hr.employee', string='Reviewing Manager', related='employee_id.parent_id', store=True, readonly=True)
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company, required=True)
    appraisal_id = fields.Many2one(
        'hr.appraisal', string='Associated Appraisal', ondelete='cascade', index=True, tracking=True)

    start_date = fields.Date(string='Start Date', default=fields.Date.context_today)
    due_date = fields.Date(string='Deadline', required=True, tracking=True)
    completion_date = fields.Date(string='Completion Date', tracking=True)

    status = fields.Selection([
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('blocked', 'Blocked'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='not_started', required=True, tracking=True)

    weight = fields.Float(
        string='Weight (%)', default=10.0,
        help="Weight of this goal towards overall objective performance.")
    progression = fields.Selection([
        ('0', '0%'),
        ('25', '25%'),
        ('50', '50%'),
        ('75', '75%'),
        ('100', '100%'),
    ], string='Progress Milestone', default='0', tracking=True)
    progress = fields.Integer(
        string='Progress (%)', default=0, tracking=True,
        help="Progress towards objective completion (0-100%).")
    tag_ids = fields.Many2many('hr.appraisal.tag', string='Tags')

    manager_approval = fields.Selection([
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Revision Requested'),
    ], string='Manager Validation', default='pending', tracking=True)
    manager_feedback = fields.Text(string='Manager Feedback & Guidance')

    carried_from_goal_id = fields.Many2one(
        'hr.appraisal.goal', string='Carried From Previous Goal', readonly=True)
    carried_to_goal_id = fields.Many2one(
        'hr.appraisal.goal', string='Carried To Next Goal', readonly=True)
    is_carried_forward = fields.Boolean(
        string='Was Carried Forward', default=False, readonly=True)

    @api.constrains('progress')
    def _check_progress(self):
        for goal in self:
            if not (0 <= goal.progress <= 100):
                raise ValidationError(_("Goal progress must be between 0% and 100%."))

    @api.onchange('template_id')
    def _onchange_template_id(self):
        if self.template_id:
            if not self.name or self.name == self.template_id.name:
                self.name = self.template_id.name
            if self.template_id.description:
                self.description = self.template_id.description
            if self.template_id.weight and (not self.weight or self.weight == 10.0):
                self.weight = self.template_id.weight
            if self.template_id.tag_ids and not self.tag_ids:
                self.tag_ids = [(6, 0, self.template_id.tag_ids.ids)]

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id and not self.appraisal_id:
            if self.employee_id.ongoing_appraisal_id:
                self.appraisal_id = self.employee_id.ongoing_appraisal_id

    @api.onchange('appraisal_id')
    def _onchange_appraisal_id(self):
        if self.appraisal_id and not self.employee_id:
            self.employee_id = self.appraisal_id.employee_id

    @api.onchange('progression')
    def _onchange_progression(self):
        if self.progression is not False and self.progression is not None:
            self.progress = int(self.progression)
            if self.progress == 100:
                self.status = 'completed'
                self.completion_date = fields.Date.context_today(self)
            elif self.status == 'completed' and self.progress < 100:
                self.status = 'in_progress'
                self.completion_date = False

    @api.onchange('progress')
    def _onchange_progress(self):
        self.progression = _get_progression_from_progress(self.progress)
        if self.progress == 100 and self.status != 'completed':
            self.status = 'completed'
            self.completion_date = fields.Date.context_today(self)
        elif self.progress < 100 and self.status == 'completed':
            self.status = 'in_progress'
            self.completion_date = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'progression' in vals and 'progress' not in vals:
                vals['progress'] = int(vals['progression'])
            elif 'progress' in vals and 'progression' not in vals:
                vals['progression'] = _get_progression_from_progress(vals['progress'])
            elif 'progression' in vals and 'progress' in vals:
                if vals.get('progress') == 0 and vals.get('progression') not in ['0', 0, False, None]:
                    vals['progress'] = int(vals['progression'])
                elif vals.get('progress', 0) > 0 and vals.get('progression') in ['0', 0, False, None]:
                    vals['progression'] = _get_progression_from_progress(vals['progress'])

            if vals.get('progress') == 100 and vals.get('status') not in ['completed', 'cancelled']:
                vals['status'] = 'completed'
                if not vals.get('completion_date'):
                    vals['completion_date'] = fields.Date.today()
            elif vals.get('progress', 0) > 0 and vals.get('status') in [False, 'not_started', None]:
                vals['status'] = 'in_progress'

            if not vals.get('employee_id') and vals.get('appraisal_id'):
                appraisal = self.env['hr.appraisal'].browse(vals['appraisal_id'])
                if appraisal.employee_id:
                    vals['employee_id'] = appraisal.employee_id.id
            if not vals.get('appraisal_id') and vals.get('employee_id'):
                emp = self.env['hr.employee'].browse(vals['employee_id'])
                if emp.ongoing_appraisal_id:
                    vals['appraisal_id'] = emp.ongoing_appraisal_id.id

        return super().create(vals_list)

    def write(self, vals):
        if 'progression' in vals and 'progress' not in vals:
            vals['progress'] = int(vals['progression'])
        elif 'progress' in vals and 'progression' not in vals:
            vals['progression'] = _get_progression_from_progress(vals['progress'])
        elif 'progression' in vals and 'progress' in vals:
            if vals.get('progress') == 0 and vals.get('progression') not in ['0', 0, False, None]:
                vals['progress'] = int(vals['progression'])
            elif vals.get('progress', 0) > 0 and vals.get('progression') in ['0', 0, False, None]:
                vals['progression'] = _get_progression_from_progress(vals['progress'])

        if 'progress' in vals:
            new_prog = vals['progress']
            if new_prog == 100:
                if 'status' not in vals:
                    vals['status'] = 'completed'
                if 'completion_date' not in vals:
                    vals['completion_date'] = fields.Date.today()
            elif new_prog < 100:
                for goal in self:
                    if goal.status == 'completed' or (goal.status == 'not_started' and new_prog > 0):
                        if 'status' not in vals:
                            vals['status'] = 'in_progress'
                        if 'completion_date' not in vals:
                            vals['completion_date'] = False
                        break

        return super().write(vals)

    def action_approve_goal(self):
        for goal in self:
            goal.manager_approval = 'approved'
            goal.message_post(body=_("Goal approved by manager %s.", self.env.user.name))

    def action_reject_goal(self):
        for goal in self:
            goal.manager_approval = 'rejected'
            goal.message_post(body=_("Goal rejected / revision requested by manager %s.", self.env.user.name))

    def action_mark_completed(self):
        for goal in self:
            goal.write({
                'progression': '100',
                'progress': 100,
                'status': 'completed',
                'completion_date': fields.Date.context_today(self),
            })
            goal.message_post(body=_("Goal marked as Completed."))

    def action_mark_done(self):
        return self.action_mark_completed()

    def action_save_as_template(self):
        self.ensure_one()
        template = self.env['hr.appraisal.goal.template'].create({
            'name': self.name,
            'description': self.description or '',
            'recommended_for': self.employee_id.job_id.name or self.employee_id.department_id.name or _('All Employees'),
            'sub_goals': self.name,
            'weight': self.weight,
            'tag_ids': [(6, 0, self.tag_ids.ids)],
        })
        self.template_id = template.id
        self.message_post(body=_("Goal saved as template '%s' in Goal Template Library.", template.name))
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Saved as Template'),
                'message': _("Goal '%s' successfully saved to Goal Template Library.", self.name),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_open_library(self):
        action = self.env['ir.actions.act_window']._for_xml_id('hr_appraisal_pro.action_hr_appraisal_goal_template_modal')
        return action

    def action_carry_forward(self, target_appraisal=None):
        """Carry forward an uncompleted goal to a new appraisal or standalone active goal."""
        self.ensure_one()
        if self.status == 'completed':
            raise ValidationError(_("Cannot carry forward an already completed goal."))
        if self.carried_to_goal_id:
            raise ValidationError(_("This goal has already been carried forward to '%s'.", self.carried_to_goal_id.name))

        new_goal = self.copy({
            'name': _("%s (Carried Forward)", self.name),
            'appraisal_id': target_appraisal.id if target_appraisal else False,
            'carried_from_goal_id': self.id,
            'progress': self.progress,
            'progression': self.progression,
            'status': 'in_progress' if self.progress > 0 else 'not_started',
            'manager_approval': 'pending',
            'start_date': fields.Date.context_today(self),
        })
        self.write({
            'carried_to_goal_id': new_goal.id,
            'is_carried_forward': True,
        })
        self.message_post(body=_("Goal carried forward to new objective #%s (%s).", new_goal.id, new_goal.name))
        return new_goal
