# Model Reference

Updated: 2026-11-01
Addon version: 20.0.6.0.0
Code reference: commit 3c36122

This is a model overview, not an introspected database schema.
Source paths below are relative to cafe_social_marketing/.

## Persistent business models

| Model | Purpose | Main relationships |
| --- | --- | --- |
| cafe.social.branch | Cafe branch details | Referenced by accounts, campaigns, posts and optional branch-specific templates |
| cafe.social.account | Platform account and publishing configuration | Required branch; selected by posts and allowed-account lists |
| cafe.social.campaign | Campaign dates, product, discount and planning | Required branch; optional product; allowed social accounts |
| cafe.social.post.template | Reusable caption text | Optional branch; selected by posts |
| cafe.social.post | Content, review, planning and publishing results | Branch, campaign, social accounts, template and attachments |

Posts and campaigns inherit Odoo mail tracking/activity functionality.
Platform extensions add fields to existing models; they do not create
separate Facebook or Instagram post models.

## Temporary wizard models

| Model | Purpose |
| --- | --- |
| cafe.social.request.changes | Collect a required manager reason and return an eligible post for revision |
| cafe.social.account.picker | Open a new account form with Facebook, Instagram or TikTok preselected |

The picker is a TransientModel, not a connected-account store.
It does not perform OAuth.

## Post status dimensions

| Field purpose | Values |
| --- | --- |
| Post state | Draft, Scheduled, Published, Cancelled |
| Approval | Not Submitted, Pending, Approved, Rejected, Changes Requested |
| Compliance | Not Validated, Passed, Failed |
| Instagram publishing result | Not Sent, Processing / Recheck, Published, Failed, Outcome Unknown |

These dimensions are separate. A planned calendar date does not prove
approval, scheduling or remote publication.

## Instagram account fields

Declared in models/instagram.py on cafe.social.account:

| Field | Purpose |
| --- | --- |
| instagram_user_id | Numeric professional Instagram account ID |
| instagram_token_env | Name of the Docker environment variable containing the token |

instagram_token_env defaults to CAFE_IG_ACCESS_TOKEN and is restricted
to Marketing Managers. The actual token is read from the environment.

## Instagram post fields

Declared in models/instagram.py on cafe.social.post:

| Field | Purpose |
| --- | --- |
| publishing_platform | Computed platform when exactly one account is selected |
| instagram_image_url | Legacy public JPEG URL input |
| instagram_hosted_image_url | Cloudinary delivery URL |
| instagram_hosted_public_id | Hosted asset identifier |
| instagram_hosted_photo_hash | Hash identifying the hosted image bytes |
| instagram_hosting_upload_key | Identifier used for the hosting operation |
| instagram_approved_fingerprint | Signature of content/configuration approved for publishing |
| instagram_container_id | Instagram media-container identifier |
| instagram_media_id | Confirmed published-media identifier |
| instagram_publish_status | Latest adapter result |
| instagram_publish_error | Latest publishing error summary |

Hosting and publishing result fields are readonly in their declarations
and protected by adapter create/write checks. They are not an immutable
publishing-attempt ledger.

## Implementation responsibilities

| Source | Responsibility |
| --- | --- |
| models/social_post.py | Base content, compliance, approval and planning |
| models/review_workflow.py | Request Changes and review restrictions |
| models/social_post_ai.py | Optional AI review and rewrite application |
| models/facebook.py | Facebook publishing, shared publishing hooks and scheduler |
| models/instagram.py | Instagram eligibility, approval fingerprint, hosting and publishing |
| models/account_picker.py | Platform selection actions |
| services/facebook_service.py | Facebook API requests |
| services/instagram_service.py | Instagram container creation, status and publication requests |
| services/cloudinary_service.py | Signed image upload and delivery URL handling |
| services/ollama_service.py | Local AI service requests |
| services/tiktok_service.py | Earlier unfinished TikTok upload prototype |

Cloudinary is an external service, not an Odoo business model.

## Access and history boundaries

Marketing Managers imply Marketing Users.

The main business models grant Marketing Users create/read/update access
and Marketing Managers create/read/update/delete access.
The Request Changes wizard has manager access.
The account picker has Marketing User create/read/update access.

Branch selection and calendar filters do not establish branch isolation.
Effective permissions also depend on Odoo runtime and installed modules.

Selected changes and feedback are retained in chatter.
No dedicated publishing-attempt or content-version model is implemented.

## Historical detail

../docs/baseline-2026-10-28/MODEL_REFERENCE.md preserves the earlier
field-level review for version 20.0.4.1.0. Its source line references and
extension-order description are historical, not current guarantees.
