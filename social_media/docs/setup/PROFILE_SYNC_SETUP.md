# Facebook and Instagram profile sync

Sync Profile uses an existing account's Meta credentials to fetch its current name/photo and Instagram username. It does not need OAuth, a tunnel or Cloudinary, and does not publish a post.

## Use it

1. Install/upgrade the current addon before using its new stored profile fields; see [Installation](INSTALLATION.md).
2. Sign in as Marketing Manager and open Configuration → Social Accounts.
3. Open an existing active Facebook/Instagram account with the correct destination ID and token-variable configuration.
4. Click Sync Profile. Inspect Cached Social Profile and its Last Profile Sync time.
5. Refresh Social Feed. Existing cards for that account use the cached name/photo; Instagram also shows its synced username.

Do not create a duplicate account just to sync a profile. The local account name/handle are not overwritten. The current profile is shown on old cards; it is not a per-publication historical snapshot.

## Cache and image handling

Metadata and a JPEG up to 192px are stored on the account. Native Odoo 20 `BinaryBytes` wraps the JPEG for the Binary field. Browser image URLs point to Odoo, not a token-bearing API URL; normal account read access remains relevant.

Feed loading makes no profile API request. Sync is manual, with no cron refresh. The service accepts only expected Meta CDN photo hosts, checks public DNS destinations, rejects redirects, bounds image input and normalises supported images to JPEG. The platform logo is used when no valid/default photo is available.

API/download failures keep the last successful cache. Changing the platform or destination ID clears it; sync rechecks identity under a row lock before storing. Cache fields are readonly and reject direct ordinary writes/creates. A manager still needs account write access.

## Troubleshooting and boundaries

- Missing token variable: configure the existing deployment credential and recreate the Odoo container.
- API rejection: check destination ID, token validity and applicable Page/Instagram read permissions; presence alone is not validity.
- Unsupported photo address/download: the cached profile is retained. Do not weaken the URL checks or paste credentials into a browser image URL.
- Old feed card: refresh and inspect Last Profile Sync; the name may intentionally differ from the local account label.

The owner reported both Facebook and Instagram sync/feed display working after correcting the Binary field write. Permission-negative cases, token failures, identity races and cache behavior have offline coverage from a release package, but still need explicit Odoo runtime checks. No raw provider errors or tokens should be shared for diagnosis.
