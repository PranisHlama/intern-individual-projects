from odoo import models


class SocialAccountPicker(models.TransientModel):
    _name = 'cafe.social.account.picker'
    _description = 'Choose Social Account Platform'

    def _open_account_form(self, platform):
        self.ensure_one()
        # The normal account form/ORM still enforces account creation permissions.
        view = self.env.ref('cafe_social_marketing.cafe_social_account_view_form')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Add Social Account',
            'res_model': 'cafe.social.account',
            'view_mode': 'form',
            'views': [(view.id, 'form')],
            'target': 'current',
            'context': {'default_platform': platform},
        }

    def action_facebook(self):
        return self._open_account_form('facebook')

    def action_instagram(self):
        return self._open_account_form('instagram')

    def action_tiktok(self):
        return self._open_account_form('tiktok')
