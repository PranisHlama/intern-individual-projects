import {
    Component,
    markup,
    proxy,
    onMounted,
    onWillUnmount,
} from "@odoo/owl";

import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";


function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "\u0026amp;")
        .replaceAll("<", "\u0026lt;")
        .replaceAll(">", "\u0026gt;")
        .replaceAll('"', "\u0026quot;")
        .replaceAll("'", "\u0026#039;");
}


function safeUrl(url) {
    if (
        /^https?:\/\//i.test(url) ||
        /^mailto:/i.test(url)
    ) {
        return escapeHtml(url);
    }

    return "#";
}


function inlineMarkdown(value) {
    let text = escapeHtml(value);

    const codeParts = [];

    text = text.replace(
        /`([^`]+)`/g,
        (_, code) => {
            const index = codeParts.length;

            codeParts.push(
                "<code>" + code + "</code>",
            );

            return "@@CODE" + index + "@@";
        },
    );

    text = text.replace(
        /\[([^\]]+)\]\(([^)\s]+)\)/g,
        (_, label, url) => {
            return (
                '<a href="' + safeUrl(url) + '" ' +
                'target="_blank" ' +
                'rel="noopener noreferrer">' +
                label + "</a>"
            );
        },
    );

    text = text.replace(
        /\*\*(.+?)\*\*/g,
        "<strong>$1</strong>",
    );

    text = text.replace(
        /(?<!\*)\*([^*]+)\*(?!\*)/g,
        "<em>$1</em>",
    );

    text = text.replace(
        /~~(.+?)~~/g,
        "<del>$1</del>",
    );

    text = text.replace(
        /@@CODE(\d+)@@/g,
        (_, index) =>
            codeParts[Number(index)],
    );

    return text;
}


function isTableSeparator(line) {
    const cells = line
        .trim()
        .replace(/^\|/, "")
        .replace(/\|$/, "")
        .split("|");

    return (
        cells.length > 0 &&
        cells.every((cell) =>
            /^:?-{3,}:?$/.test(
                cell.trim(),
            ),
        )
    );
}


function splitTableRow(line) {
    return line
        .trim()
        .replace(/^\|/, "")
        .replace(/\|$/, "")
        .split("|")
        .map((cell) => cell.trim());
}


function renderTable(lines, start) {
    const header =
        splitTableRow(lines[start]);

    const body = [];

    let index = start + 2;

    while (
        index < lines.length &&
        lines[index].trim().startsWith("|")
    ) {
        body.push(
            splitTableRow(lines[index]),
        );

        index++;
    }

    let html = '<div class="ai_chat_table_wrap"><table class="ai_chat_table"><thead><tr>';

    for (const cell of header) {
        html += '<th>' + inlineMarkdown(cell) + '</th>';
    }

    html += '</tr></thead><tbody>';

    for (const row of body) {
        html += "<tr>";

        for (
            let i = 0;
            i < header.length;
            i++
        ) {
            html += '<td>' + inlineMarkdown(row[i] ?? "") + '</td>';
        }

        html += "</tr>";
    }

    html += '</tbody></table></div>';

    return {
        html,
        nextIndex: index,
    };
}


function renderMarkdown(source) {
    const lines =
        String(source)
            .replaceAll("\r\n", "\n")
            .split("\n");

    const output = [];

    let index = 0;

    while (index < lines.length) {
        const line = lines[index];

        if (!line.trim()) {
            index++;
            continue;
        }

        /*
         * Code block
         */
        if (
            line.trim().startsWith("```")
        ) {
            const language =
                line.trim()
                    .slice(3)
                    .trim();

            const code = [];

            index++;

            while (
                index < lines.length &&
                !lines[index]
                    .trim()
                    .startsWith("```")
            ) {
                code.push(lines[index]);
                index++;
            }

            if (index < lines.length) {
                index++;
            }

            const languageClass =
                language
                    ? ' class="language-' + escapeHtml(language) + '"'
                    : "";

            output.push(
                '<pre class="ai_chat_code_block">' +
                '<code' + languageClass + '>' +
                escapeHtml(code.join("\n")) +
                '</code></pre>',
            );

            continue;
        }

        /*
         * Table
         */
        if (
            index + 1 < lines.length &&
            line.trim().startsWith("|") &&
            isTableSeparator(lines[index + 1])
        ) {
            const table = renderTable(lines, index);
            output.push(table.html);
            index = table.nextIndex;
            continue;
        }

        /*
         * Heading
         */
        const heading = line.match(/^(#{1,6})\s+(.+)$/);

        if (heading) {
            const level = heading[1].length;
            output.push('<h' + level + '>' + inlineMarkdown(heading[2]) + '</h' + level + '>');
            index++;
            continue;
        }

        /*
         * Unordered list
         */
        if (/^\s*[-*+]\s+/.test(line)) {
            const items = [];

            while (
                index < lines.length &&
                /^\s*[-*+]\s+/.test(lines[index])
            ) {
                items.push(lines[index].replace(/^\s*[-*+]\s+/, ""));
                index++;
            }

            output.push("<ul>" + items.map(item => '<li>' + inlineMarkdown(item) + '</li>').join("") + "</ul>");
            continue;
        }

        /*
         * Ordered list
         */
        if (/^\s*\d+\.\s+/.test(line)) {
            const items = [];

            while (
                index < lines.length &&
                /^\s*\d+\.\s+/.test(lines[index])
            ) {
                items.push(lines[index].replace(/^\s*\d+\.\s+/, ""));
                index++;
            }

            output.push("<ol>" + items.map(item => '<li>' + inlineMarkdown(item) + '</li>').join("") + "</ol>");
            continue;
        }

        /*
         * Blockquote
         */
        if (/^\s*>\s?/.test(line)) {
            const quote = [];

            while (
                index < lines.length &&
                /^\s*>\s?/.test(lines[index])
            ) {
                quote.push(lines[index].replace(/^\s*>\s?/, ""));
                index++;
            }

            output.push('<blockquote>' + inlineMarkdown(quote.join("\n")) + '</blockquote>');
            continue;
        }

        /*
         * Horizontal rule
         */
        if (/^(\s*[-*_]){3,}\s*$/.test(line)) {
            output.push("<hr>");
            index++;
            continue;
        }

        /*
         * Paragraph
         */
        const paragraph = [line];
        index++;

        while (
            index < lines.length &&
            lines[index].trim() &&
            !/^#{1,6}\s+/.test(lines[index]) &&
            !/^\s*[-*+]\s+/.test(lines[index]) &&
            !/^\s*\d+\.\s+/.test(lines[index]) &&
            !/^\s*>\s?/.test(lines[index]) &&
            !lines[index].trim().startsWith("```")
        ) {
            paragraph.push(lines[index]);
            index++;
        }

        output.push('<p>' + inlineMarkdown(paragraph.join("\n").replaceAll("\n", "<br>")) + '</p>');
    }

    return markup(output.join(""));
}


const STORAGE_KEY = "ai_chat_model_preference";


export class AIChatSystray
    extends Component
{
    static template = "ai_chat.AIChatSystray";

    setup() {
        this.state = proxy({
            open: false,
            loading: false,
            loadingHistory: false,
            loadingModels: false,
            confirmingNew: false,
            creatingNew: false,
            loaded: false,
            modelsLoaded: false,
            message: "",
            messages: [],
            models: [],
            selectedModelId: null,
        });

        onMounted(() => {
            this.loadModels();
        });
    }

    toggle() {
        if (this.state.open) {
            this.state.open = false;
            return;
        }
        this.state.open = true;
        if (!this.state.loaded) {
            this.loadCurrent();
        }
    }

    close() {
        this.state.open = false;
    }

    onInput(ev) {
        this.state.message = ev.target.value;
    }

    renderMessage(content) {
        return renderMarkdown(content);
    }

    scrollToBottom() {
        requestAnimationFrame(() => {
            const container = this.el?.querySelector(".ai_chat_messages");
            if (!container) return;
            container.scrollTop = container.scrollHeight;
        });
    }

    async loadModels() {
        if (this.state.loadingModels) return;
        this.state.loadingModels = true;
        try {
            const data = await rpc("/ai_chat/models", {}, { silent: true });
            if (data.error) throw new Error(data.error);
            this.state.models = data.models ?? [];
            const savedModelId = this.getSavedModelPreference();
            if (savedModelId && this.state.models.some(m => m.modelId === savedModelId)) {
                this.state.selectedModelId = savedModelId;
            } else {
                // Try backend preference if no localStorage
                await this.loadModelPreferenceFromBackend();
                if (!this.state.selectedModelId && this.state.models.length > 0) {
                    const defaultModel = this.state.models.find(m => m.isDefault) ?? this.state.models[0];
                    this.state.selectedModelId = defaultModel.modelId;
                }
            }
            this.state.modelsLoaded = true;
        } catch (error) {
            console.error("Failed to load AI models:", error);
            this.state.models = [];
            this.state.modelsLoaded = true;
        } finally {
            this.state.loadingModels = false;
        }
    }

    getSavedModelPreference() {
        try {
            const stored = localStorage.getItem(STORAGE_KEY);
            return stored ? JSON.parse(stored).modelId : null;
        } catch {
            return null;
        }
    }

    saveModelPreference(modelId) {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify({ modelId, timestamp: Date.now() }));
        } catch {
            // Ignore
        }
    }

    async loadModelPreferenceFromBackend() {
        try {
            const data = await rpc("/ai_chat/model/preference", {}, { silent: true });
            if (data.modelId && this.state.models.some(m => m.modelId === data.modelId)) {
                this.state.selectedModelId = data.modelId;
                this.saveModelPreference(data.modelId);
            }
        } catch {
            // Ignore, use localStorage
        }
    }

    async setModelPreference(modelId) {
        if (!modelId) return;
        this.state.selectedModelId = modelId;
        this.saveModelPreference(modelId);
        try {
            await rpc("/ai_chat/model/preference/set", { model_id: modelId }, { silent: true });
        } catch {
            // Ignore, localStorage is source of truth
        }
    }

    onModelSelect(modelId) {
        this.setModelPreference(modelId);
    }

    async loadCurrent() {
        if (this.state.loadingHistory) return;
        this.state.loadingHistory = true;
        try {
            const data = await rpc("/ai_chat/current", {}, { silent: true });
            if (data.error) throw new Error(data.error);
            this.state.messages = (data.messages ?? []).filter(m => (m.role === "user" || m.role === "assistant") && typeof m.content === "string");
            this.state.loaded = true;
            // Don't override localStorage preference with backend
            this.scrollToBottom();
        } catch (error) {
            console.error("Failed to load AI chat:", error);
            this.state.messages = [{ role: "assistant", content: "Unable to load the current conversation." }];
        } finally {
            this.state.loadingHistory = false;
        }
    }

    askNewChat() {
        if (this.state.loading || this.state.creatingNew) return;
        this.state.confirmingNew = true;
    }

    cancelNewChat() {
        this.state.confirmingNew = false;
    }

    async confirmNewChat() {
        if (this.state.creatingNew) return;
        this.state.creatingNew = true;
        try {
            const data = await rpc("/ai_chat/new", {}, { silent: true });
            if (data.error) throw new Error(data.error);
            this.state.messages = [];
            this.state.message = "";
            this.state.confirmingNew = false;
            this.state.loaded = true;
            this.scrollToBottom();
        } catch (error) {
            console.error("Failed to create new chat:", error);
            this.state.messages.push({ role: "assistant", content: "Unable to start a new chat." });
        } finally {
            this.state.creatingNew = false;
        }
    }

    async send() {
        const message = this.state.message.trim();
        if (!message || this.state.loading || this.state.creatingNew) return;
        this.state.messages.push({ role: "user", content: message });
        this.state.message = "";
        this.state.loading = true;
        this.scrollToBottom();
        try {
            const data = await rpc("/ai_chat/chat", { message, model_id: this.state.selectedModelId }, { silent: true });
            if (data.error) throw new Error(data.error);
            this.state.messages.push({ role: "assistant", content: data.reply });
            this.scrollToBottom();
        } catch (error) {
            console.error("AI Chat request failed:", error);
            this.state.messages.push({ role: "assistant", content: error instanceof Error ? error.message : "Sorry, something went wrong." });
            this.scrollToBottom();
        } finally {
            this.state.loading = false;
        }
    }

    onKeydown(ev) {
        if (ev.key === "Enter" && !ev.shiftKey && !ev.ctrlKey && !ev.metaKey && !ev.altKey) {
            ev.preventDefault();
            this.send();
        }
    }
}


registry.category("systray").add("ai_chat.AIChatSystray", { Component: AIChatSystray }, { sequence: 40 });