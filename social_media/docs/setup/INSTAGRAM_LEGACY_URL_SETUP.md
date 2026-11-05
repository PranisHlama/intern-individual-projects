# Legacy Instagram public-image URL

This supported alternative predates automatic Cloudinary hosting. Prefer the [attached-JPEG workflow](INSTAGRAM_SETUP.md) for new posts.

## Requirements

Use the same professional Instagram account ID, valid token configuration, campaign validation and manager approval as the attached-photo workflow. Supply a public HTTPS URL for a JPEG instead of selecting an attachment; never supply both. The image must remain reachable and unchanged while the attempt needs it.

The URL validator rejects credentials, fragments, whitespace, unsupported ports and obvious local/private destinations. It validates syntax; it is not proof that Meta can download the image or that its content is suitable. The adapter does not download the legacy image into Odoo before approval, so a remote file changing at the same URL remains an important limitation.

## Workflow

1. Prepare a Draft with one Instagram account and valid business context.
2. Enable/use the legacy public-image URL field, leaving attached media/video empty.
3. Set the externally hosted JPEG URL, validate, submit and approve.
4. Publish / Check Instagram, then verify the container/media identifiers and remote post.

Hosting can be an established public service. A local file server plus a tunnel was used during an earlier manual demo, but it is not required for the Cloudinary attachment path. Temporary tunnel URLs change on recreation and stop working when the host/tunnel stops. Do not copy old demonstration URLs into current setup.

A URL fingerprint cannot freeze the content hosted at that URL. If source bytes change, create/review a new controlled post rather than treating the same URL as immutable. As with other publishing paths, investigate uncertain results before another send.
