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
        if not isinstance(design, dict):
            raise ValueError()
        if type(design.get("version")) is not int or design["version"] not in (1, 2, 3, 4, 5, 6):
            raise ValueError()
        expected = {"version", "color", "background", "layers"}
        height = 1080
        if design["version"] >= 6:
            expected |= {"width", "height"}
            if (type(design.get("width")) is not int or design["width"] != 1080
                    or type(design.get("height")) is not int or design["height"] not in (1080, 1350)):
                raise ValueError()
            height = design["height"]
        if set(design) != expected:
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
            if design["version"] >= 3:
                common |= {"name", "hidden", "locked"}
                if (not isinstance(layer.get("name"), str) or len(layer["name"]) > 60
                        or type(layer.get("hidden")) is not bool
                        or type(layer.get("locked")) is not bool):
                    raise ValueError()
            if not number(layer.get("x"), -1080, 1080) or not number(layer.get("y"), -height, height):
                raise ValueError()
            if layer.get("kind") == "text":
                text_fields = common | {"text", "color"}
                if design["version"] >= 4:
                    text_fields |= {"width"}
                    if layer.get("width") != 0 and not number(layer.get("width"), 80, 1080):
                        raise ValueError()
                    if type(layer.get("width")) is not int:
                        raise ValueError()
                if design["version"] >= 2:
                    text_fields |= {"font", "bold", "italic", "align", "lineHeight"}
                if (set(layer) != text_fields or not isinstance(layer["text"], str)
                        or len(layer["text"]) > 180 or not color(layer["color"])
                        or not number(layer["size"], 18, 160)):
                    raise ValueError()
                if design["version"] >= 2 and (
                    layer["font"] not in ("sans", "serif", "mono")
                    or type(layer["bold"]) is not bool or type(layer["italic"]) is not bool
                    or layer["align"] not in ("left", "center", "right")
                    or not number(layer["lineHeight"], 100, 180)
                ):
                    raise ValueError()
            elif layer.get("kind") == "image":
                image_fields = common | {"data"}
                if design["version"] >= 5:
                    image_fields |= {"cropRatio", "cropZoom", "cropX", "cropY"}
                    if (layer.get("cropRatio") not in (0, 750, 1000, 1250)
                            or type(layer.get("cropRatio")) is not int
                            or not number(layer.get("cropZoom"), 100, 400)
                            or not number(layer.get("cropX"), 0, 1000)
                            or not number(layer.get("cropY"), 0, 1000)):
                        raise ValueError()
                if set(layer) != image_fields or not number(layer["size"], 32, 1080):
                    raise ValueError()
                asset(layer["data"])
            else:
                raise ValueError()
        return json.dumps(design, ensure_ascii=True, separators=(",", ":"))
    except (ValueError, TypeError, RecursionError):
        raise ValidationError("The editable design is invalid.") from None


def _decode_design_export(jpeg, validated_document):
    design = json.loads(validated_document)
    dimensions = (design.get("width", 1080), design.get("height", 1080))
    return _decode_image(jpeg, 5 * 1024 * 1024, {"JPEG"}, dimensions)


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
            "can_manage_templates": self.env.user.has_group("cafe_social_marketing.group_cafe_social_manager"),
        }

    def list_designer_templates(self, offset=0):
        self._check_designer_access()
        if type(offset) is not int or not 0 <= offset <= 100000:
            raise ValidationError("Invalid template page.")
        records = self.env["cafe.social.design.template"].search_read(
            [("active", "=", True)], ["name", "thumbnail"], order="id desc", limit=21, offset=offset,
        )
        return {"items": records[:20], "has_more": len(records) > 20}

    def get_designer_template(self, template_id):
        self._check_designer_access()
        if type(template_id) is not int or template_id <= 0:
            raise ValidationError("Select a saved design template.")
        template = self.env["cafe.social.design.template"].browse(template_id).exists()
        if not template:
            raise ValidationError("This template is no longer available.")
        template.check_access("read")
        if not template.active:
            raise ValidationError("This template was archived. Refresh the template list.")
        return {"document": template.document, "name": template.name}

    def save_designer_template(self, name, document, thumbnail):
        self._check_designer_access()
        _require_template_manager(self.env)
        template = self.env["cafe.social.design.template"].create({
            "name": name, "document": document, "thumbnail": thumbnail,
        })
        return {"id": template.id, "name": template.name}

    def archive_designer_template(self, template_id):
        self._check_designer_access()
        _require_template_manager(self.env)
        if type(template_id) is not int or template_id <= 0:
            raise ValidationError("Select a saved design template.")
        template = self.env["cafe.social.design.template"].browse(template_id).exists()
        if not template:
            raise ValidationError("This template is no longer available.")
        template.write({"active": False})
        return True

    def save_post_designer(self, document, jpeg, revision, replace_media=False):
        self._check_designer_access()
        design = _validate_document(document)
        raw = _decode_design_export(jpeg, design)
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


def _require_template_manager(env):
    if not env.user.has_group("cafe_social_marketing.group_cafe_social_manager"):
        raise ValidationError("Only a Marketing Manager can save or manage design templates.")


def _template_name(name):
    if not isinstance(name, str) or not name.strip() or len(name.strip()) > 80:
        raise ValidationError("Enter a template name between 1 and 80 characters.")
    return name.strip()


def _template_payload(values):
    if not isinstance(values, dict) or set(values) != {"name", "document", "thumbnail"}:
        raise ValidationError("Create design templates through Post Designer.")
    name = _template_name(values["name"])
    document = _validate_document(values["document"])
    design = json.loads(document)
    height = design.get("height", 1080)
    _decode_image(values["thumbnail"], 128 * 1024, {"JPEG"}, (216, height // 5))
    return {"name": name, "document": document, "thumbnail": values["thumbnail"]}


class SocialDesignTemplate(models.Model):
    _name = "cafe.social.design.template"
    _description = "Reusable Social Post Design"
    _order = "id desc"

    name = fields.Char(required=True)
    document = fields.Text(required=True, readonly=True, copy=False)
    # Validated small JPEG stored as text to avoid binary API differences.
    # Access is restricted by the same marketing-model ACL as the document.
    thumbnail = fields.Text(required=True, readonly=True, copy=False)
    active = fields.Boolean(default=True)

    @api.model_create_multi
    def create(self, vals_list):
        _require_template_manager(self.env)
        return super().create([_template_payload(vals) for vals in vals_list])

    def write(self, vals):
        _require_template_manager(self.env)
        self.check_access("write")
        if set(vals) - {"name", "active"}:
            raise ValidationError("Saved layouts are immutable. Save an edited design as a new template.")
        vals = dict(vals)
        if "name" in vals:
            vals["name"] = _template_name(vals["name"])
        if "active" in vals and type(vals["active"]) is not bool:
            raise ValidationError("Invalid template visibility.")
        return super().write(vals)

    def unlink(self):
        _require_template_manager(self.env)
        return super().unlink()
