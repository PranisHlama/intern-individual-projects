# Current functionality

Updated: 2026-11-05. Source: `76f9e2b`. Declared addon version: `20.0.6.1.0`.

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

Post Designer is an Owl 3/canvas editor for a 1080 × 1080 image. It supports three starter layouts, background colour/photo, text/photo/logo layers, drag positioning, corner resizing, canvas alignment, duplication, layer ordering and removal. Text supports system font families, bold/regular, italic, multiline alignment and line spacing. There is an eight-layer limit.

Undo/redo is bounded and session-only. Keyboard movement and shortcuts supplement mouse controls. Saving creates a private JPEG attachment and retains an editable JSON document; it replaces selected post media only with confirmation, clears the legacy Instagram URL, and resets validation/approval. Version-1 documents remain readable; new saves use version 2. Concurrent/stale saves are rejected.

Designer is limited to unpublished drafts with no active/uncertain publication attempt and no video. It has no AI image generation, automatic text wrapping, freeform crop/rotation, multi-page layout or additional aspect ratios.

## Platform publishing

| Platform/path | Implemented behavior | Evidence boundary |
| --- | --- | --- |
| Facebook | Text or one attached JPEG/PNG; immediate/scheduled publication; confirmed remote identifiers | Owner reported earlier live publication/scheduling; latest regression matrix pending |
| Instagram attachment | One JPEG and caption; automatic Cloudinary hosting, media container and publish/check flow | Owner reported live immediate publication |
| Instagram scheduling | Uses the Odoo scheduling action and adapter | Live scheduled test remains outstanding |
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
