import re

from odoo import models
from odoo.exceptions import ValidationError


class SocialPostWorkspace(models.Model):
    _inherit = "cafe.social.post"

    def action_open_facebook(self):
        self.ensure_one()
        # Normal ORM read enforces model access and record rules.
        result = self.read(["state", "facebook_publish_status", "facebook_post_id"])[0]
        remote_id = result["facebook_post_id"] or ""
        if result["state"] != "published" or result["facebook_publish_status"] != "published":
            raise ValidationError("Only a confirmed published Facebook post can be opened.")
        if not re.fullmatch(r"[0-9]+(?:_[0-9]+)?", remote_id):
            raise ValidationError("This post does not have a valid Facebook post ID.")
        if "_" in remote_id:
            page_id, post_id = remote_id.split("_")
            url = f"https://www.facebook.com/{page_id}/posts/{post_id}"
        else:
            url = f"https://www.facebook.com/{remote_id}"
        return {"type": "ir.actions.act_url", "url": url, "target": "new"}
