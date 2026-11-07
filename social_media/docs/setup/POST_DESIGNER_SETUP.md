# Post Designer

Release: `5a98517` (2026-11-07). Addon: `20.0.7.0.0`. Saved design schema: **6**.

The Owl 3/canvas editor runs inside Odoo. No separate Node service, external design account or AI model is required.
The redesigned editor and shared design library are part of this release; existing installations must [upgrade the module](INSTALLATION.md).
The library model and its ACLs require that upgrade even when frontend assets already load.

## Open the editor

Save an unpublished **Draft** with write access, no video and no active/uncertain platform publication attempt, then choose Open Designer.
An existing design reopens with its editable text, images, crops and dimensions. New designs start square.

| Area | Controls |
| --- | --- |
| Top actions | Back to post, undo/redo, square/portrait selector, manager Save template and Save JPEG to post |
| Formatting toolbar | Selected text family/size, bold/italic, alignment and colour; selected photo Crop/reposition |
| Left Blocks | Add/drag text, import a photo or logo |
| Left Templates | Shared saved designs and three built-in starter layouts |
| Left Layers | Select/name, hide/show, lock/unlock and reorder |
| Left Background | Poster colour or full-canvas photo |
| Right Properties | Selected content, size, crop, position/alignment, text width/spacing, duplicate/remove |

Desktop panels scroll independently. Narrow layouts rearrange/stack controls. Select a layer on the canvas or in Layers to reveal its settings.

## Square and portrait formats

The top selector offers **1080 × 1080 square** and **1080 × 1350 portrait**. Changing a populated canvas prompts first.
The whole layout moves vertically by half the height difference; text/photo sizes, wrapping widths and crop settings remain unchanged.
Hidden and locked layers participate in this whole-layout conversion. Undo restores the previous format and positions.

Review the edges before saving, particularly when shrinking to square. Content outside the canvas remains in the editable document but is clipped in the exported JPEG.
A background photo fills the new canvas using aspect-preserving cover cropping.
Starter layouts adapt their vertical spacing to the selected format; a saved design restores its own stored format.
Portrait output does not add Stories publishing or any new platform media adapter.

## Layers, movement and snapping

There are up to **eight** text/image layers. The top row in Layers appears in front.

- Drag inside an unlocked visible layer to move it; position fields and canvas alignment buttons provide exact placement.
- Name a layer with up to 60 characters; empty names fall back to its text/image label.
- Hide/show affects both preview and JPEG while retaining the layer in the document.
- Locked objects remain visible but reject ordinary movement, text/style edits, duplication, deletion and reordering. Unlock through Layers. Visibility can still be toggled.
- Move layers backward/forward, duplicate or remove them within the eight-layer limit.

While dragging, nearby edges/centres snap to canvas edges/centres and other visible layers. Purple guides are temporary and disappear when the drag ends.
Hold **Option/Alt while moving** to bypass snapping. Hidden layers are not targets; visible locked layers can be alignment targets.
Snapping is movement-only; keyboard nudges and corner resizing do not snap. Guides and selection handles are never exported.

## Text wrapping and formatting

Text uses system Sans serif, Serif or Monospace fallbacks, with bold/regular, italic, alignment, colour and line spacing.
System fonts may differ slightly between machines. Each text layer is limited to 180 characters.

- **Left/right midpoint handles** set box width and reflow text without changing its font size.
- **Corner handles** resize the font; a wrapped box scales its width with the font within limits.
- Enter retains a manual line break, including blank lines. Wrapped text splits long words to fit and normalises repeated inter-word spaces.
- Under Properties → Position and alignment, set a width or choose **Auto width** to return to manual line breaks only.
- Automatic-width layers, including older designs and starter text, retain their original layout until a width is set.

Explicit wrapping width is 80–1080 logical pixels; font size is 18–160. A glyph wider than the requested box establishes its minimum visible width so it is not clipped.
Text height follows its contents; keep the full box within the poster when preparing the final image.

## Photo cropping

Select a photo/logo layer, then choose **Crop / reposition** in the toolbar or Properties.

1. Choose original proportions, square (1:1), landscape (4:3) or portrait (4:5).
2. Zoom between **100–400%** and drag the image within its fixed frame. Fine-position sliders are also available.
3. Select **Apply crop** to commit the session, or **Cancel** to restore its previous state.
4. **Reset crop** returns to original proportions/100% zoom inside the session; Apply is still needed to commit that reset.

At original proportions and 100% zoom there is no overflow to pan; change frame or zoom in first.
Panning changes the source-image offset, leaving the frame position and width fixed. The photo fills the frame without stretching or empty borders.
The retained image is the designer's resized/re-encoded import, not the full-resolution upload. High zoom can look blurry.

Multiple pans/sliders form one undo step on Apply. A cancelled pointer drag restores just that drag; Cancel restores the whole crop session.
Saving, layer switching and unrelated edits/undo are blocked until Apply/Cancel. This feature crops image layers; full-canvas background controls retain their existing behavior.

## Shared saved designs

Visual designs are separate from caption/message templates with branch/campaign placeholders.

| Role | Visual template actions |
| --- | --- |
| Marketing User | Browse and apply active shared designs to editable drafts |
| Marketing Manager | Those actions plus save named copies and archive templates |

As manager, choose Templates/Save template, enter a trimmed 1–80-character name and select **Save current design**.
This stores a validated document and thumbnail in the shared marketing library. It **does not save, approve or publish the post**, or clear unsaved post-design edits.
Only save content intended for the marketing team: the library does not add branch/company isolation.

Open another draft and select the saved thumbnail. Replacing existing canvas content prompts and can be undone.
The imported document/assets form an independent copy; later edits do not alter the template. Save JPEG to post to persist the draft's copy.
Saved document/thumbnail contents are immutable; apply/edit and save a new named copy for a revised layout. The UI provides Archive, which leaves existing posts unchanged.
Names may be changed through protected model writes, but the editor does not offer an in-place layout overwrite.

The picker loads 20 metadata/thumbnail entries at a time; the full document is fetched when selected. Both Python checks and model ACLs enforce management permissions.

## Undo and keyboard

History is session-only, up to 30 states, with historical image assets trimmed around a 24 MiB base64-text budget.
One movement/resize drag is one step; continuous field edits are grouped. Crop Apply, canvas conversion, template replacement and normal layer operations are undoable.
History is not restored after reopening. Outside editable inputs, Cmd/Ctrl+Z undoes, Shift+Cmd/Ctrl+Z or Ctrl+Y redoes,
arrows move 1 px and Shift+arrows 10 px. Canvas-focused Delete/Backspace removes an eligible layer. Text inputs retain native editing shortcuts.

## Save, limits and compatibility

Save JPEG to post creates a private attachment and editable JSON. Confirm replacement when other attachments or a legacy Instagram URL are selected.
The new JPEG becomes selected media and the legacy URL is cleared; detached old attachments are not deleted.
Saving follows existing approval/compliance resets. Review and approve again before publication.
A row lock/revision check rejects stale saves and rechecks publication eligibility.

| Item | Limit |
| --- | --- |
| Source JPEG/PNG upload | 8 MiB before browser processing |
| Browser resizing | Background max side 1440 px; photo/logo max side 720 px |
| Embedded stored image | 2 MiB, server max side 1600 px |
| Editable document | 7 MiB |
| JPEG output | 5 MiB; exactly 1080 × 1080 or 1080 × 1350 to match its document |
| Shared thumbnail | JPEG, up to 128 KiB; 216 × 216 or 216 × 270 |

Schema versions 1–5 load without implicit geometry changes; new saves use version 6. See [Model reference](../reference/MODEL_REFERENCE.md#designer-persistence).
Restoring older code after new-schema saves is not a complete rollback; preserve compatible design data and required database/filestore backups.

## Troubleshooting

The initial redesigned-editor package used plain proxy-property `t-model` bindings incompatible with the installed Owl 3.
The corrected release uses `t-att-value`/`t-on-input` for template names and `t-att-checked`/`t-on-change` for replacement confirmation.
An old `Invalid t-model expression` error can indicate an old installed XML or cached asset bundle.
Check the actual container-mounted file first, then restart and hard-refresh. A repeated asset hash is a clue, not proof that installation succeeded.
Do not delete arbitrary assets/database rows or bypass installer source checks.

A missing saved-design table/access definition requires the module upgrade; frontend refresh alone does not create it.
See [Verification](../reference/VERIFICATION.md) for owner-confirmed checks and remaining template, permission, stale-save and publishing scenarios.
