# Verification status and manual checklist

Updated: 2026-11-05. Source reviewed: `76f9e2b`. Manifest: `20.0.6.1.0`.

## Evidence levels

- **Source reviewed:** behavior exists in the uploaded archive; this is not proof of runtime success.
- **Owner-reported runtime/live result:** reported during development; not independently replayed for this documentation update.
- **Earlier offline checks:** mocked/static checks were run during release preparation; they are not a complete Odoo registry, browser, permission or platform test.
- **Pending:** no explicit result is recorded for that acceptance scenario.

There is no committed automated test suite in the supplied snapshot. Do not run `unittest discover -s checks` from this checkout and describe the expected suite as present. Earlier delivery packages contained separate checks; migrate/review them into the repo as follow-up work if reproducible automation is desired. No test run was executed against the owner's Odoo/Meta credentials while reorganising these documents.

## Reported results and remaining checks

| Feature/scenario | Recorded evidence | Remaining work |
| --- | --- | --- |
| Facebook text/photo publication | Owner reported earlier live success | Regression on the latest source and failures |
| Facebook scheduling | Owner reported earlier live success | Recheck current cron/approval behavior |
| Instagram attached JPEG with Cloudinary | Owner reported immediate photo appeared | Regression, hosting failures and pending-container paths |
| Instagram scheduling | Implemented in source | Recorded due-time live test |
| Instagram reload/repeat-send checks | Source changes plus earlier offline checks | Targeted stale form/concurrent-request runtime test |
| Account picker and platform previews | Owner reported UI working | Unsupported/multi-account cases |
| Published feed and rounded cards | Owner demonstrated/confirmed local UI | Record filters, access and old simulated-data handling |
| View on Facebook | Owner explicitly reported working | Invalid-ID/unconfirmed-result runtime denial |
| Designer update | Owner reported opening/general use working | Save/reopen formatting, each corner, undo/redo/import/replacement and stale-save matrix |
| Content Calendar dragging | Owner reported working after timezone fix | Clock preservation, chatter, role denial, date/DST boundaries and actual publish after move |
| Facebook/Instagram profile sync | Owner reported working after `BinaryBytes` fix | Runtime failure/cache/identity-race and role-negative cases |
| Request Changes | Owner reported approval/review flow working earlier | Full current regression with mandatory reason and resets |
| AI Review | Existing implementation; no fresh detailed result here | Performance, response failures, advisory boundaries and resets |
| TikTok/OAuth | Incomplete or postponed | Separate requirements/implementation/verification phase |

A generic “works” report does not certify every related acceptance criterion. Preserve the limits of earlier results when reporting progress to a mentor.

## Repeatable demo/checklist

Use a dedicated test Page/account, clearly labelled demo records and intentional publication content. Record date, source commit, database/build and role for each result; keep secrets out of evidence.

1. Confirm upgrade succeeds and existing branches/accounts/campaigns open.
2. Use a campaign valid today, matching branch/account and a clear required discount. Check mismatches fail before any publish request.
3. Prepare a new Designer draft; test styles, every corner, ordering, duplicate limit and undo/redo including an image import.
4. Save JPEG, verify preview/attachment, reopen and verify the editable document. Confirm replacement warning and approval reset on a previously approved draft.
5. Open two editors; change the post in one tab and confirm the stale save in the other is rejected without replacing media.
6. Submit, request changes with a reason, revise, validate and resubmit; confirm a manager approval is needed again.
7. Publish one approved Facebook record; verify remote ID, actual Page post and View on Facebook. Keep a separate Instagram record; verify hosting/container/media result and actual post.
8. Schedule a fresh approved post. As manager, move it to an allowed future day; verify local clock, approval, validation and chatter. Observe actual publication after it becomes due.
9. Try non-manager moves, past/out-of-range times, published/cancelled records and already-started containers. They must not send or reschedule unexpectedly.
10. Sync each profile, confirm local labels remain, refresh cards, then reopen without syncing. Reading the feed must not initiate a Meta sync.
11. With isolated test credentials, check expiry/rejection/download failure and cache preservation. Do not invalidate the working publishing token solely to manufacture a test.
12. Verify ordinary users cannot Sync Profile or bypass protected writes through RPC. Check unrelated-user/branch access according to actual deployment policy.
13. Check uncertain publishing responses with mocks or a controlled harness; never resend a real post blindly to simulate a failure.

Instagram scheduled publication requires its own recorded result; Facebook success does not prove that path works.

## Result template

For each case record: scenario, source/build, actor/role, setup, steps, expected result, observed result, pass/fail/not-run, redacted evidence and follow-up. Distinguish local UI/DB checks from a confirmed external platform result. A test that was not run is not Passed.

## Known engineering boundaries

Odoo transactions do not atomically include Meta/Cloudinary requests. Row locks are not exactly-once delivery. No dedicated attempt ledger/reconciliation UI is present; the [Draft specification](../../specs/001-facebook-attempt-history/spec.md) remains future work. Branch filters do not establish access isolation. Treat the current application as a developing integration, not a certified production service.
