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

## Installation (step by step)

This guide is written so anyone can follow it. You will add two add-ons
(Odoo calls them "modules") to Odoo 20. Install **DMS first**, then
**Document Editor**, because the editor needs DMS to work.

| Folder name | Name shown in Odoo Apps | What it does |
|---|---|---|
| `dms` | Document Management System | Adds a **Documents** menu to store, organise and share files in folders. |
| `document_editor` | DMS Editor | Adds an **Edit in Browser** button to edit Word, Excel, PowerPoint and PDF files inside Odoo. |

> **What is a command?** A line of text you type into a black window called the
> **terminal** (on Windows: Command Prompt or PowerShell), then press **Enter**.
> Copy each command exactly as written.

### Before you start

- [ ] Your Odoo is **version 20** (Community). Other versions will not work.
- [ ] You can log in to Odoo as an **administrator**.
- [ ] You can open files on the computer or server where Odoo runs.
- [ ] You are allowed to **restart Odoo**. Users are logged out for about a minute, so pick a quiet time.

### Step 1: Download the two folders

Pick **one** way.

**Way A, no commands (easiest):**

1. Open <https://github.com/PranisHlama/intern-individual-projects> in your browser.
2. Switch the branch button (top left, it may say `main`) to **DMS**.
3. Click the green **Code** button, then **Download ZIP**.
4. Open the ZIP file. Inside you will find the `dms` and `document_editor` folders.

**Way B, with a command:**

```bash
git clone -b DMS https://github.com/PranisHlama/intern-individual-projects.git
```

This creates a folder `intern-individual-projects` with `dms` and `document_editor` inside it.

### Step 2: Put the folders where Odoo can find them

1. Find your **addons folder**. Open Odoo's settings file (usually `odoo.conf`)
   in a text editor such as Notepad and look for the line starting with
   `addons_path =`. It lists one or more folders separated by commas. Pick one
   you can write to, for example `custom_addons`.
2. Copy the **whole** `dms` folder and the **whole** `document_editor` folder
   into that addons folder (the folders themselves, not just the files inside).
3. Check: in the addons folder you should see `dms` and `document_editor` side
   by side, and inside each one a file called `__manifest__.py`.
4. Install two small helper programs that Document Editor needs:

   ```bash
   pip install PyJWT requests
   ```

   "Successfully installed" or "Requirement already satisfied" means it worked.
   If Odoo uses its own Python (common with the Windows installer), run this
   with that Python instead; ask your server admin if unsure.

### Step 3: Restart Odoo

Odoo only notices new folders after a restart.

| How Odoo runs | What to do |
|---|---|
| Windows installer | Press the Windows key, type **Services**, open it, find **odoo-server**, right-click it and choose **Restart**. |
| Linux server | `sudo systemctl restart odoo` |
| Docker | `docker restart <your Odoo container name>` |
| Started by hand in a terminal | Click that terminal, press **Ctrl + C** to stop it, then run the same start command again. |

Wait about a minute, then open Odoo and log in as administrator.

### Step 4: Install both add-ons from the Apps screen

1. Turn on **Developer Mode**: go to **Settings**, scroll to the bottom and
   click **Activate the developer mode**.
2. Open the **Apps** menu.
3. Click **Update Apps List** in the top bar, then **Update** in the pop-up.
4. In the search box, remove the **Apps** filter (click the small x on it),
   then type `Document Management System`.
5. Click **Activate** on **Document Management System**. Wait for the page to reload.
6. Search for `DMS Editor` and click **Activate** on it.

**Prefer commands?** Step 4 can be replaced by this one command (`mydb` = your
database name), followed by a restart as in Step 3:

```bash
odoo-bin -d mydb -i dms,document_editor --stop-after-init
```

### Step 5: Check that it works

1. Refresh the page. A **Documents** menu appears on the Odoo home screen.
2. Open **Documents → Files** and open a `.docx`, `.xlsx`, `.pptx` or `.pdf`
   file (upload one first if there are none).
3. Click **Edit in Browser (Beta)**, change something and click **Save**
   (or press **Ctrl + S**). You should see **Saved**.

Nothing else is needed for **Edit in Browser**. Node.js is *not* needed on the
server; the editor files are already built and committed in `static/lib/`.

### If something goes wrong during install

| What you see | What to do |
|---|---|
| The add-on doesn't show up in Apps | Click **Update Apps List** again and remove the **Apps** filter. Check the folders sit directly inside the addons folder (Step 2.3), not inside an extra folder. Restart Odoo. |
| Error mentioning `jwt` or `requests` | Repeat the `pip install` command in Step 2.4, then restart Odoo. |
| DMS Editor won't install and mentions `dms` | Install **Document Management System** first, then DMS Editor. |
| Odoo won't start after copying | You may not be on Odoo 20. Remove the two folders, restart, and check your version. |

### Upgrading after pulling new code

```bash
odoo-bin -d <database> -u dms,document_editor --stop-after-init
```

Then restart Odoo; new Python routes only load after a restart.

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
