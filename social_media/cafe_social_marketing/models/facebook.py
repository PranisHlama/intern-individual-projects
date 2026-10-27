import base64
import binascii
import hashlib
import os
import re

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from ..services.facebook_service import FacebookAPIError, FacebookService


class FacebookAccount(models.Model):
    _inherit = "cafe.social.account"

    facebook_page_id = fields.Char(string="Facebook Page ID", copy=False)
    facebook_token_env = fields.Char(
        string="Token Environment Variable", default="CAFE_FB_PAGE_TOKEN",
        groups="cafe_social_marketing.group_cafe_social_manager",
        help="Name of a CAFE_FB_ environment variable in the Odoo container. "
             "Enter the variable name here, never the token itself.",
    )

    def _facebook_credentials(self):
        self.ensure_one()
        account = self.sudo()
        variable = account.facebook_token_env or ""
        if not re.fullmatch(r"CAFE_FB_[A-Z0-9_]+", variable):
            raise ValidationError("Use a token variable name starting with CAFE_FB_.")
        token = os.environ.get(variable, "").strip()
        if not token:
            raise ValidationError(
                "The Facebook token environment variable is missing in the Odoo container."
            )
        if not re.fullmatch(r"[0-9]+", account.facebook_page_id or ""):
            raise ValidationError("Enter the Facebook Page's numeric ID in Social Accounts.")
        return account.facebook_page_id, token


class FacebookPost(models.Model):
    _inherit = "cafe.social.post"

    facebook_post_id = fields.Char(readonly=True, copy=False)
    facebook_photo_id = fields.Char(readonly=True, copy=False)
    facebook_approved_photo_hash = fields.Char(readonly=True, copy=False)
    facebook_publish_status = fields.Selection(
        [("not_sent", "Not Sent"), ("published", "Published"),
         ("failed", "Failed"), ("unknown", "Outcome Unknown")],
        default="not_sent", readonly=True, copy=False,
    )
    facebook_publish_error = fields.Text(readonly=True, copy=False)

    def _facebook_preflight(self):
        self.ensure_one()
        if self.state not in ("draft", "scheduled"):
            raise ValidationError("Only draft or scheduled posts can be published.")
        if self.facebook_post_id:
            raise ValidationError("This record already has a Facebook post ID. Create a new post.")
        if self.facebook_publish_status == "unknown":
            raise ValidationError(
                "The last attempt has an unknown outcome. Check your Page and reconcile "
                "the result before creating any replacement post. Automatic retry is blocked."
            )
        if self.approval_state != "approved":
            raise ValidationError("Current manager approval is required.")
        if not (self.message or "").strip():
            raise ValidationError("Enter a post message.")
        if len(self.social_account_ids) != 1 or self.social_account_ids.platform != "facebook":
            raise ValidationError(
                "Publish/Schedule currently supports exactly one Facebook account. "
                "TikTok uses its separate draft-upload action; Instagram publishing is not implemented."
            )
        if self.video_file:
            raise ValidationError(
                "This Facebook adapter supports text or one photo, not video. "
                "Existing video support remains available for TikTok."
            )
        if self.attachment_ids:
            image, _mime_type = self._facebook_photo_bytes()
            if hashlib.sha256(image).hexdigest() != self.facebook_approved_photo_hash:
                raise ValidationError("The photo needs current manager approval. Reset approval and resubmit.")
        self._ensure_post_is_compliant()
        return self.social_account_ids._facebook_credentials()

    def _facebook_photo_bytes(self):
        self.ensure_one()
        if len(self.attachment_ids) != 1:
            raise ValidationError("Attach exactly one JPEG or PNG for Facebook photo publishing.")
        attachment = self.attachment_ids.with_context(bin_size=False)
        if attachment.type != "binary":
            raise ValidationError("Upload an image file; URL attachments are not supported.")
        if attachment.file_size > 10 * 1024 * 1024:
            raise ValidationError("The image exceeds this adapter's 10 MiB limit.")
        try:
            if "raw" in attachment._fields:
                image = attachment.raw or b""
                # Odoo 20 BinaryValue (including LocalBinaryFile/BinaryBytes)
                # exposes actual file bytes through .content.
                if not isinstance(image, (bytes, bytearray, memoryview)):
                    image = image.content
            elif "datas" in attachment._fields:
                image = base64.b64decode(attachment.datas or b"", validate=True)
            else:
                raise ValidationError(
                    "This Odoo build has no supported attachment content field. "
                    "Inspect ir.attachment before attempting another upload."
                )
            if isinstance(image, (bytearray, memoryview)):
                image = bytes(image)
            if not isinstance(image, bytes):
                raise ValidationError("The attachment did not return binary image content.")
        except (ValueError, binascii.Error) as exc:
            raise ValidationError("The attached image data is invalid.") from exc
        if not image or len(image) > 10 * 1024 * 1024:
            raise ValidationError("Upload a nonempty image no larger than 10 MiB.")
        # Check the file signature, not just its extension or reported MIME type.
        if image.startswith(b"\xff\xd8\xff"):
            mime_type = "image/jpeg"
        elif image.startswith(b"\x89PNG\r\n\x1a\n"):
            mime_type = "image/png"
        else:
            raise ValidationError("Only JPEG and PNG images are supported by this adapter.")
        return image, mime_type

    def action_approve(self):
        # Validate the actual image before approving; an attachment's bytes can
        # change without updating the post's attachment relation.
        hashes = {}
        for post in self:
            if len(post.social_account_ids) == 1 and post.social_account_ids.platform == "facebook" and post.attachment_ids:
                image, _mime_type = post._facebook_photo_bytes()
                hashes[post.id] = hashlib.sha256(image).hexdigest()
        result = super().action_approve()
        for post in self:
            super(FacebookPost, post).write({"facebook_approved_photo_hash": hashes.get(post.id, False)})
        return result

    def action_schedule(self):
        for post in self:
            post._facebook_preflight()
        return super().action_schedule()

    def action_publish(self):
        self.ensure_one()
        page_id, token = self._facebook_preflight()
        # Serialize this post's attempts without silently sending the same post twice.
        self.env.cr.execute("SELECT id FROM cafe_social_post WHERE id = %s FOR UPDATE", (self.id,))
        self.invalidate_recordset()
        page_id, token = self._facebook_preflight()
        try:
            photo_id = False
            if self.attachment_ids:
                image, mime_type = self._facebook_photo_bytes()
                remote_id, photo_id = FacebookService.publish_photo(
                    page_id, token, self.message, image, mime_type,
                )
            else:
                remote_id = FacebookService.publish_text(page_id, token, self.message)
        except FacebookAPIError as exc:
            super(FacebookPost, self).write({
                "state": "draft",
                "facebook_publish_status": "unknown" if exc.uncertain else "failed",
                "facebook_publish_error": str(exc),
            })
            # Return rather than raising so Odoo does not roll back the failure record.
            return {"type": "ir.actions.client", "tag": "display_notification",
                    "params": {"title": "Facebook publishing did not confirm success",
                               "message": str(exc), "type": "warning", "sticky": True}}
        super(FacebookPost, self).write({
            "facebook_post_id": remote_id,
            "facebook_photo_id": photo_id,
            "facebook_publish_status": "published",
            "facebook_publish_error": False,
            "state": "published",
            "published_at": fields.Datetime.now(),
        })
        return True

    @api.model
    def _cron_publish_scheduled_posts(self):
        posts = self.search([
            ("state", "=", "scheduled"),
            ("scheduled_at", "!=", False),
            ("scheduled_at", "<=", fields.Datetime.now()),
        ], limit=100)
        for post in posts:
            try:
                post.action_publish()
            except ValidationError as exc:
                super(FacebookPost, post).write({"state": "draft", "facebook_publish_status": "failed",
                            "facebook_publish_error": str(exc)})

    def write(self, vals):
        if {"facebook_post_id", "facebook_photo_id", "facebook_approved_photo_hash", "facebook_publish_status", "facebook_publish_error"}.intersection(vals):
            raise ValidationError("Facebook results are maintained by the publishing adapter.")
        if vals.get("state") == "published":
            raise ValidationError("Use Publish Now; Published requires a confirmed Facebook response.")
        content = {"message", "branch_id", "campaign_id", "template_id",
                   "social_account_ids", "attachment_ids", "video_file", "video_filename"}
        if content.intersection(vals):
            if any(post.facebook_post_id or post.facebook_publish_status == "unknown" for post in self):
                raise ValidationError("Do not edit a sent or uncertain Facebook post. Reconcile it first.")
            if any(post.state == "scheduled" for post in self):
                vals = dict(vals, state="draft")
        if vals.get("approval_state") == "approved" and not self.env.user.has_group(
            "cafe_social_marketing.group_cafe_social_manager"
        ):
            raise ValidationError("Only a Marketing Manager can set approval to Approved.")
        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if {"facebook_post_id", "facebook_photo_id", "facebook_approved_photo_hash", "facebook_publish_status", "facebook_publish_error"}.intersection(vals):
                raise ValidationError("Facebook publishing results cannot be supplied on creation.")
            if vals.get("state", "draft") != "draft" or vals.get("approval_state", "not_submitted") != "not_submitted":
                raise ValidationError("Create a draft first, then use the approval and publishing actions.")
        return super().create(vals_list)
