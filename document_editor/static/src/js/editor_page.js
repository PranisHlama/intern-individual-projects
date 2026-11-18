// Shared page logic for the browser editors (SuperDoc, BetterOffice):
// loads the file from Odoo, tracks unsaved changes and uploads saves.
//
// `openEditor(options)` mounts a specific editor and returns an async
// function that exports the edited document as a Blob.

export async function startEditorPage(openEditor) {
    const app = document.getElementById("editor-app");
    const container = document.getElementById("editor-container");
    const saveButton = document.getElementById("editor-save");
    const backButton = document.getElementById("back-to-odoo");
    const statusLabel = document.getElementById("editor-status");

    const {
        contentUrl,
        saveUrl,
        csrfToken,
        fileName,
        userName,
        userEmail,
        returnUrl,
    } = app.dataset;

    // Checksum of the version the user is editing. Sent with every
    // save so the server can refuse to overwrite newer changes.
    let checksum = app.dataset.checksum;

    let exportFile = null;
    let hasUnsavedChanges = false;
    let isSaving = false;

    const setStatus = (text, isError = false) => {
        statusLabel.textContent = text;
        statusLabel.classList.toggle("browser-editor-status-error", isError);
    };

    const showFatalError = (message) => {
        const box = document.createElement("div");
        box.className = "browser-editor-error";

        const title = document.createElement("h2");
        title.textContent = "Unable to open document";

        const text = document.createElement("p");
        text.textContent = message;

        box.append(title, text);
        container.replaceChildren(box);
        setStatus("Error", true);
    };

    const setUnsaved = (value) => {
        hasUnsavedChanges = value;
        saveButton.disabled = !value || isSaving;

        if (value) {
            setStatus("Unsaved changes");
        }
    };

    const save = async () => {
        if (!exportFile || isSaving || !hasUnsavedChanges) {
            return;
        }

        isSaving = true;
        saveButton.disabled = true;
        setStatus("Saving…");

        try {
            // Export in memory; nothing is downloaded to the user's computer.
            const blob = await exportFile();

            const formData = new FormData();
            formData.append("file", blob, fileName);
            formData.append("checksum", checksum);
            formData.append("csrf_token", csrfToken);

            const response = await fetch(saveUrl, {
                method: "POST",
                body: formData,
                credentials: "same-origin",
            });

            let result = {};

            try {
                result = await response.json();
            } catch {
                // Non-JSON error page (e.g. session expired).
            }

            if (!response.ok) {
                throw new Error(
                    result.error || `Save failed (${response.status}).`
                );
            }

            checksum = result.checksum || checksum;
            isSaving = false;
            setUnsaved(false);
            setStatus(result.saved ? "Saved" : "No changes to save");
        } catch (error) {
            console.error("Save failed:", error);
            isSaving = false;
            saveButton.disabled = !hasUnsavedChanges;
            setStatus(error.message, true);
        }
    };

    saveButton.addEventListener("click", save);

    document.addEventListener("keydown", (event) => {
        if ((event.ctrlKey || event.metaKey) && event.key === "s") {
            event.preventDefault();
            save();
        }
    });

    window.addEventListener("beforeunload", (event) => {
        if (hasUnsavedChanges) {
            event.preventDefault();
            event.returnValue = "";
        }
    });

    backButton.addEventListener("click", () => {
        if (
            hasUnsavedChanges
            && !window.confirm(
                "You have unsaved changes. Leave without saving?"
            )
        ) {
            return;
        }

        hasUnsavedChanges = false;
        window.location.href = returnUrl;
    });

    try {
        const response = await fetch(contentUrl, {
            credentials: "same-origin",
            cache: "no-store",
        });

        if (!response.ok) {
            throw new Error(
                (await response.text())
                || `Document request failed (${response.status}).`
            );
        }

        exportFile = await openEditor({
            container,
            bytes: new Uint8Array(await response.arrayBuffer()),
            fileName,
            mimetype: response.headers.get("Content-Type"),
            user: { name: userName, email: userEmail },
            onReady: () => setStatus("Ready"),
            onChange: () => setUnsaved(true),
            onSaveRequest: save,
            onError: (error) => {
                console.error("Editor error:", error);
                setStatus("Editor error – see browser console", true);
            },
            onFatalError: showFatalError,
        });
    } catch (error) {
        console.error("Editor initialization failed:", error);
        showFatalError(error.message);
    }
}
