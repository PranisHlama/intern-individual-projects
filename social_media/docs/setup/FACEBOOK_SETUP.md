# Facebook Page publishing

Source: `76f9e2b`. Supported: text, or one attached JPEG/PNG with a caption; immediate and scheduled publishing. This path uses a configured Page token, not an OAuth connection wizard.

## Configure a saved account

1. Supply a valid Page token to Odoo through the deployment environment; the default name is `CAFE_FB_PAGE_TOKEN`. See [Installation](INSTALLATION.md).
2. Open Configuration → Add Social Account → Facebook, or edit an existing account instead of creating a duplicate.
3. Set the local name, matching cafe branch, Platform = Facebook, and the numeric **Page ID**, not a personal user ID.
4. Enter `CAFE_FB_PAGE_TOKEN` (or another configured `CAFE_FB_...` name) in Token Environment Variable. Do not paste the token itself.
5. Include the account in the intended campaign's allowed-account list if that list is restricted.

The token must permit the Page actions requested by the app. Previously granted test permissions included `pages_show_list`, `pages_read_engagement` and `pages_manage_posts`; platform/app access and Page tasks still govern whether requests succeed. No automated token refresh is implemented.

## Publish a controlled test

Use a dedicated test Page or intentionally authorised content. Select exactly one Facebook account, a matching branch/campaign valid now, and a caption complying with its discount requirement. For text-only publication, leave image/video selections empty. For a photo, attach exactly one nonempty JPEG/PNG no larger than 10 MiB and leave Video Attachment empty.

Validate, submit for review, approve as Marketing Manager, then Publish Now. The adapter checks image signatures and an approved photo-byte hash, locks the post and repeats preflight. Facebook still validates the uploaded content.

Confirm the stored Facebook post ID, Published status and actual Page post. View on Facebook opens the confirmed result. A local preview or an old simulated Published record does not prove a remote post exists.

## Scheduling and errors

Schedule a fresh approved post a few minutes ahead inside campaign dates. Keep Odoo, its cron, network and credentials available. Review [calendar behavior](REVIEW_CALENDAR_SETUP.md) before moving it.

- Failed: a handled rejection or preflight issue; inspect the safe summary and configuration before a permitted retry.
- Outcome Unknown: remote acceptance may have occurred; check the Page and reconcile before any replacement. Blind automatic/manual retry is blocked.
- Remote API calls and local commits are not atomic. Row locks reduce concurrent sends, not crash-related duplication risk.

No Facebook video, multi-photo publishing, retry queue or dedicated attempt-history ledger is implemented. Meta requests use Graph API `v26.0` in this source. Token expiry/revocation requires a local replacement and container recreation.

## Related guides

- [Profile photo/name sync](PROFILE_SYNC_SETUP.md)
- [Designer JPEG creation](POST_DESIGNER_SETUP.md)
- [Verification status](../reference/VERIFICATION.md)
