# Current Functionality

Baseline date: 2026-10-28. Source addon version: `20.0.4.1.0`.

## Purpose and architecture

`cafe_social_marketing` supports preparing, reviewing, approving, planning, and
publishing social content for a multi-branch cafe. Odoo stores workflow data and
runs business checks. Local Ollama reviews writing quality. Platform adapters make
outgoing requests for supported operations.

AI review is optional in the current server workflow: submitting, approving,
scheduling, and publishing do not require `ai_review_status == 'reviewed'`.
AI output does not itself approve or publish a post.

## Evidence labels

- **Source implemented**: relevant code is present; not a guarantee of runtime success.
- **User-reported live success**: previously confirmed by the project owner in this
  conversation; not repeated against this ZIP during this review.
- **Unverified**: implementation or runtime behaviour still needs acceptance checks.
- **Not implemented**: no implementation was found in this supplied source.

## Capability inventory

| Capability | Existing implementation and boundaries | Evidence |
| --- | --- | --- |
| Branches | Name, code, address, and archive flag. Branch is a data relationship, not a demonstrated security boundary. | Source implemented |
| Social accounts | Platform, handle, required branch, archive flag; Facebook Page settings and manager-restricted TikTok token fields. | Source implemented |
| Campaigns | Required branch/dates; optional product; discount and allowed-account list; Draft/Active/Completed/Cancelled actions. | Source implemented |
| Templates | Optional branch; six literal placeholders rendered into the post message. | Source implemented |
| Preview | Escaped message and branch/campaign/account text rendered as HTML. Not a platform-native image/video preview. | Source implemented |
| Compliance | Checks campaign presence, matching branch/accounts, today's campaign dates, applicable discount and TikTok video selection. Does not check campaign state. | Source implemented |
| Approval | Submit, manager Approve/Reject, content-change resets. One approval level. | Source implemented |
| Request Changes | Manager-only wizard with required reason; latest feedback fields and escaped chatter message; returns post to Draft. | Source implemented; live completion not confirmed here |
| AI review | Ollama JSON response supplies assessment, tone, clarity, issues and rewrite. Applying rewrite changes the message and resets related checks. | Source implemented; not called during this review |
| Video attachment | Dedicated binary and filename; TikTok decoding path checks guessed MIME type and size. Not proof of codec validation or successful video transfer. | Source implemented |
| Facebook publishing | One Page, text or one JPEG/PNG up to adapter's 10 MiB limit. Requires approval and rechecks compliance. | Source implemented; user previously reported immediate and single-photo publication success |
| Facebook scheduling | Odoo cron invokes the same Facebook adapter after the scheduled time. Odoo must remain running. | Source implemented; user previously reported scheduled publication success |
| Content Calendar | Branch colours/sidebar filters; uses scheduled_at; contains every state with a planned date, not only active scheduled jobs. Calendar editing is disabled. | Source implemented; user previously opened the calendar |
| Campaign Calendar | All-day date_start/date_end range, branch filters, status filters, inclusive computed duration. | Source implemented; final-day rendering and live completion unverified here |
| TikTok draft upload | Manual-token service for inbox initialization, video byte/chunk transfer and remote status query. Separate manager upload action. | Code exists; end-to-end live success not confirmed |
| Chatter | Posts/campaigns inherit mail.thread and mail.activity.mixin; selected fields tracked; Request Changes adds comments. | Source implemented; not complete version or approval history |
| Instagram / X | Values can be selected as account platform, but no publishing adapter exists. | Not implemented |
| OAuth / token refresh | No TikTok/Facebook OAuth controllers or automated refresh implementation in this ZIP. | Not implemented |
| Attempt history / automatic retries | Only latest Facebook result fields; no separate attempt model, retry queue or reconciliation UI. | Not implemented |

## Deterministic rules actually present

| Rule | Exact baseline behaviour | Source |
| --- | --- | --- |
| Campaign required for compliance | Missing campaign returns an error immediately. The database field itself is optional. | models/social_post.py: _get_compliance_checks |
| Branch matches campaign | Post branch must equal campaign branch. | Same method |
| Campaign date valid now | Uses fields.Date.context_today(self); before start or after end is rejected; endpoints inclusive. | Same method |
| Campaign status | No check of Draft/Active/Completed/Cancelled in compliance. Do not claim cancelled campaigns are blocked by status. | Same method |
| Account branch | At least one account; every selected account must belong to the post branch. | Same method |
| Campaign account restriction | Nonempty allowed-account list restricts selection; an empty list means unrestricted accounts, subject to branch checks. | Same method |
| Discount wording | For positive campaign discount, detect numeric percentages or 'percent'; require at least one and reject any value differing by more than 0.01. No discount check is required when campaign discount is zero. | Same method |
| Campaign integrity | End date cannot precede start; discount must be in 0–100. | models/campaign.py: constraints |
| Scheduled date | Must exist, be future, and its Python date must lie within campaign dates. Today's date check also runs, so future campaigns cannot yet pass preflight before their start. | action_schedule and Facebook preflight |
| Photo approval | Exact attachment bytes are hashed at approval and rechecked before publishing/scheduling. | models/facebook.py |

For a 20% campaign, text saying 30% fails. This regex does not understand all
natural-language offers and treats every detected numeric percentage as relevant.
It is not a general claims verifier.

## Important limitations and review findings

These are observations, not fixes made by this documentation task.

1. **Campaign state is not enforced in post compliance.** Older claims that status
   validity is checked are broader than the code.
2. **Branch filtering is not branch isolation.** The supplied access CSV gives
   broad model-level permissions with empty domains; no per-branch visibility
   restriction is declared here. Actual effective access also depends on runtime
   Odoo and other installed modules.
3. **Action checks are stronger than generic write protection.** Approve/Reject
   methods check manager role and pending state. Request Changes protects its own
   metadata. Facebook guards adapter result fields and non-manager approval writes.
   Other workflow metadata and generic state writes are not comprehensively
   protected in these files. Read-only UI declarations are not proof of RPC safety.
   For example, scheduling preconditions are in the action, not a general guard on
   every write of state='scheduled'. Runtime negative-access tests are needed.
4. **Related-record edits do not automatically reset all posts.** Changes to post
   content reset validation/approval; changing a linked campaign/account separately
   does not implement a cross-model invalidation mechanism. Publishing rechecks
   current compliance, but that is not content-versioned manager approval.
5. **AI reset coverage is incomplete.** Post message/branch/campaign/accounts/media
   relation changes reset stored AI results; video_file/video_filename and template_id
   alone are absent from the AI write reset set. AI does not analyse media bytes.
6. **Time interpretation needs testing.** Compliance uses the context's current
   date; scheduled bounds use scheduled_at.date() without an explicit timezone
   conversion. Calendar display timezone and scheduler context may differ near
   midnight. Cron's configured user is not explicitly set in the supplied XML.
7. **Transactions are not remote atomicity.** Facebook failures caught as
   FacebookAPIError return a notification, allowing failure fields to commit in
   ordinary successful transactions. A later error or rollback can still lose local
   changes after Facebook accepted a request. No durable job/outbox is provided.
8. **Failure handling differs across services.** AI/TikTok handlers sometimes write
   error state then raise; normal Odoo request rollback can undo those writes.
   TikTok requests.RequestException is not consistently converted to TikTokAPIError;
   service payload-shape validation is limited. Do not promise persisted error
   history or robust automatic recovery.
9. **TikTok remains a prototype.** Token is a manager-restricted Char stored through
   Odoo, not an encrypted vault field. MIME guessing is filename-based; video
   decoding assumes base64 data and has not been verified for Odoo 20 BinaryValue.
   Raw remote text may appear in TikTok errors. There is no repeated-upload guard
   comparable to Facebook's unknown-outcome protection, nor automatic public-post
   state reconciliation.
10. **Calendars are planning views.** Content Calendar omits posts without
    scheduled_at, including immediate publications with no date. The campaign
    calendar does not activate or complete campaigns automatically.
11. **History is partial.** Latest reviewer feedback overwrites earlier feedback
    fields; prior Request Changes comments remain in chatter. Chatter is not a full
    immutable content/version/approval ledger. Managers have delete permissions
    for the five main models. Branch deletion cascades to social accounts.
12. **Legacy implementation remains.** Base social_post.py contains local-only
    publish/cron methods. The loaded facebook.py extension replaces them in this
    addon. Describe the effective adapter path, not the obsolete base methods.

## Existing documentation reconciliation

- `MIGRATION_ODOO20.md` names an earlier manifest version and says external
  publishing is still planned. That is stale for Facebook in this ZIP.
- `TIKTOK_SETUP.md` describes the draft-upload code as an integration. It is useful
  implementation/setup guidance, but not evidence that OAuth or live upload was
  completed.
- `REVIEW_CALENDAR_SETUP.md` explicitly calls for local runtime acceptance checks.
  Do not convert its checklists or earlier offline build-test claims into new
  passed-test evidence.
- Standard Odoo comparisons must be scoped to the workflow reviewed and this
  project's multi-branch needs; do not claim these features are absent from all Odoo.

## Runtime verification checklist — not executed in this review

| ID | Scenario | Expected source behaviour / evidence to capture |
| --- | --- | --- |
| B01 | Correct vs incorrect percentage in the same campaign | Correct passes, mismatch blocks submission/publishing; screenshot and values |
| B02 | Wrong branch, account branch, or restricted account | Compliance fails; verify action and RPC paths separately |
| B03 | Date boundary and future campaign | Current date endpoints pass; future-start campaign fails now |
| B04 | Cancelled campaign inside valid dates | Record actual outcome; source currently lacks a state block |
| B05 | User versus manager approval/rejection | User action denied; manager can approve/reject pending post |
| B06 | Request Changes blank / cancel / valid reason | Blank blocked; cancel unchanged; valid returns Draft with feedback/chatter |
| B07 | Edit approved content and apply AI rewrite | Approval/validation reset; no publish without reapproval |
| B08 | Photo bytes changed after approval | Hash mismatch blocks publishing |
| B09 | Facebook immediate text/photo and scheduled post | Test only with authorised demo Page; capture remote IDs and actual Page post |
| B10 | Rejection, timeout, malformed/missing remote IDs | Mock service; distinguish Failed vs Unknown and no blind resend |
| B11 | Content Calendar draft and scheduled post with same date | Both can appear; only Scheduled state is selected by cron |
| B12 | Campaign one-day, inclusive multi-day, month-boundary range | Confirm visual final-day rendering and duration; not a publishing job |
| B13 | Odoo 20 AI and TikTok failures | Check actual binary handling and rollback; no live TikTok claim without test |
| B14 | Generic RPC writes and cross-branch reads | Record allowed/denied results; do not infer security from hidden buttons |

Static review is complete. All runtime checklist items remain unexecuted in this
review, even where earlier user-reported success exists.
