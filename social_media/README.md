# Cafe Social Marketing

AI-assisted social content preparation, review, planning and publishing for a multi-branch cafe, built as an **Odoo 20 Community addon**.

Staff prepare captions and images, check campaign rules, request manager approval, and publish or schedule supported Facebook and Instagram posts. Optional local AI reviews the writing; Odoo enforces the business rules and approval workflow.

## What it does

- **Branch and campaign management** — organise accounts, dates, products, discounts and allowed publishing destinations.
- **Caption templates** — reuse text with branch, campaign, product, discount and date placeholders.
- **Compliance and review** — deterministic validation, one manager approval level, rejection and Request Changes with required feedback.
- **Post Designer** — build a square image from templates, photos, logos and text; format, resize, align, duplicate and undo/redo; save a JPEG directly to the draft.
- **Facebook publishing** — publish text or a single JPEG/PNG, schedule approved posts, store remote IDs and open confirmed posts on Facebook.
- **Instagram publishing** — publish one JPEG and caption, with automatic Cloudinary hosting; retain the legacy public-URL alternative.
- **Social Feed** — view local Published Facebook/Instagram records in platform columns with captions, images, dates and branch labels.
- **Profile sync** — manually fetch an account's name and photo, cache them in Odoo, and display them in feed headers.
- **Planning** — Content Calendar with controlled manager rescheduling and Campaign Calendar with inclusive date ranges.
- **AI review** — optional local Ollama review of tone, clarity and suggested wording; no AI image generation.

## Supported platforms and scope

| Platform | Implemented path | Current boundary |
| --- | --- | --- |
| Facebook | Page text or one JPEG/PNG; immediate/scheduled publication; profile sync | No video or multi-image publishing |
| Instagram | Professional account; one JPEG and caption; Cloudinary hosting; scheduling code; profile sync | No Reels, Stories or carousels; scheduling still needs a recorded live test |
| TikTok | Earlier manual-token video inbox-upload prototype remains in source | Incomplete and postponed; Direct Post and OAuth are not available |
| X / other | Account platform selections | Publishing is not implemented; there is no LinkedIn adapter |

Use a **separate Odoo post record for each Facebook or Instagram destination**. The visual account picker opens a setup form; it does not perform OAuth login.

Owner-reported live results and outstanding tests are recorded in [Verification](docs/reference/VERIFICATION.md). A feature existing in source is not a claim that every failure path has been tested.

## Main workflow

1. Configure a branch, social account and campaign.
2. Create a draft; write or apply a caption template and attach supported media or open Designer.
3. Optionally run AI Review, then validate the post.
4. Submit for review; a Marketing Manager approves, rejects or requests changes.
5. Publish immediately or schedule the approved post.
6. Inspect the publishing result and platform post; view local Published records in Social Feed.

Content changes invalidate validation and approval. A permitted manager-only date move preserves content approval and records a chatter note. AI review cannot approve or publish a post.

See [Workflow reference](docs/reference/WORKFLOW_REFERENCE.md) for state transitions, processing checks and uncertain outcomes.

## Project layout

| Path | Contents |
| --- | --- |
| `cafe_social_marketing/models/` | Business workflow, compliance, platform adapters, Designer persistence, calendar guards and profile cache |
| `cafe_social_marketing/services/` | Facebook, Instagram, Cloudinary, profile and Ollama requests; TikTok prototype |
| `cafe_social_marketing/views/` | Odoo forms, lists, feed, calendars, menus and wizards |
| `cafe_social_marketing/static/src/` | Owl 3 Designer, canvas controls, styling and platform icons |
| `cafe_social_marketing/security/` | Marketing roles and Odoo 20 unified access definitions |
| `cafe_social_marketing/data/` | Scheduled publishing action |
| `docs/setup/` | Installation, credentials and feature setup guides |
| `docs/reference/` | Current functionality, workflows, models and verification status |
| `docs/planned/` | Notes on incomplete integrations |
| `docs/history/` and `docs/baseline-2026-10-28/` | Historical migration notes and preserved baseline |
| `specs/` | Feature requirements; the Facebook attempt-history spec remains Draft and unimplemented |
| `.specify/memory/constitution.md` | Project development principles, retained at its tooling path |

## Requirements

- Odoo 20 Community with PostgreSQL and the `base`, `mail` and `product` addons.
- Python `requests` and Pillow, plus the normal Odoo runtime dependencies.
- Internet access and configured Meta credentials for platform actions.
- Cloudinary credentials for attached Instagram photos.
- Optional Ollama service for AI Review; Designer itself needs no model or separate Node service.

The source uses Odoo 20 APIs, including Owl 3 and native binary values. This is not a drop-in Odoo 19 addon. Docker/Compose and secret files are supplied by the deployment; they are not included in this project snapshot.

## Configuration

Supply credentials to the **Odoo process/container**, not the browser or account label fields.

| Setting | Purpose |
| --- | --- |
| `CAFE_FB_PAGE_TOKEN` | Default Facebook Page token variable; each account may reference another `CAFE_FB_...` variable |
| `CAFE_IG_ACCESS_TOKEN` | Default Instagram token variable; each account may reference another `CAFE_IG_...` variable |
| `CAFE_CLOUDINARY_CLOUD_NAME` | Cloudinary product environment/cloud name |
| `CAFE_CLOUDINARY_API_KEY` | Cloudinary upload API key |
| `CAFE_CLOUDINARY_API_SECRET` | Cloudinary signing secret |
| `OLLAMA_URL` / `OLLAMA_MODEL` | Python constants in `services/ollama_service.py`, **not environment-variable settings** in this version |

Account forms store destination IDs and token **variable names**. Entering a variable name does not create the variable or refresh its token. A Compose `.env` file only injects credentials if Compose references them or uses an `env_file`.

See [Installation](docs/setup/INSTALLATION.md), [Facebook](docs/setup/FACEBOOK_SETUP.md), [Instagram](docs/setup/INSTAGRAM_SETUP.md) and [AI Review](docs/setup/AI_REVIEW_SETUP.md). Keep real tokens, secrets and machine-specific configuration out of Git.

## Installation and upgrades

1. Put `cafe_social_marketing/` in an addons directory available to your Odoo server.
2. Make its dependencies available and assign the desired users a Marketing role.
3. For a fresh database, update the Apps list and install **Cafe Social Marketing**.
4. For an existing database, back up the addon, database and required filestore, stop the normal Odoo service, and upgrade `cafe_social_marketing` before restarting.
5. Configure accounts and campaigns, then use a dedicated test Page/account to verify publishing.

For the existing local Compose deployment, after copying the reviewed source and with PostgreSQL running:

```bash
cd ~/Desktop/odoo20
docker compose stop odoo \
  && docker compose run --rm --no-deps odoo \
    odoo -d Mailintegration -u cafe_social_marketing --stop-after-init --no-http \
  && docker compose up -d odoo
```

Those service and database names are examples from the owner's environment. Confirm yours first. A restart alone does not create new stored fields. See [Installation](docs/setup/INSTALLATION.md) for backups, credential injection and presence-only checks.

## Verification and limitations

The owner reported Facebook immediate/scheduled publishing, Instagram immediate photo publishing, calendar dragging, Facebook links and Facebook/Instagram profile sync working. Designer opening and general use were reported working; its detailed acceptance matrix remains to be recorded.

The uploaded commit contains **no committed automated test suite**. Earlier release-package checks are not equivalent to tests run from this checkout. [Verification](docs/reference/VERIFICATION.md) provides a manual checklist and separates those results from unverified behavior.

Known boundaries include one approval level, no dedicated publishing-attempt ledger, no automatic retry/reconciliation screen, no imported remote feed, no social inbox/engagement analytics, and no Meta OAuth/token renewal. Remote API calls and Odoo database transactions are not atomic; interrupted publication can leave an uncertain outcome. Check the platform before resending.

## Documentation and next work

Start with the [documentation index](docs/README.md). The [roadmap](docs/ROADMAP.md) prioritises verification, publishing history and Designer improvements before more integrations.

The addon manifest in the reviewed snapshot declares `20.0.6.1.0`; this documentation describes source through commit `76f9e2b`. The older manifest description does not list every later feature. This documentation reorganisation does not change runtime code or the module version.

License: [LGPL-3.0](https://www.gnu.org/licenses/lgpl-3.0.html), as declared in the addon manifest.
