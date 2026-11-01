from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class HrAppraisalAnswer(models.Model):
    _name = 'hr.appraisal.answer'
    _description = 'Appraisal Questionnaire Answer'
    _order = 'sequence, id'

    appraisal_id = fields.Many2one(
        'hr.appraisal', string='Appraisal', required=True, ondelete='cascade', index=True)
    question_id = fields.Many2one(
        'hr.appraisal.template.question', string='Question', required=True, ondelete='cascade')
    section_id = fields.Many2one(
        'hr.appraisal.template.section', string='Section', related='question_id.section_id', store=True)
    sequence = fields.Integer(
        string='Sequence', related='question_id.sequence', store=True)
    question_type = fields.Selection(
        related='question_id.question_type', store=True, readonly=True)

    respondent_type = fields.Selection([
        ('self', 'Employee Self-Assessment'),
        ('manager', 'Manager Evaluation'),
        ('hr', 'HR Validation'),
    ], string='Respondent Role', required=True, default='self')

    text_answer = fields.Char(string='Text Answer')
    paragraph_answer = fields.Text(string='Detailed Response')
    rating_answer = fields.Float(string='Rating Score')
    choice_id = fields.Many2one(
        'hr.appraisal.question.choice', string='Selected Option',
        domain="[('question_id', '=', question_id)]")
    choice_ids = fields.Many2many(
        'hr.appraisal.question.choice', 'hr_appraisal_answer_choice_rel',
        'answer_id', 'choice_id', string='Selected Multiple Options',
        domain="[('question_id', '=', question_id)]")
    boolean_answer = fields.Boolean(string='Yes / No Answer')
    date_answer = fields.Date(string='Date Answer')
    number_answer = fields.Float(string='Numeric Value')

    matrix_answer_ids = fields.One2many(
        'hr.appraisal.answer.matrix', 'answer_id', string='Matrix Ratings', copy=True)

    comments = fields.Text(string='Additional Remarks')
    calculated_score = fields.Float(
        string='Answer Points', compute='_compute_calculated_score', store=True)

    @api.depends('question_type', 'rating_answer', 'choice_id', 'matrix_answer_ids.score_value')
    def _compute_calculated_score(self):
        for rec in self:
            if rec.question_type == 'rating':
                rec.calculated_score = rec.rating_answer
            elif rec.question_type == 'selection' and rec.choice_id:
                rec.calculated_score = rec.choice_id.score_value
            elif rec.question_type == 'matrix' and rec.matrix_answer_ids:
                scores = rec.matrix_answer_ids.mapped('score_value')
                rec.calculated_score = sum(scores) / len(scores) if scores else 0.0
            else:
                rec.calculated_score = 0.0

    @api.constrains('paragraph_answer')
    def _check_char_limit(self):
        for rec in self:
            if rec.question_id.char_limit > 0 and rec.paragraph_answer:
                if len(rec.paragraph_answer) > rec.question_id.char_limit:
                    raise ValidationError(_("Answer exceeds maximum character limit of %s.", rec.question_id.char_limit))

class HrAppraisalAnswerMatrix(models.Model):
    _name = 'hr.appraisal.answer.matrix'
    _description = 'Matrix Question Criterion Response'
    _order = 'row_id'

    answer_id = fields.Many2one(
        'hr.appraisal.answer', string='Answer Header', required=True, ondelete='cascade')
    row_id = fields.Many2one(
        'hr.appraisal.matrix.row', string='Criterion / Area', required=True)
    col_id = fields.Many2one(
        'hr.appraisal.matrix.col', string='Rating Grade', required=True)
    score_value = fields.Float(
        string='Score Points', related='col_id.score_value', store=True)
