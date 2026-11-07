# Instagram JPEG publishing with Cloudinary

Source: `76f9e2b`. Supported: one JPEG and caption for an Instagram professional account through the existing Facebook Login API route. No Reels, Stories, carousel, direct Instagram Login OAuth or automatic token renewal is implemented.

## Accounts and hosting

Configure the professional Instagram account ID and an environment-variable name such as `CAFE_IG_ACCESS_TOKEN` on its saved social account. The ID is different from its linked Facebook Page ID. The token and linked account must allow the requested Instagram operations; earlier tests used `instagram_basic` and `instagram_content_publish` alongside relevant Page permissions.

Supply these existing settings to the Odoo process:

| Variable | Purpose |
| --- | --- |
| `CAFE_IG_ACCESS_TOKEN` | Default Instagram token variable |
| `CAFE_CLOUDINARY_CLOUD_NAME` | Hosting cloud/product environment name |
| `CAFE_CLOUDINARY_API_KEY` | Signed-upload API key |
| `CAFE_CLOUDINARY_API_SECRET` | Upload signing secret |

See [Installation](INSTALLATION.md) for injection and presence-only checks. A signed upload is performed server-side with `requests`; no Cloudinary SDK or unsigned upload preset is required by this code. Keep hosting settings from unexpectedly transforming or restricting the published image.

Cloudinary provides the public HTTPS JPEG URL that Instagram fetches. It does not provide social login, credentials or token renewal. The attached-photo path needs no local image server, tunnel or manually pasted URL.

## Prepare and publish

1. Use a new Draft with exactly one Instagram account and matching branch/campaign valid now.
2. Enter a compliant caption and attach one JPEG, or use [Designer](POST_DESIGNER_SETUP.md) to create one.
3. Leave video and the legacy public image URL empty. Do not combine attachment and URL inputs.
4. Validate, submit for review and approve as Marketing Manager.
5. Click Publish / Check Instagram. Odoo checks the approved fingerprint and uploads the JPEG when needed.
6. Odoo stores the Cloudinary URL/asset ID, creates an Instagram container, checks readiness and publishes when confirmed ready.
7. For Processing / Recheck, check the existing attempt again after a short interval; do not create another post merely to refresh the form.
8. Verify Published, the Instagram Media ID and the actual platform post.

The source includes reload/repeat-send handling for confirmed publication. Targeted concurrency and refresh tests remain part of [Verification](../reference/VERIFICATION.md).

## Adapter limits

- Exactly one JPEG, at most 8 MiB, no more than 40 megapixels.
- Image dimensions from 1 to 20,000 pixels on each side, with width/height ratio from 0.8 to 1.91.
- The adapter validates image content and the approved fingerprint; it does not crop/convert unsupported attachments after approval.
- Fingerprints include caption, selected account, destination ID, token-variable name and attached JPEG bytes. Changing file bytes in place can invalidate approval even if the relation is unchanged.

These are source-defined adapter limits, not a promise that every image accepted locally will be accepted remotely.

## Scheduling, caching and retention

The owner later reported the scheduled-publication flow working. It has not been independently replayed against the latest designer release; record fresh platform evidence when running that regression. Hosting occurs when the scheduled attempt executes. The same matching hosted image can be reused for processing checks. Keep Odoo, network and valid credentials available.

Cloudinary assets are public to anyone with the delivery URL. They are not automatically deleted. Do not remove an image needed by a pending container; deleting a post in Odoo does not establish that its Cloudinary asset was deleted.

A hosting failure stops before Meta is contacted. Handled platform errors store safe summaries; uncertain outcomes require checking Instagram before another send. External upload/publication and Odoo commits are not one atomic transaction; orphan hosted media and stale local results remain possible.

## Related guides

- [Legacy public HTTPS JPEG alternative](INSTAGRAM_LEGACY_URL_SETUP.md)
- [Profile sync](PROFILE_SYNC_SETUP.md)
- [Workflow](../reference/WORKFLOW_REFERENCE.md)
