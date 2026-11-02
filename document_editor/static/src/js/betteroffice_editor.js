import { startEditorPage } from "./editor_page.js";

const { format, fontFamilies } = document.getElementById("editor-app").dataset;

startEditorPage(async (options) => {
    // Built by document_editor/frontend; one bundle per format.
    const { mountEditor } = await import(
        `/document_editor/static/lib/betteroffice/${format}-editor.js`
    );

    let editorApi = null;

    await mountEditor(options.container, {
        // PPTX only: font families used by the deck.
        ...(fontFamilies && { fontFamilies: JSON.parse(fontFamilies) }),
        file: options.bytes,
        fileName: options.fileName,
        style: { height: "100%" },
        downloadOnSave: false,
        onReady: (api) => {
            editorApi = api;
            options.onReady();
        },
        onChange: () => options.onChange(),
        // Toolbar save and Ctrl+S: upload to Odoo instead of downloading.
        onSaveRequest: () => {
            options.onSaveRequest();
            return false;
        },
        onError: (error) => options.onError(error),
    });

    return async () => {
        if (!editorApi) {
            throw new Error("The editor is still loading.");
        }

        const bytes = await editorApi.save();

        if (!bytes) {
            throw new Error("The editor could not export the document.");
        }

        return new Blob([bytes], { type: options.mimetype });
    };
});
