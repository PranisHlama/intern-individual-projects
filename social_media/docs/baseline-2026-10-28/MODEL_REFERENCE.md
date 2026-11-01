# Model Reference

Baseline: uploaded addon version `20.0.4.1.0`, reviewed 2026-10-28.
Source paths are relative to `cafe_social_marketing/` unless stated otherwise.
Field tables record explicit Python declarations, not an introspected database
schema. Framework defaults and fields inherited from base/mail models are omitted.
A field marked readonly is not, by itself, a server-side permission check.

## Model map

| Model | Kind | Purpose | Main sources |
| --- | --- | --- | --- |
| cafe.social.branch | Persistent | Cafe location | models/branch.py |
| cafe.social.account | Persistent, extended | Branch/platform account and connection settings | models/social_account.py; models/facebook.py |
| cafe.social.campaign | Persistent | Branch campaign dates, offer and allowed accounts | models/campaign.py |
| cafe.social.post.template | Persistent | Reusable caption text, optional branch | models/post_template.py |
| cafe.social.post | Persistent, extended | Content, review, schedule and latest publishing result | models/social_post.py; social_post_ai.py; facebook.py; review_workflow.py |
| cafe.social.request.changes | Transient wizard | Temporary reason collection, not permanent history | models/review_workflow.py |

The extensions using `_inherit = 'cafe.social.post'` add behaviour to the same model;
they are not separate post tables. `mail.thread`/`mail.activity.mixin` are inherited
by campaigns and posts. The addon depends on base, mail, product and Python requests.
It does not depend on the standard Social Marketing addon in this manifest.

## Relationships

| From | Field | Target | Cardinality / explicit deletion policy |
| --- | --- | --- | --- |
| Account | branch_id | Branch | Many accounts to one required branch; ondelete=cascade |
| Campaign | branch_id | Branch | Many campaigns to one required branch |
| Campaign | product_id | product.product | Optional Many2one |
| Campaign | social_account_ids | Account | Many2many allowed accounts; empty means unrestricted in compliance |
| Template | branch_id | Branch | Optional Many2one; blank supports shared template |
| Post | branch_id | Branch | Required Many2one |
| Post | campaign_id | Campaign | Optional Many2one in schema; required by compliance |
| Post | template_id | Template | Optional Many2one |
| Post | social_account_ids | Account | Many2many in schema; Facebook action permits exactly one Facebook account |
| Post | attachment_ids | ir.attachment | Many2many media relation |
| Post | approved_by_id, changes_requested_by_id | res.users | Reviewer identity references |
| Wizard | post_id | Post | Required Many2one; ondelete=cascade |

Post video_file is attachment-backed binary storage, not an explicitly declared
custom video model. Inverse One2many fields for branch posts/campaigns are not
explicitly declared. Do not invent custom relation-table names from this reference.

## Fields declared by this addon

Each table includes extensions to its model. The approval_state extension adds
changes_requested; it does not replace the original values. Options below are
source declarations and are not a guarantee of complete write protection.

### cafe.social.branch

| Field | Type | Explicit options / values | Source |
| --- | --- | --- | --- |
| name | Char | required=True | models/branch.py:9 |
| code | Char | No explicit options beyond label/help. | models/branch.py:14 |
| address | Text | No explicit options beyond label/help. | models/branch.py:18 |
| active | Boolean | default=True | models/branch.py:22 |

### cafe.social.account

| Field | Type | Explicit options / values | Source |
| --- | --- | --- | --- |
| facebook_page_id | Char | copy=False | models/facebook.py:16 |
| facebook_token_env | Char | default=CAFE_FB_PAGE_TOKEN; groups=cafe_social_marketing.group_cafe_social_manager | models/facebook.py:17 |
| name | Char | required=True | models/social_account.py:9 |
| platform | Selection | required=True; Values: [('facebook', 'Facebook'), ('instagram', 'Instagram'), ('tiktok', 'TikTok'), ('x', 'X / Twitter'), ('other', 'Other')] | models/social_account.py:14 |
| handle | Char | No explicit options beyond label/help. | models/social_account.py:26 |
| branch_id | Many2one | Target: cafe.social.branch; required=True; ondelete=cascade | models/social_account.py:30 |
| tiktok_access_token | Char | groups=cafe_social_marketing.group_cafe_social_manager | models/social_account.py:39 |
| tiktok_open_id | Char | groups=cafe_social_marketing.group_cafe_social_manager | models/social_account.py:48 |
| active | Boolean | default=True | models/social_account.py:53 |

### cafe.social.campaign

| Field | Type | Explicit options / values | Source |
| --- | --- | --- | --- |
| name | Char | required=True; tracking=True | models/campaign.py:11 |
| branch_id | Many2one | Target: cafe.social.branch; required=True; tracking=True | models/campaign.py:17 |
| product_id | Many2one | Target: product.product | models/campaign.py:24 |
| discount | Float | No explicit options beyond label/help. | models/campaign.py:29 |
| date_start | Date | required=True | models/campaign.py:33 |
| date_end | Date | required=True | models/campaign.py:38 |
| duration_days | Integer | compute=_compute_calendar_details | models/campaign.py:43 |
| calendar_all_day | Boolean | compute=_compute_calendar_details | models/campaign.py:47 |
| social_account_ids | Many2many | Target: cafe.social.account | models/campaign.py:58 |
| state | Selection | required=True; default=draft; tracking=True; Values: [('draft', 'Draft'), ('active', 'Active'), ('completed', 'Completed'), ('cancelled', 'Cancelled')] | models/campaign.py:63 |

### cafe.social.post.template

| Field | Type | Explicit options / values | Source |
| --- | --- | --- | --- |
| name | Char | required=True | models/post_template.py:8 |
| message | Text | required=True | models/post_template.py:13 |
| branch_id | Many2one | Target: cafe.social.branch | models/post_template.py:18 |
| active | Boolean | default=True | models/post_template.py:23 |

### cafe.social.post

| Field | Type | Explicit options / values | Source |
| --- | --- | --- | --- |
| facebook_post_id | Char | readonly=True; copy=False | models/facebook.py:43 |
| facebook_photo_id | Char | readonly=True; copy=False | models/facebook.py:44 |
| facebook_approved_photo_hash | Char | readonly=True; copy=False | models/facebook.py:45 |
| facebook_publish_status | Selection | default=not_sent; readonly=True; copy=False; Values: [('not_sent', 'Not Sent'), ('published', 'Published'), ('failed', 'Failed'), ('unknown', 'Outcome Unknown')] | models/facebook.py:46 |
| facebook_publish_error | Text | readonly=True; copy=False | models/facebook.py:51 |
| approval_state | Selection | ondelete={'changes_requested': 'set default'}; Adds: [('changes_requested', 'Changes Requested')] | models/review_workflow.py:10 |
| reviewer_comment | Text | readonly=True; copy=False | models/review_workflow.py:14 |
| changes_requested_by_id | Many2one | Target: res.users; readonly=True; copy=False | models/review_workflow.py:15 |
| changes_requested_at | Datetime | readonly=True; copy=False | models/review_workflow.py:18 |
| name | Char | required=True; tracking=True | models/social_post.py:18 |
| message | Text | tracking=True | models/social_post.py:24 |
| branch_id | Many2one | Target: cafe.social.branch; required=True; tracking=True | models/social_post.py:29 |
| campaign_id | Many2one | Target: cafe.social.campaign; tracking=True | models/social_post.py:36 |
| template_id | Many2one | Target: cafe.social.post.template | models/social_post.py:42 |
| social_account_ids | Many2many | Target: cafe.social.account | models/social_post.py:47 |
| attachment_ids | Many2many | Target: ir.attachment | models/social_post.py:52 |
| video_file | Binary | attachment=True | models/social_post.py:57 |
| video_filename | Char | No explicit options beyond label/help. | models/social_post.py:63 |
| has_tiktok_account | Boolean | compute=_compute_has_tiktok_account | models/social_post.py:67 |
| tiktok_publish_id | Char | readonly=True; copy=False | models/social_post.py:72 |
| tiktok_remote_status | Char | readonly=True; copy=False | models/social_post.py:78 |
| tiktok_status_message | Text | readonly=True; copy=False | models/social_post.py:84 |
| tiktok_uploaded_at | Datetime | readonly=True; copy=False | models/social_post.py:90 |
| scheduled_at | Datetime | tracking=True | models/social_post.py:96 |
| published_at | Datetime | readonly=True | models/social_post.py:101 |
| preview_html | Html | compute=_compute_preview_html | models/social_post.py:106 |
| validation_status | Selection | default=not_validated; readonly=True; tracking=True; Values: [('not_validated', 'Not Validated'), ('passed', 'Passed'), ('failed', 'Failed')] | models/social_post.py:112 |
| validation_result | Text | readonly=True | models/social_post.py:124 |
| validated_at | Datetime | readonly=True | models/social_post.py:129 |
| approval_state | Selection | default=not_submitted; readonly=True; tracking=True; Values: [('not_submitted', 'Not Submitted'), ('pending', 'Pending Approval'), ('approved', 'Approved'), ('rejected', 'Rejected')] | models/social_post.py:134 |
| submitted_at | Datetime | readonly=True | models/social_post.py:147 |
| approved_by_id | Many2one | Target: res.users; readonly=True | models/social_post.py:152 |
| approved_at | Datetime | readonly=True | models/social_post.py:158 |
| state | Selection | default=draft; tracking=True; Values: [('draft', 'Draft'), ('scheduled', 'Scheduled'), ('published', 'Published'), ('cancelled', 'Cancelled')] | models/social_post.py:163 |
| ai_review_status | Selection | default=not_reviewed; readonly=True; tracking=True; Values: [('not_reviewed', 'Not Reviewed'), ('reviewed', 'Reviewed'), ('error', 'Review Error')] | models/social_post_ai.py:10 |
| ai_overall_status | Char | readonly=True | models/social_post_ai.py:22 |
| ai_tone | Text | readonly=True | models/social_post_ai.py:27 |
| ai_clarity | Text | readonly=True | models/social_post_ai.py:32 |
| ai_issues | Text | readonly=True | models/social_post_ai.py:37 |
| ai_suggested_rewrite | Text | readonly=True | models/social_post_ai.py:42 |
| ai_reviewed_at | Datetime | readonly=True | models/social_post_ai.py:47 |

### cafe.social.request.changes

| Field | Type | Explicit options / values | Source |
| --- | --- | --- | --- |
| post_id | Many2one | Target: cafe.social.post; required=True; readonly=True; ondelete=cascade | models/review_workflow.py:88 |
| reason | Text | required=True | models/review_workflow.py:89 |

## Computed values and literal placeholders

- `duration_days`: max(0, end-start+1) when both dates exist, otherwise 0.
  `calendar_all_day` is computed True. Both are non-stored declarations.
- `has_tiktok_account`: True when any selected account has platform=tiktok.
- `preview_html`: escaped branch, campaign, account names and caption. Caption
  newlines become HTML breaks. No media-byte rendering.
- Template literals: `{{branch}}`, `{{campaign}}`, `{{product}}`, `{{discount}}`,
  `{{start_date}}`, `{{end_date}}`. These are simple string replacements.
- Applying a template checks a mismatched template branch in the explicit action.
  The onchange path copies a template and does not perform that same mismatch
  error check. Template body changes do not automatically update existing posts.

## Constraints and action ownership

| Source | Methods | Responsibility |
| --- | --- | --- |
| campaign.py | _check_campaign_dates; _check_discount | Date ordering and 0–100 discount |
| campaign.py | action_activate/complete/cancel/reset_draft | Set campaign status; no automatic date-driven lifecycle |
| social_post.py | _get_compliance_checks; action_validate_post; _ensure_post_is_compliant | Build/save report; recheck rules before protected actions |
| social_post.py | action_submit_review; action_approve/reject/reset_approval; write | Approval actions and post-content invalidation |
| review_workflow.py | action_submit_review | Adds Draft and allowed previous-approval-state constraints before base submission |
| review_workflow.py | _check_request_changes; _request_changes; action_open_request_changes | Manager and state checks, feedback, return to Draft, chatter |
| review_workflow.py | RequestChangesWizard.action_confirm | Recheck post existence and invoke controlled change request |
| social_post_ai.py | action_ai_review; action_apply_ai_suggestion; write | Review text, apply rewrite, reset stored AI review on listed edits |
| facebook.py | _facebook_credentials; _facebook_photo_bytes; _facebook_preflight | Credentials, attachment bytes/signature/hash, publishing eligibility |
| facebook.py | action_approve | Hash Facebook image then call inherited approval |
| facebook.py | action_schedule | Facebook preflight then inherited scheduling checks |
| facebook.py | action_publish; _cron_publish_scheduled_posts | Effective platform publish and due-post processing |
| facebook.py | write; create | Protect remote result fields, confirmed-publication state and selected approval writes |
| social_post.py | action_upload_tiktok_draft; action_check_tiktok_status | Separate prototype upload/status path |

`models/__init__.py` imports base models, then social_post_ai, facebook and
review_workflow. Read extensions together: the base local-only publish/cron methods
are overridden by facebook.py. Registry behaviour still requires Odoo runtime
verification; this document is not a Python-only simulation of Odoo's model registry.

## Declared access permissions

`security/ir.access.csv` uses the supplied Odoo 20 format:
`id,name,model_id,group_id/id,operation,domain`.

| Model(s) | Marketing User | Marketing Manager |
| --- | --- | --- |
| Branch, account, campaign, post, template | Create, read, update (`cru`) | Create, read, update, delete (`crud`) |
| Request Changes wizard | No access row supplied | Create, read, update, delete (`crud`) |

Manager implies Marketing User through `implied_ids`. The groups use the declared
Cafe Social Marketing privilege/category. All CSV domains are empty: branch
membership restrictions are not declared here. UI branch domains are selection
helpers, not comprehensive record access controls.

Manager-restricted model fields: account.tiktok_access_token,
account.tiktok_open_id, account.facebook_token_env. The Facebook Page ID is not
manager-restricted in its field declaration. Facebook credential lookup uses sudo
for the manager-protected configuration and reads the actual token from an Odoo
container environment variable. This is not an OAuth credential store.

Approve, Reject, Request Changes and TikTok draft upload have explicit server-side
manager checks. Facebook publishing does not add a manager-only group check: it
requires existing current approval and other preflight conditions. TikTok status
button is manager-only in the view, but its method has no equivalent explicit
manager check and reads token through sudo. See CURRENT_FUNCTIONALITY for the
remaining generic-write and effective-access verification limitations.

## History and lifecycle

- Posts and campaigns use mail chatter tracking for selected fields.
- Latest feedback fields are retained after resubmission/approval; they are not the
  authoritative current approval state. Older request reasons can remain in chatter.
- No dedicated version, approval-event or publishing-attempt model exists.
- Branch, account and template have active flags; post and campaign do not declare
  an archive flag. No custom unlink override prevents deleting published posts
  in the supplied source. General manager delete access must not be described as
  immutable audit retention.
