from datetime import datetime

import pytz
from markupsafe import Markup

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SocialPostCalendarReschedule(models.Model):
    _inherit = "cafe.social.post"

    def _check_calendar_reschedule(self):
        self.ensure_one()
        if not self.env.user.has_group("cafe_social_marketing.group_cafe_social_manager"):
            raise ValidationError("Only a Marketing Manager can reschedule a scheduled post.")
        if (self.state != "scheduled" or self.approval_state != "approved"
                or self.validation_status != "passed" or not self.scheduled_at):
            raise ValidationError("Only an approved, validated scheduled post can be moved.")
        if (self.facebook_post_id or self.facebook_photo_id
                or self.facebook_publish_status != "not_sent"
                or self.instagram_container_id or self.instagram_media_id
                or self.instagram_publish_status != "not_sent"
                or self.tiktok_publish_id):
            raise ValidationError("Publishing has already started. Check the platform result before changing this post.")

    def _calendar_schedule_target(self, value):
        self.ensure_one()
        try:
            target = fields.Datetime.to_datetime(value)
        except (TypeError, ValueError):
            raise ValidationError("Choose a valid date and time.") from None
        if not target:
            raise ValidationError("A scheduled post must keep a scheduled date and time.")
        if self.env.context.get("cafe_calendar_reschedule"):
            old_local = fields.Datetime.context_timestamp(self, self.scheduled_at)
            new_local = fields.Datetime.context_timestamp(self, target)
            # Calendar moves select a new day; the approved local clock time remains.
            local_clock = old_local.time().replace(tzinfo=None)
            try:
                # Odoo may return ZoneInfo (.key) or pytz (.zone).
                zone_name = (getattr(old_local.tzinfo, "key", None)
                             or getattr(old_local.tzinfo, "zone", None)
                             or self.env.context.get("tz") or self.env.user.tz or "UTC")
                local = pytz.timezone(zone_name).localize(
                    datetime.combine(new_local.date(), local_clock), is_dst=None,
                )
            except (pytz.AmbiguousTimeError, pytz.NonExistentTimeError):
                raise ValidationError("That date has a daylight-saving time conflict. Set the time in the post form.") from None
            target = local.astimezone(pytz.UTC).replace(tzinfo=None)
        if target <= fields.Datetime.now():
            raise ValidationError("The new scheduled date and time must be in the future.")
        local_date = fields.Datetime.context_timestamp(self, target).date()
        campaign = self.campaign_id
        if campaign and (
            (campaign.date_start and local_date < campaign.date_start)
            or (campaign.date_end and local_date > campaign.date_end)
        ):
            raise ValidationError("The new date must be within the campaign dates.")
        return target

    def write(self, vals):
        if "scheduled_at" not in vals or not self:
            return super().write(vals)
        self.check_access("write")
        # Share the publishing row lock so a move cannot race a publisher.
        self.env.cr.execute(
            "SELECT id FROM cafe_social_post WHERE id IN %s ORDER BY id FOR UPDATE",
            (tuple(self.ids),),
        )
        self.invalidate_recordset()
        calendar_move = self.env.context.get("cafe_calendar_reschedule")
        if calendar_move or any(post.state == "scheduled" for post in self):
            if len(self) != 1 or set(vals) != {"scheduled_at"}:
                raise ValidationError("Reschedule one post at a time without changing its content.")
            self._check_calendar_reschedule()
            target = self._calendar_schedule_target(vals["scheduled_at"])
            if target == self.scheduled_at:
                return True
            # Existing branch, account, photo fingerprint, credentials and compliance checks.
            # This does not send a network publish request.
            self._social_publish_preflight()
            before = fields.Datetime.context_timestamp(self, self.scheduled_at)
            result = super().write(dict(vals, scheduled_at=target))
            after = fields.Datetime.context_timestamp(self, target)
            self.message_post(
                body=Markup(
                    "<p>Schedule changed by {}: <strong>{}</strong> → <strong>{}</strong>. "
                    "The manager approved this schedule change; content approval is unchanged.</p>"
                ).format(
                    self.env.user.display_name,
                    before.strftime("%Y-%m-%d %H:%M %Z"),
                    after.strftime("%Y-%m-%d %H:%M %Z"),
                ),
                subtype_xmlid="mail.mt_note",
            )
            return result
        if any(post.state in ("published", "cancelled") for post in self):
            raise ValidationError("Published and cancelled posts cannot be rescheduled.")
        return super().write(vals)

    @api.model
    def _cron_publish_scheduled_posts(self):
        posts = self.search([
            ("state", "=", "scheduled"),
            ("scheduled_at", "!=", False),
            ("scheduled_at", "<=", fields.Datetime.now()),
        ], limit=100)
        for post in posts:
            # A manager may move a due post after the initial search. Lock and
            # recheck it before action_publish, which shares the same row lock.
            self.env.cr.execute(
                "SELECT id FROM cafe_social_post WHERE id = %s FOR UPDATE", (post.id,),
            )
            post.invalidate_recordset()
            if (post.state != "scheduled" or not post.scheduled_at
                    or post.scheduled_at > fields.Datetime.now()):
                continue
            try:
                post.action_publish()
            except ValidationError as exc:
                post._publish_validation_failure(exc)
