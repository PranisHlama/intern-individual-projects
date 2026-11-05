import base64
import binascii
import io
import json

from PIL import Image, UnidentifiedImageError

from odoo import api, fields, models
from odoo.exceptions import ValidationError

SIZE = 1080
MAX_DESIGN = 7 * 1024 * 1024
DESIGN_FIELDS = {"designer_document", "designer_attachment_id"}


def _decode_image(encoded, limit, formats, dimensions=None):
    if not isinstance(encoded, str) or len(encoded) > (limit * 4 // 3 + 4):
        raise ValidationError("The image exceeds the designer size limit.")
    try:
        raw = base64.b64decode(encoded, validate=True)
        if not raw or len(raw) > limit:
            raise ValueError()
        with Image.open(io.BytesIO(raw)) as image:
            if (image.format not in formats or max(image.size) > 1600
                    or (dimensions and image.size != dimensions)):
                raise ValueError()
            image.verify()
        with Image.open(io.BytesIO(raw)) as image:
            image.load()
    except (ValueError, TypeError, OSError, binascii.Error, UnidentifiedImageError,
            Image.DecompressionBombError):
        raise ValidationError("The designer received an invalid or unsupported image.") from None
    return raw


def _validate_document(document):
    if not isinstance(document, str) or len(document) > MAX_DESIGN:
        raise ValidationError("The editable design exceeds the size limit.")
    try:
        design = json.loads(document)
        if not isinstance(design, dict) or set(design) != {"version", "color", "background", "layers"}:
            raise ValueError()
        if type(design["version"]) is not int or design["version"] not in (1, 2):
            raise ValueError()

        def color(value):
            return (isinstance(value, str) and len(value) == 7 and value.startswith("#")
                    and all(c in "0123456789abcdefABCDEF" for c in value[1:]))

        def number(value, low, high):
            return type(value) is int and low <= value <= high

        def asset(value):
            _decode_image(value, 2 * 1024 * 1024, {"JPEG", "PNG"})

        if not color(design["color"]) or not isinstance(design["layers"], list) or len(design["layers"]) > 8:
            raise ValueError()
        if design["background"] != "":
            asset(design["background"])
        for layer in design["layers"]:
            if not isinstance(layer, dict):
                raise ValueError()
            common = {"kind", "x", "y", "size"}
            if not number(layer.get("x"), -1080, 1080) or not number(layer.get("y"), -1080, 1080):
                raise ValueError()
            if layer.get("kind") == "text":
                text_fields = common | {"text", "color"}
                if design["version"] == 2:
                    text_fields |= {"font", "bold", "italic", "align", "lineHeight"}
                if (set(layer) != text_fields or not isinstance(layer["text"], str)
                        or len(layer["text"]) > 180 or not color(layer["color"])
                        or not number(layer["size"], 18, 160)):
                    raise ValueError()
                if design["version"] == 2 and (
                    layer["font"] not in ("sans", "serif", "mono")
                    or type(layer["bold"]) is not bool or type(layer["italic"]) is not bool
                    or layer["align"] not in ("left", "center", "right")
                    or not number(layer["lineHeight"], 100, 180)
                ):
                    raise ValueError()
            elif layer.get("kind") == "image":
                if set(layer) != common | {"data"} or not number(layer["size"], 32, 1080):
                    raise ValueError()
                asset(layer["data"])
            else:
                raise ValueError()
        return json.dumps(design, ensure_ascii=True, separators=(",", ":"))
    except (ValueError, TypeError, RecursionError):
        raise ValidationError("The editable design is invalid.") from None


class SocialPostDesigner(models.Model):
    _inherit = "cafe.social.post"

    designer_document = fields.Text(readonly=True, copy=False)
    designer_attachment_id = fields.Many2one("ir.attachment", readonly=True, copy=False, ondelete="set null")

    def _check_designer_access(self):
        self.ensure_one()
        self.check_access("write")
        if (self.state != "draft" or self.facebook_post_id or self.facebook_photo_id
                or self.facebook_publish_status == "unknown"
                or self.instagram_container_id or self.instagram_media_id
                or self.instagram_publish_status == "unknown"
                or self.tiktok_publish_id):
            raise ValidationError("Open an unpublished draft with no active publishing attempt.")
        if self.video_file:
            raise ValidationError("Remove the video before designing a photo post.")

    def action_open_post_designer(self):
        self._check_designer_access()
        return {
            "type": "ir.actions.client",
            "tag": "cafe_social_marketing.post_designer",
            "name": "Post Designer",
            "params": {"post_id": self.id},
        }

    def _designer_revision(self):
        # Include attachment IDs as well as the complete saved document; Odoo's
        # write_date can be serialized with second precision.
        import hashlib
        value = json.dumps([
            str(self.write_date), self.approval_state, self.attachment_ids.ids,
            self.instagram_image_url, self.designer_document,
        ])
        return hashlib.sha256(value.encode()).hexdigest()

    def get_post_designer(self):
        self._check_designer_access()
        return {
            "document": self.designer_document or "",
            "revision": self._designer_revision(),
            "has_other_media": bool(self.attachment_ids - self.designer_attachment_id or self.instagram_image_url),
        }

    def save_post_designer(self, document, jpeg, revision, replace_media=False):
        self._check_designer_access()
        design = _validate_document(document)
        raw = _decode_image(jpeg, 5 * 1024 * 1024, {"JPEG"}, (SIZE, SIZE))
        self.env.cr.execute("SELECT id FROM cafe_social_post WHERE id = %s FOR UPDATE", (self.id,))
        self.invalidate_recordset()
        self._check_designer_access()
        if revision != self._designer_revision():
            raise ValidationError("This post changed while the designer was open. Reopen the designer before saving.")
        if (self.attachment_ids - self.designer_attachment_id or self.instagram_image_url) and replace_media is not True:
            raise ValidationError("Confirm that the design should replace the existing post media.")
        attachment_model = self.env["ir.attachment"]
        content = {"raw": raw} if "raw" in attachment_model._fields else {"datas": base64.b64encode(raw)}
        attachment = attachment_model.with_context(image_no_postprocess=True).create({
            "name": "Social Post Design.jpg",
            "type": "binary",
            "mimetype": "image/jpeg",
            "res_model": self._name,
            "res_id": self.id,
            "public": False,
            **content,
        })
        # The inherited write still runs platform guards and approval resets.
        super().write({
            "designer_document": design,
            "designer_attachment_id": attachment.id,
            "attachment_ids": [(6, 0, [attachment.id])],
            "instagram_image_url": False,
        })
        return self._designer_revision()

    def write(self, vals):
        if DESIGN_FIELDS.intersection(vals):
            raise ValidationError("Save editable designs through Post Designer.")
        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        if any(DESIGN_FIELDS.intersection(vals) for vals in vals_list):
            raise ValidationError("Save editable designs through Post Designer.")
        return super().create(vals_list)
