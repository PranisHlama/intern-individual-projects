import base64
import mimetypes
import re

from markupsafe import Markup, escape
from odoo import api, fields, models
from odoo.exceptions import ValidationError

from ..services.tiktok_service import TikTokAPIError, TikTokService


class CafeSocialPost(models.Model):
    _name = "cafe.social.post"
    _description = "Social Media Post"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    name = fields.Char(
        string="Post Title",
        required=True,
        tracking=True,
    )

    message = fields.Text(
        string="Post Message",
        tracking=True,
    )

    branch_id = fields.Many2one(
        "cafe.social.branch",
        string="Branch",
        required=True,
        tracking=True,
    )

    campaign_id = fields.Many2one(
        "cafe.social.campaign",
        string="Campaign",
        tracking=True,
    )

    template_id = fields.Many2one(
        "cafe.social.post.template",
        string="Post Template",
    )

    social_account_ids = fields.Many2many(
        "cafe.social.account",
        string="Post On",
    )

    attachment_ids = fields.Many2many(
        "ir.attachment",
        string="Media",
    )

    video_file = fields.Binary(
        string="Video Attachment",
        attachment=True,
        help="Video attached for platforms such as TikTok.",
    )

    video_filename = fields.Char(
        string="Video Filename",
    )

    has_tiktok_account = fields.Boolean(
        string="Has TikTok Account",
        compute="_compute_has_tiktok_account",
    )

    tiktok_publish_id = fields.Char(
        string="TikTok Publish ID",
        readonly=True,
        copy=False,
    )

    tiktok_remote_status = fields.Char(
        string="TikTok Status",
        readonly=True,
        copy=False,
    )

    tiktok_status_message = fields.Text(
        string="TikTok Status Message",
        readonly=True,
        copy=False,
    )

    tiktok_uploaded_at = fields.Datetime(
        string="Uploaded to TikTok At",
        readonly=True,
        copy=False,
    )

    scheduled_at = fields.Datetime(
        string="Scheduled Date",
        tracking=True,
    )

    published_at = fields.Datetime(
        string="Published At",
        readonly=True,
    )

    preview_html = fields.Html(
        string="Post Preview",
        compute="_compute_preview_html",
        sanitize=False,
    )

    validation_status = fields.Selection(
        [
            ("not_validated", "Not Validated"),
            ("passed", "Passed"),
            ("failed", "Failed"),
        ],
        string="Compliance Status",
        default="not_validated",
        readonly=True,
        tracking=True,
    )

    validation_result = fields.Text(
        string="Validation Result",
        readonly=True,
    )

    validated_at = fields.Datetime(
        string="Last Validated",
        readonly=True,
    )

    approval_state = fields.Selection(
        [
            ("not_submitted", "Not Submitted"),
            ("pending", "Pending Approval"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        string="Approval Status",
        default="not_submitted",
        readonly=True,
        tracking=True,
    )

    submitted_at = fields.Datetime(
        string="Submitted At",
        readonly=True,
    )

    approved_by_id = fields.Many2one(
        "res.users",
        string="Approved By",
        readonly=True,
    )

    approved_at = fields.Datetime(
        string="Approved At",
        readonly=True,
    )

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("scheduled", "Scheduled"),
            ("published", "Published"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    # ---------------------------------------------------------
    # VIDEO / TIKTOK HELPERS
    # ---------------------------------------------------------

    @api.depends("social_account_ids", "social_account_ids.platform")
    def _compute_has_tiktok_account(self):
        for post in self:
            post.has_tiktok_account = any(
                account.platform == "tiktok"
                for account in post.social_account_ids
            )

    def _get_tiktok_accounts(self):
        self.ensure_one()
        return self.social_account_ids.filtered(
            lambda account: account.platform == "tiktok"
        )

    def _get_tiktok_account(self):
        self.ensure_one()
        accounts = self._get_tiktok_accounts()

        if not accounts:
            raise ValidationError(
                "Select a TikTok social account before using TikTok upload."
            )

        if len(accounts) > 1:
            raise ValidationError(
                "The current TikTok MVP supports one TikTok account per post."
            )

        return accounts[0]

    def _get_video_mimetype(self):
        self.ensure_one()
        mime_type, _encoding = mimetypes.guess_type(
            self.video_filename or ""
        )
        return mime_type or "application/octet-stream"

    def _decode_video(self):
        self.ensure_one()

        if not self.video_file:
            raise ValidationError(
                "Attach a video before sending this post to TikTok."
            )

        mime_type = self._get_video_mimetype()

        if mime_type not in TikTokService.SUPPORTED_MIME_TYPES:
            raise ValidationError(
                "TikTok video must be MP4, MOV, or WebM. "
                "MP4 with H.264 is recommended."
            )

        try:
            video_data = base64.b64decode(self.video_file)
        except Exception as exc:
            raise ValidationError(
                "The attached video could not be decoded."
            ) from exc

        if not video_data:
            raise ValidationError("The attached video is empty.")

        if len(video_data) > TikTokService.MAX_VIDEO_SIZE:
            raise ValidationError(
                "TikTok video uploads cannot exceed 4 GB."
            )

        return video_data, mime_type

    def action_upload_tiktok_draft(self):
        if not self.env.user.has_group(
            "cafe_social_marketing.group_cafe_social_manager"
        ):
            raise ValidationError(
                "Only a Marketing Manager can send an approved post to TikTok."
            )

        for post in self:
            post._ensure_post_is_compliant()

            if post.approval_state != "approved":
                raise ValidationError(
                    "The post must be approved before it can be uploaded to TikTok."
                )

            account = post._get_tiktok_account()
            access_token = account.sudo().tiktok_access_token

            if not access_token:
                raise ValidationError(
                    "The selected TikTok account does not have an access token. "
                    "Add a token in Social Accounts first."
                )

            video_data, mime_type = post._decode_video()

            try:
                publish_id = TikTokService.upload_video_as_draft(
                    access_token,
                    video_data,
                    mime_type,
                )
            except TikTokAPIError as exc:
                post.write({
                    "tiktok_remote_status": "FAILED",
                    "tiktok_status_message": str(exc),
                })
                raise ValidationError(str(exc)) from exc

            post.write({
                "tiktok_publish_id": publish_id,
                "tiktok_remote_status": "UPLOADED",
                "tiktok_status_message": (
                    "Video sent to TikTok. Open TikTok inbox to continue "
                    "editing and complete the post."
                ),
                "tiktok_uploaded_at": fields.Datetime.now(),
            })

            post.message_post(
                body=(
                    "Video uploaded to TikTok as a draft. "
                    f"Publish ID: {publish_id}"
                )
            )

        return True

    def action_check_tiktok_status(self):
        for post in self:
            if not post.tiktok_publish_id:
                raise ValidationError(
                    "This post has not been sent to TikTok yet."
                )

            account = post._get_tiktok_account()
            access_token = account.sudo().tiktok_access_token

            if not access_token:
                raise ValidationError(
                    "The selected TikTok account does not have an access token."
                )

            try:
                data = TikTokService.fetch_status(
                    access_token,
                    post.tiktok_publish_id,
                )
            except TikTokAPIError as exc:
                raise ValidationError(str(exc)) from exc

            remote_status = data.get("status") or "UNKNOWN"
            fail_reason = data.get("fail_reason") or ""
            post_ids = (
                data.get("publicaly_available_post_id")
                or data.get("publicly_available_post_id")
                or []
            )

            details = [f"Status: {remote_status}"]
            if fail_reason:
                details.append(f"Reason: {fail_reason}")
            if post_ids:
                details.append(
                    "TikTok Post ID: " + ", ".join(map(str, post_ids))
                )

            post.write({
                "tiktok_remote_status": remote_status,
                "tiktok_status_message": "\n".join(details),
            })

        return True

    # ---------------------------------------------------------
    # POST PREVIEW
    # ---------------------------------------------------------

    @api.depends(
        "message",
        "branch_id",
        "campaign_id",
        "social_account_ids",
    )
    def _compute_preview_html(self):
        for post in self:
            branch = escape(
                post.branch_id.name or "No branch selected"
            )

            campaign = escape(
                post.campaign_id.name or "No campaign selected"
            )

            accounts = ", ".join(
                post.social_account_ids.mapped("name")
            )

            accounts = escape(
                accounts or "No social account selected"
            )

            message = escape(
                post.message or "Your post preview will appear here."
            )

            message = message.replace(
                "\n",
                Markup("<br/>"),
            )

            post.preview_html = Markup("""
                <div style="
                    width: 100%;
                    max-width: 900px;
                    min-height: 260px;
                    box-sizing: border-box;
                    border: 1px solid #ddd;
                    border-radius: 14px;
                    padding: 28px;
                    background: white;
                    margin-top: 10px;
                ">

                    <div style="
                        font-size: 22px;
                        font-weight: 700;
                        margin-bottom: 12px;
                    ">
                        Cafe Social Marketing
                    </div>

                    <div style="
                        color: #666;
                        font-size: 15px;
                        line-height: 1.6;
                        margin-bottom: 20px;
                    ">
                        <div>
                            <strong>Branch:</strong> {}
                        </div>

                        <div>
                            <strong>Campaign:</strong> {}
                        </div>

                        <div>
                            <strong>Posting on:</strong> {}
                        </div>
                    </div>

                    <div style="
                        font-size: 18px;
                        line-height: 1.7;
                        white-space: normal;
                    ">
                        {}
                    </div>

                </div>
            """).format(
                branch,
                campaign,
                accounts,
                message,
            )

    # ---------------------------------------------------------
    # DYNAMIC TEMPLATES
    # ---------------------------------------------------------

    def _render_template_message(self, template):
        self.ensure_one()

        message = template.message or ""

        campaign = self.campaign_id
        branch = self.branch_id

        branch_name = branch.name if branch else ""

        campaign_name = campaign.name if campaign else ""

        product_name = (
            campaign.product_id.display_name
            if campaign and campaign.product_id
            else ""
        )

        if campaign:
            discount = campaign.discount or 0

            if float(discount).is_integer():
                discount_text = str(int(discount))
            else:
                discount_text = str(discount)

            start_date = (
                fields.Date.to_string(campaign.date_start)
                if campaign.date_start
                else ""
            )

            end_date = (
                fields.Date.to_string(campaign.date_end)
                if campaign.date_end
                else ""
            )
        else:
            discount_text = ""
            start_date = ""
            end_date = ""

        replacements = {
            "{{branch}}": branch_name,
            "{{campaign}}": campaign_name,
            "{{product}}": product_name,
            "{{discount}}": discount_text,
            "{{start_date}}": start_date,
            "{{end_date}}": end_date,
        }

        for placeholder, value in replacements.items():
            message = message.replace(
                placeholder,
                value,
            )

        return message

    @api.onchange("template_id")
    def _onchange_template_id(self):
        for post in self:
            if post.template_id:

                if (
                    not post.branch_id
                    and post.template_id.branch_id
                ):
                    post.branch_id = post.template_id.branch_id

                post.message = post._render_template_message(
                    post.template_id
                )

    def action_apply_template(self):
        for post in self:
            if not post.template_id:
                raise ValidationError(
                    "Please select a post template first."
                )

            template = post.template_id

            if (
                post.branch_id
                and template.branch_id
                and post.branch_id != template.branch_id
            ):
                raise ValidationError(
                    "The selected template belongs to a different branch."
                )

            values = {}

            if not post.branch_id and template.branch_id:
                values["branch_id"] = template.branch_id.id
                post.branch_id = template.branch_id

            values["message"] = post._render_template_message(
                template
            )

            post.write(values)

    # ---------------------------------------------------------
    # COMPLIANCE VALIDATION
    # ---------------------------------------------------------

    def _get_compliance_checks(self):
        self.ensure_one()

        passed = []
        errors = []

        campaign = self.campaign_id

        if not campaign:
            errors.append(
                "No campaign has been selected."
            )
            return passed, errors

        # 1. Branch validation
        if self.branch_id == campaign.branch_id:
            passed.append(
                "Branch matches the selected campaign."
            )
        else:
            errors.append(
                "Post branch does not match the campaign branch."
            )

        # 2. Campaign date validation
        today = fields.Date.context_today(self)

        if campaign.date_start and today < campaign.date_start:
            errors.append(
                "The campaign has not started yet."
            )
        elif campaign.date_end and today > campaign.date_end:
            errors.append(
                "The campaign has expired."
            )
        else:
            passed.append(
                "Campaign date is valid."
            )

        # 3. Social account validation
        if not self.social_account_ids:
            errors.append(
                "No social account has been selected."
            )
        else:
            wrong_branch_accounts = self.social_account_ids.filtered(
                lambda account: account.branch_id != self.branch_id
            )

            if wrong_branch_accounts:
                errors.append(
                    "One or more social accounts belong to a different branch."
                )
            else:
                passed.append(
                    "Selected social accounts match the post branch."
                )

            if campaign.social_account_ids:
                invalid_accounts = (
                    self.social_account_ids
                    - campaign.social_account_ids
                )

                if invalid_accounts:
                    names = ", ".join(
                        invalid_accounts.mapped("name")
                    )

                    errors.append(
                        "These accounts are not allowed for this campaign: "
                        + names
                    )
                else:
                    passed.append(
                        "Selected social accounts are allowed by the campaign."
                    )
            else:
                passed.append(
                    "Campaign has no social-account restriction."
                )

        # 4. TikTok video validation
        tiktok_accounts = self._get_tiktok_accounts()

        if tiktok_accounts:
            if len(tiktok_accounts) > 1:
                errors.append(
                    "Only one TikTok account can be selected per post in the current MVP."
                )

            if not self.video_file:
                errors.append(
                    "A video attachment is required when TikTok is selected."
                )
            else:
                mime_type = self._get_video_mimetype()
                if mime_type not in TikTokService.SUPPORTED_MIME_TYPES:
                    errors.append(
                        "TikTok video must be MP4, MOV, or WebM."
                    )
                else:
                    passed.append(
                        "TikTok video attachment has a supported format."
                    )

        # 5. Discount validation
        expected_discount = campaign.discount or 0

        if expected_discount > 0:
            message = self.message or ""

            matches = re.findall(
                r"(?<!\d)(\d+(?:\.\d+)?)\s*(?:%|percent\b)",
                message,
                flags=re.IGNORECASE,
            )

            mentioned_discounts = [
                float(value)
                for value in matches
            ]

            if not mentioned_discounts:
                errors.append(
                    f"The campaign discount is {expected_discount:g}%, "
                    "but no discount was detected in the post."
                )
            else:
                wrong_discounts = [
                    value
                    for value in mentioned_discounts
                    if abs(value - expected_discount) > 0.01
                ]

                if wrong_discounts:
                    values = ", ".join(
                        f"{value:g}%"
                        for value in wrong_discounts
                    )

                    errors.append(
                        f"Discount mismatch. Campaign discount is "
                        f"{expected_discount:g}%, but the post contains "
                        f"{values}."
                    )
                else:
                    passed.append(
                        f"Discount matches the campaign "
                        f"({expected_discount:g}%)."
                    )
        else:
            passed.append(
                "Campaign has no discount requirement."
            )

        return passed, errors

    def action_validate_post(self):
        for post in self:
            passed, errors = post._get_compliance_checks()

            result_lines = []

            for message in passed:
                result_lines.append(
                    "✓ " + message
                )

            for message in errors:
                result_lines.append(
                    "✗ " + message
                )

            post.write({
                "validation_status": (
                    "failed"
                    if errors
                    else "passed"
                ),
                "validation_result": "\n".join(
                    result_lines
                ),
                "validated_at": fields.Datetime.now(),
            })

    def _ensure_post_is_compliant(self):
        self.ensure_one()

        passed, errors = self._get_compliance_checks()

        if errors:
            error_text = "\n".join(
                "• " + error
                for error in errors
            )

            raise ValidationError(
                "This post cannot be scheduled or published "
                "because it failed compliance validation:\n\n"
                + error_text
            )

        return True

    # ---------------------------------------------------------
    # APPROVAL WORKFLOW
    # ---------------------------------------------------------

    def action_submit_review(self):
        for post in self:
            # Compliance must pass first.
            post._ensure_post_is_compliant()

            post.write({
                "approval_state": "pending",
                "submitted_at": fields.Datetime.now(),
                "validation_status": "passed",
                "validated_at": fields.Datetime.now(),
                "approved_by_id": False,
                "approved_at": False,
            })

    def action_approve(self):
        if not self.env.user.has_group(
            "cafe_social_marketing.group_cafe_social_manager"
        ):
            raise ValidationError(
                "Only a Marketing Manager can approve social posts."
            )

        for post in self:
            if post.approval_state != "pending":
                raise ValidationError(
                    "Only posts waiting for approval can be approved."
                )

            post._ensure_post_is_compliant()

            post.write({
                "approval_state": "approved",
                "approved_by_id": self.env.user.id,
                "approved_at": fields.Datetime.now(),
            })

    def action_reject(self):
        if not self.env.user.has_group(
            "cafe_social_marketing.group_cafe_social_manager"
        ):
            raise ValidationError(
                "Only a Marketing Manager can reject social posts."
            )

        for post in self:
            if post.approval_state != "pending":
                raise ValidationError(
                    "Only posts waiting for approval can be rejected."
                )

            post.write({
                "approval_state": "rejected",
                "approved_by_id": False,
                "approved_at": False,
            })

    def action_reset_approval(self):
        for post in self:
            post.write({
                "approval_state": "not_submitted",
                "submitted_at": False,
                "approved_by_id": False,
                "approved_at": False,
            })

    @api.onchange(
        "message",
        "branch_id",
        "campaign_id",
        "social_account_ids",
        "attachment_ids",
        "video_file",
        "video_filename",
    )
    def _onchange_reset_validation(self):
        for post in self:
            post.validation_status = "not_validated"
            post.validation_result = False
            post.validated_at = False

            if post.approval_state in (
                "pending",
                "approved",
                "rejected",
            ):
                post.approval_state = "not_submitted"
                post.submitted_at = False
                post.approved_by_id = False
                post.approved_at = False

    def write(self, vals):
        content_fields = {
            "message",
            "branch_id",
            "campaign_id",
            "template_id",
            "social_account_ids",
            "attachment_ids",
            "video_file",
            "video_filename",
        }

        content_changed = bool(
            content_fields.intersection(vals.keys())
        )

        if content_changed:
            for post in self:
                if post.state == "published":
                    raise ValidationError(
                        "A published post cannot be modified. "
                        "Create a new post if you need to change its content."
                    )

            vals = dict(vals)

            vals.update({
                "validation_status": "not_validated",
                "validation_result": False,
                "validated_at": False,
                "approval_state": "not_submitted",
                "submitted_at": False,
                "approved_by_id": False,
                "approved_at": False,
            })

        return super().write(vals)

    # ---------------------------------------------------------
    # POST WORKFLOW
    # ---------------------------------------------------------

    def action_schedule(self):
        for post in self:
            if not post.message:
                raise ValidationError(
                    "Please enter a post message before scheduling."
                )

            if not post.scheduled_at:
                raise ValidationError(
                    "Please select a scheduled date and time first."
                )

            if post.scheduled_at <= fields.Datetime.now():
                raise ValidationError(
                    "The scheduled date must be in the future."
                )

            if not post.social_account_ids:
                raise ValidationError(
                    "Please select at least one social account."
                )

            # Compliance MUST pass before scheduling.
            post._ensure_post_is_compliant()
            if post.approval_state != "approved":
                raise ValidationError(
                    "This post must be approved before it can be scheduled."
                )

            if post.campaign_id:
                scheduled_date = post.scheduled_at.date()

                if (
                    post.campaign_id.date_start
                    and scheduled_date < post.campaign_id.date_start
                ):
                    raise ValidationError(
                        "The selected scheduling date is before "
                        "the campaign starts."
                    )

                if (
                    post.campaign_id.date_end
                    and scheduled_date > post.campaign_id.date_end
                ):
                    raise ValidationError(
                        "The selected scheduling date is after "
                        "the campaign ends."
                    )

            post.write({
                "state": "scheduled",
                "validation_status": "passed",
                "validated_at": fields.Datetime.now(),
            })

    def action_publish(self):
        for post in self:
            if not post.message:
                raise ValidationError(
                    "Please enter a post message before publishing."
                )

            if not post.social_account_ids:
                raise ValidationError(
                    "Please select at least one social account."
                )

            # Compliance MUST pass before publishing.
            post._ensure_post_is_compliant()
            if post.approval_state != "approved":
                raise ValidationError(
                    "This post must be approved before it can be published."
                )

            post.write({
                "state": "published",
                "published_at": fields.Datetime.now(),
                "validation_status": "passed",
                "validated_at": fields.Datetime.now(),
            })

    def action_cancel(self):
        self.write({
            "state": "cancelled",
        })

    def action_reset_draft(self):
        self.write({
            "state": "draft",
            "published_at": False,
        })

    # ---------------------------------------------------------
    # AUTOMATIC SCHEDULER
    # ---------------------------------------------------------
    @api.model
    def _cron_publish_scheduled_posts(self):
        now = fields.Datetime.now()

        posts = self.search([
            ("state", "=", "scheduled"),
            ("scheduled_at", "!=", False),
            ("scheduled_at", "<=", now),
        ], limit=100)

        for post in posts:
            passed, errors = post._get_compliance_checks()

            if errors:
                result_lines = []

                for message in passed:
                    result_lines.append(
                        "✓ " + message
                    )

                for message in errors:
                    result_lines.append(
                        "✗ " + message
                    )

                post.write({
                    "state": "draft",
                    "validation_status": "failed",
                    "validation_result": "\n".join(
                        result_lines
                    ),
                    "validated_at": now,
                })

                continue

            post.write({
                "state": "published",
                "published_at": now,
                "validation_status": "passed",
                "validated_at": now,
            })