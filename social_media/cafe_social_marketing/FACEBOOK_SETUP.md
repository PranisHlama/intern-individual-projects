# Facebook text and single-photo publishing MVP — Odoo 20 Community

This update preserves video attachments and the existing separate TikTok draft
upload. Instagram and Facebook video/multi-photo publishing are not implemented yet.
Publish Now and Schedule now require exactly one Facebook account, text or one JPEG/PNG image,
current approval, and successful deterministic compliance checks. Previously
they only changed the local record state.

## 1. Configure the token in Docker

Keep your verified Page token private. Do not paste it into chats, commit it,
or enter it into the Odoo account's environment-variable-name field.

In your existing Docker Compose project folder, create a private file named
`facebook.env` using a text editor:

```dotenv
CAFE_FB_PAGE_TOKEN=PASTE_YOUR_VERIFIED_PAGE_TOKEN_HERE
```

Replace the placeholder locally. Run `chmod 600 facebook.env` and exclude this
file from git. Under your existing Odoo service (not PostgreSQL), add:

```yaml
env_file:
  - ./facebook.env
```

If `env_file` already exists, append the file to that list. Preserve your current
ports, volumes, environment and service names. A Docker Compose `.env` file
alone does not automatically put its variables into the container.
From this Compose folder run `docker compose up -d` to recreate the changed
Odoo service. Do not remove database volumes. For multiple Pages, use separate
variables such as `CAFE_FB_BRANCH_TWO_TOKEN` and set their names per account.

This keeps the token out of the addon and Odoo database, but Docker administrators
can still inspect container environment variables. This is a local development
credential arrangement, not production secret management or OAuth renewal.
Tokens can expire or be revoked; replace them and recreate the Odoo service.

## 2. Install the updated addon

Back up your existing addon and database first. Replace only the
`cafe_social_marketing` folder in the host custom addons directory mounted at
`/mnt/extra-addons`. Do not delete other addons or Odoo 19 files.

Find that host directory with:

```bash
docker inspect odoo20 --format '{{range .Mounts}}{{println .Source "->" .Destination}}{{end}}'
```

Restart Odoo after replacing the addon, then upgrade Cafe Social Marketing
from Apps in developer mode. An Apps upgrade is required; a restart alone
does not create the new fields. If you use CLI upgrading instead, first confirm
the current project's database name. Do not assume the mail-client database
is your social-marketing database.

The source retains the uploaded module's Odoo 20 `ir.access.csv` migration.
There is no live Odoo runtime available in this build environment, so installation
and end-to-end API behavior must be checked on your actual Odoo instance.

## 3. Set up the Social Account

As Marketing Manager, open Social Accounts and create or edit a Facebook account:

* Platform: Facebook
* Branch: your test branch
* Facebook Page ID: `1451594584702943`
* Token Environment Variable: `CAFE_FB_PAGE_TOKEN`

The Page ID is not a personal Facebook user ID. Keep the account selected by its
campaign and ensure its branch matches the post/campaign.

## 4. Test one actual text post

Create a new post with a valid campaign and exactly that Facebook account.
Use content that passes your campaign rules; for example, if the campaign offers
20%, include 20%, not a different discount. For a text post, leave Media and Video Attachment empty. For a photo post,
attach exactly one JPEG or PNG under Media and leave Video Attachment empty.
The adapter limits images to 10 MiB and checks their signatures; Facebook still
validates whether it can decode the file. Validate, submit for review, approve as Marketing Manager, and Publish Now.

Success: Odoo displays a Facebook post ID and Published state; verify the same
message on the test Page. Do not assume app-development posts have production
visibility to all viewers. Graph API version is v26.0, matching your Explorer.

Failure: the post returns to Draft, records a code/status, and stays unpublished.
After fixing permissions or an expired token, a definite rejection can be retried.
Outcome Unknown: a timeout or unexpected response might follow a successful
remote publish. Check the Page; the same record is blocked from automatic/manual
retry to reduce duplicates. This MVP does not provide reconciliation UI; resolve
the remote result before creating a replacement. Do not blindly resend.

## 5. Verify scheduling and approval

Schedule a newly approved text or single-photo post a few minutes ahead. The scheduled action
should send it through the same Facebook adapter when due. Editing a scheduled
post's content returns it to Draft and resets approval. Removing approval must
prevent automatic publishing. Unsupported platforms/media are blocked. The approved photo hash is checked
again before publishing to detect edits to the attached file after approval.
Previously approved photo posts need to be reset and reapproved after upgrade.

The scheduler checks at most 100 due records per run. Cron timing depends on
your existing scheduled-action configuration and Odoo availability. Network
requests run synchronously; this MVP has no job queue or automatic retries.
Odoo transactions and external API calls are not atomic: a crash or database
rollback after remote success can lose the local result. Check the Page after
interrupted publishing. This is not exactly-once delivery.

## Changes and validation

Added Facebook service, account configuration, result fields, server-side workflow
guards, and real text/single-photo publishing. Stored failures do not get rolled back by raising
an Odoo exception. Approval is checked again when due; edits cancel scheduling.
Other platforms can no longer be marked Published by the generic action.

Offline checks cover outbound request structure, safe errors, malformed responses,
workflow preflight, and scheduler approval rejection. Live Odoo installation, access
rules, Meta permissions, actual publishing, and cron execution still need your
local verification. Older records already marked Published are not migrated;
they might have been local simulations and should not be presented as proof of
actual platform publishing.

Attachment hotfix: prefer raw binary content when available; use base64 datas only
on builds that expose it. Reads explicitly disable bin_size. Regression checks
cover an Odoo 20-style attachment with no datas field. No database fields changed
from v5; replacing code and restarting applies this specific fix.

Second attachment hotfix: Odoo 20 returns a BinaryValue wrapper; read its
.content bytes. Verified against the user-provided ir.attachment source.
No database schema or credential changes are needed.
