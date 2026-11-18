import { createElement } from "react";
import { createRoot } from "react-dom/client";
import { PptxEditor } from "@betteroffice/pptx-react";
import {
    loadBundledFontBytes,
    resolveBundledFamilyFace,
} from "@betteroffice/fonts";

// Office defaults every deck can fall back to.
const BASE_FAMILIES = ["Calibri", "Arial"];

// The editor needs font bytes up front. Load the open, metric-compatible
// face for each family the deck uses (e.g. Calibri -> Carlito).
async function loadFonts(families) {
    const loads = [];

    for (const family of new Set([...BASE_FAMILIES, ...families])) {
        for (const bold of [false, true]) {
            for (const italic of [false, true]) {
                const face = resolveBundledFamilyFace(family, bold, italic);

                if (face) {
                    loads.push(
                        loadBundledFontBytes(face).then((bytes) => ({
                            family,
                            bold,
                            italic,
                            bytes: new Uint8Array(bytes),
                        }))
                    );
                }
            }
        }
    }

    // A missing face only degrades layout; do not block opening the deck.
    const results = await Promise.allSettled(loads);

    return results
        .filter((result) => result.status === "fulfilled")
        .map((result) => result.value);
}

export async function mountEditor(element, { fontFamilies = [], ...props }) {
    const fonts = await loadFonts(fontFamilies);

    createRoot(element).render(createElement(PptxEditor, { ...props, fonts }));
}
