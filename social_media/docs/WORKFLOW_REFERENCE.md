# Workflow Reference

Updated: 2026-11-01
Addon version: 20.0.6.0.0
Code reference: commit 3c36122

This describes implemented workflows. Live verification status is recorded
separately in CURRENT_FUNCTIONALITY.md.

## 1. Configure accounts and campaigns

1. Create a cafe branch.
2. Use the social account picker to select a platform.
3. Complete the account form and assign its branch.
4. Configure platform identifiers and token environment-variable names.
5. Create a campaign with branch, dates, discount and allowed accounts.

The picker opens account forms; it does not authorize platform access.
Actual Facebook, Instagram and Cloudinary credentials are supplied to Docker
outside Git.

## 2. Prepare and review content

1. Create a Draft post and select its branch, campaign and social account.
2. Enter a caption or apply a reusable template.
3. Attach supported media.
4. Optionally run AI Review and inspect its suggestions.
5. Validate the post against deterministic business rules.
6. Submit for Review.
7. A Marketing Manager approves, rejects or requests changes.

AI output does not approve or publish content.
Approval has one manager level.

Compliance checks include campaign presence, branch/account consistency,
current campaign dates and applicable discount wording.
Campaign status itself is not enforced by the existing compliance checks.

## 3. Request Changes

1. The manager opens Request Changes on an eligible post.
2. The manager enters a required, nonblank reason.
3. Confirmation sets Changes Requested and returns the post to Draft.
4. Latest reviewer feedback is stored and a chatter comment is added.
5. The author revises, validates and resubmits the post.
6. A manager reviews it again.

The planned date may remain on the record.
A Draft post with a retained date can appear on the calendar but is not
an active scheduled job.

## 4. Facebook publication

Supported content: text or one attached JPEG/PNG.

1. Select exactly one Facebook account.
2. Obtain approval for the content.
3. Choose Publish Now or a future scheduled time.
4. The adapter rechecks approval, compliance, media and credentials.
5. Publishing locks the post and repeats eligibility checks.
6. Odoo sends text or image bytes to Facebook.
7. Confirmed remote identifiers are stored and the post becomes Published.

Handled failures are recorded as Failed or Outcome Unknown.
Unknown outcomes block blind resending and require investigation.
There is no dedicated attempt-history model or reconciliation interface.

## 5. Instagram publication through Cloudinary

Supported content: one attached JPEG with a caption.

1. Select exactly one Instagram account.
2. Attach one eligible JPEG and clear any legacy image URL.
3. Validate, submit and obtain manager approval.
4. Publish Now, or schedule through the implemented scheduling action.
5. Odoo rechecks the approved content and publishing eligibility.
6. At publication time, Odoo uploads the JPEG to Cloudinary when needed.
7. Cloudinary returns a public image URL.
8. Odoo creates an Instagram media container using that URL.
9. Odoo checks container readiness before requesting publication.
10. Confirmed media identifiers and publishing results are stored.

The attached image is hosted automatically; manual URL pasting and a local
image-server tunnel are unnecessary for this workflow.
Hosted Cloudinary assets are not automatically deleted after publication.

The legacy alternative accepts a public HTTPS JPEG URL instead of an
attachment. Do not supply both.

Instagram scheduling exists in source but still needs live verification.
Immediate publication was reported working, with a remaining form/state
refresh issue requiring investigation. Check stored identifiers and the
actual Instagram post before attempting any resend.

## 6. Scheduling and calendars

Odoo's scheduler processes due posts in Scheduled state.
Odoo must remain running; configured cron intervals do not guarantee
publication at an exact second.

| View | Meaning |
| --- | --- |
| Content Calendar | Posts with a planned scheduled_at date, including states other than Scheduled |
| Campaign Calendar | Campaign date ranges, branch filters and inclusive duration |

Calendar editing is disabled; change dates through record forms.
Calendar display does not activate or complete campaigns automatically.
Immediate publications without a planned date may not appear on the
Content Calendar.

## 7. TikTok boundary

The installed source retains an earlier manual-token video inbox-upload
prototype. End-to-end live operation is not confirmed.

The prepared v10 OAuth update is not installed.
TikTok integration is postponed. A picker card or upload button does not
prove a working connection or successful public publication.

## 8. Verification boundaries

Reported live results:
- Facebook immediate publishing and scheduling.
- Instagram immediate photo publishing with automatic hosting.
- Visual social account picker.

Still requiring verification:
- Instagram scheduling.
- Instagram stored state and form refresh after publication.
- Access-control negative cases and date/time boundaries.
- End-to-end TikTok connection and upload.

Remote platform requests and local database changes are not one atomic
transaction. A crash or rollback after remote acceptance can leave an
uncertain local result.

## 9. Future development

The Facebook attempt-history specification remains Draft.
Before implementing a future change, review its requirements and acceptance
criteria, create a plan and tasks, then record actual verification results.

Historical workflow details are retained in:
baseline-2026-10-28/WORKFLOW_REFERENCE.md
