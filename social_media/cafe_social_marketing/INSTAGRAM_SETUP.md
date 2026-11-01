# Instagram attached photos + social account picker — v9

Version: 20.0.6.0.0. Baseline: the v8 Instagram URL-based post was published and
confirmed by the owner on alexg_oing. This update adds automatic photo hosting and
a platform chooser; its live Cloudinary/Odoo acceptance checks are still pending.

## What you get

- Add Social Account popup with Facebook, Instagram and TikTok cards.
- Each card opens the normal account setup form with Platform selected.
- New Instagram photo posts use one attached JPEG. Odoo handles hosting and the URL.
- Existing v8 URL-based posts remain supported; old approval fingerprints are retained.
- Facebook continues using its existing direct text/single-photo upload service.

This picker does not implement OAuth sign-in or auto-discover accounts. Existing
Facebook/Instagram IDs and token variables still need configuration. TikTok's card
opens its existing test setup; it does not complete TikTok OAuth or publication.

## 1. Create a Cloudinary account (once)

Open https://cloudinary.com/users/register_free and choose the free plan if suitable.
Cloudinary's pricing page currently lists a free plan with no credit card required;
usage limits still apply: https://cloudinary.com/pricing .

In the product environment dashboard/settings, locate the cloud name, API key and
API secret (the API Keys section). Keep those credentials private. Use a normal
image-upload environment with no default cropping, transformations or access-control
rules that would change the photo or prevent Meta downloading it. No unsigned
upload preset is needed: the addon signs its uploads on the Odoo server.

## 2. Add hosting credentials to your existing Docker env file

In Mac Terminal:

```bash
open -e ~/Desktop/odoo20/facebook.env
```

Keep the working CAFE_FB_PAGE_TOKEN and CAFE_IG_ACCESS_TOKEN lines unchanged. Append:

```dotenv
CAFE_CLOUDINARY_CLOUD_NAME=YOUR_CLOUD_NAME
CAFE_CLOUDINARY_API_KEY=YOUR_API_KEY
CAFE_CLOUDINARY_API_SECRET=YOUR_API_SECRET
```

Replace the placeholders locally and save. Do not paste the file or secrets into
chat, Git, Odoo account fields or screenshots. The existing Odoo Compose service
must still reference `./facebook.env` through env_file, as it does for your tokens.

## 3. Extract the update

Download cafe_social_marketing_odoo20_instagram_v9.zip into Downloads, then:

```bash
mkdir -p ~/Downloads/cafe-instagram-v9
unzip -o ~/Downloads/cafe_social_marketing_odoo20_instagram_v9.zip -d ~/Downloads/cafe-instagram-v9
```

## 4. Stop Odoo, back up and upgrade

The correct installed database was confirmed in the previous session as
**Mailintegration**, including its exact uppercase M. PostgreSQL must remain running.
Do not merely restart Odoo after copying new model files: the new stored columns
need an upgrade, otherwise the web client can report UndefinedColumn again.

Run one command at a time:

```bash
cd ~/Desktop/odoo20
docker stop odoo20
mkdir -p ~/Desktop/odoo-addon-backups
cp -R ~/Desktop/odoo20/addons/cafe_social_marketing ~/Desktop/odoo-addon-backups/cafe_social_marketing-before-v9-$(date +%Y%m%d-%H%M%S)
docker exec odoo20-db pg_dump -U odoo -d Mailintegration -Fc > ~/Desktop/odoo-addon-backups/Mailintegration-before-v9-$(date +%Y%m%d-%H%M%S).dump
rsync -av --exclude='__pycache__' --exclude='*.pyc' ~/Downloads/cafe-instagram-v9/cafe_social_marketing/ ~/Desktop/odoo20/addons/cafe_social_marketing/
docker compose run --rm --no-deps odoo odoo -d Mailintegration -u cafe_social_marketing --stop-after-init --no-http
```

Immediately after the upgrade command, check its exit status:

```bash
echo $?
```

It must be **0** with no upgrade traceback. If not, leave the normal Odoo service
stopped and share the error. The backup above is addon source and a database dump;
it is not a full Docker/filestore backup. This update does not modify the filestore
layout or delete your attachments.

After a successful upgrade, recreate Odoo to load the new env-file values:

```bash
chmod 600 facebook.env
docker compose up -d --no-deps --force-recreate odoo
docker exec odoo20 python3 -c 'import os; names=("CAFE_CLOUDINARY_CLOUD_NAME","CAFE_CLOUDINARY_API_KEY","CAFE_CLOUDINARY_API_SECRET","CAFE_IG_ACCESS_TOKEN"); print({n: bool(os.getenv(n)) for n in names})'
```

All values should be True. This check prints booleans, never credentials. It only
checks presence, not credential validity. Refresh http://localhost:8000 after Odoo
starts.

## 5. Test the platform popup

Open Cafe Social Marketing > Configuration > **Add Social Account**, or click
**Add Social Account** in the Social Accounts list header. Three platform cards
should appear. Click Instagram; the ordinary new account form opens with Instagram
selected. Cancel if you already have Instagram Demo; do not create duplicates.
You can still open/edit your existing accounts through Social Accounts.

## 6. Test Instagram without a tunnel or image server

Use a NEW post; an old URL-based published post stays locked. Keep the existing
Instagram Demo account: ID 17841446238462669, handle alexg_oing, environment-variable
name CAFE_IG_ACCESS_TOKEN. Make sure the campaign allows this account and branch.

1. Stop the image server and cloudflared test tunnel with Ctrl+C in their windows.
   They are not used for this new attachment test.
2. Create a new social post. Select exactly one Instagram account.
3. Choose a matching branch and campaign valid today; enter a caption matching any
   campaign discount requirement.
4. Use the normal **Attachments** field to upload exactly one JPEG photo. For your
   existing test image, select `~/instagram-demo/test.jpeg` in the Mac file picker.
5. Leave Video Attachment empty. No public URL entry is needed or shown for a new post.
6. Save, Validate Post, Submit for Review and approve as Marketing Manager.
7. Click **Publish / Check Instagram**. Odoo uploads the approved JPEG to Cloudinary,
   records its delivery URL, creates the Meta container and publishes when ready.
8. If Processing / Recheck appears, wait briefly and click the same button again.
9. Confirm local Published, Instagram Media ID and the actual photo on alexg_oing.

For scheduling, create another new approved photo post with a future Scheduled At
inside the campaign range, then click Schedule Instagram. Hosting happens at the
due publishing attempt. Keep Mac/Docker/Odoo running, with Internet and valid tokens.
The image server and tunnel can remain stopped. Processing may take another cron run.

## Photo rules and approval

- This adapter accepts JPEG only, at most 8 MiB, up to 40 megapixels and width/height
  ratio from 0.8 (4:5) to 1.91. These are conservative adapter limits. It does not
  crop, resize or convert a photo after approval; PNG needs conversion beforehand.
- The approval fingerprint includes exact attached JPEG bytes, caption, selected
  account, Instagram user ID and token-variable name. In-place file changes fail
  publishing preflight even if the attachment relation did not change.
- Existing content-edit resets still apply. Once an Instagram container exists,
  content and Request Changes are locked, as in v8.
- Uploaded bytes are signed-uploaded only after approval/compliance at publication.
  Cloudinary stores them as public media: anyone with the delivery URL can retrieve
  the photo. They remain there until you remove them in Cloudinary. Do not delete
  files needed by a pending container. No automatic cleanup/retention policy yet.
- A cached hosted URL is reused only when its saved photo hash matches current bytes.
  Changing a photo and approving it again uses a different hosted asset name.
- Legacy v8 URL-based posts continue using the old flow; keep their URLs reachable
  and the images unchanged. Legacy details are in INSTAGRAM_LEGACY_URL_SETUP.md.

## Errors, retries and limits

Hosting failures stop before Meta is called and display an error in Odoo. Publish
can retry with the same generated upload identifier; overwrite=false avoids replacing
an existing asset. A saved hosted URL avoids another upload for processing checks.

Meta create/publish uncertainties still block automatic resending; check Instagram
before creating replacements. The previous v8 container result rules remain.

API errors intentionally do not echo raw remote messages, credentials or request
exceptions into records. Check numeric codes, token expiry/permissions, Cloudinary
configuration and usage limits. This MVP still has manual Meta token renewal.

Remote services and the Odoo transaction are not atomic. A crash or DB rollback
can lose tracking after an external operation; orphan hosted photos are possible.
This update does not provide crash-proof exactly-once delivery, a reconciliation
screen, background hosting cleanup or general retry history.

## Checks and remaining acceptance

93 offline checks pass, including existing Facebook, review/calendar, Instagram
URL flow, signed hosting contracts, redaction, source byte tampering, caching,
hosting failure isolation, and picker actions/assets. Python syntax and XML/XPath
checks are also run. The tests mock Odoo and HTTP and do not prove live installation,
Cloudinary credentials or real publication. The owner must perform the live tests
above and a Facebook publishing regression after upgrading.

From the extracted ZIP folder:

```bash
python3 -m venv .venv
.venv/bin/pip install requests lxml markupsafe Pillow
.venv/bin/python -m unittest discover -s checks -q
```

## Source and spec-driven development

The ZIP includes the complete addon, offline checks, and specs/003-instagram-hosting-account-picker.
Copy that spec beside your existing specs within social_media when preparing the
feature PR. Keep your existing constitution and earlier specs. No Git branches,
commits, pushes or changes to your Mac were made while preparing this ZIP.

Official references:
- https://cloudinary.com/documentation/image_upload_api_reference
- https://cloudinary.com/documentation/authentication_signatures
- https://cloudinary.com/pricing
