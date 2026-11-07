# Current functionality

Updated: 2026-11-07. Recorded code release: `5a98517`. Addon version: `20.0.7.0.0`.

This is a retrospective implementation reference. Verification is recorded separately in [VERIFICATION.md](VERIFICATION.md); source availability and owner-reported results are different evidence levels.

## Business features

- Branch and social account management, with a required branch on each account.
- Campaigns with required dates, optional product, discount, allowed accounts and an inclusive duration display.
- Reusable caption templates with `{{branch}}`, `{{campaign}}`, `{{product}}`, `{{discount}}`, `{{start_date}}` and `{{end_date}}`.
- Separate post state, approval status and compliance result.
- One Marketing Manager approval level; Submit, Approve, Reject and Request Changes with required feedback.
- Optional Ollama writing review and suggested rewrite.
- Content Calendar, Campaign Calendar and branch/campaign filters.

Validation checks campaign presence, branch/account consistency, current campaign dates and applicable discount wording. Empty campaign allowed-account lists impose no additional account restriction. Campaign state is not enforced by these checks. Branch filters are not branch-level access isolation.

## Editor, previews and Designer

The post form provides side-by-side editing and a platform-specific preview, with Review, AI Review and Publishing details tabs. Previews are local representations; they are not embedded Facebook/Instagram renderers and do not guarantee the final platform layout.

Post Designer is an Owl 3/canvas editor for **1080 × 1080 square** and **1080 × 1350 portrait** images, with up to eight text/image layers. A compact action/formatting toolbar, left Blocks/Templates/Layers/Background sidebar, neutral workspace and selected-object Properties replace the earlier large-heading layout.

- Layer selection/naming, hide/show, lock/unlock, ordering, duplicate and removal.
- Drag movement and canvas/visible-layer alignment guides; Option/Alt bypasses snapping. Hidden objects are excluded from snapping targets; visible locked objects remain targets.
- Text family, bold/italic, alignment and spacing. Side midpoint handles set wrapping width without changing font size; corners resize text. Manual/blank line breaks are retained, and long words split to fit. Automatic-width layers retain manual breaks until a width is set.
- Image crop frames (original, square, 4:3 landscape, 4:5 portrait), 100–400% zoom, drag positioning and Apply/Cancel/Reset. The stored source image is retained; full-canvas background cropping is unchanged.
- Whole-layout square/portrait conversion preserves sizes/crops and centres layers vertically, including hidden/locked layers; templates adapt vertical spacing when applied. Review boundaries when shrinking a canvas.
- Bounded session-only undo/redo and keyboard movement. Saving creates a private JPEG and editable JSON, clears a legacy Instagram URL and resets validation/approval through existing guarded content writes. Concurrent/stale saves are rejected.

The shared visual-template library is separate from caption templates. Marketing Managers save named immutable copies and archive layouts; Marketing Users browse/apply independent copies. Saving a template does not save/approve the post; applying changes the editor until Save JPEG to post. Python gates and model ACLs enforce manager management. The library is shared across the marketing application, without new branch/company isolation.

Versions 1–5 remain readable; new saved documents use **schema 6**, with validated canvas dimensions. The server checks that the JPEG matches the selected dimensions. Addon version and document schema are different version numbers.

Designer remains limited to unpublished drafts with write access, no active/uncertain publishing attempt and no video. It does not provide AI image generation, background removal, rotation, multi-page editing, multi-select/grouping or arbitrary canvas sizes. [Designer setup](../setup/POST_DESIGNER_SETUP.md) covers controls, permissions and storage limits.

## Platform publishing

| Platform/path | Implemented behavior | Evidence boundary |
| --- | --- | --- |
| Facebook | Text or one attached JPEG/PNG; immediate/scheduled publication; confirmed remote identifiers | Owner reported earlier live publication/scheduling; latest regression matrix pending |
| Instagram attachment | One JPEG and caption; automatic Cloudinary hosting, media container and publish/check flow | Owner reported live immediate publication |
| Instagram scheduling | Uses the Odoo scheduling action and adapter | Owner reported the scheduled flow working; latest-release regression and independent platform evidence remain pending |
| Instagram legacy URL | Public HTTPS JPEG instead of an attachment | Earlier manual/public-URL publication reported; continued hosting is required |
| TikTok | Manual-token video inbox-upload prototype and status actions remain | Incomplete, not end-to-end verified, postponed |
| X / other | Platform selections | No publishing adapter; no LinkedIn integration |

Facebook and Instagram use separate post records. Supported media limits are adapter limits, documented in the setup guides; not every platform format is supported.

Instagram now returns a reload action after confirmed success and checks for an already-published result before and after acquiring its row lock. This addresses stale form/repeated-action behavior in source; targeted live concurrency and refresh verification remains outstanding. Never use repeated publishing as a page-refresh mechanism.

## Social Feed and profile sync

Social Feed groups local records in Published state with one Facebook/Instagram platform. It shows account labels/profiles, captions, attached post images, publication dates and branches. It does not import existing platform posts, comments, likes, messages or analytics. Older locally simulated Published records are not proof of a remote publication.

View on Facebook opens only a confirmed Facebook result with a valid remote identifier. The button is also available on eligible post forms.

Marketing Managers can explicitly Sync Profile for an active Facebook/Instagram account. The service reads its remote name/photo and Instagram username through existing credentials, normalises a small JPEG, and caches it in Odoo. Feed loading makes no external profile request. Local account name/handle remain unchanged; API/download failures retain the existing cache. Missing/default photos use a platform-logo fallback. Identity changes clear the cache; source identity is also checked during display and after a concurrent sync.

Profile sync does not require OAuth or a tunnel. It does not renew tokens, update the composer preview or maintain a historical profile snapshot per post. Old cards display the account's current cached profile.

## Scheduling and calendars

A configured minute-interval cron searches up to 100 due Scheduled posts per run. It locks and rechecks records, then uses the same platform publishing actions. Odoo, PostgreSQL, network connectivity and valid credentials must remain available; execution is not guaranteed at an exact second.

Content Calendar has controlled drag rescheduling for Marketing Managers. Only approved, validated, not-yet-attempted Scheduled posts may move; the new datetime must be in the future and within campaign dates. Calendar day moves preserve the old local clock time; ambiguous/nonexistent daylight-saving times are rejected. Content approval remains unchanged, publishing preflight is repeated, and a chatter note records the move.

Draft records with retained planned dates may appear but are not scheduled jobs. Campaign Calendar remains a date-range view with no automatic campaign activation/completion.

## Credentials, history and limitations

Facebook/Instagram use environment-variable tokens; Cloudinary uses environment credentials. OAuth account connection and automatic token renewal are absent from this source. The TikTok prototype uses a separate manual token field, not the Meta credential path.

Chatter tracks selected workflow changes and review feedback. Latest platform result fields are not an immutable publishing-attempt ledger. The [attempt-history specification](../../specs/001-facebook-attempt-history/spec.md) is Draft and unimplemented.

Remote service operations and the database transaction are not atomic. There is no general retry queue, reconciliation UI or crash-proof exactly-once delivery. Cloudinary assets are not automatically cleaned up. No multi-level review, social inbox, engagement analytics, Facebook video, Instagram multi-image/Reels/Stories, or completed TikTok Direct Post is provided.

See [Workflow](WORKFLOW_REFERENCE.md), [Model reference](MODEL_REFERENCE.md) and the [roadmap](../ROADMAP.md). The [October 28 baseline](../baseline-2026-10-28/CURRENT_FUNCTIONALITY.md) is historical and unchanged.
