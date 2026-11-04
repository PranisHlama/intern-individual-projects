/** @odoo-module **/

import { Component, onMounted, proxy, useProps } from "@odoo/owl";
import { standardActionServiceProps } from "@web/webclient/actions/action_plugin";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const SIDE = 1080;
let nextCanvasId = 0;
const BLOCK_TYPE = "application/x-cafe-designer-block";
const textLayer = (text, x, y, size, color) => ({ kind: "text", text, x, y, size, color });
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
const initialDesign = () => ({ version: 1, color: "#f4e8d4", background: "", layers: [] });
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
            hasOtherMedia: false, error: "",
        });
        this.images = new Map();
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
            version: 1, color: preset.color, background: "",
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
                this.state.design = design;
            }
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

    changed() {
        this.state.dirty = true;
        this.draw();
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
        this.active[field] = value;
        this.changed();
    }

    setColor(event) {
        this.setDesignColor(event.target.value);
    }

    setDesignColor(color) {
        if (this.busy) return;
        this.state.design.color = color;
        this.changed();
    }

    bounds(ctx, layer) {
        if (layer.kind === "image") {
            const img = this.images.get(layer.data);
            return [layer.size, img ? layer.size * img.height / img.width : layer.size];
        }
        ctx.font = `bold ${layer.size}px sans-serif`;
        const lines = layer.text.split("\n");
        return [Math.max(24, ...lines.map(line => ctx.measureText(line).width)), lines.length * layer.size * 1.22];
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
                layer.text.split("\n").forEach((line, i) => ctx.fillText(line, layer.x, layer.y + i * layer.size * 1.22));
            }
        }
        if (selection && this.active) {
            const [w, h] = this.bounds(ctx, this.active);
            ctx.strokeStyle = "#168c85";
            ctx.lineWidth = 4;
            ctx.setLineDash([12, 8]);
            ctx.strokeRect(this.active.x - 5, this.active.y - 5, w + 10, h + 10);
            ctx.setLineDash([]);
        }
    }

    point(event) {
        const r = this.canvasElement.getBoundingClientRect();
        return [(event.clientX - r.left) * SIDE / r.width, (event.clientY - r.top) * SIDE / r.height];
    }

    pointerDown(event) {
        if (this.busy || event.button !== 0 || this.drag) return;
        const [x, y] = this.point(event);
        const ctx = this.canvasElement.getContext("2d");
        const layers = this.state.design.layers;
        for (let i = layers.length - 1; i >= 0; i--) {
            const l = layers[i];
            const [w, h] = this.bounds(ctx, l);
            if (x >= l.x && x <= l.x + w && y >= l.y && y <= l.y + h) {
                this.select(i);
                this.drag = { id: event.pointerId, index: i, dx: x - l.x, dy: y - l.y };
                event.currentTarget.setPointerCapture(event.pointerId);
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
        layer.x = clamp(x - this.drag.dx, -SIDE, SIDE);
        layer.y = clamp(y - this.drag.dy, -SIDE, SIDE);
        this.changed();
    }

    pointerEnd(event) {
        if (this.drag?.id === event.pointerId) this.drag = null;
    }

    async goBack() {
        if (this.state.saving) return;
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
        if (this.busy || (this.state.hasOtherMedia && !this.state.replace)) return;
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
