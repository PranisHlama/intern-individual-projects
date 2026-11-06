// Bundles React + the BetterOffice React editors into ES modules.
// The BetterOffice core packages are copied unmodified instead of bundled:
// they load their Web Worker and WASM relative to their own files
// (import.meta.url), so they must keep their original layout. The editor
// page maps their bare imports to these copies with an import map.
import { build } from "esbuild";
import { cpSync, rmSync } from "node:fs";

const OUT = "../static/lib/betteroffice";
const FORMATS = ["xlsx", "pptx"];
const noTypes = (path) => !path.endsWith(".d.ts") && !path.endsWith(".map");

rmSync(OUT, { recursive: true, force: true });

for (const format of FORMATS) {
    await build({
        entryPoints: [`src/${format}.js`],
        outfile: `${OUT}/${format}-editor.js`,
        bundle: true,
        format: "esm",
        minify: true,
        legalComments: "eof",
        define: { "process.env.NODE_ENV": '"production"' },
        external: [
            `@betteroffice/${format}`,
            `@betteroffice/${format}/*`,
            "@betteroffice/fonts",
        ],
    });

    cpSync(`node_modules/@betteroffice/${format}/dist`, `${OUT}/${format}`, {
        recursive: true,
        filter: noTypes,
    });
    cpSync(
        `node_modules/@betteroffice/${format}/LICENSE`,
        `${OUT}/${format}/LICENSE`,
    );
}

// The fonts package fetches each face from ../assets/ relative to dist/.
for (const part of ["dist", "assets", "LICENSES", "LICENSE"]) {
    cpSync(`node_modules/@betteroffice/fonts/${part}`, `${OUT}/fonts/${part}`, {
        recursive: true,
        filter: noTypes,
    });
}
