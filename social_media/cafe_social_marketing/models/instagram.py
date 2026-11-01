"""Instagram single-image publishing using the existing Facebook Login setup."""
import hashlib
import io
import warnings
import uuid
import ipaddress
import json
import os
import re
from urllib.parse import urlsplit

from PIL import Image, UnidentifiedImageError

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from ..services.instagram_service import InstagramAPIError, InstagramService
from ..services.cloudinary_service import CloudinaryError, CloudinaryService


RESULT_FIELDS = {
    'instagram_approved_fingerprint', 'instagram_container_id', 'instagram_media_id',
    'instagram_publish_status', 'instagram_publish_error',
    'instagram_hosted_image_url', 'instagram_hosted_public_id', 'instagram_hosted_photo_hash',
    'instagram_hosting_upload_key',
}
CONTENT_FIELDS = {
    'message', 'branch_id', 'campaign_id', 'template_id', 'social_account_ids',
    'attachment_ids', 'video_file', 'video_filename', 'instagram_image_url',
}


def validate_image_url(value):
    """Validate URL syntax without fetching user-controlled URLs on the ERP server."""
    value = value or ''
    try:
        parsed = urlsplit(value)
        if (not value or any(c.isspace() or ord(c) < 32 for c in value)
                or parsed.scheme != 'https' or not parsed.hostname
                or parsed.username is not None or parsed.password is not None
                or parsed.fragment or parsed.port not in (None, 443)):
            raise ValueError()
        host = parsed.hostname.lower().rstrip('.')
        if host == 'localhost' or host.endswith(('.localhost', '.local', '.internal')) or '.' not in host:
            raise ValueError()
        try:
            address = ipaddress.ip_address(host)
        except ValueError:
            if not re.fullmatch(r'[a-z0-9.-]+', host):
                raise ValueError()
        else:
            if not address.is_global:
                raise ValueError()
    except (ValueError, TypeError):
        raise ValidationError('Enter a public HTTPS image URL with no spaces, credentials, fragment or custom port.') from None
    return value


class InstagramAccount(models.Model):
    _inherit = 'cafe.social.account'

    instagram_user_id = fields.Char(string='Instagram Account ID', copy=False)
    instagram_token_env = fields.Char(
        string='Instagram Token Environment Variable', default='CAFE_IG_ACCESS_TOKEN',
        groups='cafe_social_marketing.group_cafe_social_manager',
        help='Environment variable name only, starting with CAFE_IG_. Never enter the token here.',
    )

    def _instagram_credentials(self):
        self.ensure_one()
        account = self.sudo()
        variable = account.instagram_token_env or ''
        if not re.fullmatch(r'CAFE_IG_[A-Z0-9_]+', variable):
            raise ValidationError('Use an Instagram token variable name starting with CAFE_IG_.')
        if not re.fullmatch(r'[0-9]+', account.instagram_user_id or ''):
            raise ValidationError('Enter the numeric Instagram professional account ID in Social Accounts.')
        token = os.environ.get(variable, '').strip()
        if not token:
            raise ValidationError('The Instagram token variable is missing from the Odoo container.')
        return account.instagram_user_id, token


class InstagramPost(models.Model):
    _inherit = 'cafe.social.post'

    publishing_platform = fields.Char(compute='_compute_publishing_platform')
    instagram_image_url = fields.Char(string='Public JPEG URL', copy=False,
        help='Instagram downloads this public image. Keep the image and URL available through publication.')
    instagram_hosted_image_url = fields.Char(string='Hosted Photo URL', readonly=True, copy=False)
    instagram_hosted_public_id = fields.Char(readonly=True, copy=False)
    instagram_hosted_photo_hash = fields.Char(readonly=True, copy=False)
    instagram_hosting_upload_key = fields.Char(readonly=True, copy=False)
    instagram_approved_fingerprint = fields.Char(readonly=True, copy=False)
    instagram_container_id = fields.Char(readonly=True, copy=False)
    instagram_media_id = fields.Char(readonly=True, copy=False)
    instagram_publish_status = fields.Selection([
        ('not_sent', 'Not Sent'), ('processing', 'Processing / Recheck'),
        ('published', 'Published'), ('failed', 'Failed'), ('unknown', 'Outcome Unknown'),
    ], default='not_sent', readonly=True, copy=False)
    instagram_publish_error = fields.Text(readonly=True, copy=False)

    @api.depends('social_account_ids', 'social_account_ids.platform')
    def _compute_publishing_platform(self):
        for post in self:
            post.publishing_platform = post.social_account_ids.platform if len(post.social_account_ids) == 1 else False

    def _is_instagram(self):
        self.ensure_one()
        return len(self.social_account_ids) == 1 and self.social_account_ids.platform == 'instagram'

    def _instagram_content_check(self):
        if not (self.message or '').strip() or len(self.message) > 2200:
            raise ValidationError('Instagram requires a caption of 1–2200 characters.')
        if self.video_file:
            raise ValidationError('This Instagram version supports one JPEG photo, not video.')
        if self.attachment_ids:
            if self.instagram_image_url:
                raise ValidationError('Use one attached JPEG or a legacy public URL, not both. Clear the legacy URL to use an attachment.')
            self._instagram_photo_bytes()
        else:
            if not self.instagram_image_url:
                raise ValidationError('Attach one JPEG photo for Instagram.')
            validate_image_url(self.instagram_image_url)

    def _instagram_photo_bytes(self):
        # Reuse the working Odoo 20 BinaryValue reader; apply tighter IG JPEG rules.
        if len(self.attachment_ids) != 1:
            raise ValidationError('For Instagram, attach exactly one JPEG photo.')
        image, mime_type = self._facebook_photo_bytes()
        if mime_type != 'image/jpeg' or len(image) > 8 * 1024 * 1024:
            raise ValidationError('For Instagram, attach exactly one JPEG no larger than 8 MiB.')
        try:
            with warnings.catch_warnings():
                warnings.simplefilter('error', Image.DecompressionBombWarning)
                with Image.open(io.BytesIO(image)) as photo:
                    width, height = photo.size
                    if photo.format != 'JPEG' or not (1 <= width <= 20000 and 1 <= height <= 20000):
                        raise ValueError()
                    if width * height > 40_000_000 or not (0.8 <= width / height <= 1.91):
                        raise ValueError()
                    photo.verify()
        except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning):
            raise ValidationError('Use a valid JPEG with an aspect ratio from 4:5 to 1.91:1 and no more than 40 megapixels. This adapter does not crop images.') from None
        return image

    def _instagram_delivery_url(self):
        if not self.attachment_ids:
            return validate_image_url(self.instagram_image_url)
        image = self._instagram_photo_bytes()
        photo_hash = hashlib.sha256(image).hexdigest()
        # Recheck bytes immediately before any hosting operation, even after preflight.
        if self.instagram_approved_fingerprint != self._instagram_fingerprint(image):
            raise ValidationError('The attached photo changed after approval. Resubmit for manager approval.')
        if self.instagram_hosted_image_url and self.instagram_hosted_photo_hash == photo_hash:
            return self.instagram_hosted_image_url
        if not self.instagram_hosting_upload_key:
            self._write_publish_result({'instagram_hosting_upload_key': uuid.uuid4().hex})
        public_id = 'cafe_social/' + self.instagram_hosting_upload_key + '_' + photo_hash
        url, remote_id = CloudinaryService.upload_jpeg(image, public_id)
        self._write_publish_result({'instagram_hosted_image_url': url,
            'instagram_hosted_public_id': remote_id, 'instagram_hosted_photo_hash': photo_hash})
        return url

    def _get_compliance_checks(self):
        passed, errors = super()._get_compliance_checks()
        if self._is_instagram():
            try:
                self._instagram_content_check()
            except ValidationError as exc:
                errors.append(str(exc))
            else:
                passed.append('Instagram caption and photo source are valid. Attached photos are hosted automatically at publication.')
        return passed, errors

    def _instagram_fingerprint(self, photo_bytes=None):
        account = self.social_account_ids.sudo()
        value = [self.message or '', self.instagram_image_url or '', account.id,
                 account.instagram_user_id or '', account.instagram_token_env or '']
        if self.attachment_ids:
            # Keep v8 URL-only hashes unchanged; bind new attachment approvals to exact bytes.
            value.append(['jpeg_sha256', hashlib.sha256(
                self._instagram_photo_bytes() if photo_bytes is None else photo_bytes).hexdigest()])
        return hashlib.sha256(json.dumps(value, ensure_ascii=False).encode()).hexdigest()

    def _instagram_preflight(self):
        self.ensure_one()
        if self.state not in ('draft', 'scheduled') or not self._is_instagram():
            raise ValidationError('Select exactly one Instagram account on a draft or scheduled post.')
        if self.instagram_media_id or self.instagram_publish_status in ('published', 'unknown'):
            raise ValidationError('This Instagram post was sent or has an uncertain outcome. Check Instagram before creating a replacement.')
        if self.instagram_container_id and self.instagram_publish_status == 'failed':
            raise ValidationError('This Instagram container failed. Check its result, then create a new post if needed.')
        if self.facebook_post_id or self.facebook_publish_status == 'unknown':
            raise ValidationError('This record already has a Facebook publishing result. Create a separate Instagram post.')
        if self.approval_state != 'approved':
            raise ValidationError('Current manager approval is required.')
        self._instagram_content_check()
        if self.instagram_approved_fingerprint != self._instagram_fingerprint():
            raise ValidationError('Instagram content or account configuration changed. Resubmit for manager approval.')
        self._ensure_post_is_compliant()
        if self.attachment_ids and not (self.instagram_hosted_image_url and
                self.instagram_hosted_photo_hash == hashlib.sha256(self._instagram_photo_bytes()).hexdigest()):
            try:
                CloudinaryService.credentials()
            except CloudinaryError as exc:
                raise ValidationError(str(exc)) from None
        return self.social_account_ids._instagram_credentials()

    def _social_publish_preflight(self):
        if self._is_instagram():
            return self._instagram_preflight()
        return super()._social_publish_preflight()

    def action_approve(self):
        fingerprints = {}
        for post in self:
            if post._is_instagram():
                post._instagram_content_check()
                post.social_account_ids._instagram_credentials()
                fingerprints[post.id] = post._instagram_fingerprint()
        result = super().action_approve()
        for post in self:
            post._write_publish_result({'instagram_approved_fingerprint': fingerprints.get(post.id, False)})
        return result

    @staticmethod
    def _instagram_notice(message, warning=False):
        return {'type': 'ir.actions.client', 'tag': 'display_notification', 'params': {
            'title': 'Instagram publishing', 'message': message,
            'type': 'warning' if warning else 'info', 'sticky': True,
        }}

    def _publish_validation_failure(self, error):
        if self._is_instagram():
            return self._write_publish_result({'state': 'draft', 'instagram_publish_status': 'failed',
                                               'instagram_publish_error': str(error)})
        return super()._publish_validation_failure(error)

    def action_publish(self):
        self.ensure_one()
        if not self._is_instagram():
            return super().action_publish()
        self._instagram_preflight()
        self.env.cr.execute('SELECT id FROM cafe_social_post WHERE id = %s FOR UPDATE', (self.id,))
        self.invalidate_recordset()
        user_id, token = self._instagram_preflight()
        phase = 'create'
        try:
            if not self.instagram_container_id:
                try:
                    image_url = self._instagram_delivery_url()
                except CloudinaryError as exc:
                    self._write_publish_result({'state': 'draft', 'instagram_publish_status': 'failed',
                        'instagram_publish_error': str(exc)})
                    return self._instagram_notice(str(exc), True)
                container = InstagramService.create_container(user_id, token, self.message, image_url)
                self._write_publish_result({'instagram_container_id': container,
                    'instagram_publish_status': 'processing', 'instagram_publish_error': False})
            phase = 'status'
            status = InstagramService.container_status(self.instagram_container_id, token)
            if status == 'IN_PROGRESS':
                return self._instagram_notice('Image is processing. Click Publish again to check the same container. Scheduled posts recheck on the next scheduled action.')
            if status in ('ERROR', 'EXPIRED'):
                self._write_publish_result({'state': 'draft', 'instagram_publish_status': 'failed',
                    'instagram_publish_error': 'Instagram container is ' + status + '. Check the image requirements and public URL.'})
                return self._instagram_notice(self.instagram_publish_error, True)
            if status == 'PUBLISHED':
                self._write_publish_result({'state': 'draft', 'instagram_publish_status': 'unknown',
                    'instagram_publish_error': 'Container is already published, but no media ID is saved. Check Instagram; automatic retry is blocked.'})
                return self._instagram_notice(self.instagram_publish_error, True)
            phase = 'publish'
            media_id = InstagramService.publish_container(user_id, token, self.instagram_container_id)
        except InstagramAPIError as exc:
            if phase == 'status':
                vals = {'instagram_publish_status': 'processing', 'instagram_publish_error': str(exc)}
            else:
                vals = {'state': 'draft', 'instagram_publish_status': 'unknown' if exc.uncertain else 'failed',
                        'instagram_publish_error': str(exc)}
            self._write_publish_result(vals)
            return self._instagram_notice(str(exc), True)
        self._write_publish_result({'instagram_media_id': media_id, 'instagram_publish_status': 'published',
            'instagram_publish_error': False, 'state': 'published', 'published_at': fields.Datetime.now()})
        return self._instagram_notice('Published to Instagram. Media ID: ' + media_id)

    def write(self, vals):
        if RESULT_FIELDS.intersection(vals):
            raise ValidationError('Instagram results are maintained by the publishing adapter.')
        if CONTENT_FIELDS.intersection(vals):
            if any(post.instagram_container_id or post.instagram_media_id or post.instagram_publish_status == 'unknown' for post in self):
                raise ValidationError('An Instagram attempt exists. Check its result before creating a replacement post; content is locked.')
        if 'instagram_image_url' in vals:
            vals = dict(vals, approval_state='not_submitted', approved_by_id=False, approved_at=False,
                        validation_status='not_validated', validation_result=False, validated_at=False, submitted_at=False,
                        ai_review_status='not_reviewed', ai_overall_status=False, ai_tone=False,
                        ai_clarity=False, ai_issues=False, ai_suggested_rewrite=False, ai_reviewed_at=False)
            if any(post.state == 'scheduled' for post in self):
                vals['state'] = 'draft'
        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        if any(RESULT_FIELDS.intersection(vals) for vals in vals_list):
            raise ValidationError('Instagram results cannot be supplied when creating a post.')
        return super().create(vals_list)
