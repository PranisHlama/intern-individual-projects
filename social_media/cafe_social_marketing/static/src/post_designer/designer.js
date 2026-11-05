/** @odoo-module **/

import { Component, onMounted, proxy, useProps } from "@odoo/owl";
import { standardActionServiceProps } from "@web/webclient/actions/action_plugin";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const SIDE = 1080;
let nextCanvasId = 0;
const BLOCK_TYPE = "application/x-cafe-designer-block";
const textLayer = (text, x, y, size, color) => ({
    kind: "text", text, x, y, size, color,
    font: "sans", bold: true, italic: false, align: "left", lineHeight: 122,
});
const FONT_FAMILIES = { sans: "Arial, sans-serif", serif: "Georgia, serif", mono: "monospace" };
const copyDesign = (design) => ({ ...design, layers: design.layers.map(layer => ({ ...layer })) });
const sameDesign = (a, b) => a.color === b.color && a.background === b.background
    && a.layers.length === b.layers.length && a.layers.every((layer, i) => {
        const other = b.layers[i];
        return Object.keys(layer).length === Object.keys(other).length
            && Object.keys(layer).every(key => layer[key] === other[key]);
    });
const normalizeDesign = (design) => ({ ...design, version: 2,
    layers: design.layers.map(layer => layer.kind === "text" ? {
        font: "sans", bold: true, italic: false, align: "left", lineHeight: 122, ...layer,
    } : { ...layer }),
});
const TEMPLATES = [
    { id: "weekend", label: "Weekend Offer", color: "#233b32", layers: [
        textLayer("THE WEEKEND SPECIAL", 84, 84, 34, "#d7ce9d"),
        textLayer("Coffee\nwith friends", 78, 198, 118, "#fff5e3"),
        textLayer("20% OFF", 82, 635, 91, "#f5c27b"),
        textLayer("SATURDAY & SUNDAY  /  DINE IN", 84, 917, 35, "#d7ce9d"),
    ] },
    { id: "menu", label: "New Menu Item", color: "#f7dfbd", layers: [
        textLayer("FRESH ON THE MENU", 82, 83, 36, "#884b35"),
        textLayer("Iced\nCaramel Latte", 76, 190, 112, "#47291e"),
        textLayer("ESPRESSO  /  MILK  /  CARAMEL", 83, 654, 34, "#884b35"),
        textLayer("AVAILABLE NOW", 82, 897, 53, "#47291e"),
    ] },
    { id: "branch", label: "Branch Announcement", color: "#572d43", layers: [
        textLayer("A NEW PLACE TO SIP", 83, 82, 35, "#ffd4b4"),
        textLayer("Hello,\nLalitpur!", 75, 214, 143, "#fff6ec"),
        textLayer("OUR NEW BRANCH IS OPEN", 82, 693, 43, "#ffd4b4"),
        textLayer("COME SAY HI", 82, 917, 34, "#fff6ec"),
    ] },
];
const MODEL = "cafe.social.post";
const initialDesign = () => ({ version: 2, color: "#f4e8d4", background: "", layers: [] });
const clamp = (n, min, max) => Math.max(min, Math.min(max, Math.round(n)));
const srcFor = (data) => `data:image/${data.startsWith("/9j/") ? "jpeg" : "png"};base64,${data}`;

export class PostDesigner extends Component {
    static template = "cafe_social_marketing.PostDesigner";
    props = useProps(standardActionServiceProps);

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.postId = this.props.action.params.post_id;
        this.canvasId = "o_cafe_designer_canvas_" + ++nextCanvasId;
        this.templates = TEMPLATES;
        this.state = proxy({
            tab: "blocks", previews: {},
            design: initialDesign(), selected: -1, loading: true, saving: false,
            importing: false, dirty: false, failed: false, replace: false,
            hasOtherMedia: false, error: "", undoCount: 0, redoCount: 0, interacting: false,
        });
        this.images = new Map();
        this.history = [];
        this.historyIndex = -1;
        this.historyGroup = null;
        onMounted(() => {
            for (const preset of this.templates) {
                const thumbnail = document.createElement("canvas");
                thumbnail.width = thumbnail.height = 216;
                this.draw(thumbnail, false, preset);
                this.state.previews[preset.id] = thumbnail.toDataURL("image/png");
            }
            return this.load();
        });
    }

    get canvasElement() {
        return document.getElementById(this.canvasId);
    }

    setTab(tab) {
        if (["blocks", "customize", "design"].includes(tab)) this.state.tab = tab;
    }

    chooseTemplate(id) {
        if (this.busy) return;
        const preset = this.templates.find(item => item.id === id);
        if (!preset) return;
        const existing = this.state.design;
        if ((this.state.dirty || existing.background || existing.layers.length)
            && !window.confirm("Replace the current canvas with this template? The post changes only when you save.")) return;
        this.state.design = {
            version: 2, color: preset.color, background: "",
            layers: preset.layers.map(layer => ({ ...layer })),
        };
        this.state.selected = 1;
        this.state.tab = "customize";
        this.pruneImages();
        this.changed();
    }

    moveLayer(delta) {
        const i = this.state.selected;
        const j = i + delta;
        const layers = this.state.design.layers;
        if (this.busy || i < 0 || j < 0 || j >= layers.length) return;
        const [layer] = layers.splice(i, 1);
        layers.splice(j, 0, layer);
        this.select(j);
        this.changed();
    }

    dragBlock(event, kind) {
        if (this.busy || this.state.design.layers.length >= 8) {
            event.preventDefault();
            return;
        }
        event.dataTransfer.setData(BLOCK_TYPE, kind);
        event.dataTransfer.effectAllowed = "copy";
    }

    allowBlockDrop(event) {
        if (!this.busy && Array.from(event.dataTransfer.types).includes(BLOCK_TYPE)) {
            event.preventDefault();
            event.dataTransfer.dropEffect = "copy";
        }
    }

    dropBlock(event) {
        const kind = event.dataTransfer.getData(BLOCK_TYPE);
        if (!["headline", "offer"].includes(kind)) return;
        event.preventDefault();
        this.addText(kind, this.point(event));
    }

    get active() {
        return this.state.design.layers[this.state.selected];
    }

    get busy() {
        return this.state.loading || this.state.saving || this.state.importing || this.state.failed;
    }

    async load() {
        try {
            const data = await this.orm.call(MODEL, "get_post_designer", [[this.postId]]);
            this.revision = data.revision;
            this.state.hasOtherMedia = data.has_other_media;
            if (data.document) {
                const design = JSON.parse(data.document);
                await Promise.all([design.background, ...design.layers.map(l => l.data)]
                    .filter(Boolean).map(asset => this.loadImage(asset)));
                this.state.design = normalizeDesign(design);
            }
            this.savedDesign = copyDesign(this.state.design);
            this.recordHistory();
            this.draw();
        } catch (error) {
            this.state.failed = true;
            this.showError(error, "Could not open the designer.");
        } finally {
            this.state.loading = false;
        }
    }

    showError(error, fallback) {
        this.state.error = error?.data?.message || error?.message || fallback;
    }

    async loadImage(data) {
        if (!this.images.has(data)) {
            const image = new Image();
            image.src = srcFor(data);
            await image.decode();
            this.images.set(data, image);
        }
    }

    changed(group = null, record = true) {
        this.state.dirty = !this.savedDesign || !sameDesign(this.state.design, this.savedDesign);
        if (record) this.recordHistory(group);
        this.draw();
    }

    recordHistory(group = null) {
        const current = this.history[this.historyIndex];
        if (current && sameDesign(current.design, this.state.design)) return;
        const entry = { design: copyDesign(this.state.design), selected: this.state.selected };
        this.history.splice(this.historyIndex + 1);
        if (group && this.historyGroup === group && this.historyIndex > 0) {
            this.history[this.historyIndex] = entry;
        } else {
            this.history.push(entry);
            this.historyIndex++;
        }
        this.historyGroup = group;
        const assetBytes = () => {
            const assets = new Set();
            for (const item of this.history) {
                if (item.design.background) assets.add(item.design.background);
                for (const layer of item.design.layers) if (layer.data) assets.add(layer.data);
            }
            return Array.from(assets).reduce((total, data) => total + data.length, 0);
        };
        while (this.history.length > 30 || (this.history.length > 1 && assetBytes() > 24 * 1024 * 1024)) {
            this.history.shift();
            this.historyIndex--;
        }
        this.syncHistory();
        this.pruneImages();
    }

    syncHistory() {
        this.state.undoCount = this.historyIndex;
        this.state.redoCount = this.history.length - this.historyIndex - 1;
    }

    finishEdit() {
        this.historyGroup = null;
    }

    undo() { this.restoreHistory(-1); }
    redo() { this.restoreHistory(1); }

    restoreHistory(delta) {
        if (this.busy || this.drag) return;
        const index = this.historyIndex + delta;
        if (index < 0 || index >= this.history.length) return;
        this.historyIndex = index;
        const entry = this.history[index];
        this.state.design = copyDesign(entry.design);
        this.state.selected = entry.selected;
        this.historyGroup = null;
        this.syncHistory();
        this.changed(null, false);
    }

    async importImage(event, mode) {
        const background = mode === "background";
        const file = event.target.files?.[0];
        event.target.value = "";
        if (!file || this.busy) {
            return;
        }
        if (!["image/jpeg", "image/png"].includes(file.type) || file.size > 8 * 1024 * 1024) {
            this.state.error = "Choose a JPEG or PNG up to 8 MiB.";
            return;
        }
        if (!background && this.state.design.layers.length >= 8) {
            this.state.error = "Remove a layer before adding another.";
            return;
        }
        this.state.importing = true;
        this.state.error = "";
        const url = URL.createObjectURL(file);
        try {
            const image = new Image();
            image.src = url;
            await image.decode();
            const scale = Math.min(1, (background ? 1440 : 720) / Math.max(image.naturalWidth, image.naturalHeight));
            const canvas = document.createElement("canvas");
            canvas.width = Math.max(1, Math.round(image.naturalWidth * scale));
            canvas.height = Math.max(1, Math.round(image.naturalHeight * scale));
            const context = canvas.getContext("2d");
            if (background) {
                context.fillStyle = "#ffffff";
                context.fillRect(0, 0, canvas.width, canvas.height);
            }
            context.drawImage(image, 0, 0, canvas.width, canvas.height);
            const data = canvas.toDataURL(background ? "image/jpeg" : "image/png", 0.88).split(",")[1];
            if (!data || data.length > 2 * 1024 * 1024 * 4 / 3) {
                throw new Error("Try a smaller image.");
            }
            await this.loadImage(data);
            if (background) {
                this.state.design.background = data;
            } else {
                const photo = mode === "photo";
                const size = photo ? clamp(Math.min(880, 480 * image.naturalWidth / image.naturalHeight), 32, 880) : 185;
                this.state.design.layers.push({
                    kind: "image", data, x: photo ? Math.round((SIDE - size) / 2) : 810,
                    y: photo ? 455 : 78, size,
                });
                this.select(this.state.design.layers.length - 1);
            }
            this.changed();
            this.pruneImages();
        } catch (error) {
            this.showError(error, "Could not load this image.");
        } finally {
            URL.revokeObjectURL(url);
            this.state.importing = false;
        }
    }

    pruneImages() {
        const active = new Set([this.state.design.background, ...this.state.design.layers.map(layer => layer.data)]);
        for (const entry of this.history) {
            active.add(entry.design.background);
            for (const layer of entry.design.layers) active.add(layer.data);
        }
        for (const key of this.images.keys()) {
            if (!active.has(key)) this.images.delete(key);
        }
    }

    addText(kind, point) {
        if (this.busy || this.state.design.layers.length >= 8) return;
        const offer = kind === "offer";
        const hex = this.state.design.color;
        const channels = [1, 3, 5].map(i => Number.parseInt(hex.slice(i, i + 2), 16));
        const dark = channels[0] * 0.299 + channels[1] * 0.587 + channels[2] * 0.114 < 145;
        const color = this.state.design.background || dark ? "#ffffff" : "#273831";
        const [x, y] = point || [82, offer ? 780 : 180];
        this.state.design.layers.push(textLayer(
            offer ? "20% OFF" : "Your headline",
            clamp(x, 0, 960), clamp(y, 0, 960), offer ? 78 : 92, color,
        ));
        this.select(this.state.design.layers.length - 1);
        this.changed();
    }

    select(index) {
        this.finishEdit();
        this.state.selected = index;
        if (index >= 0) this.state.tab = "customize";
        this.draw();
    }

    removeLayer() {
        if (!this.active || this.busy) return;
        this.state.design.layers.splice(this.state.selected, 1);
        this.state.selected = -1;
        this.pruneImages();
        this.changed();
    }

    removeBackground() {
        if (this.busy) return;
        this.state.design.background = "";
        this.pruneImages();
        this.changed();
    }

    updateLayer(event, field) {
        if (!this.active || this.busy) return;
        let value = event.target.value;
        if (field === "size") {
            value = this.active.kind === "text" ? clamp(Number(value), 18, 160) : clamp(Number(value), 32, 1080);
        } else if (field === "x" || field === "y") {
            value = clamp(Number(value), -SIDE, SIDE);
        }
        if (field === "font" && !Object.hasOwn(FONT_FAMILIES, value)) return;
        if (field === "align" && !["left", "center", "right"].includes(value)) return;
        if (field === "lineHeight") value = clamp(Number(value), 100, 180);
        if (typeof value === "number" && !Number.isFinite(value)) return;
        this.active[field] = value;
        this.changed(["text", "color", "size", "lineHeight"].includes(field)
            ? "layer:" + this.state.selected + ":" + field : null);
    }

    setColor(event) {
        this.setDesignColor(event.target.value, "background-color");
    }

    setDesignColor(color, group = null) {
        if (this.busy) return;
        this.state.design.color = color;
        this.changed(group);
    }

    bounds(ctx, layer) {
        if (layer.kind === "image") {
            const img = this.images.get(layer.data);
            return [layer.size, img ? layer.size * img.height / img.width : layer.size];
        }
        ctx.font = `${layer.italic ? "italic " : ""}${layer.bold === false ? "normal" : "bold"} ${layer.size}px ${FONT_FAMILIES[layer.font] || FONT_FAMILIES.sans}`;
        const lines = layer.text.split("\n");
        return [Math.max(24, ...lines.map(line => ctx.measureText(line).width)), lines.length * layer.size * (layer.lineHeight || 122) / 100];
    }

    draw(out = this.canvasElement, selection = true, design = this.state.design) {
        if (!out) return;
        const ctx = out.getContext("2d");
        ctx.setTransform(out.width / SIDE, 0, 0, out.height / SIDE, 0, 0);
        ctx.fillStyle = design.color;
        ctx.fillRect(0, 0, SIDE, SIDE);
        const background = this.images.get(design.background);
        if (background) {
            const scale = Math.max(SIDE / background.width, SIDE / background.height);
            const w = background.width * scale, h = background.height * scale;
            ctx.drawImage(background, (SIDE - w) / 2, (SIDE - h) / 2, w, h);
        }
        for (const layer of design.layers) {
            const [w, h] = this.bounds(ctx, layer);
            if (layer.kind === "image") {
                const img = this.images.get(layer.data);
                if (img) ctx.drawImage(img, layer.x, layer.y, w, h);
            } else {
                ctx.fillStyle = layer.color;
                ctx.textBaseline = "top";
                ctx.textAlign = layer.align || "left";
                const x = layer.x + (layer.align === "center" ? w / 2 : layer.align === "right" ? w : 0);
                layer.text.split("\n").forEach((line, i) => ctx.fillText(line, x,
                    layer.y + i * layer.size * (layer.lineHeight || 122) / 100));
                ctx.textAlign = "left";
            }
        }
        if (selection && this.active) {
            const [w, h] = this.bounds(ctx, this.active);
            ctx.strokeStyle = "#168c85";
            ctx.lineWidth = 4;
            ctx.setLineDash([12, 8]);
            ctx.strokeRect(this.active.x - 5, this.active.y - 5, w + 10, h + 10);
            ctx.setLineDash([]);
            const handleSize = this.handleRadius() * 1.4;
            for (const handle of this.handles(this.active, w, h)) {
                ctx.fillStyle = "#ffffff";
                ctx.fillRect(handle.x - handleSize / 2, handle.y - handleSize / 2, handleSize, handleSize);
                ctx.strokeRect(handle.x - handleSize / 2, handle.y - handleSize / 2, handleSize, handleSize);
            }
        }
    }

    toggleStyle(field) {
        if (this.busy || this.active?.kind !== "text" || !["bold", "italic"].includes(field)) return;
        this.active[field] = !this.active[field];
        this.changed();
    }

    duplicateLayer() {
        if (!this.active || this.busy || this.state.design.layers.length >= 8) return;
        const layer = { ...this.active, x: clamp(this.active.x + 24, -SIDE, SIDE),
            y: clamp(this.active.y + 24, -SIDE, SIDE) };
        this.state.design.layers.splice(this.state.selected + 1, 0, layer);
        this.select(this.state.selected + 1);
        this.changed();
    }

    alignLayer(direction) {
        if (!this.active || this.busy) return;
        const [w, h] = this.bounds(this.canvasElement.getContext("2d"), this.active);
        const positions = { left: ["x", 0], center: ["x", (SIDE - w) / 2], right: ["x", SIDE - w],
            top: ["y", 0], middle: ["y", (SIDE - h) / 2], bottom: ["y", SIDE - h] };
        if (!Object.hasOwn(positions, direction)) return;
        const [axis, value] = positions[direction];
        this.active[axis] = clamp(value, -SIDE, SIDE);
        this.changed();
    }

    keyDown(event) {
        if (this.busy || this.drag || event.target.closest("input, textarea, select, [contenteditable]")) return;
        const modifier = event.ctrlKey || event.metaKey;
        const key = event.key.toLowerCase();
        if (modifier && key === "z") {
            event.preventDefault();
            event.shiftKey ? this.redo() : this.undo();
        } else if (modifier && key === "y") {
            event.preventDefault(); this.redo();
        } else if (this.active && !modifier && !event.altKey) {
            const arrows = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] };
            if (Object.hasOwn(arrows, event.key)) {
                event.preventDefault();
                const step = event.shiftKey ? 10 : 1;
                this.active.x = clamp(this.active.x + arrows[event.key][0] * step, -SIDE, SIDE);
                this.active.y = clamp(this.active.y + arrows[event.key][1] * step, -SIDE, SIDE);
                this.changed();
            } else if (["Delete", "Backspace"].includes(event.key) && event.target === this.canvasElement) {
                event.preventDefault(); this.removeLayer();
            }
        }
    }

    handles(layer, w, h) {
        return [
            { x: layer.x, y: layer.y, sx: -1, sy: -1, ax: layer.x + w, ay: layer.y + h },
            { x: layer.x + w, y: layer.y, sx: 1, sy: -1, ax: layer.x, ay: layer.y + h },
            { x: layer.x, y: layer.y + h, sx: -1, sy: 1, ax: layer.x + w, ay: layer.y },
            { x: layer.x + w, y: layer.y + h, sx: 1, sy: 1, ax: layer.x, ay: layer.y },
        ];
    }

    handleRadius() {
        return 10 * SIDE / (this.canvasElement?.getBoundingClientRect().width || SIDE);
    }

    point(event) {
        const r = this.canvasElement.getBoundingClientRect();
        return [(event.clientX - r.left) * SIDE / r.width, (event.clientY - r.top) * SIDE / r.height];
    }

    pointerDown(event) {
        if (this.busy || event.button !== 0 || this.drag) return;
        this.finishEdit();
        this.canvasElement.focus({ preventScroll: true });
        const [x, y] = this.point(event);
        const ctx = this.canvasElement.getContext("2d");
        if (this.active) {
            const [w, h] = this.bounds(ctx, this.active);
            const handle = this.handles(this.active, w, h).find(point =>
                Math.abs(x - point.x) <= this.handleRadius() && Math.abs(y - point.y) <= this.handleRadius());
            if (handle) {
                this.drag = { id: event.pointerId, index: this.state.selected, resize: true,
                    handle, w, h, original: { x: this.active.x, y: this.active.y, size: this.active.size } };
                this.state.interacting = true;
                event.currentTarget.setPointerCapture(event.pointerId);
                event.preventDefault();
                return;
            }
        }
        const layers = this.state.design.layers;
        for (let i = layers.length - 1; i >= 0; i--) {
            const l = layers[i];
            const [w, h] = this.bounds(ctx, l);
            if (x >= l.x && x <= l.x + w && y >= l.y && y <= l.y + h) {
                this.select(i);
                this.drag = { id: event.pointerId, index: i, dx: x - l.x, dy: y - l.y,
                    original: { x: l.x, y: l.y, size: l.size } };
                this.state.interacting = true;
                event.currentTarget.setPointerCapture(event.pointerId);
                event.preventDefault();
                return;
            }
        }
        this.select(-1);
    }

    pointerMove(event) {
        if (this.busy || this.drag?.id !== event.pointerId) return;
        const [x, y] = this.point(event);
        const layer = this.state.design.layers[this.drag.index];
        if (!layer) return;
        if (this.drag.resize) {
            const { handle, w, h, original } = this.drag;
            const dx = (x - handle.ax) * handle.sx, dy = (y - handle.ay) * handle.sy;
            const scale = Math.max(0, (dx * w + dy * h) / (w * w + h * h));
            layer.size = clamp(original.size * scale, layer.kind === "text" ? 18 : 32,
                layer.kind === "text" ? 160 : 1080);
            const [newW, newH] = this.bounds(this.canvasElement.getContext("2d"), layer);
            layer.x = clamp(handle.sx < 0 ? handle.ax - newW : handle.ax, -SIDE, SIDE);
            layer.y = clamp(handle.sy < 0 ? handle.ay - newH : handle.ay, -SIDE, SIDE);
        } else {
            layer.x = clamp(x - this.drag.dx, -SIDE, SIDE);
            layer.y = clamp(y - this.drag.dy, -SIDE, SIDE);
        }
        this.changed(null, false);
    }

    pointerEnd(event) {
        if (this.drag?.id !== event.pointerId) return;
        if (event.type === "pointercancel") {
            Object.assign(this.state.design.layers[this.drag.index], this.drag.original);
        }
        this.drag = null;
        this.state.interacting = false;
        this.changed();
    }

    async goBack() {
        if (this.state.saving || this.state.importing || this.drag) return;
        if (this.state.dirty && !window.confirm("Leave without saving the design?")) return;
        await this.openPost();
    }

    openPost() {
        return this.action.doAction({
            type: "ir.actions.act_window", name: "Social Post",
            res_model: MODEL, res_id: this.postId, views: [[false, "form"]], target: "current",
        });
    }

    async save() {
        if (this.busy || this.drag || (this.state.hasOtherMedia && !this.state.replace)) return;
        this.state.saving = true;
        this.state.error = "";
        try {
            const output = document.createElement("canvas");
            output.width = output.height = SIDE;
            this.draw(output, false);
            const jpeg = output.toDataURL("image/jpeg", 0.91).split(",")[1];
            const documentJson = JSON.stringify(this.state.design);
            if (new Blob([documentJson]).size > 7 * 1024 * 1024) {
                throw new Error("The editable design is too large. Remove an image or use smaller files.");
            }
            this.revision = await this.orm.call(MODEL, "save_post_designer", [
                [this.postId], documentJson, jpeg, this.revision, this.state.replace,
            ]);
            this.state.dirty = false;
            this.state.hasOtherMedia = false;
            this.notification.add("JPEG attached. Submit the updated post for review.", { type: "success" });
            await this.openPost();
        } catch (error) {
            this.showError(error, "Could not save the design.");
        } finally {
            this.state.saving = false;
        }
    }
}

registry.category("actions").add("cafe_social_marketing.post_designer", PostDesigner);
