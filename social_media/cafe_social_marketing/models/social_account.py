from odoo import fields, models


class CafeSocialAccount(models.Model):
    _name = "cafe.social.account"
    _description = "Social Media Account"
    _order = "name"

    name = fields.Char(
        string="Account Name",
        required=True,
    )

    platform = fields.Selection(
        [
            ("facebook", "Facebook"),
            ("instagram", "Instagram"),
            ("tiktok", "TikTok"),
            ("x", "X / Twitter"),
            ("other", "Other"),
        ],
        string="Platform",
        required=True,
    )

    handle = fields.Char(
        string="Handle",
    )

    branch_id = fields.Many2one(
        "cafe.social.branch",
        string="Branch",
        required=True,
        ondelete="cascade",
    )



    tiktok_access_token = fields.Char(
        string="TikTok Access Token",
        groups="cafe_social_marketing.group_cafe_social_manager",
        help=(
            "Development/testing token used by the TikTok Content Posting API. "
            "For production, replace manual token entry with TikTok OAuth."
        ),
    )

    tiktok_open_id = fields.Char(
        string="TikTok Open ID",
        groups="cafe_social_marketing.group_cafe_social_manager",
    )

    active = fields.Boolean(
        default=True,
    )