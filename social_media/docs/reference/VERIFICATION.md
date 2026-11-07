# Verification status and manual checklist

Updated: 2026-11-07. Recorded code release: `5a98517`; addon `20.0.7.0.0`.

## Evidence levels and source basis

- **Source reviewed:** the earlier uploaded repository archive (`76f9e2b`) and delivered designer sources, through the corrected Studio package. The owner showed the release commit/push output; the remote branch was not independently fetched for this documentation update.
- **Owner-reported local/live result:** reported in the development conversation, not independently replayed. Reports span multiple development stages; not all scenarios were rerun on `5a98517`.
- **Offline package checks:** the corrected Studio package passed 42 mocked frontend behavior checks and 19 Python tests (13 validator methods and 6 mocked-ORM permission/endpoint methods). Syntax, access-file, manifest and installer checks also passed.
- **Pending:** no explicit result is recorded for that scenario. A generic “works” confirms the reported interaction, not every related acceptance criterion.

Those package tests do not constitute an actual Odoo registry, Owl browser, role session, database save or live platform test.
The supplied repository snapshot and subsequent code commits shown here add no committed test suite. Until tests are deliberately migrated/reviewed into the checkout, do not describe the delivery-package suite as a reproducible repository test command.
No owner database, credentials or remote platform was exercised while updating these documents. No new runtime tests were performed for this documentation-only change.

## Owner-reported checks

| Feature/scenario | Recorded result | Evidence boundary / remaining work |
| --- | --- | --- |
| Facebook immediate text/photo and scheduling | Earlier live success reported | Latest-release regression, failure and uncertainty cases |
| Instagram attached JPEG/Cloudinary | Earlier immediate photo success reported | Latest regression and hosting/container failure cases |
| Instagram scheduled publishing | Owner reported success after the due-time scheduling checklist | Not independently replayed; no separate live evidence captured here |
| Instagram reload/repeat-send safeguards | Code and earlier offline checks | Stale form/concurrent-request runtime scenarios remain pending |
| Picker, platform previews, local feed and Facebook links | Owner reported working | Unsupported destinations, filters, access and old simulated Published data |
| Facebook/Instagram profile sync | Owner reported working after native binary fix | Cache/identity race, failure and role-negative runtime cases |
| Caption change after approval | Publishing was blocked | Explicit reset-field assertions and direct RPC enforcement still pending |
| Request Changes | Empty reason refused; nonempty reason returned to Draft and was visible | Broader state/permission regression still pending |
| Marketing User review interface | Approve unavailable | Hidden button is not proof of server-side denial; direct action/RPC test pending |
| Calendar rescheduling | Date changed, clock preserved, chatter entry visible | Negative permissions, date/DST bounds and publication after moved due time |
| Layer/snap controls | Corrected labels/editor controls and snapping reported working | Exhaustive lock/hide/reorder/history runtime checks pending |
| Text wrapping | Side midpoint handle preserved font; corner resizing was confirmed intentional | Dedicated wrapped-width save/reopen, manual-break and long-word runtime matrix pending |
| Photo cropping | Crop worked, persisted on reopening, JPEG matched preview | All frame/zoom/Cancel/Reset/history cases not individually confirmed |
| Portrait canvas | Owner confirmed format persisted and JPEG dimensions/layout matched the requested check | Square/portrait conversion, edge clipping and live portrait publication regression pending |
| Redesigned editor | Owner said it ran after the repeated Owl error; guarded source copy and push then succeeded | Fresh visual/responsive regression and full existing-tool matrix pending |
| Shared saved designs | Source, validation/permission mocks and code release available | Explicit real save/apply-copy independence, archive, pagination and live-role results pending |
| AI Review | Existing implementation | Fresh performance/failure/advisory-boundary checks pending |
| TikTok/OAuth | Incomplete/postponed | Separate requirements, implementation and verification phase |

## Focused editor/template acceptance

Use a dedicated unpublished draft and record the source/build, database and actor/role. Keep tokens/private data out of screenshots/logs.

1. Confirm module upgrade creates the design-template model/ACLs. Open an existing square and portrait/cropped design; check toolbar/sidebar/Properties at normal laptop and narrow widths.
2. Exercise layer naming, visibility and locking; hidden content must be absent from JPEG, and locked ordinary edits must fail. Check selected ordering and eight-layer cap.
3. Drag near edges/centres/visible objects; test Option/Alt bypass and confirm exported JPEG has no guides.
4. Use side handles for wrapping and corners for font sizing. Check manual/blank lines, long words, Auto width, undo/redo and saved width after reopening.
5. Choose crop frames, zoom/pan, cancel, reset/apply and undo/redo. Check the fixed frame, original source availability and JPEG appearance.
6. Switch square/portrait, check layout boundaries, alignment/snapping below the old square boundary, undo/redo and exact exported dimensions.
7. As manager, save a named shared template. The post should remain unsaved/unapproved as before the template save.
8. Apply it to another draft, edit the copy, save/reopen the post, then reapply the original template to confirm it is unchanged. Verify its stored format and crop/hidden/locked settings.
9. As Marketing User, apply a layout and verify save/archive management is unavailable. Separately test server-side denial through controlled RPC, not just button visibility.
10. As manager, archive a layout; refresh the list and check it cannot be applied through the designer endpoint. Existing copied posts must remain unchanged.
11. Check invalid/empty names, invalid thumbnail/document payloads, stale post revisions and already-started publication. Invalid saves must not replace post media.
12. Save a JPEG over existing selected media only with explicit replacement confirmation, then verify the established approval/validation reset and stale-save protection.

## Publishing/review regression

Use clearly labelled demo content and intentional publication destinations. Record actual remote identifiers/evidence separately from local UI/database state.

1. Open branches/accounts/campaigns after upgrade. Check branch/account/campaign/discount mismatches fail before external requests.
2. Submit, request changes with mandatory reason, revise, validate, resubmit and approve. Check protected actions as Marketing User and an unrelated user through actual server calls.
3. Publish one approved Facebook and one separate Instagram record; confirm platform posts, remote IDs, local status and Facebook link.
4. Schedule a fresh post per platform, observe its real publication once, and record the result. Do not reuse a prior Facebook result as evidence for Instagram.
5. Reschedule an approved future post; check retained clock, chatter and eventual publication at the new date. Check past/campaign-range/DST and non-manager denials.
6. Sync profiles with existing working credentials; verify failures retain the cache and ordinary feed reads do not fetch remotely. Test identity/race scenarios without exposing tokens.
7. Exercise uncertain responses with mocks or a controlled harness. Check the platform before resending; never blindly duplicate a real publication to simulate failure.

## Result template and boundaries

Record: scenario, source/build, actor/role, setup, steps, expected and observed results, pass/fail/not-run, redacted evidence and follow-up.
A test that was not run is not Passed. A local model/UI check is not proof of an external platform result.

Odoo transactions do not atomically include Meta/Cloudinary calls. Row locks are not exactly-once delivery; no immutable publishing-attempt ledger/reconciliation UI exists.
The [attempt-history specification](../../specs/001-facebook-attempt-history/spec.md) remains Draft/unimplemented. Branch filters and the shared visual library do not establish branch/company isolation.
