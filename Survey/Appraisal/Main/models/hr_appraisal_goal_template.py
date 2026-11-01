from odoo import api, fields, models, _

class HrAppraisalGoalTemplate(models.Model):
    _name = 'hr.appraisal.goal.template'
    _description = 'Goal Template Library'
    _order = 'id desc'

    name = fields.Char(string='Name', required=True)
    recommended_for = fields.Char(
        string='Recommended for',
        help="Target roles, departments, or levels recommended for this goal.")
    sub_goals = fields.Char(
        string='Sub Goals',
        help="Sub-goals or milestone objectives included in this template.")
    description = fields.Html(string='Description / Key Results')
    weight = fields.Float(string='Default Weight (%)', default=10.0)
    tag_ids = fields.Many2many('hr.appraisal.tag', string='Tags')
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company)
    active = fields.Boolean(string='Active', default=True)

    def action_create_goal(self):
        """Create a new goal from this template or open a form view with prefilled values."""
        self.ensure_one()
        context = dict(self.env.context)
        context.update({
            'default_name': self.name,
            'default_description': self.description,
            'default_weight': self.weight,
            'default_template_id': self.id,
            'default_tag_ids': [(6, 0, self.tag_ids.ids)],
        })
        return {
            'name': _("New Goal from Template"),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.appraisal.goal',
            'view_mode': 'form',
            'target': 'current',
            'context': context,
        }
