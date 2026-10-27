from odoo import api, fields, models
from odoo.exceptions import ValidationError


class CafeSocialCampaign(models.Model):
    _name = "cafe.social.campaign"
    _description = "Social Marketing Campaign"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_start desc, id desc"

    name = fields.Char(
        string="Campaign Name",
        required=True,
        tracking=True,
    )

    branch_id = fields.Many2one(
        "cafe.social.branch",
        string="Branch",
        required=True,
        tracking=True,
    )

    product_id = fields.Many2one(
        "product.product",
        string="Product",
    )

    discount = fields.Float(
        string="Discount (%)",
    )

    date_start = fields.Date(
        string="Start Date",
        required=True,
    )

    date_end = fields.Date(
        string="End Date",
        required=True,
    )

    duration_days = fields.Integer(
        string="Duration (days)", compute="_compute_calendar_details",
        help="Total campaign days, including both the start and end date.",
    )
    calendar_all_day = fields.Boolean(compute="_compute_calendar_details")

    @api.depends("date_start", "date_end")
    def _compute_calendar_details(self):
        for campaign in self:
            campaign.calendar_all_day = True
            campaign.duration_days = (
                max(0, (campaign.date_end - campaign.date_start).days + 1)
                if campaign.date_start and campaign.date_end else 0
            )

    social_account_ids = fields.Many2many(
        "cafe.social.account",
        string="Allowed Social Accounts",
    )

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        required=True,
        tracking=True,
    )

    # ---------------------------------------------------------
    # VALIDATION
    # ---------------------------------------------------------

    @api.constrains("date_start", "date_end")
    def _check_campaign_dates(self):
        for campaign in self:
            if (
                campaign.date_start
                and campaign.date_end
                and campaign.date_end < campaign.date_start
            ):
                raise ValidationError(
                    "The campaign end date cannot be before the start date."
                )

    @api.constrains("discount")
    def _check_discount(self):
        for campaign in self:
            if campaign.discount < 0 or campaign.discount > 100:
                raise ValidationError(
                    "Discount must be between 0% and 100%."
                )

    # ---------------------------------------------------------
    # CAMPAIGN WORKFLOW
    # ---------------------------------------------------------

    def action_activate(self):
        for campaign in self:
            campaign.state = "active"

    def action_complete(self):
        for campaign in self:
            campaign.state = "completed"

    def action_cancel(self):
        for campaign in self:
            campaign.state = "cancelled"

    def action_reset_draft(self):
        for campaign in self:
            campaign.state = "draft"
