import hashlib

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.binary import BinaryBytes

from ..services.meta_profile_service import MetaProfileService, ProfileSyncError

CACHE_FIELDS = {
    'profile_name', 'profile_username', 'profile_image', 'profile_synced_at',
    'profile_source_id', 'profile_source_platform',
}
IDENTITY_FIELDS = {'platform', 'facebook_page_id', 'instagram_user_id'}


class SocialAccountProfile(models.Model):
    _inherit = 'cafe.social.account'

    profile_name = fields.Char(string='Synced Name', readonly=True, copy=False)
    profile_username = fields.Char(string='Synced Username', readonly=True, copy=False)
    profile_image = fields.Binary(string='Profile Photo', readonly=True, copy=False, attachment=False)
    profile_synced_at = fields.Datetime(string='Last Profile Sync', readonly=True, copy=False)
    profile_source_id = fields.Char(readonly=True, copy=False)
    profile_source_platform = fields.Char(readonly=True, copy=False)
    profile_display_name = fields.Char(compute='_compute_profile_display')
    profile_avatar_url = fields.Char(compute='_compute_profile_display')

    def _profile_identity(self):
        self.ensure_one()
        field = {'facebook': 'facebook_page_id', 'instagram': 'instagram_user_id'}.get(self.platform)
        return self.platform, (self[field] or '') if field else ''

    @api.depends('name', 'platform', 'facebook_page_id', 'instagram_user_id', 'profile_name',
                 'profile_image', 'profile_synced_at', 'profile_source_id', 'profile_source_platform')
    def _compute_profile_display(self):
        for account in self:
            identity = account._profile_identity()
            valid = bool(identity[1]) and identity == (account.profile_source_platform, account.profile_source_id)
            account.profile_display_name = (account.profile_name if valid else False) or account.name
            account.profile_avatar_url = False
            record_id = account._origin.id
            if valid and account.profile_image and type(record_id) is int and record_id > 0:
                stamp = hashlib.sha256(str(account.profile_synced_at).encode()).hexdigest()[:16]
                account.profile_avatar_url = f'/web/image/cafe.social.account/{record_id}/profile_image?unique={stamp}'

    def action_sync_social_profile(self):
        self.ensure_one()
        if not self.env.user.has_group('cafe_social_marketing.group_cafe_social_manager'):
            raise ValidationError('Only a Marketing Manager can sync social profiles.')
        self.check_access('write')
        if not self.active or self.platform not in ('facebook', 'instagram'):
            raise ValidationError('Select an active Facebook or Instagram account.')
        platform = self.platform
        remote_id, token = (self._facebook_credentials() if platform == 'facebook'
                            else self._instagram_credentials())
        try:
            profile = MetaProfileService.fetch(platform, remote_id, token)
        except ProfileSyncError as exc:
            raise ValidationError(str(exc)) from None
        # Fetch outside the lock, then prevent a concurrent account switch from
        # binding fetched details to a different destination.
        self.env.cr.execute('SELECT id FROM cafe_social_account WHERE id = %s FOR UPDATE', (self.id,))
        self.invalidate_recordset()
        self.check_access('write')
        if not self.active or self._profile_identity() != (platform, remote_id):
            raise ValidationError('The account changed during the sync. No profile was saved; retry.')
        super().write({
            'profile_name': profile['name'], 'profile_username': profile['username'],
            'profile_image': BinaryBytes(profile['image']) if profile['image'] else False,
            'profile_synced_at': fields.Datetime.now(),
            'profile_source_id': remote_id, 'profile_source_platform': platform,
        })
        return {'type': 'ir.actions.client', 'tag': 'display_notification', 'params': {
            'title': 'Profile synced', 'message': 'The cached name and photo are ready for the feed.',
            'type': 'success', 'sticky': False,
            'next': {'type': 'ir.actions.client', 'tag': 'reload'},
        }}

    def write(self, vals):
        if CACHE_FIELDS.intersection(vals):
            raise ValidationError('Update cached profiles through Sync Profile.')
        if IDENTITY_FIELDS.intersection(vals):
            vals = dict(vals, **{name: False for name in CACHE_FIELDS})
        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        if any(CACHE_FIELDS.intersection(vals) for vals in vals_list):
            raise ValidationError('Update cached profiles through Sync Profile.')
        return super().create(vals_list)


class SocialPostProfile(models.Model):
    _inherit = 'cafe.social.post'

    feed_profile_name = fields.Char(compute='_compute_feed_profile')
    feed_profile_avatar = fields.Char(compute='_compute_feed_profile')
    feed_profile_username = fields.Char(compute='_compute_feed_profile')

    @api.depends('social_account_ids', 'social_account_ids.profile_display_name',
                 'social_account_ids.profile_avatar_url', 'social_account_ids.profile_username',
                 'social_account_ids.profile_source_platform', 'social_account_ids.profile_source_id',
                 'social_account_ids.platform', 'social_account_ids.instagram_user_id',
                 'social_account_ids.facebook_page_id')
    def _compute_feed_profile(self):
        for post in self:
            accounts = post.social_account_ids
            post.feed_profile_name = False
            post.feed_profile_avatar = False
            post.feed_profile_username = False
            if len(accounts) == 1 and accounts.platform in ('facebook', 'instagram'):
                post.feed_profile_name = accounts.profile_display_name
                post.feed_profile_avatar = accounts.profile_avatar_url
                if (accounts.platform == 'instagram' and accounts._profile_identity()
                        == (accounts.profile_source_platform, accounts.profile_source_id)):
                    post.feed_profile_username = accounts.profile_username
