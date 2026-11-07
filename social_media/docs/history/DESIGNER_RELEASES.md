# Designer release history

Recorded from the owner's Git output and the delivered sources. These are code-release notes, not a claim that every acceptance case passed.
The shared repository's `main` README and other projects are outside this change.

| Commit | Scope |
| --- | --- |
| `a591029` | Initial template-based social post designer |
| `e8e3944` | Font/style/position/resize and editing controls |
| `153fe19` | Layer naming/hide/lock, compact controls, snapping and text wrapping |
| `5a98517` | Photo cropping, portrait canvases, redesigned editing workspace, shared design templates and corrected Owl 3 input bindings |

The separate documentation reorganisation was `2eabc9e`. Source for earlier business/platform behavior came from the uploaded `76f9e2b` archive.
Later commit/push output was supplied by the owner; this documentation task did not independently fetch the remote branch.

## Release 20.0.7.0.0

This release adds `cafe.social.design.template`, loaded from the already-imported `models/post_designer.py`, plus its read/management access rules.
It requires a module upgrade on an existing database. It is distinct from `cafe.social.post.template`, which stores captions.
The new editor layout provides a top action/format toolbar, left content panels, grey canvas area and selected-object Properties.
Managers save immutable shared layouts and archive them; Marketing Users apply copies to editable drafts.
Existing designer save/access/revision/approval paths remain in place.

New saved documents use schema **6**, with explicit square/portrait dimensions. Older versions 1–5 remain readable.
The addon version and document schema are different numbers. New-schema data must be considered when restoring older code.

## Owl 3 binding correction

The first redesigned-editor package used `t-model` on plain proxy properties for a template name and replacement checkbox.
The installed Owl 3 expected a function with a `.set` method, causing `Invalid t-model expression` when the relevant branch rendered.
The corrected source uses explicit value/checked attributes and input/change handlers. The owner subsequently reported the editor running,
passed the source-copy binding guard and pushed `5a98517`.

The correction changed frontend files; it did not remove the module-upgrade requirement for the newly introduced template model.
Restart/hard-refresh can pick up frontend fixes after a successful upgrade; they do not create missing model tables/ACLs.

## Evidence boundary

Cropping and portrait persistence/JPEG checks were owner-confirmed before the redesign. The corrected editor opening was reported working.
The final package passed 42 mocked frontend checks and 19 Python validator/permission tests, plus static/installer checks.
Shared-template save/apply-copy independence, archive and live role/RPC scenarios remain unconfirmed in the conversation.
See [Verification](../reference/VERIFICATION.md) and [Designer setup](../setup/POST_DESIGNER_SETUP.md) for the current checklist.
