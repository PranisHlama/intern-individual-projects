# Current Functionality

Updated: 2026-11-01
Addon version: 20.0.6.0.0
Code reference: commit 3c36122

## Purpose

Cafe Social Marketing is an Odoo 20 addon for preparing, reviewing,
planning and publishing social content for a multi-branch cafe.

This document describes existing functionality after implementation.
It is not a specification written before the original development.

## Business features

- Branch and social account management.
- Campaigns with dates, discount information and allowed accounts.
- Reusable text templates with dynamic placeholders.
- Text preview.
- Deterministic compliance validation.
- Marketing User and Marketing Manager roles.
- Submit, Approve, Reject and Request Changes with manager feedback.
- Optional AI-assisted text review through local Ollama.
- Content Calendar with branch filters.
- Campaign Calendar showing date ranges and inclusive duration.

Post state, approval status and validation status are separate fields.
There is one manager approval level.

Branch filters support planning; they do not establish branch-level
record isolation.

## Platform publishing

| Platform | Existing functionality | Verification |
| --- | --- | --- |
| Facebook | Text or one attached JPEG/PNG; immediate and scheduled publication | Previously reported working by project owner |
| Instagram | One attached JPEG and caption, automatically hosted on Cloudinary; legacy public-image URL mode also exists | Immediate photo publication reported working |
| Instagram scheduling | Implemented through Odoo scheduling | Live verification pending |
| TikTok | Earlier manual-token video inbox-upload prototype remains in source | End-to-end integration incomplete and postponed |
| X / other | Account platform selections | Publishing not implemented |

These are user-reported results, not a new automated or live test run.
Earlier Facebook tests do not prove every later release is regression-free.

## Instagram workflow

1. Configure a professional Instagram account ID and token variable name.
2. Create a post with exactly one Instagram account and one JPEG.
3. Validate, submit and obtain manager approval.
4. Publish the approved content.
5. Odoo uploads the JPEG to Cloudinary automatically.
6. Instagram fetches the hosted image and prepares a media container.
7. Odoo requests publication and stores the returned media identifier.

Cloudinary removes manual image-server and URL-pasting steps for attached
JPEGs. It does not provide account login or token renewal.

Facebook and Instagram use separate Odoo post records.

## Account picker

The visual picker offers Facebook, Instagram and TikTok.
Selecting a card opens an account form with the platform preselected.
It does not perform OAuth login or automatically connect an account.

## Credentials and services

Facebook and Instagram tokens are supplied through Docker environment
variables. Cloudinary credentials are also supplied through environment
variables. Actual credentials must remain outside Git.

The existing TikTok prototype has a different, manual token-storage path.
The prepared TikTok v10 OAuth update is not installed in this version.

AI review is optional and does not approve or publish content.
Scheduled publication requires Odoo and its scheduler to remain running.

## Known limitations

- No multi-level approval.
- No dedicated publishing-attempt history model.
- No automatic retry queue or uncertain-outcome reconciliation interface.
- No Facebook video publishing.
- No Instagram Reels, Stories or carousel publishing.
- No implemented social inbox or engagement analytics.
- No automated Facebook or Instagram OAuth/token renewal.
- Cloudinary assets are not automatically deleted after publication.
- Campaign state is not enforced by the existing compliance checks.
- Calendar display does not automatically activate or complete campaigns.

An Instagram publication appeared remotely, but the form did not immediately
show completion and a repeated action returned a validation error.
Stored state and form-refresh behaviour still need verification.
Do not resend a remotely published post merely to refresh the screen.

## Documentation and future work

The October 28 documentation is preserved in baseline-2026-10-28/.
Its field-level details and findings describe version 20.0.4.1.0.

The Facebook attempt-history specification remains Draft and unimplemented.
Future changes should have requirements and acceptance criteria before
implementation, followed by recorded verification results.
