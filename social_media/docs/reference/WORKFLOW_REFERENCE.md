# Workflow reference

Updated: 2026-11-05. Source: `76f9e2b`. Manifest version: `20.0.6.1.0`.

This describes the implemented paths. It is not a test report; see [Verification](VERIFICATION.md).

## 1. Configure the business context

1. Create a cafe branch.
2. Open Configuration → Add Social Account, choose a platform, and complete its ordinary account form.
3. Enter the Facebook Page or Instagram professional account ID and the **name** of its token environment variable. The visual picker does not perform OAuth.
4. Create a campaign with matching branch, valid dates, any required discount/product and allowed accounts.
5. As Marketing Manager, optionally Sync Profile on the saved Facebook/Instagram account; refresh Social Feed to see the cached name/photo.

Real Meta and Cloudinary credentials must reach the Odoo process through local deployment configuration, outside Git. See [Installation](../setup/INSTALLATION.md).

## 2. Prepare captions and images

Create a Draft post, select the branch/campaign and exactly one supported platform account, then enter a caption or apply a template. Template placeholders are substituted from the selected branch/campaign; rendered text remains editable.

Attach eligible media or save the draft and Open Designer. In Designer, choose a layout or add layers, format/arrange the image, then Save JPEG to post. Explicitly confirm replacement if the post already selects other media. Saving stores the editable document and a 1080-square JPEG; old detached attachments are not deleted by Designer.

The local preview follows the selected platform. It is a layout approximation, not a remote rendering or a live platform feed.

## 3. Validate and review

1. Optionally run AI Review, inspect its advice and apply a suggested rewrite if useful.
2. Validate the post against deterministic rules.
3. Submit for Review; the implementation rechecks compliance.
4. A Marketing Manager approves or rejects a pending post, or requests changes on an eligible pending/approved post.

Campaign presence, matching branches/accounts, current campaign dates and discount wording are checked. Campaign status itself is not enforced. Scheduling far ahead does not bypass today's campaign validity check.

AI review is advisory and separate from approval. Applying a rewrite or otherwise changing approval-relevant content resets validation/approval. Saving a changed design follows that same reset path. Published content is locked against these edits.

## 4. Request Changes

The manager opens Request Changes, supplies a nonblank reason, and confirms. The action clears the approval identity/time, sets Changes Requested and returns the eligible record to Draft. Latest feedback is stored and a chatter comment is added.

A retained planned date can keep the Draft visible on Content Calendar; it is not an active scheduled job. The author revises, validates and resubmits before a manager reviews again. Existing confirmed/uncertain Facebook results and Instagram containers/media restrict this path to prevent changes during an external attempt.

## 5. Facebook publishing

Supported: text or one attached JPEG/PNG; exactly one Facebook account.

Publish Now checks current approval, compliance, account credentials and media. Photo bytes are checked against the approved hash. The adapter locks the post and repeats preflight before sending the request. A confirmed response supplies the required remote ID, then Odoo stores the result and marks Published.

A handled rejection records Failed; uncertain responses/timeouts record Outcome Unknown. The adapter returns a notification rather than rolling back those handled failure fields through a raised exception. Unknown outcomes block blind repeat sends. Check the real Page before retrying or creating a replacement.

View on Facebook is available for confirmed Published results with a numeric identifier. It opens the remote post in a new tab without sending a new publish request.

## 6. Instagram publishing

Supported: one attached JPEG and caption, or the legacy public HTTPS JPEG alternative. Do not supply both. Use one Instagram account and a separate Odoo record from Facebook.

1. Validate, submit and approve the caption and eligible image/configuration.
2. Publish / Check Instagram, or schedule through the implemented action.
3. At publication time, preflight and fingerprint checks repeat under the shared post lock.
4. For attached media, the adapter signs a Cloudinary upload or reuses the matching cached hosted URL.
5. Instagram receives that URL and creates a media container.
6. Odoo checks container readiness. Processing / Recheck means the container is not yet confirmed ready; the existing container is checked on the next action/cron pass.
7. Publication confirmation stores the Instagram media ID and Published result. Success returns a reload notification; repeat calls on an already confirmed record should return its result without resending.

Once a container exists, content changes are restricted. Unknown outcomes need investigation. A hosted public image must remain accessible while needed by Instagram; there is no automatic Cloudinary cleanup.

Manual image-server/tunnel setup is unnecessary for attached JPEGs. The legacy URL path requires its external hosting to remain reachable. Instagram scheduling and repeat-send concurrency still need focused live tests.

## 7. Scheduling and controlled date moves

Schedule an approved/validated eligible post for a future time inside its campaign dates. The configured cron runs at a one-minute interval and considers up to 100 due Scheduled records. It locks/rechecks each due record before invoking the platform adapter; it is not an exact-second queue.

In Content Calendar, a Marketing Manager may move one Scheduled post with no publishing attempt. The action accepts only a date change, rechecks preflight, future time and campaign boundaries, and preserves content approval. Day dragging preserves the previous local time; a chatter note records old/new times and the actor. The server also guards form/RPC date changes on Scheduled records.

User moves, unapproved/unvalidated records, published/cancelled records and records with started or uncertain attempts are rejected. Ambiguous/nonexistent daylight-saving local times require an explicit valid time in the form. The scheduler rechecks due time after locking so a recently moved post is not sent from its old search result.

| View | Meaning |
| --- | --- |
| Content Calendar | Planned `scheduled_at` values, including visible non-Scheduled records; guarded rescheduling applies to eligible Scheduled posts |
| Campaign Calendar | Campaign date ranges, filters and inclusive duration; not automatic campaign lifecycle control |

## 8. Profile sync and feed reads

Sync Profile requires manager membership and account write access. It fetches metadata/photo before locking, then rechecks access and remote identity before saving. Failed fetches leave the previous cache. Cache fields cannot be supplied through ordinary account create/write calls.

Feed reads use cached account fields and local image endpoints under existing access rules. They do not call Meta or publish content. Changing the destination ID/platform clears old profile metadata. Multi-account/unsupported cards retain fallback labels; the main published feed is intended for the single-platform Facebook/Instagram paths.

## 9. Incomplete paths and transaction limits

TikTok retains an earlier manual-token upload/status prototype; it is not a verified end-to-end connection or Direct Post workflow. Meta OAuth was postponed and is absent from this source. There is no dedicated attempt-history ledger yet.

Remote acceptance cannot be rolled back with an Odoo database transaction. A crash after acceptance can leave stale local state or orphan hosted media. Locks reduce concurrent sends but do not provide exactly-once delivery across crashes. Verify the platform result before another send.

Historical details remain in the unchanged [October 28 workflow reference](../baseline-2026-10-28/WORKFLOW_REFERENCE.md).
