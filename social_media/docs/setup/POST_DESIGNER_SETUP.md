# Post Designer

The browser-based Owl 3/canvas editor is part of the addon. No AI image model, separate JavaScript service, npm installation or external design account is required. Follow [Installation](INSTALLATION.md) for the addon; do not reinstall an older release ZIP over the current source.

## Open and edit

Save an unpublished Draft with no active/uncertain platform attempt and no video, then click Open Designer. Choose Weekend Offer, New Menu Item or Branch Announcement, or start with blocks. The canvas is fixed at 1080 × 1080 with up to eight layers.

- Add text, a photo or logo; choose a background colour/photo.
- Select a layer and drag inside it to move, or use numeric position fields.
- Drag a corner to resize. Images keep their aspect ratio; text changes font size.
- Choose Sans serif, Serif or Monospace; toggle Bold/Italic and set multiline alignment/line spacing.
- Use Left/Centre/Right and Top/Middle/Bottom for canvas alignment, and send layers backward/forward.
- Duplicate/remove a layer within the eight-layer limit.

Text line breaks are manual; there is no automatic wrapping. Font families use system fallbacks, so appearance can vary by device. There is no freeform crop, rotation, multi-page design or additional output aspect ratio.

## Undo and keyboard controls

Undo/redo restores edits, layer operations, imports and template changes during the current session. One drag is grouped as one step; focused continuous field edits are grouped. History retains up to 30 states and trims historical image assets around a 24 MiB base64-text budget. It is not saved after reopening.

Outside editable inputs, use Cmd/Ctrl+Z to undo; Shift+Cmd/Ctrl+Z or Ctrl+Y to redo; arrows move one pixel and Shift+arrows move ten. With the canvas focused, Delete/Backspace removes the selected layer. Text fields retain their native editing shortcuts.

## Save and reopen

Save JPEG to post exports the canvas without selection controls, creates a private JPEG attachment and stores the editable JSON. Confirm replacement when other attachments or a legacy Instagram URL are selected. Old detached attachments are not deleted; the new JPEG becomes the selected media and the legacy URL is cleared.

Saving resets compliance/approval through the inherited content-write path. Review and approve again before publishing. A revision check under a row lock rejects a stale editor if the post changed elsewhere. If publication started while the editor was open, save eligibility is checked again.

Version-1 documents remain readable. New saves use version 2 for font/style/alignment/spacing fields; restoring old validator code is not a complete rollback for newly saved documents.

## Size limits and acceptance checks

JPEG/PNG imports are limited to 8 MiB before browser processing, and resized/re-encoded before storage. The server allows embedded source assets up to 2 MiB each with dimensions up to 1600 pixels; the editable document limit is 7 MiB. Output is a 1080-square JPEG up to 5 MiB. Oversize/invalid designs must be simplified rather than bypassing validation.

Verify old designs reopen, styles survive save/reopen, every resize corner behaves correctly, import/delete/template undo works, and replacement/approval resets are correct. Test stale saves in two tabs and denial on scheduled/published posts. See [Verification](../reference/VERIFICATION.md) for what the owner reported versus outstanding cases.
