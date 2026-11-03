// Load with this file's ?v= so a cached old editor_page.js is never reused.
const { startEditorPage } = await import(
    `./editor_page.js${new URL(import.meta.url).search}`
);

// Empty `file` so the viewer starts blank; the document is opened below.
const VIEWER_URL = "/document_editor/static/lib/pdfjs/web/viewer.html?file=";
const VIEWER_CSS = "/document_editor/static/src/css/pdfjs_viewer.css";

startEditorPage(async (options) => {
    const iframe = document.createElement("iframe");
    iframe.className = "browser-editor-frame";
    iframe.title = options.fileName;

    const loaded = new Promise((resolve) => {
        iframe.addEventListener("load", resolve, { once: true });
    });

    // The viewer announces itself to this page before starting, which is
    // the documented moment to change its options.
    document.addEventListener("webviewerloaded", (event) => {
        const appOptions = event.detail.source.PDFViewerApplicationOptions;

        // Page manager editing: delete, reorder, merge ("Add file") and
        // split ("Export selected"). Still marked experimental in PDF.js.
        appOptions.set("enableSplitMerge", true);
    }, { once: true });
    iframe.src = VIEWER_URL;
    options.container.replaceChildren(iframe);
    await loaded;

    const viewer = iframe.contentWindow;
    const app = viewer.PDFViewerApplication;
    await app.initializedPromise;

    const style = viewer.document.createElement("link");
    style.rel = "stylesheet";
    style.href = VIEWER_CSS;
    viewer.document.head.append(style);

    // Dropping a PDF on the page would open it in place of this document.
    // Drops inside the page manager ("Add file" to merge) still work.
    viewer.addEventListener("drop", (event) => {
        if (!event.target.closest?.("#viewsManager")) {
            event.preventDefault();
            event.stopPropagation();
        }
    }, true);

    // Every PDF.js save ends in downloadManager.download(). Full-document
    // saves go to Odoo instead; only the page manager's "Export selected"
    // (a split into a new file) stays a normal download.
    let pendingExport = null;
    let isExportingSelection = false;
    const download = app.downloadManager.download.bind(app.downloadManager);
    const downloadOrSave = app.downloadOrSave.bind(app);

    app.eventBus.on("saveextractedpages", () => {
        isExportingSelection = true;
    });

    app.downloadManager.download = (data, url, filename) => {
        if (isExportingSelection) {
            isExportingSelection = false;
            download(data, url, filename);
        } else if (pendingExport) {
            pendingExport(data);
            pendingExport = null;
        } else {
            // Ctrl+S or the menu inside the viewer: save to Odoo.
            options.onSaveRequest();
        }
    };

    let isModified = false;

    const openDocument = async (data) => {
        isModified = false;
        await app.open({ data });
    };

    await openDocument(options.bytes);
    options.onReady();

    // PDF.js has no single "changed" event; watch its own change flags
    // (annotations and forms, page manager edits, merged files).
    setInterval(() => {
        const modified = Boolean(
            app._annotationStorageModified
            || app._mergedDocumentNeedsSaving
            || app.pdfThumbnailViewer?.hasStructuralChanges()
        );

        if (modified && !isModified) {
            options.onChange();
        }

        isModified = modified;
    }, 500);

    return async () => {
        const data = await new Promise((resolve, reject) => {
            pendingExport = resolve;
            isExportingSelection = false;

            // Exports annotations, form values and page changes, then
            // hands the bytes to downloadManager.download above.
            downloadOrSave().then(() => {
                if (pendingExport) {
                    pendingExport = null;
                    reject(new Error("PDF.js could not export the document."));
                }
            }, reject);
        });

        // Blob copies the bytes; reopening the viewer may take ownership.
        const blob = new Blob([data], { type: options.mimetype });
        const page = app.page;

        // Reload the exported result so the viewer's change flags reset
        // and it shows exactly what is being saved.
        app.pdfDocument?.annotationStorage.resetModified();
        app.eventBus.on("pagesinit", () => {
            app.page = Math.min(page, app.pagesCount);
        }, { once: true });
        await openDocument(data);

        return blob;
    };
});
