from odoo import api, fields, models, _

class HrAppraisalSkillEvaluation(models.Model):
    _name = 'hr.appraisal.skill.evaluation'
    _description = 'Appraisal Skill & Gap Evaluation'
    _order = 'skill_type_id, skill_id'

    appraisal_id = fields.Many2one(
        'hr.appraisal', string='Appraisal', required=True, ondelete='cascade', index=True)
    employee_id = fields.Many2one(
        'hr.employee', string='Employee', related='appraisal_id.employee_id', store=True, readonly=True)
    
    skill_id = fields.Many2one('hr.skill', string='Skill', required=True)
    skill_type_id = fields.Many2one(
        'hr.skill.type', string='Skill Type', related='skill_id.skill_type_id', store=True, readonly=True)
    
    current_level_id = fields.Many2one(
        'hr.skill.level', string='Current Level',
        domain="[('skill_type_id', '=', skill_type_id)]")
    current_level_progress = fields.Integer(
        string='Current Level %', related='current_level_id.level_progress', readonly=True)

    evaluated_level_id = fields.Many2one(
        'hr.skill.level', string='Evaluated Level',
        domain="[('skill_type_id', '=', skill_type_id)]")
    evaluated_level_progress = fields.Integer(
        string='Evaluated Level %', related='evaluated_level_id.level_progress', readonly=True)

    target_level_id = fields.Many2one(
        'hr.skill.level', string='Target Level',
        domain="[('skill_type_id', '=', skill_type_id)]")
    target_level_progress = fields.Integer(
        string='Target Level %', related='target_level_id.level_progress', readonly=True)

    gap_status = fields.Selection([
        ('exceeds', 'Exceeds Target Level'),
        ('meets', 'Meets Target Level'),
        ('gap', 'Skill Gap Identified'),
    ], string='Gap Status', compute='_compute_gap_status', store=True)

    gap_description = fields.Char(string='Gap Summary', compute='_compute_gap_status', store=True)
    improvement_recommendation = fields.Text(string='Development / Training Recommendations')
    action_taken = fields.Boolean(string='Profile Updated', default=False, readonly=True)

    @api.depends('evaluated_level_progress', 'target_level_progress', 'current_level_progress')
    def _compute_gap_status(self):
        for rec in self:
            eval_prog = rec.evaluated_level_progress or rec.current_level_progress or 0
            target_prog = rec.target_level_progress or 0
            if target_prog == 0:
                rec.gap_status = 'meets'
                rec.gap_description = _("No target baseline set.")
            elif eval_prog >= target_prog + 15:
                rec.gap_status = 'exceeds'
                rec.gap_description = _("Current/evaluated level exceeds target (+%d%%)", eval_prog - target_prog)
            elif eval_prog >= target_prog:
                rec.gap_status = 'meets'
                rec.gap_description = _("Meets expected level.")
            else:
                rec.gap_status = 'gap'
                rec.gap_description = _("Skill gap of -%d%%", target_prog - eval_prog)

    def action_apply_to_employee_profile(self):
        """Sync validated skill evaluation back to employee's official hr.employee.skill profile."""
        for rec in self:
            if not rec.employee_id or not rec.skill_id or not rec.evaluated_level_id:
                continue
            emp_skill = self.env['hr.employee.skill'].search([
                ('employee_id', '=', rec.employee_id.id),
                ('skill_id', '=', rec.skill_id.id),
            ], limit=1)
            if emp_skill:
                emp_skill.skill_level_id = rec.evaluated_level_id.id
            else:
                self.env['hr.employee.skill'].create({
                    'employee_id': rec.employee_id.id,
                    'skill_id': rec.skill_id.id,
                    'skill_type_id': rec.skill_type_id.id,
                    'skill_level_id': rec.evaluated_level_id.id,
                })
            rec.action_taken = True
