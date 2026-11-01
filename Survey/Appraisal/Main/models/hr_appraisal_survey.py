from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class HrAppraisalSurvey(models.Model):
    _name = 'hr.appraisal.survey'
    _description = 'Appraisal Survey / Assessment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'survey_type, id desc'

    name = fields.Char(
        string='Survey Title', compute='_compute_name', store=True, readonly=False, tracking=True)
    
    appraisal_id = fields.Many2one(
        'hr.appraisal', string='Appraisal Cycle', required=True, ondelete='cascade',
        index=True, tracking=True)
    
    survey_type = fields.Selection([
        ('self', 'Self Assessment'),
        ('peer', 'Peer Assessment'),
        ('manager', 'Manager Evaluation'),
    ], string='Survey Type', required=True, default='self', tracking=True)
    
    template_id = fields.Many2one(
        'hr.appraisal.template', string='Survey Template', required=True, ondelete='restrict',
        tracking=True)
    
    employee_id = fields.Many2one(
        'hr.employee', string='Employee Appraised', related='appraisal_id.employee_id',
        store=True, readonly=True)
    
    respondent_id = fields.Many2one(
        'hr.employee', string='Reviewer / Respondent', required=True, tracking=True)
    
    user_id = fields.Many2one(
        'res.users', string='Respondent User', related='respondent_id.user_id',
        store=True, readonly=True)
    
    state = fields.Selection([
        ('draft', 'Draft / Pending'),
        ('in_progress', 'In Progress'),
        ('submitted', 'Submitted / Completed'),
    ], string='Status', default='draft', tracking=True)
    
    date_deadline = fields.Date(
        string='Deadline', related='appraisal_id.date_close', store=True, readonly=False)
    
    date_completed = fields.Datetime(
        string='Date Completed', readonly=True, tracking=True)
    
    score = fields.Float(
        string='Survey Score (0-5)', compute='_compute_score', store=True, digits=(3, 2))
    
    answer_ids = fields.One2many(
        'hr.appraisal.survey.answer', 'survey_id', string='Survey Answers', copy=True)
    
    answer_count = fields.Integer(
        string='Answers Count', compute='_compute_answer_count')
    
    summary = fields.Text(
        string='Overall Feedback & Reflection',
        help="Overall qualitative review, takeaways, or recommendations.")
    
    company_id = fields.Many2one(
        'res.company', string='Company', related='appraisal_id.company_id', store=True)

    @api.depends('survey_type', 'employee_id.name', 'appraisal_id.name')
    def _compute_name(self):
        type_labels = {
            'self': _('Self Assessment'),
            'peer': _('Peer Assessment'),
            'manager': _('Manager Evaluation'),
        }
        for rec in self:
            label = type_labels.get(rec.survey_type, _('Survey'))
            emp_name = rec.employee_id.name or _('Employee')
            app_name = rec.appraisal_id.name or ''
            rec.name = f"[{label}] {emp_name} - {app_name}".strip(' -')

    @api.depends('answer_ids.score_value', 'answer_ids.rating_answer', 'answer_ids.question_type')
    def _compute_score(self):
        for rec in self:
            rated_answers = rec.answer_ids.filtered(lambda a: a.question_type == 'rating' and a.rating_answer > 0)
            if rated_answers:
                rec.score = sum(rated_answers.mapped('rating_answer')) / len(rated_answers)
            else:
                choice_scored = rec.answer_ids.filtered(lambda a: a.score_value > 0)
                if choice_scored:
                    rec.score = sum(choice_scored.mapped('score_value')) / len(choice_scored)
                else:
                    rec.score = 0.0

    @api.depends('answer_ids')
    def _compute_answer_count(self):
        for rec in self:
            rec.answer_count = len(rec.answer_ids)

    @api.onchange('survey_type', 'appraisal_id')
    def _onchange_survey_type_default_respondent(self):
        if self.appraisal_id:
            if self.survey_type == 'self':
                self.respondent_id = self.appraisal_id.employee_id
            elif self.survey_type == 'manager':
                self.respondent_id = self.appraisal_id.manager_id
            if not self.template_id:
                domain = [('active', '=', True)]
                if self.survey_type == 'self':
                    domain.append(('target_role', 'in', ['employee', 'both']))
                elif self.survey_type == 'manager':
                    domain.append(('target_role', 'in', ['manager', 'both']))
                elif self.survey_type == 'peer':
                    domain.append(('target_role', 'in', ['both', 'peer', 'employee']))
                template = self.env['hr.appraisal.template'].search(domain, limit=1)
                if template:
                    self.template_id = template

    @api.onchange('template_id')
    def _onchange_template_id(self):
        if self.template_id:
            self.action_load_questions()

    def action_load_questions(self):
        """Populate survey answer lines from the selected template."""
        self.ensure_one()
        if not self.template_id:
            return
        
        Answer = self.env['hr.appraisal.survey.answer']
        existing_q_ids = self.answer_ids.mapped('question_id.id')
        new_lines = []

        for q in self.template_id.question_ids:
            if self.survey_type == 'self' and q.target_respondent not in ['both', 'employee']:
                continue
            if self.survey_type == 'manager' and q.target_respondent not in ['both', 'manager']:
                continue

            if q.id not in existing_q_ids:
                new_lines.append((0, 0, {
                    'survey_id': self.id,
                    'question_id': q.id,
                }))

        if new_lines:
            self.update({'answer_ids': new_lines})

    def action_start(self):
        for rec in self:
            if not rec.answer_ids and rec.template_id:
                rec.action_load_questions()
            rec.state = 'in_progress'

    def action_submit(self):
        for rec in self:
            mandatory_unanswered = rec.answer_ids.filtered(
                lambda a: a.is_required and not (
                    a.text_answer or a.paragraph_answer or a.rating_answer or a.choice_id or a.boolean_answer
                )
            )
            if mandatory_unanswered:
                names = ", ".join(mandatory_unanswered.mapped('question_id.name')[:3])
                raise ValidationError(_("Please answer all mandatory questions before submitting: %s", names))

            rec.state = 'submitted'
            rec.date_completed = fields.Datetime.now()
            
            type_label = dict(rec._fields['survey_type'].selection).get(rec.survey_type, rec.survey_type)
            msg = _("Survey <b>%s</b> completed by <b>%s</b> for employee <b>%s</b> with overall score <b>%.2f/5.0</b>.",
                    type_label, rec.respondent_id.name, rec.employee_id.name, rec.score)
            rec.message_post(body=msg)
            if rec.appraisal_id:
                rec.appraisal_id.message_post(body=msg)

    def action_reset_draft(self):
        for rec in self:
            rec.state = 'draft'
            rec.date_completed = False

    def action_open_form(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.name,
            'res_model': 'hr.appraisal.survey',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_open_appraisal(self):
        self.ensure_one()
        return {
            'name': _("Appraisal"),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.appraisal',
            'res_id': self.appraisal_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

class HrAppraisalSurveyAnswer(models.Model):
    _name = 'hr.appraisal.survey.answer'
    _description = 'Appraisal Survey Answer'
    _order = 'sequence, id'

    survey_id = fields.Many2one(
        'hr.appraisal.survey', string='Survey', required=True, ondelete='cascade', index=True)
    
    question_id = fields.Many2one(
        'hr.appraisal.template.question', string='Question', required=True, ondelete='cascade')
    
    section_id = fields.Many2one(
        'hr.appraisal.template.section', string='Section', related='question_id.section_id', store=True)
    
    sequence = fields.Integer(
        string='Sequence', related='question_id.sequence', store=True)
    
    question_type = fields.Selection(
        related='question_id.question_type', store=True, readonly=True)
    
    is_required = fields.Boolean(
        string='Mandatory', related='question_id.is_required', store=True, readonly=True)
    
    rating_min = fields.Integer(
        string='Min Rating', related='question_id.rating_min', readonly=True)
    
    rating_max = fields.Integer(
        string='Max Rating', related='question_id.rating_max', readonly=True)
    
    help_text = fields.Text(
        string='Guidelines', related='question_id.help_text', readonly=True)
    
    text_answer = fields.Char(string='Short Text')
    paragraph_answer = fields.Text(string='Detailed Response')
    rating_answer = fields.Float(string='Rating (1-5)')
    choice_id = fields.Many2one(
        'hr.appraisal.question.choice', string='Selected Option',
        domain="[('question_id', '=', question_id)]")
    boolean_answer = fields.Boolean(string='Yes / No')
    comments = fields.Char(string='Remarks / Notes')
    
    score_value = fields.Float(
        string='Points / Score', compute='_compute_score_value', store=True)

    @api.depends('question_type', 'rating_answer', 'choice_id')
    def _compute_score_value(self):
        for rec in self:
            if rec.question_type == 'rating':
                rec.score_value = rec.rating_answer
            elif rec.question_type == 'selection' and rec.choice_id:
                rec.score_value = rec.choice_id.score_value
            elif rec.question_type == 'boolean':
                rec.score_value = 5.0 if rec.boolean_answer else 1.0
            else:
                rec.score_value = 0.0
