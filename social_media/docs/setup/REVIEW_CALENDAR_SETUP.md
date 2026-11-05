# Review workflow and calendars

## Roles and review

Use the existing Marketing User/Marketing Manager groups. Managers imply Users; approval/rejection and Request Changes have action-level manager checks. This guide does not establish branch isolation or certify all access-control paths; verify those in the target Odoo runtime.

1. Prepare a compliant Draft, optionally use AI Review, then Validate Post.
2. Submit for Review.
3. A manager approves or rejects a pending post, or opens Request Changes on an eligible pending/approved draft/scheduled post.
4. Request Changes requires a nonblank reason, stores latest feedback and adds a chatter comment, clears approval identity/time and returns the post to Draft.
5. Revise, validate and resubmit before another approval.

Changing approval-relevant caption, branch, campaign, account or media invalidates validation/approval. A planned date may remain on a Draft returned for revision; that is not an active publishing schedule. Existing remote/uncertain results restrict changes. See [Workflow](../reference/WORKFLOW_REFERENCE.md).

## Content Calendar

Content Calendar shows posts with a planned `scheduled_at`, including visible non-Scheduled states. Immediate publications without a planned date may not appear. Filters are planning aids, not record-isolation rules.

The calendar now permits **controlled rescheduling**, replacing the older read-only setup:

- Only a Marketing Manager with normal write access may move an approved, validated Scheduled post.
- No Facebook/Instagram/TikTok attempt may already have started or produced a result; adapter statuses must still be Not Sent.
- Move one post at a time and change only its scheduled date/time.
- New time must be future and within campaign dates. Existing credentials, media fingerprint and compliance are rechecked without sending a publish request.
- A calendar day drag retains the previous local clock time, using the user's timezone. Ambiguous/nonexistent daylight-saving times are rejected for explicit correction in the form.
- Content approval is retained for this allowed manager date change; a chatter note records the actor and old/new times.

The server guards Scheduled date changes through forms/RPC as well as calendar moves. A visible draggable card does not imply the current user/record is eligible. Published/cancelled posts and unapproved, already-processing or uncertain attempts cannot be rescheduled this way.

## Scheduler

The configured scheduled action is Cafe Social Marketing: Publish Scheduled Posts, with a one-minute interval. It considers up to 100 due records per pass, locks them and rechecks due time/state before invoking the platform adapter. This reduces races with calendar moves; it is not an exact-second delivery guarantee or crash-proof queue.

Keep Odoo, database, internet and credentials available. A changed date that appears in the calendar is not proof a later external publish succeeded. Test an actual due Facebook/Instagram post separately.

## Campaign Calendar

Campaign Calendar shows start/end ranges, branch filters and inclusive duration (`end - start + 1`). Campaign date order and a 0–100% discount range are constrained in the model. This view does not automatically activate or complete campaigns. The current post compliance check does not require campaign state to be Active.

## Verification

The owner reported calendar dragging working after a timezone compatibility fix. Preservation of local clock time, chatter, negative permissions, campaign edges, daylight-saving handling and actual publication after moving require explicit recorded checks. Use the [verification checklist](../reference/VERIFICATION.md), not this guide as evidence those cases passed.
