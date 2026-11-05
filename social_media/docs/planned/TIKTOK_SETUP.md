# TikTok prototype — incomplete and postponed

This is a source-boundary note, not a verified installation recipe. The current addon has a TikTok picker card, manual-token account fields, video attachment checks, upload-to-inbox and status-request code. End-to-end authorisation/upload/publication has not been confirmed for this project.

## What remains in source

- `tiktok_access_token` and `tiktok_open_id` on the social account, using a manual manager-visible token path.
- Video fields and TikTok-related compliance checks on `cafe.social.post`.
- `action_upload_tiktok_draft()` and `action_check_tiktok_status()` plus latest remote status/identifier fields.
- A `services/tiktok_service.py` prototype for upload initialisation, transfer and status requests.

An inbox-upload response is not evidence a video is publicly published. A picker card or a button is not a working OAuth connection.

## Before resuming this phase

Write/review requirements, scopes, consent/privacy UX, token storage/renewal, failure/retry behavior and acceptance criteria. Recheck the current TikTok developer-console requirements and sandbox restrictions against official documentation at that time; do not reuse an old screenshot or assume production approval.

Distinguish an upload that the creator finishes in TikTok from Direct Post. Treat OAuth, refresh, supported upload format/limits, scheduled behavior and remote confirmation as unverified until exercised. Earlier prepared OAuth packages are not installed or represented as complete in this branch.

The Meta environment-variable setup does not secure or renew the TikTok prototype's manually entered token. Audit that path before production use. Keep real credentials outside Git and never present a draft upload as confirmed public publication.

See the [roadmap](../ROADMAP.md) and [verification boundaries](../reference/VERIFICATION.md).
