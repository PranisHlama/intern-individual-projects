from markupsafe import Markup, escape

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SocialPostReview(models.Model):
    _inherit = "cafe.social.post"

    approval_state = fields.Selection(
        selection_add=[("changes_requested", "Changes Requested")],
        ondelete={"changes_requested": "set default"},
    )
    reviewer_comment = fields.Text(string="Last Changes Requested", readonly=True, copy=False)
    changes_requested_by_id = fields.Many2one(
        "res.users", string="Requested By", readonly=True, copy=False,
    )
    changes_requested_at = fields.Datetime(readonly=True, copy=False)

    def _check_request_changes(self):
        self.ensure_one()
        if not self.env.user.has_group("cafe_social_marketing.group_cafe_social_manager"):
            raise ValidationError("Only a Marketing Manager can request changes.")
        if self.state not in ("draft", "scheduled") or self.approval_state not in ("pending", "approved"):
            raise ValidationError("Request changes only on a pending or approved draft/scheduled post.")
        if self.facebook_post_id or self.facebook_publish_status == "unknown":
            raise ValidationError("Reconcile the existing Facebook result before changing this post.")

    def action_open_request_changes(self):
        self._check_request_changes()
        return {
            "type": "ir.actions.act_window",
            "name": "Request Changes",
            "res_model": "cafe.social.request.changes",
            "view_mode": "form",
            "target": "new",
            "context": {"default_post_id": self.id},
        }

    def _request_changes(self, reason):
        self._check_request_changes()
        reason = (reason or "").strip()
        if not reason:
            raise ValidationError("Explain what needs to change before sending the request.")
        # Bypass this class's metadata write guard, while keeping inherited
        # model access rules and the existing Facebook guards intact.
        super().write({
            "approval_state": "changes_requested",
            "state": "draft",
            "approved_by_id": False,
            "approved_at": False,
            "reviewer_comment": reason,
            "changes_requested_by_id": self.env.user.id,
            "changes_requested_at": fields.Datetime.now(),
        })
        self.message_post(
            body=Markup("<p><strong>Changes requested</strong></p><p>%s</p>") % escape(reason),
            subtype_xmlid="mail.mt_comment",
        )
        return True

    def action_submit_review(self):
        for post in self:
            if post.state != "draft" or post.approval_state not in (
                "not_submitted", "rejected", "changes_requested",
            ):
                raise ValidationError("Only a draft awaiting submission can be sent for review.")
        return super().action_submit_review()

    def write(self, vals):
        if {"reviewer_comment", "changes_requested_by_id", "changes_requested_at"}.intersection(vals):
            raise ValidationError("Review feedback is set through Request Changes.")
        if vals.get("approval_state") == "changes_requested":
            raise ValidationError("Use Request Changes and provide a reason.")
        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        if any({"reviewer_comment", "changes_requested_by_id", "changes_requested_at"}.intersection(vals) for vals in vals_list):
            raise ValidationError("Review feedback cannot be supplied when creating a post.")
        return super().create(vals_list)


class RequestChangesWizard(models.TransientModel):
    _name = "cafe.social.request.changes"
    _description = "Request Social Post Changes"

    post_id = fields.Many2one("cafe.social.post", required=True, readonly=True, ondelete="cascade")
    reason = fields.Text(string="What needs to change?", required=True)

    def action_confirm(self):
        self.ensure_one()
        post = self.post_id.exists()
        if not post:
            raise ValidationError("The social post no longer exists.")
        post._request_changes(self.reason)
        return {"type": "ir.actions.act_window_close"}
