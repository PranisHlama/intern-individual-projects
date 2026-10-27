from odoo import fields, models


class CafeSocialPostTemplate(models.Model):
    _name = "cafe.social.post.template"
    _description = "Social Post Template"

    name = fields.Char(
        string="Template Name",
        required=True,
    )

    message = fields.Text(
        string="Template Message",
        required=True,
    )

    branch_id = fields.Many2one(
        "cafe.social.branch",
        string="Branch",
    )

    active = fields.Boolean(
        default=True,
    )