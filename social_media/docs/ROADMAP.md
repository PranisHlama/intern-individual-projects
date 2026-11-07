# Next phases

Updated: 2026-11-07. Recorded release: `5a98517`, addon `20.0.7.0.0`.
This is prioritisation with explicit evidence boundaries, not a claim that source code alone proves runtime completeness.

## Delivered code

The project README/guides were reorganised in `2eabc9e`. The designer then gained layer naming/hide/lock,
compact controls, snapping, text wrapping, cropping, portrait format and a redesigned workspace with shared saved layouts.
See [release history](history/DESIGNER_RELEASES.md) and [verification](reference/VERIFICATION.md) for what the owner actually confirmed.
Saving/applying independent templates and live template-role restrictions still need explicit Odoo results.

## Priority order

| Phase | Scope | Completion evidence |
| --- | --- | --- |
| 1. Finish editor/template acceptance | Save/reopen all new editing tools, template independence/archive, live roles/RPC, stale saves and approval reset | Recorded checklist tied to the current build; maintain the existing editor before adding more tools |
| 2. End-to-end publishing reliability | Designer → validation → review → immediate/scheduled Facebook/Instagram; failure/uncertainty scenarios | Local versus live evidence separated; exact output/media and duplicate-risk cases recorded |
| 3. Reproducible checks | Review and migrate suitable package tests into the repository; add meaningful Odoo runtime cases | Test commands runnable from a fresh checkout; mocks not labelled integration tests |
| 4. Publishing history | Review/implement the existing Facebook attempt-history Draft | Requirements, permission/failure criteria, regression and explicit transaction limits |
| 5. Selective designer follow-up | Only demonstrated needs: branch brand presets or multi-select/grouping | Reviewed scope, legacy compatibility and save/export checks; background removal remains postponed |
| 6. Account onboarding | Revisit Facebook/Instagram OAuth and token lifecycle | Full callback/configuration/storage/permission flow and repeatable deployment, without requiring foreground Terminal sessions |
| 7. Additional platforms | Reassess TikTok/LinkedIn after core reliability | Current provider access requirements, agreed scope, consent UX and real supported publication evidence |

The application does not need another designer feature to justify the existing work. Commit count/source volume is not evidence of correctness.
First finish the template/permission regression and update the evidence record as tests are actually performed.

OAuth is absent from this source. Local HTTPS was configured during an experiment, but a complete Meta login was not verified and the addon changes were rolled back.
TikTok remains [incomplete/postponed](planned/TIKTOK_SETUP.md), and no LinkedIn adapter exists.
The [attempt-history spec](../specs/001-facebook-attempt-history/spec.md) remains Draft/unimplemented.

The [constitution](../.specify/memory/constitution.md) stays at its tooling path. This retrospective documentation update does not amend governance,
turn old code into evidence of earlier spec-driven development, or replace reviewed requirements for future work.
