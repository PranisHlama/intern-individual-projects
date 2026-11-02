# DMS Document Editor

Edit Word, Excel, PowerPoint and PDF files from **Odoo DMS** directly in the
browser. Users click a button on a DMS file, edit it in a full-page editor and
press **Save**; the original DMS record is updated in place. No manual
download/upload, no external account.

- Odoo: 20.0 (Community)
- Depends on: `dms` (OCA)
- Author: Aayush Poudel
- License: LGPL-3 (bundled editors have their own licenses, see [Licensing](#licensing))

---

## What it does

The module adds two buttons to the DMS file form:

| Button | Editor | File types | Needs a separate server? |
|---|---|---|---|
| **Edit in Browser (Beta)** | SuperDoc | `.docx` | No |
| | BetterOffice Spreadsheet | `.xlsx` | No |
| | BetterOffice Presentation | `.pptx` | No |
| | PDF.js | `.pdf` | No |
| **Edit with ONLYOFFICE** | ONLYOFFICE Docs | `.docx` `.xlsx` `.pptx` `.csv` `.pdf` `.md` | **Yes**, ONLYOFFICE Document Server |

**Edit in Browser** is the new path. Every editor is shipped inside this module
and runs entirely in the user's browser. The ONLYOFFICE path is the older
integration and stays until the browser editors are fully tested.

The editor is chosen by file extension. A button only appears when the user has
write access and the file is not locked by another user.

---

## Installation

1. **Python packages.** `controllers/main.py` (the ONLYOFFICE integration)
   imports these at load time, so they are required even if you only use the
   browser editors:

   ```bash
   pip install PyJWT requests
   ```

2. **Add the module** to your addons path (with `dms` available), then update
   the apps list and install **DMS ONLYOFFICE Document Editor**, or from the
   command line:

   ```bash
   odoo-bin -d <database> -i document_editor
   ```

3. **Upgrading** after pulling changes:

   ```bash
   odoo-bin -d <database> -u document_editor --stop-after-init
   ```

   Then restart Odoo; new Python routes only load after a restart.

Nothing else is needed for **Edit in Browser**. Node.js is *not* needed on the
server; the editor files are already built and committed in `static/lib/`.

### Optional: ONLYOFFICE

Only if you want the **Edit with ONLYOFFICE** button to work:

1. Run an ONLYOFFICE Document Server with JWT enabled.
2. In **Settings → Document Editor**, fill in:
   - **ONLYOFFICE URL**: address the *browser* uses to reach ONLYOFFICE,
     e.g. `http://localhost:8080`.
   - **Odoo Base URL**: address *ONLYOFFICE* uses to reach Odoo,
     e.g. `http://web:8069` inside Docker Compose.
   - **ONLYOFFICE JWT Secret**: same value as `JWT_SECRET` on the server.

---

## Using it

1. Open **Documents → Files** and open a `.docx`, `.xlsx`, `.pptx` or `.pdf`.
2. Click **Edit in Browser (Beta)**.
3. Edit the document.
4. Click **Save** in the purple header (or press **Ctrl+S**).
   The status shows *Saved* and a note appears in the file's chatter.
5. Click **← Back to Odoo** to return. You are warned if there are unsaved changes.

If someone else saved the same file after you opened it, your save is refused
with a message instead of overwriting their work. Reload the editor to get the
latest version.

---

## How it works

```
DMS form ──button──▶ /document_editor/browser/open/<id>    (checks access, renders page)
                         │
 browser ◀──────────────┘  /document_editor/browser/content/<id>   (downloads the file)
   │  edits locally (SuperDoc / BetterOffice / PDF.js)
   └──Save──▶ /document_editor/browser/save/<id>          (validates, writes, audits)
```

All three routes run as the **logged-in user** (`auth="user"`), so the normal
DMS access rules apply, and every route re-checks on the server:

- the file exists and its type is supported;
- the user has **write** permission (`permission_write`);
- the file is not locked by another user (DMS lock);
- on save: the upload is not empty, not larger than 100 MB and starts with the
  right file signature (`PK` for Office files, `%PDF` for PDF);
- on save: the checksum the editor opened matches the current one, otherwise
  `409 Conflict` (protects against overwriting someone else's newer save);
- CSRF token is required on save.

A save writes the new content to the **same** `dms.file` record, posts
*"Document content was modified using …"* to its chatter and logs an `AUDIT:`
line. A failed or rejected save never changes the stored file.

### Code map

| Path | Purpose |
|---|---|
| `controllers/browser_editor.py` | The three browser-editor routes and the `BROWSER_EDITORS` table (extension → editor) |
| `controllers/main.py` | ONLYOFFICE integration (config, content, callback routes) |
| `models/document_editor.py` | Button actions on `dms.file` |
| `views/dms_file_views.xml` | The two buttons on the DMS form |
| `views/editor_templates.xml` | Shared editor page layout + one small page per editor |
| `static/src/js/editor_page.js` | Shared page logic: load, unsaved changes, Save, conflict handling |
| `static/src/js/superdoc_editor.js` | DOCX adapter |
| `static/src/js/betteroffice_editor.js` | XLSX/PPTX adapter |
| `static/src/js/pdfjs_editor.js` | PDF adapter |
| `static/lib/` | Bundled editors (do not edit by hand) |
| `frontend/` | Build setup for the BetterOffice bundles (developers only) |

---

## Editor capabilities and limits

### DOCX: SuperDoc 1.47.2
Text, formatting, tables, lists, images via the SuperDoc toolbar.
We use the 1.x line on purpose: SuperDoc 2.x loads a proprietary engine from a
CDN whose license forbids redistribution. Telemetry is disabled.

### XLSX: BetterOffice 0.5.1
Cell values, formulas (recalculated), formatting, multiple sheets.
BetterOffice is young (0.x). There is no published feature list, so test
workbooks with charts, pivot tables or macros before relying on it.

### PPTX: BetterOffice 0.5.1
Slide text, shapes and images. Fonts: the deck's fonts are replaced by bundled
open look-alikes (e.g. Calibri → Carlito, Arial → Liberation Sans) for layout;
the saved file keeps the original font names. Fonts we don't ship (e.g. Aptos)
use a fallback, so line breaks may differ slightly from PowerPoint.

### PDF: PDF.js 6.4.299
| Works | Not possible |
|---|---|
| Add text boxes, highlight, comments, freehand drawing, add images | Edit existing PDF text or images |
| Signatures (typed, drawn or image) | Certificate-based digital signatures |
| Fill forms | Create new form fields |
| Delete, reorder, copy/paste pages; merge ("Add file"); split ("Export selected", downloads a new file) | Rotate pages permanently (rotate is view only) |

Page management is still marked *experimental* in PDF.js and is switched on by
this module.

### All editors
- **One editor at a time per file.** There is no real-time co-editing; a second
  person saving later gets the conflict message. (Real-time collaboration would
  need an extra WebSocket server.)
- Browsers: current Chrome, Edge or Firefox; Safari 16.4+.

---

## Developer guide

### Upgrading BetterOffice (XLSX/PPTX)

Requires Node.js on your development machine only.

```bash
cd document_editor/frontend
# edit the pinned versions in package.json, then:
npm install
npm run build
```

`build.mjs` regenerates `static/lib/betteroffice/`:
- `xlsx-editor.js`, `pptx-editor.js`: React + the editor UI, bundled by esbuild;
- `xlsx/`, `pptx/`, `fonts/`: the BetterOffice core packages, copied
  **unmodified**. They load their Web Worker, WASM and font files relative to
  their own location, so their folder layout must not change.

The editor page maps the package names to these folders with an import map in
`views/editor_templates.xml`. If a new BetterOffice version adds an export
path, add it to that import map.

Keep versions pinned exactly, read the release notes (0.x releases may remove
APIs) and re-test open/edit/save for both formats. Commit the rebuilt
`static/lib/betteroffice/`; `frontend/node_modules/` is ignored.

### Upgrading SuperDoc (DOCX)

Copy `dist/superdoc.min.js`, `dist/style.css` and `LICENSE` from the npm package
`superdoc@<version>` into `static/lib/superdoc/`. **Stay on 1.x** unless you
have reviewed the 2.x DOCX Engine license (see Licensing).

### Upgrading PDF.js

Download `pdfjs-<version>-dist.zip` from
<https://github.com/mozilla/pdf.js/releases>, replace `static/lib/pdfjs/build`
and `static/lib/pdfjs/web` (you may drop `*.map` files and the sample PDF), and
re-test. `pdfjs_editor.js` relies on a few viewer internals
(`PDFViewerApplication.downloadManager`, `downloadOrSave`, the
`saveextractedpages` event, the `enableSplitMerge` option), so check those still
exist after an upgrade.

### Adding another file type

1. Add an entry to `BROWSER_EDITORS` in `controllers/browser_editor.py`:
   ```python
   "odt": {
       "name": "MyEditor",                              # shown in chatter
       "template": "document_editor.myeditor_page",     # editor page
       "mimetype": "application/vnd.oasis.opendocument.text",
       "signature": b"PK",                              # required file header
   },
   ```
2. Add a template that calls the shared layout:
   ```xml
   <template id="myeditor_page">
       <t t-call="document_editor.browser_editor_layout">
           <div id="editor-container" class="browser-editor-fill"/>
           <script type="module" src="/document_editor/static/src/js/myeditor_editor.js"/>
       </t>
   </template>
   ```
3. Write a small adapter. `startEditorPage` handles loading, Save, conflicts and
   the unsaved-changes warning; your function only mounts the editor and returns
   an async function that exports the edited file as a `Blob`:
   ```js
   import { startEditorPage } from "./editor_page.js";

   startEditorPage(async (options) => {
       // options: container, bytes, fileName, mimetype, user,
       //          onReady(), onChange(), onSaveRequest(), onError(e), onFatalError(msg)
       const editor = await mountMyEditor(options.container, options.bytes);
       editor.on("ready", options.onReady);
       editor.on("change", options.onChange);

       return async () => new Blob([await editor.export()], { type: options.mimetype });
   });
   ```
4. Add the extension to the button's `invisible` list in
   `views/dms_file_views.xml`.
5. Bundle the editor in `static/lib/` (no CDNs: the module must work offline)
   and check its license allows redistribution.

---

## Licensing

| Component | License | Notes |
|---|---|---|
| This module | LGPL-3 | |
| SuperDoc 1.47.2 | **AGPL-3.0** | Combining it with this module puts the distributed product under AGPL terms, or buy SuperDoc's commercial license. |
| BetterOffice 0.5.1 + fonts | Apache-2.0, OFL-1.1 | Free to bundle and redistribute. |
| PDF.js 6.4.299 | Apache-2.0 | Free to bundle and redistribute. |
| React 19 | MIT | Inside the BetterOffice bundles. |
| ONLYOFFICE Docs | AGPL-3.0 / commercial | Separate server, not shipped with this module. |

**Do not upgrade SuperDoc to 2.x without legal review:** 2.x depends on the
proprietary `@superdoc/docx-engine`, which may not be redistributed.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| **Edit in Browser** button missing | File type not supported, no write access, or locked by another user. Hard-refresh the page (Ctrl+Shift+R). After pulling code, upgrade the module and restart Odoo. |
| "This document was changed by someone else…" | Someone saved after you opened it. Go back and reopen the editor; your unsaved changes are lost. |
| "This document is locked by …" | Another user locked it in DMS. Ask them to unlock it. |
| Editor shows "Unable to open document" | Open the browser console (F12) for details. Check that `/document_editor/static/lib/...` files load (not 404). |
| XLSX/PPTX stuck loading | The browser must load module workers and `.wasm` files. Check the console; old browsers and strict proxies can block them. |
| Module fails to load: `No module named 'jwt'` | `pip install PyJWT requests` (see Installation). |
| Save fails with 413 | The file is larger than 100 MB (`MAX_FILE_SIZE` in `controllers/browser_editor.py`). |
