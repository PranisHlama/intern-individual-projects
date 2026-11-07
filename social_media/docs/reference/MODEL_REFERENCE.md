# Model reference

Updated: 2026-11-07. Recorded code release: `5a98517`. Addon version: `20.0.7.0.0`.

This is a source-based overview, not an introspected database schema. Source paths refer to [cafe_social_marketing/](../../cafe_social_marketing/).

## Business and wizard models

| Model | Purpose and relationships |
| --- | --- |
| `cafe.social.branch` | Cafe details; referenced by accounts, campaigns, posts and optional branch-specific templates |
| `cafe.social.account` | Required branch, platform/name/handle, platform credentials configuration and profile cache |
| `cafe.social.campaign` | Required branch/dates, optional product, discount, allowed accounts, lifecycle state and computed inclusive duration |
| `cafe.social.post.template` | Reusable caption and optional branch |
| `cafe.social.design.template` | Shared immutable visual design document/thumbnail; manager-managed and independent of individual post copies |
| `cafe.social.post` | Caption/media, branch/campaign/accounts/template, compliance, review, schedule and platform results |
| `cafe.social.request.changes` | Transient wizard collecting the manager's required reason and selected post |
| `cafe.social.account.picker` | Transient platform chooser opening an ordinary new account form |

Posts and campaigns inherit mail tracking/activity functionality. Facebook, Instagram, workspace, rescheduling and profile classes extend existing models; they do not create separate platform post models. `models/post_designer.py` both extends posts and declares the separate saved-design template model. Cloudinary and Ollama are services, not business models.

## Post status dimensions

| Field | Values/meaning |
| --- | --- |
| `state` | `draft`, `scheduled`, `published`, `cancelled` |
| `approval_state` | `not_submitted`, `pending`, `approved`, `rejected`, `changes_requested` |
| `validation_status` | `not_validated`, `passed`, `failed` |
| `facebook_publish_status` | `not_sent`, `published`, `failed`, `unknown` |
| `instagram_publish_status` | `not_sent`, `processing`, `published`, `failed`, `unknown` |
| `scheduled_at` / `published_at` | Planned time versus recorded publication time |
| `reviewer_comment`, `changes_requested_by_id`, `changes_requested_at` | Latest Request Changes metadata, maintained through its action |

A planned date does not establish approval, an active job, or successful remote publication. Latest-result fields are not an immutable ledger.

## Account configuration

| Fields | Responsibility |
| --- | --- |
| `name`, `platform`, `handle`, `branch_id`, `active` | Local account identity, branch and archive flag |
| `facebook_page_id`, `facebook_token_env` | Facebook numeric Page ID and environment-variable name; default token variable `CAFE_FB_PAGE_TOKEN` |
| `instagram_user_id`, `instagram_token_env` | Instagram professional ID and environment-variable name; default `CAFE_IG_ACCESS_TOKEN` |
| `tiktok_access_token`, `tiktok_open_id` | Older manager-visible manual token/identifier fields; prototype boundary |

Meta token-variable fields are manager-restricted; helpers read real tokens from the process environment. Profile sync reuses those helpers. There is no installed Meta OAuth credential-vault model.

## Profile cache and feed fields

Declared in [models/social_profile.py](../../cafe_social_marketing/models/social_profile.py).

| Model/fields | Purpose |
| --- | --- |
| Account: `profile_name`, `profile_username` | Separate cached remote display name/username, leaving local labels intact |
| Account: `profile_image` | Readonly, non-copied Binary field stored on the account (`attachment=False`); normalised JPEG written using Odoo 20 `BinaryBytes` |
| Account: `profile_synced_at` | Last successful sync time |
| Account: `profile_source_id`, `profile_source_platform` | Bind the cache to the fetched destination |
| Account: `profile_display_name`, `profile_avatar_url` | Non-stored computed name fallback and local `/web/image/...` URL when identity matches |
| Post: `feed_profile_name`, `feed_profile_avatar`, `feed_profile_username` | Non-stored computed header fields from a sole supported account |
| Post: `feed_platform` | Stored computed Facebook/Instagram platform for a single selected account |
| Post: `feed_image_url` | Computed local URL for a sole eligible attachment |

Profile syncing requires manager membership/write access and rechecks identity under a row lock. Cache fields reject direct ordinary writes/creates; changing the platform or destination ID clears them. Feed rendering makes no remote profile request.

## Publishing and hosting results

Facebook fields include `facebook_post_id`, `facebook_photo_id`, `facebook_approved_photo_hash`, `facebook_publish_status` and `facebook_publish_error`.

Instagram adds:

| Fields | Purpose |
| --- | --- |
| `publishing_platform` | Computed sole selected platform for publishing |
| `instagram_image_url` | Legacy external JPEG URL input |
| `instagram_hosted_image_url`, `instagram_hosted_public_id` | Cloudinary delivery URL and asset identifier |
| `instagram_hosted_photo_hash`, `instagram_hosting_upload_key` | Hosted-byte identity and upload operation key |
| `instagram_approved_fingerprint` | Approved caption/media/destination/configuration fingerprint |
| `instagram_container_id`, `instagram_media_id` | Prepared media container and confirmed published media ID |
| `instagram_publish_status`, `instagram_publish_error` | Latest adapter result/error summary |

Instagram hosting/result fields reject ordinary direct writes through adapter guards. Publication locks the post and repeats preflight. See [Workflow](WORKFLOW_REFERENCE.md) for uncertainty and retry boundaries.

## Designer persistence

Declared in [models/post_designer.py](../../cafe_social_marketing/models/post_designer.py).

| Field/API | Responsibility |
| --- | --- |
| `designer_document` | Readonly, non-copied JSON; versions 1–6 accepted, with new saves using 6 |
| `designer_attachment_id` | Readonly, non-copied generated JPEG relation |
| `action_open_post_designer()` | Unpublished-draft/write-access guard and client action |
| `get_post_designer()` | Document, revision, existing-media indicator and `can_manage_templates` capability |
| `save_post_designer()` | Document/JPEG dimension checks, row lock/revision recheck, replacement confirmation and inherited content write |
| `list_designer_templates(offset)` | Active metadata/thumbnail page (20 items and `has_more`); checks current post access |
| `get_designer_template(id)` | Read-access/active checks and selected template document |
| `save_designer_template(name, document, thumbnail)` | Manager-only immutable snapshot create; no post media/approval write |
| `archive_designer_template(id)` | Manager-only archive; no mutation of existing post copies |

Document schema history:

| Version | Addition |
| --- | --- |
| 1 | Background and text/image layers |
| 2 | Text `font`, `bold`, `italic`, `align`, `lineHeight` |
| 3 | All-layer `name`, `hidden`, `locked` |
| 4 | Text `width`: 0 for automatic/manual-break layout, otherwise 80–1080 logical pixels |
| 5 | Image `cropRatio` (0/750/1000/1250), `cropZoom` (100–400), `cropX`/`cropY` (0–1000) |
| 6 | Root `width: 1080` and `height: 1080` or `1350`; y-coordinate bounds follow height |

Older documents are normalised in the editor without implicit layout changes. Image sources remain embedded; crop settings are non-destructive to that stored source. History and snap guides are not persisted. Export excludes selection/guide controls and hidden layers. The JPEG replaces selected media without deleting detached attachments, clears `instagram_image_url` and resets existing approval/validation.

## Saved visual design model

Also declared in `models/post_designer.py`; the existing import loads both classes.

| Field | Meaning |
| --- | --- |
| `name` | Required trimmed 1–80-character label |
| `document` | Required readonly/non-copied validated JSON snapshot; normal writes cannot overwrite it |
| `thumbnail` | Required readonly/non-copied validated JPEG base64 **Text** field; not an Odoo Binary field |
| `active` | Archive flag, default True |

Thumbnails are 216 × 216 or 216 × 270 and at most 128 KiB. Full documents use the same 7 MiB/embedded-image validation as post designs. Base model audit fields record creation/update metadata; no post foreign key or live dependency binds a draft to its source template.

The unified ACL grants Marketing User `r` and Marketing Manager `crud` for this model. Python requires manager membership for create/write/unlink; create validates all payload fields and write permits only valid `name`/boolean `active`. There is no sudo/public route. These are shared marketing layouts, not a company/branch-isolated library. Templates are revised by saving a new copy; the UI uses archive rather than permanent deletion.

## Implementation responsibilities

| Source | Responsibility |
| --- | --- |
| `models/social_post.py` | Base content, templates, compliance, approval, feed computations and TikTok prototype actions |
| `models/review_workflow.py` | Request Changes wizard, feedback and review restrictions |
| `models/social_post_ai.py` | Advisory review results and suggested rewrite application |
| `models/facebook.py` | Facebook publishing, credentials, photo hash, guarded shared publishing hooks |
| `models/instagram.py` | Instagram approval fingerprint, hosting/container publishing and refresh/repeat-send behavior |
| `models/post_designer.py` | Editable document/JPEG validation, guarded post persistence and shared immutable design model/APIs |
| `models/post_workspace.py` | Confirmed Facebook result URL action |
| `models/calendar_reschedule.py` | Manager-only date moves, timezone handling, row locks and due-time recheck |
| `models/social_profile.py` | Account profile cache, sync permission checks and computed feed headers |
| `models/account_picker.py` | Platform selection actions |
| `services/facebook_service.py`, `services/instagram_service.py` | Platform requests and safe adapter errors |
| `services/cloudinary_service.py` | Signed hosting request and delivery response checks |
| `services/meta_profile_service.py` | Metadata fetch, constrained photo download and small JPEG conversion |
| `services/ollama_service.py` | Optional local writing-review request |
| `services/tiktok_service.py` | Incomplete video upload/status prototype |
| `static/src/post_designer/` | Owl 3 canvas editor, templates and shared workspace/feed styling |

## Access and history boundaries

Marketing Managers imply Marketing Users. The unified `security/ir.access.csv` grants the original business models `cru` to Users and `crud` to Managers; visual design templates grant Users read only and Managers `crud`. Wizard grants are separate. Action guards add requirements, but this source review is not a comprehensive security certification. Branch filters do not establish branch isolation.

Chatter holds selected changes/feedback. No dedicated publishing-attempt or content-version model exists. The constitution and attempt-history specification describe desired future standards/features, not proof of current completeness.

The unchanged [October 28 model baseline](../baseline-2026-10-28/MODEL_REFERENCE.md) retains historical field-level review and source references.
