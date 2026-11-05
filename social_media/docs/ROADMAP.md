# Next phases

Source baseline: `76f9e2b` (2026-11-05). This is prioritisation, not a promise that the listed features are implemented.

| Phase | Scope | Completion evidence |
| --- | --- | --- |
| 1. Consolidate documentation | Project README, organised guides, accurate functionality/workflow/model references | Working links, preserved historical baseline and clear implemented/planned boundaries |
| 2. Verify reliability | Designer → validation → review → immediate/scheduled publishing; permission, token, date and uncertain-outcome cases | Recorded checklist from [Verification](reference/VERIFICATION.md), with live results separated from mocks |
| 3. Publishing history | Review and implement the existing Facebook attempt-history Draft | Acceptance criteria, server-side permissions, current workflow regression and explicit transaction limits |
| 4. Designer refinement | Prioritise actual usability gaps: crop, wrapping, snapping and useful layouts | Reviewed scope, old-document compatibility and save/export acceptance checks |
| 5. Account onboarding | Revisit Facebook/Instagram OAuth and token handling | Verified provider callback/configuration flow, state/permissions/storage tests and repeatable deployment setup |
| 6. Additional platforms | Reassess TikTok or LinkedIn after core reliability | Current platform access requirements, agreed scope, consent UX and real supported publication evidence |

The completed Designer controls and profile sync do not remove the need for end-to-end regression tests. Avoid treating commit count or source volume as evidence of completeness.

OAuth is not installed in this source. A local HTTPS callback was configured during an experiment, but a complete Meta login flow was not verified and the addon changes were rolled back. Future work should avoid requiring users to manage foreground Terminal sessions; whether using local HTTPS or hosted Odoo, validate the full flow before claiming it works.

TikTok remains [incomplete and postponed](planned/TIKTOK_SETUP.md). No LinkedIn adapter exists. The [attempt-history spec](../specs/001-facebook-attempt-history/spec.md) remains Draft and unimplemented; do not relabel it as completed merely because the documentation is organised.

Keep the project [constitution](../.specify/memory/constitution.md) at its existing path. Review requirements and acceptance criteria before implementation, record limitations honestly, and keep credentials/machine-specific files out of Git. The repository collaboration workflow should follow the maintainer's current instructions; this documentation update does not amend governance.
