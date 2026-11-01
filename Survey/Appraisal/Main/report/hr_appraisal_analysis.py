from odoo import api, fields, models, tools

class HrAppraisalAnalysis(models.Model):
    _name = 'hr.appraisal.analysis'
    _description = 'Appraisal Analytical Report'
    _auto = False
    _order = 'date_close desc'

    employee_id = fields.Many2one('hr.employee', string='Employee', readonly=True)
    manager_id = fields.Many2one('hr.employee', string='Manager', readonly=True)
    department_id = fields.Many2one('hr.department', string='Department', readonly=True)
    job_id = fields.Many2one('hr.job', string='Job Position', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    plan_id = fields.Many2one('hr.appraisal.plan', string='Appraisal Plan', readonly=True)
    stage_id = fields.Many2one('hr.appraisal.stage', string='Stage', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_self', 'Waiting Self Assessment'),
        ('self_done', 'Self Assessment Submitted'),
        ('waiting_manager', 'Waiting Manager Review'),
        ('manager_done', 'Manager Review Completed'),
        ('waiting_hr', 'Waiting HR Validation'),
        ('done', 'Completed'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True)

    review_period = fields.Char(string='Review Period', readonly=True)
    date_start = fields.Date(string='Start Date', readonly=True)
    date_close = fields.Date(string='Deadline', readonly=True)
    date_completed = fields.Date(string='Completion Date', readonly=True)
    days_to_complete = fields.Float(string='Days to Complete', readonly=True)

    is_overdue = fields.Boolean(string='Is Overdue', readonly=True)
    competency_score = fields.Float(string='Competency Score', readonly=True, aggregator='avg')
    goal_score = fields.Float(string='Goal Score', readonly=True, aggregator='avg')
    calculated_score = fields.Float(string='Calculated Score', readonly=True, aggregator='avg')
    final_score = fields.Float(string='Final Score', readonly=True, aggregator='avg')
    appraisal_count = fields.Integer(string='Number of Appraisals', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE or REPLACE VIEW %s AS (
                SELECT
                    a.id AS id,
                    a.employee_id AS employee_id,
                    a.manager_id AS manager_id,
                    a.department_id AS department_id,
                    a.job_id AS job_id,
                    a.company_id AS company_id,
                    a.plan_id AS plan_id,
                    a.stage_id AS stage_id,
                    s.stage_type AS state,
                    a.review_period AS review_period,
                    a.date_start AS date_start,
                    a.date_close AS date_close,
                    a.date_completed AS date_completed,
                    CASE 
                        WHEN a.date_completed IS NOT NULL THEN (a.date_completed - a.date_start)
                        ELSE NULL 
                    END AS days_to_complete,
                    CASE 
                        WHEN a.date_close < CURRENT_DATE AND s.stage_type NOT IN ('done', 'cancel') THEN TRUE
                        ELSE FALSE
                    END AS is_overdue,
                    COALESCE(a.competency_score, 0.0) AS competency_score,
                    COALESCE(a.goal_score, 0.0) AS goal_score,
                    COALESCE(a.calculated_score, 0.0) AS calculated_score,
                    COALESCE(a.final_score, 0.0) AS final_score,
                    1 AS appraisal_count
                FROM hr_appraisal a
                LEFT JOIN hr_appraisal_stage s ON a.stage_id = s.id
            )
        """ % self._table)
