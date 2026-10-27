# Request Changes and Branch Content Calendar — v6

Based on v5 fix2, including the verified Odoo 20 BinaryValue.content reader.
Facebook text/single-photo publishing, scheduler, environment-variable tokens,
AI review, and existing TikTok draft upload code remain in the module.

## Install

Back up the current addon before replacing it. Keep your current facebook.env
and Docker Compose configuration. Extract only cafe_social_marketing into:

`/Users/prabinkauchha/desktop/odoo20/addons`

Restart odoo20, then in Odoo Apps upgrade Cafe Social Marketing. This upgrade
is mandatory: it adds feedback fields, a transient wizard model, its access
permission, the selection value and new views. A restart alone is insufficient.
Do not uninstall the module or delete your database. The upgrade does not
require another Meta login or token. If the local source changed since v5 fix2,
merge those changes before installing this ZIP.

## Request Changes

1. Create and validate a post, then Submit for Review.
2. As Marketing Manager, click Request Changes.
3. Enter a reason such as "Mention Baneshwor branch and correct the discount".
4. Send Request. A blank/whitespace reason is blocked. Cancel closes the dialog
   without changing the post.
5. The post returns to Draft with approval status Changes Requested; approval
   author/date are cleared. For scheduled posts this also stops scheduling.
6. The latest reason, requester and request time appear on the form. The reason
   is also added to chatter. Earlier reasons remain in chatter when another
   request is sent. This is not a complete versioned approval-history feature.
7. The author edits content. Existing validation/approval reset behavior applies.
   Validate again and Submit for Review, then manager Approve.
8. Publish/schedule again only after current approval. Photo approval still
   checks the image content hash.

Managers may request changes on pending or approved draft/scheduled posts.
Published, cancelled and uncertain Facebook publishing results are blocked.
Marketing Users may read feedback but cannot invoke the wizard or forge feedback
through direct record writes. Reject is retained for outright rejection.
The latest feedback is retained after resubmission/approval as context; it does
not mean that the post is still awaiting changes. Use Approval Status for that.

## Calendar

Open Social Marketing > Content Calendar.

* Posts are placed by Scheduled Date, in the logged-in user's Odoo timezone.
* Branches have distinct colors and sidebar filters.
* Search by branch or campaign; filter Draft, Scheduled, Published, Cancelled,
  or Changes Requested. No Scheduled-only default filter hides other states.
* Month is the initial view; standard calendar navigation supports other scales.
* Click an event to inspect its summary. Use Posts/the list-form views to edit
  and run workflow actions. Calendar creation, dragging and deletion are disabled.
* Unscheduled drafts do not appear. The normal Posts list retains all posts.
* Published posts retain their planned scheduled date. This calendar is a planning
  view, not a log of exact remote publication times. An immediately published
  post without Scheduled Date does not appear here.
* Requesting changes retains the planned date but turns the post into a Draft.
  Its calendar presence does not mean a publishing job is still scheduled.

## Local acceptance checks

Check both roles (a manager plus a regular Marketing User):

1. User cannot Request Changes; manager can open dialog on a pending post.
2. Blank reason is rejected, and Cancel leaves approval/state unchanged.
3. Request on an approved scheduled post returns it to Draft and blocks cron
   publishing. Feedback appears to the author and in chatter.
4. Edit, validate, resubmit, approve, then publish a fresh test photo to Facebook.
5. Schedule another test photo; ensure automated publishing still works.
6. Create posts with dates in two branches; verify colors and sidebar filters.
7. Confirm an unscheduled draft remains in Posts and is absent from Calendar.
8. Confirm dragging cannot change scheduled dates and no quick-create dialog opens.

Offline tests use lightweight Odoo/HTTP stubs for review authorization, mandatory
feedback, state transitions, write protection, content checks, and existing Facebook
behavior. XML syntax, inherited view targets and manifest references are checked.
No live Odoo runtime or Meta credentials are available in the build environment;
upgrade, visual rendering and end-to-end publishing require your Mac verification.

## Campaign Calendar — v7

Open Social Marketing > Campaign Calendar. Campaigns appear as all-day ranges
using existing Start Date and End Date, colored/filtered by branch. Click to
inspect campaign, product, discount, status and Duration (days). The duration
includes both dates: October 10–20 = 11 days; October 10–10 = 1 day.
The campaign form also shows the computed duration beside the dates.

Dates remain the source of truth. This does not automatically activate or
complete campaigns. Creation, dragging, resizing and deletion in the calendar
are disabled; use Campaigns to edit records. The post calendar remains separate.

Restart Odoo then upgrade Cafe Social Marketing in Apps; required for the new
computed fields and views. No token or Docker environment changes are needed.
Verify a one-day campaign, a multi-day campaign including its final day, a range
crossing a month boundary, branch filtering, and the existing post calendar.
Date rendering requires local UI verification, beyond offline duration tests.
