from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..services.ollama_service import review_social_post


class CafeSocialPostAI(models.Model):
    _inherit = "cafe.social.post"

    ai_review_status = fields.Selection(
        [
            ("not_reviewed", "Not Reviewed"),
            ("reviewed", "Reviewed"),
            ("error", "Review Error"),
        ],
        string="AI Review Status",
        default="not_reviewed",
        readonly=True,
        tracking=True,
    )

    ai_overall_status = fields.Char(
        string="AI Assessment",
        readonly=True,
    )

    ai_tone = fields.Text(
        string="Tone",
        readonly=True,
    )

    ai_clarity = fields.Text(
        string="Clarity",
        readonly=True,
    )

    ai_issues = fields.Text(
        string="Potential Issues",
        readonly=True,
    )

    ai_suggested_rewrite = fields.Text(
        string="Suggested Rewrite",
        readonly=True,
    )

    ai_reviewed_at = fields.Datetime(
        string="AI Reviewed At",
        readonly=True,
    )

    def action_ai_review(self):
        for post in self:
            if not post.message:
                raise ValidationError(
                    "Please enter a post message before running AI Review."
                )

            campaign = post.campaign_id

            post_data = {
                "message": post.message or "",
                "branch": (
                    post.branch_id.name
                    if post.branch_id
                    else ""
                ),
                "campaign": (
                    campaign.name
                    if campaign
                    else ""
                ),
                "product": (
                    campaign.product_id.display_name
                    if campaign and campaign.product_id
                    else ""
                ),
                "discount": (
                    f"{campaign.discount:g}%"
                    if campaign and campaign.discount
                    else ""
                ),
                "start_date": (
                    fields.Date.to_string(
                        campaign.date_start
                    )
                    if campaign and campaign.date_start
                    else ""
                ),
                "end_date": (
                    fields.Date.to_string(
                        campaign.date_end
                    )
                    if campaign and campaign.date_end
                    else ""
                ),
                "social_accounts": ", ".join(
                    post.social_account_ids.mapped("name")
                ),
            }

            try:
                result = review_social_post(
                    post_data
                )

            except RuntimeError as error:
                post.write({
                    "ai_review_status": "error",
                })

                raise UserError(
                    str(error)
                )

            issues = result.get(
                "potential_issues",
                [],
            )

            if isinstance(issues, list):
                issues_text = "\n".join(
                    "• " + str(issue)
                    for issue in issues
                )
            else:
                issues_text = str(issues)

            post.write({
                "ai_review_status": "reviewed",
                "ai_overall_status": result.get(
                    "overall_status",
                    "",
                ),
                "ai_tone": result.get(
                    "tone",
                    "",
                ),
                "ai_clarity": result.get(
                    "clarity",
                    "",
                ),
                "ai_issues": issues_text,
                "ai_suggested_rewrite": result.get(
                    "suggested_rewrite",
                    "",
                ),
                "ai_reviewed_at": fields.Datetime.now(),
            })

    def action_apply_ai_suggestion(self):
        for post in self:
            if not post.ai_suggested_rewrite:
                raise ValidationError(
                    "There is no AI suggestion to apply."
                )

            suggestion = post.ai_suggested_rewrite

            post.write({
                "message": suggestion,
            })

    @api.onchange(
        "message",
        "branch_id",
        "campaign_id",
        "social_account_ids",
    )
    def _onchange_reset_ai_review(self):
        for post in self:
            post.ai_review_status = "not_reviewed"
            post.ai_overall_status = False
            post.ai_tone = False
            post.ai_clarity = False
            post.ai_issues = False
            post.ai_suggested_rewrite = False
            post.ai_reviewed_at = False

    def write(self, vals):
        content_fields = {
            "message",
            "branch_id",
            "campaign_id",
            "social_account_ids",
            "attachment_ids",
        }

        if content_fields.intersection(vals.keys()):
            vals = dict(vals)

            vals.update({
                "ai_review_status": "not_reviewed",
                "ai_overall_status": False,
                "ai_tone": False,
                "ai_clarity": False,
                "ai_issues": False,
                "ai_suggested_rewrite": False,
                "ai_reviewed_at": False,
            })

        return super().write(vals)