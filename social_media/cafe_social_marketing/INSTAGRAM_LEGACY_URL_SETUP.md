# Instagram single-image integration — v8 / 20.0.5.0.0

This update adds Instagram publishing to the Odoo workflow, plus Facebook and
Instagram icons on the corresponding publish and schedule buttons. It uses the
Facebook Login route already tested manually with Graph API Explorer.

Supported: one Instagram professional account, caption, one public HTTPS JPEG URL,
manager approval, deterministic validation, immediate publish and Odoo scheduling.
Not included: Instagram binary uploads, Reels, carousels, Stories, OAuth/refresh or
TikTok completion. Facebook still supports text or one attached JPEG/PNG image.
Create separate Odoo posts for Facebook and Instagram.

## 1. Install over the existing addon

Download cafe_social_marketing_odoo20_instagram_v8.zip into Downloads. The ZIP
contains the full addon, feature specification, and offline checks. In Mac Terminal:

```bash
mkdir -p ~/Downloads/cafe-instagram-v8
unzip -o ~/Downloads/cafe_social_marketing_odoo20_instagram_v8.zip -d ~/Downloads/cafe-instagram-v8
mkdir -p ~/Desktop/odoo-addon-backups
cp -R ~/Desktop/odoo20/addons/cafe_social_marketing ~/Desktop/odoo-addon-backups/cafe_social_marketing-before-instagram-$(date +%Y%m%d-%H%M%S)
rsync -av --exclude='__pycache__' --exclude='*.pyc' ~/Downloads/cafe-instagram-v8/cafe_social_marketing/ ~/Desktop/odoo20/addons/cafe_social_marketing/
docker restart odoo20
```

This backup covers addon source, not your database or filestore. Use your normal
Odoo database backup before a module upgrade. In Odoo, enable developer mode if
needed, open Apps, locate the installed Cafe Social Marketing module (remove the
Apps filter if necessary), and choose Upgrade from its menu. Restart alone does
not create the new fields. Refresh the browser after the upgrade.

No database name or DB password is needed for these commands. If upgrade fails,
keep the traceback and stop before testing publishing.

## 2. Add the Instagram token separately

Use the Facebook **User access token** from the successful Instagram Graph API
Explorer test. It must authorize the app and selected professional Instagram
account, with instagram_basic, instagram_content_publish, pages_read_engagement
and pages_show_list granted. Do not substitute an Instagram Login token: this
adapter calls graph.facebook.com using the Facebook Login route.

Keep the existing CAFE_FB_PAGE_TOKEN line and its value unchanged. Open the
existing private env file:

```bash
open -e ~/Desktop/odoo20/facebook.env
```

Append this separate line, replacing the placeholder locally with the token:

```dotenv
CAFE_IG_ACCESS_TOKEN=PASTE_INSTAGRAM_TEST_USER_TOKEN_HERE
```

Do not put quotes, extra spaces or a literal placeholder in the real value. Save,
then recreate the Odoo service so Compose reloads the existing env_file:

```bash
cd ~/Desktop/odoo20
chmod 600 facebook.env
docker compose up -d --force-recreate odoo
docker exec odoo20 python3 -c 'import os; print("Instagram token loaded:", bool(os.getenv("CAFE_IG_ACCESS_TOKEN")))'
```

Expected: `Instagram token loaded: True`. This prints no token. Do not paste tokens
into chats, Git, screenshots or Odoo account fields. This assumes your existing
Compose Odoo service already loads `./facebook.env`, as used by Facebook.

The token must still be valid when a scheduled post runs. This MVP does not
extend or refresh tokens. Check expiry in Meta's Access Token Debugger locally;
a working test token today is not a promise it will work next week.

## 3. Configure the Instagram social account

Create or edit an Instagram Social Account in Odoo:

- Account Name: Instagram Demo
- Platform: Instagram
- Handle: alexg_oing
- Branch: the branch used by the post and campaign
- Instagram Account ID: 17841446238462669
- Instagram Token Environment Variable: CAFE_IG_ACCESS_TOKEN

The numeric ID is the professional Instagram account ID, not the Facebook Page
ID (1451594584702943). The environment field contains the variable NAME only.
A Marketing Manager sees that configuration field. Include this social account
in the campaign's allowed accounts if that campaign restricts accounts.

## 4. Make the JPEG reachable again

Your earlier Quick Tunnel URL may have stopped working. Start the existing image
server and tunnel again if needed. In Terminal window 1:

```bash
cd ~/instagram-demo
python3 -m http.server 8001 --bind 127.0.0.1
```

In Terminal window 2:

```bash
cloudflared tunnel --url http://127.0.0.1:8001
```

Copy the **new HTTPS trycloudflare.com URL** printed by cloudflared and append
`/test.jpeg`. Open it in a browser to confirm it returns the actual JPEG. Use the
actual filename if different. Do not reuse an old tunnel address without testing.
Serve only the intended demo-image folder; the URL is public. The Odoo server does
not need to be exposed by this tunnel.

Keep both terminals, Mac/Docker and Odoo running through publication. For a
scheduled demo, they must still be running when the scheduled action executes.
Use a JPEG image meeting Meta's current publishing requirements. Odoo checks URL
syntax; Meta checks and downloads the image itself.

## 5. Test from Odoo

1. Create a NEW draft with exactly one Instagram account.
2. Select matching branch and valid campaign; caption discount must match campaign.
3. Paste the public JPEG URL into Instagram Publishing > Public JPEG URL.
4. Leave normal image attachments and Video Attachment empty for this Instagram post.
5. Optionally run AI review. Validate Post, Submit for Review, then approve as Manager.
6. Click the Instagram icon button **Publish / Check Instagram**.
7. If Processing / Recheck appears, refresh/open the record and click that button
   again after a short wait. It checks the same container, without creating another.
8. Success stores an Instagram Media ID and changes Odoo state to Published. Confirm
   the actual post on alexg_oing.

For scheduling, use a separate approved draft with a future scheduled time inside
the campaign range and click **Schedule Instagram**. Odoo's existing scheduled
action publishes due posts and rechecks processing containers on subsequent runs.
A short processing delay after the scheduled time is expected. Odoo timezone
conversion and your existing campaign-date checks still apply.

## 6. Failure handling and limitations

- Before publishing: editing the URL resets approval, compliance and AI review.
- The approval fingerprint includes caption, URL, account record, numeric IG ID and
  token variable NAME. Account destination changes require approval again.
- URL approval does not freeze the remotely hosted bytes. Keep that image unchanged.
- Once a container exists, content is locked and Request Changes is blocked. Continue
  checking that container, or check its outcome before creating a replacement post.
- API errors show numeric HTTP/API codes without echoing token or remote error text.
- Status-read failures retain the container for rechecking. Terminal container errors
  stop the schedule. Check Meta image requirements and public reachability.
- Network errors during create/publish, or missing response IDs, can have an unknown
  outcome. Automatic retry is blocked. Check Instagram before creating a replacement.
- Remote API calls and the Odoo database are not one atomic transaction. A process
  crash, transaction failure or later request rollback can lose local tracking after
  remote success. This release does not offer crash-proof exactly-once publishing,
  reconciliation, a reset/retry action or historical attempt tracking.

## 7. Validation included with this ZIP

68 offline checks passed: API request contracts, timeout/redaction handling,
processing/recheck, approval snapshot, content locks, scheduling dispatch and
existing Facebook/review/calendar regression checks. Python syntax and XML/XPath
checks passed. These use Odoo stubs and mocked HTTP: they do not establish runtime
compatibility, token validity or actual publication from Odoo.

Required owner checks after upgrade: new fields/buttons visible, Facebook test,
Instagram immediate post, Instagram scheduled post, changed URL requires renewed
approval, Request Changes and both calendars still work. Use demo content.

To run the offline checks from the extracted ZIP folder with Python 3:

```bash
python3 -m venv .venv
.venv/bin/pip install requests lxml markupsafe
.venv/bin/python -m unittest discover -s checks -q
```

## 8. Repository copy (after local testing)

Keep this feature spec and checks under the social_media project alongside the
addon when preparing the next feature PR. Do not initialize another Spec Kit or
overwrite your constitution. The ZIP's specs directory contains only this feature.
Do not commit facebook.env or any tokens. No branch, commit or push was performed
on your Mac by this update.
