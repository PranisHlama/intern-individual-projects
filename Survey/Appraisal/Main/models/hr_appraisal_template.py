from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class HrAppraisalTemplate(models.Model):
    _name = 'hr.appraisal.template'
    _description = 'Appraisal Questionnaire Template'
    _order = 'name'

    name = fields.Char(string='Template Title', required=True, translate=True)
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company)
    description = fields.Html(string='Instructions / Description', translate=True)
    target_role = fields.Selection([
        ('both', 'Both Employee & Manager'),
        ('employee', 'Employee Self-Assessment Only'),
        ('manager', 'Manager Evaluation Only'),
        ('peer', 'Peer Assessment (360 Review)'),
        ('all', 'All Review Types'),
    ], string='Target Audience', default='both', required=True)
    survey_type = fields.Selection([
        ('all', 'General / Universal'),
        ('self', 'Self Assessment'),
        ('peer', 'Peer Assessment'),
        ('manager', 'Manager Evaluation'),
    ], string='Survey Category', default='all')
    
    section_ids = fields.One2many(
        'hr.appraisal.template.section', 'template_id', string='Sections', copy=True)
    question_ids = fields.One2many(
        'hr.appraisal.template.question', 'template_id', string='Questions', copy=True)

    question_count = fields.Integer(
        string='Questions Count', compute='_compute_question_count')

    @api.depends('question_ids')
    def _compute_question_count(self):
        for rec in self:
            rec.question_count = len(rec.question_ids)

    def action_duplicate_template(self):
        self.ensure_one()
        new_template = self.copy({
            'name': _("%s (Copy)", self.name)
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.appraisal.template',
            'view_mode': 'form',
            'res_id': new_template.id,
        }

class HrAppraisalTemplateSection(models.Model):
    _name = 'hr.appraisal.template.section'
    _description = 'Appraisal Questionnaire Section'
    _order = 'sequence, id'

    name = fields.Char(string='Section Title', required=True, translate=True)
    sequence = fields.Integer(string='Sequence', default=10)
    template_id = fields.Many2one(
        'hr.appraisal.template', string='Appraisal Template', required=True, ondelete='cascade')
    description = fields.Text(string='Section Objective / Guidelines', translate=True)
    question_ids = fields.One2many(
        'hr.appraisal.template.question', 'section_id', string='Questions')

class HrAppraisalTemplateQuestion(models.Model):
    _name = 'hr.appraisal.template.question'
    _description = 'Appraisal Question'
    _order = 'sequence, id'

    name = fields.Char(string='Question / Prompt', required=True, translate=True)
    sequence = fields.Integer(string='Sequence', default=10)
    template_id = fields.Many2one(
        'hr.appraisal.template', string='Template', required=True, ondelete='cascade')
    section_id = fields.Many2one(
        'hr.appraisal.template.section', string='Section', ondelete='cascade',
        domain="[('template_id', '=', template_id)]")
    
    question_type = fields.Selection([
        ('text', 'Single Line Text'),
        ('paragraph', 'Paragraph / Long Text'),
        ('rating', 'Numeric Rating Scale'),
        ('selection', 'Single Choice (Dropdown / Radio)'),
        ('multiple_choice', 'Multiple Choice (Checkboxes)'),
        ('boolean', 'Yes / No Toggle'),
        ('date', 'Date Picker'),
        ('number', 'Numeric Value'),
        ('matrix', 'Matrix Rating Grid'),
    ], string='Question Type', required=True, default='paragraph')

    is_required = fields.Boolean(string='Mandatory', default=False)
    target_respondent = fields.Selection([
        ('both', 'Both Employee & Manager'),
        ('employee', 'Employee Only (Self-Assessment)'),
        ('manager', 'Manager Only (Evaluation)'),
        ('peer', 'Peer Reviewers (360 Review)'),
        ('all', 'All Reviewers'),
        ('hr', 'HR Validation Only'),
    ], string='Respondent Scope', default='both', required=True)

    rating_min = fields.Integer(string='Minimum Rating', default=1)
    rating_max = fields.Integer(string='Maximum Rating', default=5)
    char_limit = fields.Integer(
        string='Character Limit', default=0,
        help="Maximum characters allowed. Set to 0 for unlimited.")
    help_text = fields.Text(string='Help / Guidance Note', translate=True)

    choice_ids = fields.One2many(
        'hr.appraisal.question.choice', 'question_id', string='Options', copy=True)
    matrix_row_ids = fields.One2many(
        'hr.appraisal.matrix.row', 'question_id', string='Matrix Criteria (Rows)', copy=True)
    matrix_col_ids = fields.One2many(
        'hr.appraisal.matrix.col', 'question_id', string='Matrix Scales (Columns)', copy=True)

    is_conditional = fields.Boolean(
        string='Is Conditional', default=False,
        help="Show this question only when a parent question meets a specific answer.")
    parent_question_id = fields.Many2one(
        'hr.appraisal.template.question', string='Parent Question',
        domain="[('template_id', '=', template_id), ('id', '!=', id)]")
    trigger_choice_id = fields.Many2one(
        'hr.appraisal.question.choice', string='Show When Answer Equals',
        domain="[('question_id', '=', parent_question_id)]")

    @api.constrains('rating_min', 'rating_max')
    def _check_ratings(self):
        for q in self:
            if q.question_type == 'rating' and q.rating_min >= q.rating_max:
                raise ValidationError(_("Minimum rating (%s) must be strictly less than maximum rating (%s).",
                                        q.rating_min, q.rating_max))

class HrAppraisalQuestionChoice(models.Model):
    _name = 'hr.appraisal.question.choice'
    _description = 'Question Option Choice'
    _order = 'sequence, id'

    name = fields.Char(string='Choice Option', required=True, translate=True)
    sequence = fields.Integer(string='Sequence', default=10)
    question_id = fields.Many2one(
        'hr.appraisal.template.question', string='Question', required=True, ondelete='cascade')
    score_value = fields.Float(string='Score Weight / Points', default=0.0)

class HrAppraisalMatrixRow(models.Model):
    _name = 'hr.appraisal.matrix.row'
    _description = 'Matrix Question Criterion (Row)'
    _order = 'sequence, id'

    name = fields.Char(string='Criterion / Topic', required=True, translate=True)
    sequence = fields.Integer(string='Sequence', default=10)
    question_id = fields.Many2one(
        'hr.appraisal.template.question', string='Question', required=True, ondelete='cascade')

class HrAppraisalMatrixCol(models.Model):
    _name = 'hr.appraisal.matrix.col'
    _description = 'Matrix Question Scale (Column)'
    _order = 'sequence, id'

    name = fields.Char(string='Scale Label', required=True, translate=True)
    sequence = fields.Integer(string='Sequence', default=10)
    score_value = fields.Float(string='Numeric Equivalent', default=1.0)
    question_id = fields.Many2one(
        'hr.appraisal.template.question', string='Question', required=True, ondelete='cascade')
