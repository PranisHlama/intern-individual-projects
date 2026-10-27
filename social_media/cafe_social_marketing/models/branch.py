from odoo import fields, models


class CafeSocialBranch(models.Model):
    _name = "cafe.social.branch"
    _description = "Cafe Branch"
    _order = "name"

    name = fields.Char(
        string="Branch Name",
        required=True,
    )

    code = fields.Char(
        string="Branch Code",
    )

    address = fields.Text(
        string="Address",
    )

    active = fields.Boolean(
        default=True,
    )