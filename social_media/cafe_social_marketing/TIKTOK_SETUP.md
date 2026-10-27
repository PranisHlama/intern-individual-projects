# TikTok Integration (Odoo 20 MVP)

This version adds a real TikTok Content Posting API **Upload to TikTok** flow for videos.
It uploads an approved Odoo post's video to TikTok as a draft. The TikTok user then opens the TikTok inbox, finishes editing, and publishes it from TikTok.

## What is implemented

- Dedicated video attachment on `cafe.social.post`
- MP4, MOV and WebM format validation
- TikTok-specific compliance check when a TikTok account is selected
- TikTok access token field on Social Account (Marketing Manager only)
- `video.upload` draft initialization
- Binary FILE_UPLOAD to TikTok, including chunked uploads
- TikTok `publish_id` storage
- TikTok status check action

## TikTok developer setup

1. Create/register an app in TikTok for Developers.
2. Add the Content Posting API product.
3. Obtain approval/authorization for the `video.upload` scope.
4. Authorize a TikTok user and obtain a user access token.
5. In Odoo open Social Accounts, choose platform TikTok, and paste the access token into the TikTok Integration section.

For this MVP the token is entered manually. The next phase should replace this with TikTok Login Kit OAuth and refresh-token handling.

## Odoo workflow

1. Create a Social Account with Platform = TikTok.
2. Add its TikTok access token.
3. Create a social post and select that TikTok account.
4. Attach an MP4, MOV or WebM video.
5. Run compliance validation.
6. Submit and approve the post.
7. A Marketing Manager clicks **Upload Video to TikTok Draft**.
8. Open TikTok inbox to continue editing and publish.
9. Use **Check TikTok Status** in Odoo to fetch the latest remote status.

## Important distinction

Upload-to-draft is an official TikTok Content Posting API integration, but it is not the same as Direct Post. Direct Post requires the `video.publish` scope, creator-info UX, privacy controls, and TikTok audit considerations. It should be implemented as a separate next phase rather than pretending a draft upload is already publicly published.
