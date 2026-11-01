from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class HrAppraisal(models.Model):
    _name = 'hr.appraisal'
    _description = 'Employee Appraisal Record'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_close asc, id desc'

    name = fields.Char(
        string='Reference', required=True, copy=False, readonly=True,
        default=lambda self: _('New'))
    
    employee_id = fields.Many2one(
        'hr.employee', string='Employee', required=True, tracking=True, index=True)
    employee_user_id = fields.Many2one(
        'res.users', string='Employee User Account', related='employee_id.user_id', store=True, readonly=True)
    manager_id = fields.Many2one(
        'hr.employee', string='Reviewing Manager', tracking=True, index=True)
    manager_user_id = fields.Many2one(
        'res.users', string='Manager User Account', related='manager_id.user_id', store=True, readonly=True)
    department_id = fields.Many2one(
        'hr.department', string='Department', tracking=True, index=True)
    job_id = fields.Many2one(
        'hr.job', string='Job Position', tracking=True)
    avatar_128 = fields.Image(related='employee_id.avatar_128', string='Employee Avatar')
    manager_avatar_128 = fields.Image(related='manager_id.avatar_128', string='Manager Avatar')
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company, required=True, index=True)
    
    plan_id = fields.Many2one(
        'hr.appraisal.plan', string='Appraisal Plan', tracking=True, ondelete='set null')
    template_id = fields.Many2one(
        'hr.appraisal.template', string='Questionnaire Template')
    rating_scale_id = fields.Many2one(
        'hr.appraisal.rating.scale', string='Rating Scale')
    hr_responsible_id = fields.Many2one(
        'res.users', string='HR Officer Responsible', default=lambda self: self.env.user, tracking=True)

    review_period = fields.Char(string='Review Period', required=False, default=lambda self: _('Annual Review'))
    date_start = fields.Date(
        string='Start Date', default=fields.Date.context_today, required=True, tracking=True)
    date_close = fields.Date(
        string='Submission Deadline', required=True, tracking=True)
    date_completed = fields.Date(string='Final Completion Date', readonly=True, tracking=True)

    stage_id = fields.Many2one(
        'hr.appraisal.stage', string='Stage', required=True, tracking=True, index=True,
        default=lambda self: self._get_default_stage(), group_expand='_read_group_stage_ids')
    state = fields.Selection(
        related='stage_id.stage_type', string='Stage Status', store=True, readonly=True, index=True)

    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Important'),
        ('2', 'High Priority'),
        ('3', 'Urgent / Executive'),
    ], string='Priority', default='0', tracking=True)

    tag_ids = fields.Many2many(
        'hr.appraisal.tag', 'hr_appraisal_tag_rel', 'appraisal_id', 'tag_id', string='Tags')
    notes = fields.Html(string='General Notes & Guidance')
    confidential_notes = fields.Html(
        string='HR Confidential Observations',
        help="Restricted strictly to HR Managers and System Administrators.")

    self_assessment_status = fields.Selection([
        ('not_started', 'Not Started'),
        ('in_progress', 'Drafting'),
        ('submitted', 'Submitted'),
    ], string='Self Assessment Status', default='not_started', tracking=True)
    self_assessment_date = fields.Datetime(string='Self Submission Timestamp', readonly=True)
    self_assessment_progress = fields.Integer(
        string='Self Assessment Progress (%)', compute='_compute_self_assessment_progress')
    self_strengths = fields.Text(string='Self-Identified Strengths')
    self_development_areas = fields.Text(string='Self-Identified Growth Opportunities')
    self_career_aspirations = fields.Text(string='Personal Career Aspirations')
    self_general_comments = fields.Text(string='Employee Closing Remarks')

    manager_assessment_status = fields.Selection([
        ('pending', 'Pending Evaluation'),
        ('in_progress', 'Drafting Evaluation'),
        ('submitted', 'Evaluation Completed'),
    ], string='Manager Evaluation Status', default='pending', tracking=True)
    manager_assessment_date = fields.Datetime(string='Manager Submission Timestamp', readonly=True)
    manager_overall_summary = fields.Text(string='Overall Performance Summary')
    manager_strengths = fields.Text(string='Observed Strengths & Achievements')
    manager_weaknesses = fields.Text(string='Areas for Improvement')
    manager_goals_feedback = fields.Text(string='Goals & Objectives Review')
    
    promotion_recommendation = fields.Selection([
        ('none', 'Not Ready / Maintain Role'),
        ('ready_now', 'Ready for Immediate Promotion'),
        ('within_1yr', 'High Potential - Ready Within 1 Year'),
        ('realign', 'Role Realignment / Reassignment Recommended'),
    ], string='Promotion Recommendation', default='none', tracking=True)

    salary_recommendation = fields.Selection([
        ('none', 'No Adjustment'),
        ('standard_merit', 'Standard Merit Increase (3-5%)'),
        ('high_performer', 'High Performer Exceptional Increase (6-10%)'),
        ('market_correction', 'Market Rate Upward Correction'),
        ('freeze', 'Salary Freeze'),
    ], string='Compensation Recommendation', default='none', tracking=True)

    training_recommendation = fields.Html(string='Recommended Development Courses & Action Plan')
    manager_confidential_notes = fields.Text(
        string='Manager Confidential Notes for HR',
        help="Visible only to reviewing Manager and HR Officers.")

    hr_validation_date = fields.Datetime(string='HR Sign-Off Timestamp', readonly=True)
    hr_validation_notes = fields.Text(string='HR Committee Summary / Calibration Notes')
    hr_approved = fields.Boolean(string='HR Validation Endorsed', default=False, readonly=True)

    competency_score = fields.Float(
        string='Competency Weighted Score', compute='_compute_appraisal_scores', store=True, digits=(3, 2))
    goal_score = fields.Float(
        string='Goal Achievement Score', compute='_compute_appraisal_scores', store=True, digits=(3, 2))
    goal_progress = fields.Float(
        string='Goal Completion (%)', compute='_compute_appraisal_scores', store=True, digits=(5, 1))
    calculated_score = fields.Float(
        string='System Calculated Score', compute='_compute_appraisal_scores', store=True, digits=(3, 2))
    score_override = fields.Float(
        string='Calibrated Score Override', digits=(3, 2), tracking=True,
        help="If set, this calibrated score takes precedence over the automated calculation.")
    score_override_reason = fields.Text(string='Score Override Justification')
    final_score = fields.Float(
        string='Final Overall Score', compute='_compute_final_score', store=True, digits=(3, 2), tracking=True)

    competency_line_ids = fields.One2many(
        'hr.appraisal.competency.evaluation', 'appraisal_id', string='Competency Evaluations', copy=True)
    goal_ids = fields.One2many(
        'hr.appraisal.goal', 'appraisal_id', string='Appraisal Goals', copy=True)
    skill_evaluation_ids = fields.One2many(
        'hr.appraisal.skill.evaluation', 'appraisal_id', string='Skill Gap Evaluations', copy=True)
    career_plan_ids = fields.One2many(
        'hr.appraisal.career.plan', 'appraisal_id', string='Career Development Plans')
    meeting_ids = fields.One2many(
        'hr.appraisal.meeting', 'appraisal_id', string='Appraisal Meetings')
    survey_ids = fields.One2many(
        'hr.appraisal.survey', 'appraisal_id', string='Surveys & Assessments')
    answer_ids = fields.One2many(
        'hr.appraisal.answer', 'appraisal_id', string='Questionnaire Answers', copy=True)
    audit_log_ids = fields.One2many(
        'hr.appraisal.audit.log', 'appraisal_id', string='Audit Logs', readonly=True)

    meeting_count = fields.Integer(string='Meetings Count', compute='_compute_sub_counts')
    goal_count = fields.Integer(string='Goals Count', compute='_compute_sub_counts')
    skill_count = fields.Integer(string='Skills Count', compute='_compute_sub_counts')
    audit_count = fields.Integer(string='Audit Events Count', compute='_compute_sub_counts')
    survey_count = fields.Integer(string='Surveys Count', compute='_compute_sub_counts')
    is_overdue = fields.Boolean(string='Overdue', compute='_compute_is_overdue', store=True)

    def _get_default_stage(self):
        return self.env['hr.appraisal.stage'].search([('stage_type', '=', 'draft')], limit=1)

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        return self.env['hr.appraisal.stage'].search([], order=order)

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            self.manager_id = self.employee_id.parent_id
            self.department_id = self.employee_id.department_id
            self.job_id = self.employee_id.job_id
            self.company_id = self.employee_id.company_id
            standalone_goals = self.env['hr.appraisal.goal'].search([
                ('employee_id', '=', self.employee_id.id),
                ('appraisal_id', '=', False),
                ('status', 'in', ['not_started', 'in_progress', 'blocked']),
            ])
            if standalone_goals:
                self.goal_ids = [(4, g.id) for g in standalone_goals]

    @api.depends('competency_line_ids.weighted_score', 'competency_line_ids.weight', 'goal_ids.progress', 'goal_ids.weight')
    def _compute_appraisal_scores(self):
        for rec in self:
            total_comp_weight = sum(rec.competency_line_ids.mapped('weight')) or 0.0
            total_comp_weighted_score = sum(rec.competency_line_ids.mapped('weighted_score')) or 0.0
            rec.competency_score = (total_comp_weighted_score / total_comp_weight) if total_comp_weight > 0 else 0.0

            goals = rec.goal_ids.filtered(lambda g: g.status != 'cancelled')
            total_goal_weight = sum(goals.mapped('weight')) or 0.0
            if total_goal_weight > 0:
                weighted_progress = sum((g.progress / 100.0) * g.weight for g in goals)
                rec.goal_score = (weighted_progress / total_goal_weight) * 5.0
                rec.goal_progress = (weighted_progress / total_goal_weight) * 100.0
            else:
                rec.goal_score = 0.0
                rec.goal_progress = 0.0

            if goals and rec.competency_line_ids:
                rec.calculated_score = (rec.competency_score * 0.6) + (rec.goal_score * 0.4)
            elif rec.competency_line_ids:
                rec.calculated_score = rec.competency_score
            elif goals:
                rec.calculated_score = rec.goal_score
            else:
                rec.calculated_score = 0.0

    @api.depends('calculated_score', 'score_override')
    def _compute_final_score(self):
        for rec in self:
            if rec.score_override > 0:
                rec.final_score = rec.score_override
            else:
                rec.final_score = rec.calculated_score

    @api.depends('answer_ids', 'template_id.question_ids')
    def _compute_self_assessment_progress(self):
        for rec in self:
            questions = rec.template_id.question_ids.filtered(
                lambda q: q.target_respondent in ['both', 'employee'])
            if not questions:
                rec.self_assessment_progress = 100 if rec.self_assessment_status == 'submitted' else 0
                continue
            answered = rec.answer_ids.filtered(
                lambda a: a.respondent_type == 'self' and (
                    a.text_answer or a.paragraph_answer or a.rating_answer or a.choice_id or a.choice_ids or a.matrix_answer_ids or a.boolean_answer or a.date_answer or a.number_answer))
            rec.self_assessment_progress = min(100, int((len(answered) / len(questions)) * 100))

    @api.depends('meeting_ids', 'goal_ids', 'skill_evaluation_ids', 'audit_log_ids', 'survey_ids')
    def _compute_sub_counts(self):
        for rec in self:
            rec.meeting_count = len(rec.meeting_ids)
            rec.goal_count = len(rec.goal_ids)
            rec.skill_count = len(rec.skill_evaluation_ids)
            rec.audit_count = len(rec.audit_log_ids)
            rec.survey_count = len(rec.survey_ids)

    @api.depends('date_close', 'state')
    def _compute_is_overdue(self):
        today = fields.Date.context_today(self)
        for rec in self:
            rec.is_overdue = bool(rec.date_close and rec.date_close < today and rec.state not in ['done', 'cancel'])

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hr.appraisal') or _('APP/%s') % fields.Date.today().year
        records = super().create(vals_list)
        for rec in records:
            rec._log_audit('stage_change', False, rec.stage_id.name, _("Appraisal created in %s stage.", rec.stage_id.name))
            if rec.employee_id and not rec.goal_ids:
                standalone_goals = self.env['hr.appraisal.goal'].search([
                    ('employee_id', '=', rec.employee_id.id),
                    ('appraisal_id', '=', False),
                    ('status', 'in', ['not_started', 'in_progress', 'blocked']),
                ])
                if standalone_goals:
                    standalone_goals.write({'appraisal_id': rec.id})
                    rec._compute_appraisal_scores()
        return records

    def action_link_employee_goals(self):
        """Finds any active standalone goals for the appraisal's employee and links them."""
        self.ensure_one()
        standalone_goals = self.env['hr.appraisal.goal'].search([
            ('employee_id', '=', self.employee_id.id),
            ('appraisal_id', '=', False),
            ('status', '!=', 'cancelled'),
        ])
        if not standalone_goals:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Standalone Goals Found'),
                    'message': _("All goals for %s are already linked to this appraisal.", self.employee_id.name),
                    'type': 'info',
                    'sticky': False,
                }
            }
        count = len(standalone_goals)
        standalone_goals.write({'appraisal_id': self.id})
        self._compute_appraisal_scores()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Goals Linked'),
                'message': _("%d standalone goal(s) successfully linked to this appraisal.", count),
                'type': 'success',
                'sticky': False,
            }
        }

    def write(self, vals):
        old_scores = {rec.id: rec.final_score for rec in self} if 'score_override' in vals else {}
        old_managers = {rec.id: rec.manager_id for rec in self} if 'manager_id' in vals else {}
        old_deadlines = {rec.id: rec.date_close for rec in self} if 'date_close' in vals else {}

        res = super().write(vals)

        for rec in self:
            if 'score_override' in vals and old_scores.get(rec.id) != rec.final_score:
                rec._log_audit('score_change', str(old_scores.get(rec.id)), str(rec.final_score),
                               vals.get('score_override_reason', _("Score overridden.")))
            if 'manager_id' in vals and old_managers.get(rec.id) != rec.manager_id:
                rec._log_audit('manager_change', old_managers[rec.id].name if old_managers.get(rec.id) else 'None',
                               rec.manager_id.name if rec.manager_id else 'None', _("Reviewing manager reassigned."))
            if 'date_close' in vals and old_deadlines.get(rec.id) != rec.date_close:
                rec._log_audit('deadline_change', str(old_deadlines.get(rec.id)), str(rec.date_close), _("Deadline adjusted."))

        return res

    def _log_audit(self, action_type, old_val, new_val, notes=None):
        self.ensure_one()
        self.env['hr.appraisal.audit.log'].create({
            'appraisal_id': self.id,
            'user_id': self.env.user.id,
            'action_type': action_type,
            'old_value': str(old_val) if old_val else '',
            'new_value': str(new_val) if new_val else '',
            'notes': notes or '',
        })

    def _populate_template_questions(self):
        """Populate initial questionnaire answer lines if a template is linked."""
        self.ensure_one()
        if not self.template_id:
            return
        Answer = self.env['hr.appraisal.answer']
        MatrixAnswer = self.env['hr.appraisal.answer.matrix']
        for q in self.template_id.question_ids:
            if q.target_respondent in ['both', 'employee']:
                existing_self = Answer.search([
                    ('appraisal_id', '=', self.id),
                    ('question_id', '=', q.id),
                    ('respondent_type', '=', 'self'),
                ], limit=1)
                if not existing_self:
                    ans = Answer.create({
                        'appraisal_id': self.id,
                        'question_id': q.id,
                        'respondent_type': 'self',
                    })
                    if q.question_type == 'matrix' and q.matrix_row_ids and q.matrix_col_ids:
                        for row in q.matrix_row_ids:
                            MatrixAnswer.create({
                                'answer_id': ans.id,
                                'row_id': row.id,
                                'col_id': q.matrix_col_ids[0].id,
                            })

            if q.target_respondent in ['both', 'manager']:
                existing_mgr = Answer.search([
                    ('appraisal_id', '=', self.id),
                    ('question_id', '=', q.id),
                    ('respondent_type', '=', 'manager'),
                ], limit=1)
                if not existing_mgr:
                    ans = Answer.create({
                        'appraisal_id': self.id,
                        'question_id': q.id,
                        'respondent_type': 'manager',
                    })
                    if q.question_type == 'matrix' and q.matrix_row_ids and q.matrix_col_ids:
                        for row in q.matrix_row_ids:
                            MatrixAnswer.create({
                                'answer_id': ans.id,
                                'row_id': row.id,
                                'col_id': q.matrix_col_ids[0].id,
                            })

    def _populate_standard_competencies(self):
        """Populate active standard competencies for this appraisal evaluation."""
        self.ensure_one()
        active_comps = self.env['hr.appraisal.competency'].search([
            ('active', '=', True),
            ('company_id', '=', self.company_id.id),
        ])
        EvalLine = self.env['hr.appraisal.competency.evaluation']
        for comp in active_comps:
            existing = EvalLine.search([
                ('appraisal_id', '=', self.id),
                ('competency_id', '=', comp.id),
            ], limit=1)
            if not existing:
                EvalLine.create({
                    'appraisal_id': self.id,
                    'competency_id': comp.id,
                    'weight': comp.default_weight or 1.0,
                })

    def _populate_employee_skills(self):
        """Preload employee existing skills from hr.employee.skill."""
        self.ensure_one()
        if not self.employee_id:
            return
        emp_skills = self.env['hr.employee.skill'].search([('employee_id', '=', self.employee_id.id)])
        EvalSkill = self.env['hr.appraisal.skill.evaluation']
        for es in emp_skills:
            existing = EvalSkill.search([
                ('appraisal_id', '=', self.id),
                ('skill_id', '=', es.skill_id.id),
            ], limit=1)
            if not existing:
                EvalSkill.create({
                    'appraisal_id': self.id,
                    'skill_id': es.skill_id.id,
                    'current_level_id': es.skill_level_id.id,
                    'evaluated_level_id': es.skill_level_id.id,
                })

    def _set_stage(self, stage_type, transition_note=""):
        target_stage = self.env['hr.appraisal.stage'].search([('stage_type', '=', stage_type)], limit=1)
        if not target_stage:
            raise UserError(_("Stage of type '%s' is not defined in the system.", stage_type))
        for rec in self:
            old_stage_name = rec.stage_id.name
            rec.stage_id = target_stage.id
            rec._log_audit('stage_change', old_stage_name, target_stage.name, transition_note)
            
            if target_stage.mail_template_id:
                target_stage.mail_template_id.send_mail(rec.id, force_send=True)
            if target_stage.auto_activity_type_id:
                rec._schedule_stage_activity(target_stage)

    def _schedule_stage_activity(self, stage):
        self.ensure_one()
        assign_user = self.employee_user_id
        if stage.auto_activity_user == 'manager' and self.manager_user_id:
            assign_user = self.manager_user_id
        elif stage.auto_activity_user == 'hr' and self.hr_responsible_id:
            assign_user = self.hr_responsible_id

        if assign_user:
            self.activity_schedule(
                activity_type_id=stage.auto_activity_type_id.id,
                summary=stage.auto_activity_summary or stage.name,
                user_id=assign_user.id,
                date_deadline=self.date_close,
            )

    def action_send_self_assessment(self):
        """Transition from Draft to Waiting Self Assessment."""
        for rec in self:
            rec._populate_template_questions()
            rec._populate_standard_competencies()
            rec._populate_employee_skills()
            rec.action_generate_default_surveys()
            rec._set_stage('waiting_self', _("Self-assessment initiated and dispatched to employee."))
            rec.self_assessment_status = 'in_progress'
            rec.message_post(body=_("Appraisal self-assessment requested for %s.", rec.employee_id.name))

    def action_launch_campaign(self):
        action = self.env['ir.actions.act_window']._for_xml_id('hr_appraisal_pro.action_appraisal_create_wizard')
        return action

    def action_submit_self_assessment(self):
        """Employee submits self assessment."""
        for rec in self:
            unanswered = rec.answer_ids.filtered(
                lambda a: a.respondent_type == 'self' and a.question_id.is_required and not (
                    a.text_answer or a.paragraph_answer or a.rating_answer or a.choice_id or a.choice_ids or a.matrix_answer_ids or a.boolean_answer or a.date_answer or a.number_answer))
            if unanswered:
                raise ValidationError(_("Please answer all mandatory self-assessment questions before submitting."))

            rec.self_assessment_status = 'submitted'
            rec.self_assessment_date = fields.Datetime.now()
            rec._set_stage('self_done', _("Employee completed and submitted self-assessment."))
            rec.message_post(body=_("Self-assessment successfully submitted by employee."))

    def action_start_manager_review(self):
        """Advance to Waiting Manager Review."""
        for rec in self:
            rec.manager_assessment_status = 'in_progress'
            rec._set_stage('waiting_manager', _("Manager performance evaluation initiated."))

    def action_submit_manager_review(self):
        """Manager completes performance rating and feedback."""
        for rec in self:
            unrated = rec.competency_line_ids.filtered(lambda c: not c.manager_rating_id)
            if unrated:
                raise ValidationError(_("Please provide a rating for all competencies before submitting the review."))

            rec.manager_assessment_status = 'submitted'
            rec.manager_assessment_date = fields.Datetime.now()
            rec._set_stage('manager_done', _("Manager evaluation completed."))
            rec.message_post(body=_("Manager evaluation completed by %s.", self.env.user.name))

    def action_send_hr_validation(self):
        """Send appraisal to HR for review and calibration."""
        for rec in self:
            rec._set_stage('waiting_hr', _("Submitted to HR for review and calibration."))

    def action_validate_hr(self):
        """HR finalizes appraisal, locks records, updates employee skills."""
        for rec in self:
            rec.hr_approved = True
            rec.hr_validation_date = fields.Datetime.now()
            rec.date_completed = fields.Date.context_today(self)
            rec._set_stage('done', _("HR calibration approved and appraisal completed."))
            
            for skill_eval in rec.skill_evaluation_ids:
                skill_eval.action_apply_to_employee_profile()

            rec.action_carry_forward_unfinished_goals()

            rec.message_post(body=_("Appraisal finalized and locked with score %s.", rec.final_score))

    def action_cancel(self):
        """Cancel appraisal record."""
        for rec in self:
            rec._set_stage('cancel', _("Appraisal cancelled."))
            rec.message_post(body=_("Appraisal cycle has been cancelled."))

    def action_reopen(self):
        """Reopen cancelled or completed appraisal (HR only)."""
        draft_stage = self._get_default_stage()
        for rec in self:
            rec.stage_id = draft_stage.id
            rec.hr_approved = False
            rec.date_completed = False
            rec._log_audit('reset', rec.stage_id.name, draft_stage.name, _("Appraisal reopened by HR."))
            rec.message_post(body=_("Appraisal reopened and reset to Draft."))

    def action_schedule_meeting(self):
        """Quick action wizard/creation to schedule 1-on-1 review meeting."""
        self.ensure_one()
        meeting = self.env['hr.appraisal.meeting'].create({
            'appraisal_id': self.id,
            'name': _("Review: %s", self.name),
            'start_datetime': fields.Datetime.now() + relativedelta(days=1),
        })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Appraisal Review Meeting'),
            'res_model': 'hr.appraisal.meeting',
            'res_id': meeting.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_carry_forward_unfinished_goals(self):
        """Carries forward any incomplete goals into pending goal pool."""
        for rec in self:
            incomplete_goals = rec.goal_ids.filtered(lambda g: g.status in ['not_started', 'in_progress', 'blocked'])
            for goal in incomplete_goals:
                if not goal.carried_to_goal_id:
                    goal.action_carry_forward()

    def action_open_surveys(self):
        """Open all survey forms linked to this appraisal cycle."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Surveys & Assessments: %s', self.name),
            'res_model': 'hr.appraisal.survey',
            'view_mode': 'list,kanban,form',
            'domain': [('appraisal_id', '=', self.id)],
            'context': {
                'default_appraisal_id': self.id,
                'default_employee_id': self.employee_id.id,
            },
        }

    def action_generate_default_surveys(self):
        """Generates the 3 separate surveys (Self, Peer, Manager) if they don't already exist."""
        Survey = self.env['hr.appraisal.survey']
        Job = self.env['hr.job']
        for rec in self:
            job = rec.job_id or (rec.employee_id.job_id if rec.employee_id else False)
            if not job:
                job = Job.search([], limit=1)
                if not job:
                    job = Job.create({'name': 'Employee'})
            for s_type, resp in [
                ('self', rec.employee_id),
                ('manager', rec.manager_id),
                ('peer', rec.employee_id),
            ]:
                if resp and not rec.survey_ids.filtered(lambda s: s.survey_type == s_type):
                    survey = Survey.create({
                        'appraisal_id': rec.id,
                        'survey_type': s_type,
                        'job_id': job.id if job else False,
                        'employee_id': rec.employee_id.id if rec.employee_id else False,
                        'respondent_id': resp.id,
                    })
                    survey.action_load_questions()

    def action_launch_survey_popup(self, survey_type='self'):
        """Opens a Google Forms-styled Survey popup dialog."""
        self.ensure_one()
        Survey = self.env['hr.appraisal.survey']
        job = self.job_id or (self.employee_id.job_id if self.employee_id else False)
        if not job:
            job = self.env['hr.job'].search([], limit=1)

        survey = self.survey_ids.filtered(lambda s: s.survey_type == survey_type and s.state == 'draft')
        if not survey:
            resp_id = self.employee_id.id
            if survey_type == 'manager' and self.manager_id:
                resp_id = self.manager_id.id
            survey = Survey.create({
                'appraisal_id': self.id,
                'job_id': job.id if job else False,
                'survey_type': survey_type,
                'employee_id': self.employee_id.id if self.employee_id else False,
                'respondent_id': resp_id,
            })
            survey.action_load_questions()
        else:
            survey = survey[0]
            if not survey.answer_ids:
                survey.action_load_questions()

        return {
            'name': _('Survey: %s', dict(survey._fields['survey_type'].selection).get(survey.survey_type)),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.appraisal.survey',
            'res_id': survey.id,
            'view_mode': 'form',
            'view_id': self.env.ref('hr_appraisal_pro.view_hr_appraisal_survey_form').id,
            'target': 'new',
            'context': {
                'default_appraisal_id': self.id,
                'default_job_id': job.id if job else False,
                'default_survey_type': survey_type,
                'default_employee_id': self.employee_id.id if self.employee_id else False,
            },
        }

    def action_open_self_survey(self):
        """Opens the Self Assessment Survey in a popup window."""
        return self.action_launch_survey_popup(survey_type='self')

    def action_open_manager_survey(self):
        """Opens the Manager Evaluation Survey in a popup window."""
        return self.action_launch_survey_popup(survey_type='manager')

    def action_open_peer_survey(self):
        """Opens the Peer Assessment Survey in a popup window."""
        return self.action_launch_survey_popup(survey_type='peer')

    @api.model
    def cron_check_deadline_reminders(self):
        """Send automated reminder 7 days, 3 days, and on deadline day."""
        today = fields.Date.context_today(self)
        appraisals = self.search([
            ('state', 'in', ['waiting_self', 'waiting_manager', 'waiting_hr']),
            ('date_close', '!=', False),
        ])
        for app in appraisals:
            delta = (app.date_close - today).days
            if delta in [7, 3, 0]:
                template = self.env.ref('hr_appraisal_pro.mail_template_appraisal_deadline_reminder', raise_if_not_found=False)
                if template:
                    template.send_mail(app.id, force_send=True)
                app.message_post(body=_("Automated deadline reminder sent (%d day(s) remaining).", delta))

    @api.model
    def cron_escalate_overdue_appraisals(self):
        """Escalate overdue reviews to department head or HR."""
        today = fields.Date.context_today(self)
        overdue_records = self.search([
            ('state', 'in', ['waiting_self', 'waiting_manager']),
            ('date_close', '<', today),
        ])
        for app in overdue_records:
            app.priority = '3'
            template = self.env.ref('hr_appraisal_pro.mail_template_appraisal_escalation', raise_if_not_found=False)
            if template:
                template.send_mail(app.id, force_send=True)
            app.message_post(body=_("ESCALATION: Appraisal is overdue beyond deadline %s.", app.date_close))

    @api.model
    def cron_auto_archive_completed(self):
        """Auto-archive appraisals completed more than 365 days ago."""
        threshold = fields.Date.context_today(self) - relativedelta(years=1)
        old_completed = self.search([
            ('state', '=', 'done'),
            ('date_completed', '<', threshold),
            ('active', '=', True),
        ])
        old_completed.write({'active': False})

    @api.model
    def get_dashboard_metrics(self):
        """Fetch real-time metrics for the interactive Owl Dashboard."""
        Appraisal = self.env['hr.appraisal']
        user = self.env.user
        today = fields.Date.context_today(self)

        total_active = Appraisal.search_count([('state', 'not in', ['done', 'cancel'])])
        waiting_self = Appraisal.search_count([('state', '=', 'waiting_self')])
        waiting_manager = Appraisal.search_count([('state', '=', 'waiting_manager')])
        waiting_hr = Appraisal.search_count([('state', '=', 'waiting_hr')])
        completed = Appraisal.search_count([('state', '=', 'done')])
        overdue = Appraisal.search_count([('state', 'not in', ['done', 'cancel']), ('date_close', '<', today)])

        done_records = Appraisal.search([('state', '=', 'done')])
        scores = done_records.filtered(lambda a: a.final_score > 0).mapped('final_score')
        avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0

        my_count = Appraisal.search_count([('employee_user_id', '=', user.id), ('state', 'not in', ['done', 'cancel'])])
        team_count = Appraisal.search_count([('manager_user_id', '=', user.id), ('state', 'not in', ['done', 'cancel'])])

        recent = Appraisal.search([], order='id desc', limit=6)
        recent_data = [{
            'id': r.id,
            'name': r.name,
            'employee': r.employee_id.name,
            'manager': r.manager_id.name or 'Unassigned',
            'department': r.department_id.name or 'General',
            'deadline': str(r.date_close) if r.date_close else '',
            'stage': r.stage_id.name,
            'score': f"{r.final_score:.2f}" if r.final_score > 0 else 'N/A',
            'is_overdue': r.is_overdue,
        } for r in recent]

        return {
            'total_active': total_active,
            'waiting_self': waiting_self,
            'waiting_manager': waiting_manager,
            'waiting_hr': waiting_hr,
            'completed': completed,
            'overdue': overdue,
            'avg_score': avg_score,
            'my_count': my_count,
            'team_count': team_count,
            'recent_appraisals': recent_data,
        }

class HrAppraisalTag(models.Model):
    _name = 'hr.appraisal.tag'
    _description = 'Appraisal Tag'

    name = fields.Char(string='Tag Name', required=True, translate=True)
    color = fields.Integer(string='Color Index', default=0)
