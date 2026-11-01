from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class HrAppraisalCompetencyCategory(models.Model):
    _name = 'hr.appraisal.competency.category'
    _description = 'Competency Category'
    _order = 'sequence, name'

    name = fields.Char(string='Category Name', required=True, translate=True)
    sequence = fields.Integer(string='Sequence', default=10)
    description = fields.Text(string='Description', translate=True)
    competency_ids = fields.One2many(
        'hr.appraisal.competency', 'category_id', string='Competencies')

class HrAppraisalCompetency(models.Model):
    _name = 'hr.appraisal.competency'
    _description = 'Competency'
    _order = 'category_id, name'

    name = fields.Char(string='Competency Title', required=True, translate=True)
    category_id = fields.Many2one(
        'hr.appraisal.competency.category', string='Category', required=True, index=True)
    description = fields.Text(string='Behavioral Descriptors / Expectations', translate=True)
    default_weight = fields.Float(string='Default Weight', default=1.0, required=True)
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company)

    @api.constrains('default_weight')
    def _check_default_weight(self):
        for rec in self:
            if rec.default_weight <= 0:
                raise ValidationError(_("Competency weight must be strictly positive."))

class HrAppraisalRatingScale(models.Model):
    _name = 'hr.appraisal.rating.scale'
    _description = 'Appraisal Rating Scale'
    _order = 'name'

    name = fields.Char(string='Scale Name', required=True, translate=True)
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company)
    level_ids = fields.One2many(
        'hr.appraisal.rating.scale.level', 'scale_id', string='Scale Levels', copy=True)
    min_score = fields.Float(string='Minimum Score', compute='_compute_min_max_score', store=True)
    max_score = fields.Float(string='Maximum Score', compute='_compute_min_max_score', store=True)

    @api.depends('level_ids.score_value')
    def _compute_min_max_score(self):
        for scale in self:
            scores = scale.level_ids.mapped('score_value')
            if scores:
                scale.min_score = min(scores)
                scale.max_score = max(scores)
            else:
                scale.min_score = 0.0
                scale.max_score = 5.0

class HrAppraisalRatingScaleLevel(models.Model):
    _name = 'hr.appraisal.rating.scale.level'
    _description = 'Rating Scale Level'
    _order = 'score_value desc, sequence'

    scale_id = fields.Many2one(
        'hr.appraisal.rating.scale', string='Scale', required=True, ondelete='cascade')
    name = fields.Char(string='Level Label', required=True, translate=True)
    score_value = fields.Float(string='Score Value (Points)', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    description = fields.Text(string='Performance Description', translate=True)
    color = fields.Integer(string='Color Index', default=0)

class HrAppraisalCompetencyEvaluation(models.Model):
    _name = 'hr.appraisal.competency.evaluation'
    _description = 'Appraisal Competency Evaluation'
    _order = 'category_id, competency_id'

    appraisal_id = fields.Many2one(
        'hr.appraisal', string='Appraisal', required=True, ondelete='cascade', index=True)
    competency_id = fields.Many2one(
        'hr.appraisal.competency', string='Competency', required=True)
    category_id = fields.Many2one(
        'hr.appraisal.competency.category', string='Category',
        related='competency_id.category_id', store=True, readonly=True)
    description = fields.Text(
        string='Expectations', related='competency_id.description', readonly=True)
    weight = fields.Float(string='Weight', default=1.0, required=True)

    self_rating_id = fields.Many2one(
        'hr.appraisal.rating.scale.level', string='Self Rating')
    self_score = fields.Float(
        string='Self Score', compute='_compute_self_score', store=True)
    self_comments = fields.Text(string='Self Assessment Comments')

    manager_rating_id = fields.Many2one(
        'hr.appraisal.rating.scale.level', string='Manager Rating')
    manager_score = fields.Float(
        string='Manager Score', compute='_compute_manager_score', store=True)
    manager_comments = fields.Text(string='Manager Evaluation Comments')

    hr_rating_id = fields.Many2one(
        'hr.appraisal.rating.scale.level', string='HR Rating')
    hr_score = fields.Float(
        string='HR Score', compute='_compute_hr_score', store=True)
    hr_comments = fields.Text(string='HR Remarks')

    final_score = fields.Float(
        string='Final Competency Score', compute='_compute_final_scores', store=True)
    weighted_score = fields.Float(
        string='Weighted Score', compute='_compute_final_scores', store=True)

    @api.depends('self_rating_id')
    def _compute_self_score(self):
        for rec in self:
            rec.self_score = rec.self_rating_id.score_value if rec.self_rating_id else 0.0

    @api.depends('manager_rating_id')
    def _compute_manager_score(self):
        for rec in self:
            rec.manager_score = rec.manager_rating_id.score_value if rec.manager_rating_id else 0.0

    @api.depends('hr_rating_id')
    def _compute_hr_score(self):
        for rec in self:
            rec.hr_score = rec.hr_rating_id.score_value if rec.hr_rating_id else 0.0

    @api.depends('manager_score', 'hr_score', 'weight')
    def _compute_final_scores(self):
        for rec in self:
            effective = rec.hr_score if rec.hr_score > 0 else rec.manager_score
            rec.final_score = effective
            rec.weighted_score = effective * (rec.weight or 1.0)
