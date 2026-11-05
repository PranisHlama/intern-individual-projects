# Documentation

Current source reviewed: `76f9e2b` (2026-11-05). Manifest version: `20.0.6.1.0`.

This is documentation of implemented code and owner-reported verification, written after those features were built. It is not evidence that the existing implementation followed every current development principle from its inception.

## Current references

- [Current functionality](reference/CURRENT_FUNCTIONALITY.md)
- [Workflow reference](reference/WORKFLOW_REFERENCE.md)
- [Model reference](reference/MODEL_REFERENCE.md)
- [Verification status and checklist](reference/VERIFICATION.md)
- [Roadmap](ROADMAP.md)

## Setup guides

- [Installation, upgrades and environment configuration](setup/INSTALLATION.md)
- [Facebook publishing](setup/FACEBOOK_SETUP.md)
- [Instagram with Cloudinary](setup/INSTAGRAM_SETUP.md)
- [Legacy Instagram public-image URL](setup/INSTAGRAM_LEGACY_URL_SETUP.md)
- [Post Designer](setup/POST_DESIGNER_SETUP.md)
- [Review and calendars](setup/REVIEW_CALENDAR_SETUP.md)
- [Profile sync](setup/PROFILE_SYNC_SETUP.md)
- [Optional AI Review](setup/AI_REVIEW_SETUP.md)

## Planned work and governance

- [TikTok prototype boundaries](planned/TIKTOK_SETUP.md) — incomplete and postponed.
- [Facebook attempt-history specification](../specs/001-facebook-attempt-history/spec.md) — Draft; not implemented.
- [Project constitution](../.specify/memory/constitution.md) — kept at its tooling path.

Specifications and the constitution stay in their established locations; they are linked here rather than moved into setup documentation. Changes to governance or implementation are outside this documentation-only update.

## Historical documents

- [Original Odoo 20 migration notes](history/MIGRATION_ODOO20.md) — moved from the addon and labelled historical.
- [October 28 functionality baseline](baseline-2026-10-28/CURRENT_FUNCTIONALITY.md)
- [October 28 workflow baseline](baseline-2026-10-28/WORKFLOW_REFERENCE.md)
- [October 28 model baseline](baseline-2026-10-28/MODEL_REFERENCE.md)

The three October 28 baseline files are preserved byte-for-byte. Their old versions, source paths and conclusions are historical, not current guarantees.

## Repository maintenance

General setup/reference Markdown belongs here rather than alongside addon Python modules. Keep the project overview in [the project README](../README.md). The shared repository's root README and other project branches are outside this project's documentation scope.

The running addon on the owner's Desktop is a deployment copy. After this reorganisation, avoid copying old Markdown guides back from that deployment into the repository. When synchronising code, use an explicit source-file selection or exclude `*.md`; manage documentation here separately.

Do not stage local secret files, database dumps, temporary installers, editor tooling or a separately cloned repository nested inside this project. Decide the disposition of such local folders separately; this update neither moves nor deletes them.
