# Workflow Reference

Baseline: uploaded addon version `20.0.4.1.0`, reviewed 2026-10-28.
This describes the effective source implementation. It is not a record of tests
executed against a running Odoo instance.

## Preparation and review

1. Create a branch and social account. For Facebook, configure numeric Page ID and
   an environment-variable name; actual token is supplied to Docker separately.
2. Create a campaign with branch, dates, product/discount and optional account
   restriction. Its state is managed separately; current post compliance does not
   require Active state.
3. Create a Draft post. Select branch/campaign/accounts, enter text or apply a
   template, and optionally attach media. Facebook supports no attachment or one
   JPEG/PNG; a selected TikTok account requires a supported video for compliance.
4. Optionally run AI Review. Read tone, clarity, issues and rewrite. Applying the
   suggestion changes the message and resets approval/validation/AI results.
5. Run Validate Post to save a readable compliance result. The normal Submit button
   requires the saved Passed flag. The server submission method independently
   rechecks actual compliance, rather than relying on that flag alone.
6. Submit for Review. The review extension permits only Draft with Not Submitted,
   Rejected, or Changes Requested approval status. Base submission sets Pending,
   records submitted_at, clears approver metadata and marks validation Passed.
7. Manager approves, rejects, or requests changes. Approval rechecks compliance;
   Facebook photo approval records the image hash. No second reviewer or prohibition
   on approving one's own post is implemented.

## Two separate state dimensions

Post state is Draft / Scheduled / Published / Cancelled. Approval state is Not
Submitted / Pending / Approved / Rejected / Changes Requested. Compliance status is
Not Validated / Passed / Failed. These are separate fields, not one combined state.

| Action / trigger | Preconditions in the action path | Result |
| --- | --- | --- |
| Submit for Review | Draft; allowed previous approval state; compliance passes | Pending; submission time; approver cleared |
| Approve | Manager; Pending; compliance passes; valid Facebook image if present | Approved; approver/time; photo hash |
| Reject | Manager; Pending | Rejected; approver cleared; no mandatory reason |
| Request Changes | Manager; pending/approved Draft or Scheduled; no confirmed FB post or Unknown result; nonblank reason | Draft + Changes Requested; approver cleared; latest reason/requester/time plus chatter |
| Edit protected content | Not Published, no confirmed FB ID or Unknown result | Validation and approval cleared; a Scheduled post becomes Draft |
| Reset Approval | Base method writes Not Submitted and clears submission/approver | Does not itself reset post state or clear all related reports |
| Schedule | Facebook preflight; future scheduled_at within campaign date bounds | Scheduled; validation Passed/time |
| Publish Now / cron | Facebook preflight and locked recheck | Confirmed Published, or Draft with Failed/Unknown result |
| Cancel | Base method sets Cancelled | Does not delete a remote Facebook post |
| Reset to Draft | Base method sets Draft, clears published_at | Does not clear Facebook IDs or solve unknown outcome |

This table describes action methods and normal UI paths. It does not claim every
precondition is universally enforced for arbitrary direct record writes.

## Request Changes detail

The manager opens a transient `cafe.social.request.changes` wizard. Cancel closes
without applying feedback. Confirm rejects whitespace-only reason and rechecks post
eligibility. The final write returns to Draft, sets Changes Requested and clears
approved_by_id/approved_at. scheduled_at is retained; validation status/report and
submitted_at are not explicitly cleared by this action. A retained date or Passed
badge does not imply the post is approved or still scheduled.

The latest feedback fields persist after later review as context. Editing actual
content resets approval to Not Submitted; the user validates/resubmits and the
manager approves again. Resubmission can occur without changing content: the code
does not require proof that the requested edit was made.

## Effective Facebook publishing sequence

1. `_facebook_preflight()` requires Draft/Scheduled, no stored remote post ID, no
   Unknown result, Approved, nonblank text, exactly one Facebook account, no
   video_file, eligible photo if attached, successful current compliance and valid
   Page/token configuration.
2. `SELECT ... FOR UPDATE` locks this post's database row. The record cache is
   invalidated and preflight repeated, serialising attempts for the same record.
3. With no attachment, `FacebookService.publish_text` POSTs to the configured Page
   `/feed`. With one image, `publish_photo` sends multipart bytes to `/photos`.
4. The source service defaults to Graph API `v26.0`, uses a Bearer header,
   connect/read timeout `(10,45)` and disables redirects. This is a source setting,
   not a claim about current platform requirements or token lifetime.
5. Text needs a numeric Page_post-style remote ID. Photo needs a numeric photo ID
   and a Page_post-style post_id. Missing/malformed IDs produce Unknown.
6. On confirmed success, write remote IDs, Published result/state and published_at;
   clear latest error. No separate attempt history row is created.
7. Caught FacebookAPIError writes Draft plus Failed/Unknown and returns a warning
   notification instead of raising. Most API rejections are Failed; network errors,
   server HTTP 5xx, non-JSON/wrong-shaped responses and missing IDs are treated as
   uncertain. Numeric HTTP/API codes are used in rejection summaries rather than
   copying raw remote error messages.
8. Unknown blocks further publication and content edits. No reconciliation action
   exists in this ZIP. Repeating Publish Now is not a safe reconciliation strategy.

The row lock prevents one class of concurrent resend on the same record. It is
not exactly-once delivery across the database and Facebook, across new replacement
records, or across a crash/rollback after remote acceptance.

## Scheduler

`data/ir_cron.xml` declares an active action every one minute calling
`model._cron_publish_scheduled_posts()`. The effective implementation is facebook.py,
not the older local-only cron in social_post.py.

It selects up to 100 Scheduled posts whose scheduled_at is not false and is due,
then calls action_publish per post. ValidationError returns the post to Draft with
Failed/latest error. API errors handled inside action_publish also return to Draft,
so there is no automatic retry queue. No per-post savepoint or unexpected-error
recovery is declared. Cron's actual runtime frequency, user and transaction outcome
must be checked in Odoo; interval configuration is not an exact delivery guarantee.

## Content and campaign calendars

| Calendar | Placement | Visibility / behaviour |
| --- | --- | --- |
| Content Calendar | scheduled_at | Action filters only nonempty dates, not state; branch colours/sidebar; branch/campaign search and state/Changes Requested filters |
| Campaign Calendar | date_start to date_end; all-day flag True | Branch colours/sidebar; status filters; duration includes both endpoints |

Both start in month view and disable create/edit/delete/quick_create in the calendar
architecture. Edit dates through the normal form. Content Calendar shows planned
time, not published_at or a remote audit log. A Draft returned for changes may
remain visible at its retained planned time but is no longer picked by cron.

For campaigns, October 10–20 computes 11 days and a same-day campaign computes 1.
The range's final-day rendering, timezone boundaries and month transitions need a
live UI check. Calendar date display does not drive campaign activation/completion.

## AI service boundary

The service POSTs caption and branch/campaign/product/discount/date/account context
to `http://host.docker.internal:11434/api/chat` with model `qwen2.5-coder:7b`,
stream=False, format=json and 90-second timeout. These are hardcoded source values.
They are separate from the Pi development assistant's provider/model configuration.

It parses the HTTP response JSON then message.content JSON. It does not enforce a
complete output schema beyond parsing/access used by the caller. The UI stores
assessment, tone, clarity, potential issues, rewrite and timestamp. AI is asked not
to decide deterministic business facts. It receives textual context, not images or
video. AI success is not a required gate in the publishing preflight.

## TikTok prototype boundary

A manager-only upload action rechecks compliance and Approved status, selects one
TikTok account, reads its manually stored token, decodes the video and requests
`/v2/post/publish/inbox/video/init/`. The service PUTs byte chunks to the returned
upload URL and records publish_id plus UPLOADED status/time, then posts to chatter.

The source accepts MIME types video/mp4, video/quicktime and video/webm; it declares
4 GiB maximum file size, 5 MiB minimum/64 MiB normal maximum chunks and adjusts a
small final remainder. These are implementation limits, not freshly verified
platform specifications. The whole video is decoded into memory.

The independent status action POSTs to `/v2/post/publish/status/fetch/` and records
status/details. It does not mark the Odoo post Published or apply the caption via
the upload init payload. The user must finish inside TikTok. OAuth callbacks,
refresh tokens, Direct Post, duplicate-upload handling and production audit
completion are not implemented. Source presence must not be presented as a
successful live integration.

## Documentation-first continuation

This baseline captures implemented behaviour and gaps. Next development should
choose a specific existing gap or requested feature, write its intended behaviour
and acceptance criteria, clarify uncertainties, plan tasks, then implement and
verify. Do not silently turn a baseline limitation into an implemented fix.
The attempt-history proposal is paused and excluded from this task.
