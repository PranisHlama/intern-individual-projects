// Load with this file's ?v= so a cached old editor_page.js is never reused.
const { startEditorPage } = await import(
    `./editor_page.js${new URL(import.meta.url).search}`
);

startEditorPage(async (options) => {
    if (typeof SuperDoc === "undefined") {
        throw new Error("SuperDoc library is not available.");
    }

    let isReady = false;

    const superdoc = new SuperDoc({
        selector: options.container,
        toolbar: "#superdoc-toolbar",
        document: new File([options.bytes], options.fileName, {
            type: options.mimetype,
        }),
        documentMode: "editing",
        user: options.user,
        // Do not send document-open events to SuperDoc's servers.
        telemetry: {
            enabled: false,
        },
        onReady: () => {
            isReady = true;
            options.onReady();
        },
        onEditorUpdate: () => {
            if (isReady) {
                options.onChange();
            }
        },
        onContentError: ({ error }) => {
            console.error("SuperDoc content error:", error);
            options.onFatalError(
                "The document could not be read by SuperDoc."
            );
        },
        onException: ({ error }) => options.onError(error),
    });

    return () => superdoc.export({
        exportType: ["docx"],
        isFinalDoc: false,
        triggerDownload: false,
    });
});
