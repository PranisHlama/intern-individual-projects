import { createElement } from "react";
import { createRoot } from "react-dom/client";
import { XlsxEditor } from "@betteroffice/xlsx-react";

export function mountEditor(element, props) {
    createRoot(element).render(createElement(XlsxEditor, props));
}
