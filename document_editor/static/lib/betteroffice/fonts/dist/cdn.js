// package.json
var version = "0.4.2";

// ../fonts-cjk/package.json
var version2 = "0.4.2";

// src/bytes.ts
function builtinModule(name) {
  const proc = globalThis.process;
  if (typeof proc?.getBuiltinModule !== "function") return void 0;
  try {
    return proc.getBuiltinModule(name);
  } catch {
    return void 0;
  }
}
function readFileAsset(url) {
  if (url.protocol !== "file:") return void 0;
  const fs = builtinModule("node:fs");
  const nodeUrl = builtinModule("node:url");
  if (!fs || !nodeUrl) return void 0;
  try {
    const bytes = fs.readFileSync(nodeUrl.fileURLToPath(url.href));
    return bytes.buffer.slice(
      bytes.byteOffset,
      bytes.byteOffset + bytes.byteLength
    );
  } catch {
    return void 0;
  }
}
function validateByteLength(face, bytes) {
  if (bytes.byteLength !== face.byteLength) {
    throw new Error(
      `Bundled font ${face.file} has ${bytes.byteLength} bytes; expected ${face.byteLength}`
    );
  }
  return bytes;
}
var bytesCache = /* @__PURE__ */ new Map();
function loadFontBytes(face, url, timeoutMs) {
  const key = `${url.href}|${face.byteLength}|${timeoutMs ?? ""}`;
  const cached = bytesCache.get(key);
  if (cached) return cached;
  const promise = (async () => {
    const onDisk = readFileAsset(url);
    if (onDisk) return validateByteLength(face, onDisk);
    const response = await fetch(
      url,
      timeoutMs === void 0 ? void 0 : {
        signal: AbortSignal.timeout(timeoutMs),
        credentials: "omit",
        referrerPolicy: "no-referrer"
      }
    );
    if (!response.ok) {
      throw new Error(
        `Failed to fetch bundled font ${face.file}: HTTP ${response.status}`
      );
    }
    return validateByteLength(face, await response.arrayBuffer());
  })();
  promise.catch(() => {
    if (bytesCache.get(key) === promise) bytesCache.delete(key);
  });
  bytesCache.set(key, promise);
  return promise;
}

// src/manifest.ts
function familyFaces(family, metricCompatWith, fileBase, byteLengths) {
  return [
    {
      family,
      metricCompatWith,
      weight: 400,
      style: "normal",
      file: `${fileBase}-Regular.ttf`,
      byteLength: byteLengths[0]
    },
    {
      family,
      metricCompatWith,
      weight: 700,
      style: "normal",
      file: `${fileBase}-Bold.ttf`,
      byteLength: byteLengths[1]
    },
    {
      family,
      metricCompatWith,
      weight: 400,
      style: "italic",
      file: `${fileBase}-Italic.ttf`,
      byteLength: byteLengths[2]
    },
    {
      family,
      metricCompatWith,
      weight: 700,
      style: "italic",
      file: `${fileBase}-BoldItalic.ttf`,
      byteLength: byteLengths[3]
    }
  ];
}
var BUNDLED_FONTS = [
  ...familyFaces(
    "Carlito",
    "Calibri",
    "Carlito",
    [628032, 682468, 615236, 808508]
  ),
  {
    family: "Selawik",
    metricCompatWith: "Segoe UI",
    weight: 400,
    style: "normal",
    file: "Selawik-Regular.ttf",
    byteLength: 44224
  },
  {
    family: "Selawik",
    metricCompatWith: "Segoe UI",
    weight: 700,
    style: "normal",
    file: "Selawik-Bold.ttf",
    byteLength: 44068
  },
  {
    family: "Selawik",
    metricCompatWith: "Segoe UI Light",
    weight: 400,
    style: "normal",
    file: "Selawik-Light.ttf",
    byteLength: 44232
  },
  {
    family: "Selawik",
    metricCompatWith: "Segoe UI Semilight",
    weight: 400,
    style: "normal",
    file: "Selawik-Semilight.ttf",
    byteLength: 44260
  },
  {
    family: "Selawik",
    metricCompatWith: "Segoe UI Semibold",
    weight: 400,
    style: "normal",
    file: "Selawik-Semibold.ttf",
    byteLength: 44192
  },
  ...familyFaces("Caladea", "Cambria", "Caladea", [81600, 84492, 83780, 83356]),
  ...familyFaces(
    "Liberation Sans",
    "Arial",
    "LiberationSans",
    [410712, 414456, 415816, 408996]
  ),
  ...familyFaces(
    "Liberation Serif",
    "Times New Roman",
    "LiberationSerif",
    [393576, 370096, 375632, 376772]
  ),
  ...familyFaces(
    "Liberation Mono",
    "Courier New",
    "LiberationMono",
    [319508, 307996, 281536, 284068]
  ),
  // Families the office-quality references are actually drawn with. The Google
  // families are the same font PowerPoint used, so their lines break where the
  // deck wrote them; Gelasio is Georgia's metric-compatible clone and Comic
  // Relief is Comic Sans MS's (#797).
  ...familyFaces("Gelasio", "Georgia", "Gelasio", [107588, 107864, 107904, 107932]),
  ...familyFaces("Inter", "Inter", "Inter", [341396, 343104, 344784, 346628]),
  ...familyFaces("Roboto", "Roboto", "Roboto", [157584, 158316, 163212, 164100]),
  ...familyFaces(
    "Source Sans 3",
    "Source Sans Pro",
    "SourceSans3",
    [379576, 379468, 240444, 240384]
  ),
  ...familyFaces("DM Sans", "DM Sans", "DMSans", [56856, 56784, 61472, 61324]),
  ...familyFaces("Open Sans", "Open Sans", "OpenSans", [130484, 130504, 136020, 135700]),
  ...familyFaces(
    "Montserrat",
    "Montserrat",
    "Montserrat",
    [374500, 374640, 384612, 384792]
  ),
  ...familyFaces("Poppins", "Poppins", "Poppins", [28468, 28108, 30772, 30388]),
  // Faces the references use that ship no italic, or none at all: the missing
  // ones fall back through the chain.
  {
    family: "Oswald",
    metricCompatWith: "Oswald",
    weight: 400,
    style: "normal",
    file: "Oswald-Regular.ttf",
    byteLength: 78404
  },
  {
    family: "Oswald",
    metricCompatWith: "Oswald",
    weight: 700,
    style: "normal",
    file: "Oswald-Bold.ttf",
    byteLength: 78736
  },
  {
    family: "Heebo",
    metricCompatWith: "Heebo",
    weight: 400,
    style: "normal",
    file: "Heebo-Regular.ttf",
    byteLength: 42368
  },
  {
    family: "Heebo",
    metricCompatWith: "Heebo",
    weight: 700,
    style: "normal",
    file: "Heebo-Bold.ttf",
    byteLength: 42732
  },
  {
    family: "DM Serif Display",
    metricCompatWith: "DM Serif Display",
    weight: 400,
    style: "normal",
    file: "DMSerifDisplay-Regular.ttf",
    byteLength: 70440
  },
  {
    family: "DM Serif Display",
    metricCompatWith: "DM Serif Display",
    weight: 400,
    style: "italic",
    file: "DMSerifDisplay-Italic.ttf",
    byteLength: 68560
  },
  // Comic Relief ships no italics, so those fall back through the chain.
  {
    family: "Comic Relief",
    metricCompatWith: "Comic Sans MS",
    weight: 400,
    style: "normal",
    file: "ComicRelief-Regular.ttf",
    byteLength: 80324
  },
  {
    family: "Comic Relief",
    metricCompatWith: "Comic Sans MS",
    weight: 700,
    style: "normal",
    file: "ComicRelief-Bold.ttf",
    byteLength: 94684
  },
  // RTL script fallbacks. No metricCompatWith: Hebrew/Arabic documents mostly
  // name Latin families (Arial, Times New Roman, ...) whose mapping stays with
  // the Liberation faces; these faces ride the per-script fallback chain.
  {
    family: "Noto Sans Hebrew",
    weight: 400,
    style: "normal",
    file: "NotoSansHebrew-Regular.ttf",
    byteLength: 26860,
    script: "hebrew"
  },
  {
    family: "Noto Sans Hebrew",
    weight: 700,
    style: "normal",
    file: "NotoSansHebrew-Bold.ttf",
    byteLength: 26860,
    script: "hebrew"
  },
  {
    family: "Noto Sans Arabic",
    weight: 400,
    style: "normal",
    file: "NotoSansArabic-Regular.ttf",
    byteLength: 234892,
    script: "arabic"
  },
  {
    family: "Noto Sans Arabic",
    weight: 700,
    style: "normal",
    file: "NotoSansArabic-Bold.ttf",
    byteLength: 261460,
    script: "arabic"
  },
  {
    family: "Noto Naskh Arabic",
    weight: 400,
    style: "normal",
    file: "NotoNaskhArabic-Regular.ttf",
    byteLength: 247336,
    script: "arabic"
  },
  // CJK coverage faces (Regular-only statics; see the module doc). The sans
  // face precedes the serif face of the same script bucket on purpose.
  {
    family: "Noto Sans SC",
    metricCompatWith: "Microsoft YaHei",
    weight: 400,
    style: "normal",
    file: "NotoSansSC-Regular.otf",
    byteLength: 8331336,
    script: "cjk-sc"
  },
  {
    family: "Noto Serif SC",
    metricCompatWith: "SimSun",
    weight: 400,
    style: "normal",
    file: "NotoSerifSC-Regular.otf",
    byteLength: 11625800,
    script: "cjk-sc"
  },
  {
    family: "Noto Sans TC",
    metricCompatWith: "Microsoft JhengHei",
    weight: 400,
    style: "normal",
    file: "NotoSansTC-Regular.otf",
    byteLength: 5683368,
    script: "cjk-tc"
  },
  {
    family: "Noto Sans JP",
    metricCompatWith: "MS Gothic",
    weight: 400,
    style: "normal",
    file: "NotoSansJP-Regular.otf",
    byteLength: 4533028,
    script: "cjk-jp"
  },
  {
    family: "Noto Sans KR",
    metricCompatWith: "Malgun Gothic",
    weight: 400,
    style: "normal",
    file: "NotoSansKR-Regular.otf",
    byteLength: 4644748,
    script: "cjk-kr"
  }
];
var WORD_FAMILY_ALIASES = {
  helvetica: "arial",
  times: "times new roman",
  courier: "courier new",
  // Metric-compatible clones of the core families. A deck that asks for one
  // was laid out against those metrics, so it resolves to the same face rather
  // than through the last-resort pick (#797).
  arimo: "arial",
  "liberation sans": "arial",
  "nimbus sans": "arial",
  "helvetica neue": "arial",
  carlito: "calibri",
  tinos: "times new roman",
  "liberation serif": "times new roman",
  "nimbus roman": "times new roman",
  cousine: "courier new",
  "liberation mono": "courier new",
  "nimbus mono ps": "courier new",
  caladea: "cambria",
  // Simplified Chinese — sans
  simhei: "microsoft yahei",
  dengxian: "microsoft yahei",
  微软雅黑: "microsoft yahei",
  黑体: "microsoft yahei",
  等线: "microsoft yahei",
  // Simplified Chinese — serif
  nsimsun: "simsun",
  fangsong: "simsun",
  kaiti: "simsun",
  宋体: "simsun",
  仿宋: "simsun",
  楷体: "simsun",
  // Traditional Chinese (the Ming/Kai serif families map to the sans face —
  // Noto Serif TC is not vendored)
  微軟正黑體: "microsoft jhenghei",
  pmingliu: "microsoft jhenghei",
  mingliu: "microsoft jhenghei",
  "dfkai-sb": "microsoft jhenghei",
  新細明體: "microsoft jhenghei",
  細明體: "microsoft jhenghei",
  標楷體: "microsoft jhenghei",
  // Japanese (the Mincho serif families map to the sans face — Noto Serif JP
  // is not vendored)
  "ms pgothic": "ms gothic",
  meiryo: "ms gothic",
  "yu gothic": "ms gothic",
  "ｍｓ ゴシック": "ms gothic",
  "ｍｓ ｐゴシック": "ms gothic",
  メイリオ: "ms gothic",
  游ゴシック: "ms gothic",
  "ms mincho": "ms gothic",
  "ms pmincho": "ms gothic",
  "yu mincho": "ms gothic",
  "ｍｓ 明朝": "ms gothic",
  "ｍｓ ｐ明朝": "ms gothic",
  游明朝: "ms gothic",
  // Korean (Batang/Gungsuh serif map to the sans face — Noto Serif KR is not
  // vendored)
  "맑은 고딕": "malgun gothic",
  gulim: "malgun gothic",
  dotum: "malgun gothic",
  batang: "malgun gothic",
  gungsuh: "malgun gothic",
  굴림: "malgun gothic",
  돋움: "malgun gothic",
  바탕: "malgun gothic",
  궁서: "malgun gothic"
};
var metricCompatByWordFamily = /* @__PURE__ */ new Map();
for (const face of BUNDLED_FONTS) {
  if (face.metricCompatWith !== void 0) {
    metricCompatByWordFamily.set(
      face.metricCompatWith.toLowerCase(),
      face.family
    );
  }
}
function resolveMetricCompatFamily(wordFamily) {
  const key = wordFamily.trim().toLowerCase();
  return metricCompatByWordFamily.get(WORD_FAMILY_ALIASES[key] ?? key);
}
function resolveMetricCompatFace(wordFamily, bold, italic) {
  const family = resolveMetricCompatFamily(wordFamily);
  if (!family) return void 0;
  if (family === "Selawik") {
    if (italic) return void 0;
    const key = wordFamily.trim().toLowerCase();
    const target = bold && key === "segoe ui semibold" ? "segoe ui" : key;
    const weight2 = bold && target === "segoe ui" ? 700 : 400;
    return BUNDLED_FONTS.find(
      (f) => f.metricCompatWith?.toLowerCase() === target && f.weight === weight2
    );
  }
  const faces = BUNDLED_FONTS.filter((f) => f.family === family);
  const weight = bold ? 700 : 400;
  const style = italic ? "italic" : "normal";
  return faces.find((f) => f.weight === weight && f.style === style) ?? faces.find((f) => f.weight === 400 && f.style === "normal");
}
var bundledFamilyByName = new Map(
  BUNDLED_FONTS.map((face) => [face.family.toLowerCase(), face.family])
);
var UNVENDORED_NOTO_SERIF = {
  "noto serif tc": "Noto Sans TC",
  "noto serif jp": "Noto Sans JP",
  "noto serif kr": "Noto Sans KR"
};
function resolveBundledFamilyFace(family, bold, italic) {
  if (resolveMetricCompatFamily(family) === "Selawik") {
    return italic ? void 0 : resolveMetricCompatFace(family, bold, false);
  }
  const key = family.trim().toLowerCase();
  const bundled = bundledFamilyByName.get(key) ?? UNVENDORED_NOTO_SERIF[key] ?? resolveMetricCompatFamily(family);
  const weight = bold ? 700 : 400;
  const style = italic ? "italic" : "normal";
  return BUNDLED_FONTS.find(
    (f) => f.family === bundled && f.weight === weight && f.style === style
  );
}
function resolveScriptFallbackFace(script, bold, italic) {
  const faces = BUNDLED_FONTS.filter((f) => f.script === script);
  if (faces.length === 0) return void 0;
  const weight = bold ? 700 : 400;
  const style = italic ? "italic" : "normal";
  return faces.find((f) => f.weight === weight && f.style === style) ?? faces.find((f) => f.weight === weight && f.style === "normal") ?? faces.find((f) => f.weight === 400 && f.style === "normal") ?? faces[0];
}
function looksSerif(family) {
  const lower = family.toLowerCase();
  return lower.includes("antiqua") || lower.includes("bookman") || lower.includes("calisto") || lower.includes("schoolbook") || lower.includes("goudy") || lower.includes("perpetua") || lower.includes("rockwell") || lower.includes("caslon") || lower.includes("constantia") || lower.includes("didot") || lower.includes("baskerville") || lower.includes("times") || lower.includes("georgia") || lower.includes("garamond") || lower.includes("palatino") || lower.includes("baskerville") || lower.includes("bodoni") || lower.includes("cambria") || lower.includes("minion") || lower.includes("mincho") || lower.includes("明朝") || lower.includes("明體") || lower.includes("宋") || lower.includes("ming") || lower.includes("song") || lower.includes("serif");
}
var WIDTH_MATCHED_SUBSTITUTES = /* @__PURE__ */ new Map([
  ["verdana", {
    family: "Montserrat",
    digitAdvances: { regular: 0.636, bold: 0.711, italic: 0.636, boldItalic: 0.711 }
  }]
]);
function resolveWidthMatchedSubstitute(family) {
  return WIDTH_MATCHED_SUBSTITUTES.get(family.trim().toLowerCase());
}
var LIGHTER_THAN_REGULAR = /* @__PURE__ */ new Set([
  "thin",
  "hairline",
  "extralight",
  "ultralight",
  "semilight",
  "light",
  "medium"
]);
function lightVariantOf(family, italic) {
  const words = family.trim().split(/[\s-]+/);
  if (words.length < 2) return void 0;
  if (!LIGHTER_THAN_REGULAR.has(words[words.length - 1].toLowerCase())) {
    return void 0;
  }
  return resolveMetricCompatFace(words.slice(0, -1).join(" "), false, italic);
}
function looksMono(family) {
  const lower = family.toLowerCase();
  return lower.includes("consolas") || lower.includes("monaco") || lower.includes("menlo") || lower.includes("console") || lower.includes("andale") || lower.includes("inconsolata") || lower.includes("cascadia") || lower.includes("typewriter") || /(^|[\s-])mono([\s-]|$)/.test(lower);
}
var HEAVIER_THAN_REGULAR = /* @__PURE__ */ new Set([
  "black",
  "heavy",
  "extrabold",
  "ultrabold",
  "extrablack",
  "ultra"
]);
function heavyVariantOf(family, italic) {
  const words = family.trim().split(/[\s-]+/);
  if (words.length < 2 || !HEAVIER_THAN_REGULAR.has(words[words.length - 1].toLowerCase())) {
    return void 0;
  }
  return resolveMetricCompatFace(words.slice(0, -1).join(" "), true, italic);
}
function resolveLastResortFace(family, bold, italic, office = "powerpoint") {
  return resolveLastResortChoice(family, bold, italic, office).face;
}
function resolveLastResortChoice(family, bold, italic, office = "powerpoint") {
  const primary = resolveMetricCompatFace(family, bold, italic);
  const base = resolveBaseFace(family, bold, italic, office, primary !== void 0);
  if (base.file !== primary?.file) return { face: base, onlyIfPrimaryFails: false };
  const alternate = base.family === "Liberation Sans" ? "Calibri" : "Arial";
  return { face: resolveMetricCompatFace(alternate, bold, italic), onlyIfPrimaryFails: true };
}
function resolveGlyphFallbackFace(family, bold, italic, office = "powerpoint") {
  const primary = resolveMetricCompatFace(family, bold, italic);
  const face = primary ?? resolveBaseFace(family, bold, italic, office);
  if (face.family !== "Selawik") return void 0;
  return primary ? resolveLastResortFace(family, bold, italic, office) : resolveBaseFace(family, bold, italic, office, true);
}
function resolveBaseFace(family, bold, italic, office, excludeSelawik = false) {
  const light = lightVariantOf(family, italic);
  if (light && (!excludeSelawik || light.family !== "Selawik")) return light;
  if (light) bold = false;
  const heavy = heavyVariantOf(family, italic);
  if (heavy && (!excludeSelawik || heavy.family !== "Selawik")) return heavy;
  if (looksMono(family)) {
    return resolveMetricCompatFace("Courier New", bold, italic);
  }
  const matched = resolveWidthMatchedSubstitute(family);
  if (matched) {
    const face = resolveMetricCompatFace(matched.family, bold, italic);
    if (face) return face;
  }
  const sans = office === "word" ? "Arial" : "Calibri";
  const base = looksSerif(family) ? "Times New Roman" : sans;
  return resolveMetricCompatFace(base, bold, italic);
}

// src/provider.ts
function fontProvider(loadBytes) {
  const load = (face) => () => loadBytes(face);
  return {
    resolve(family, bold, italic) {
      const face = resolveMetricCompatFace(family, bold, italic);
      return face ? Object.assign(load(face), { measureAs: face.family === "Selawik" ? "Segoe UI" : void 0 }) : void 0;
    },
    resolveFamily(family, bold, italic) {
      const face = resolveBundledFamilyFace(family, bold, italic);
      return face ? load(face) : void 0;
    },
    resolveScriptFallback(script, bold, italic) {
      const face = resolveScriptFallbackFace(script, bold, italic);
      return face ? load(face) : void 0;
    },
    resolveGlyphFallback(family, bold, italic, office = "powerpoint") {
      const face = resolveGlyphFallbackFace(family, bold, italic, office);
      return face ? load(face) : void 0;
    },
    resolveLastResort(family, bold, italic, office) {
      const { face, onlyIfPrimaryFails } = resolveLastResortChoice(family, bold, italic, office);
      return onlyIfPrimaryFails ? Object.assign(load(face), { onlyIfPrimaryFails }) : load(face);
    }
  };
}

// src/cdn.ts
var BASE_URL = `https://cdn.jsdelivr.net/npm/@betteroffice/fonts@${version}/assets/`;
var CJK_BASE_URL = `https://cdn.jsdelivr.net/npm/@betteroffice/fonts-cjk@${version2}/assets/`;
function assetBase(value) {
  const href = String(value);
  const base = href.endsWith("/") ? href : `${href}/`;
  return new URL(
    base,
    typeof location === "undefined" ? void 0 : location.href
  );
}
function createFontProvider(options = {}) {
  const base = assetBase(options.baseUrl ?? BASE_URL);
  const cjkBase = assetBase(
    options.cjkBaseUrl ?? options.baseUrl ?? CJK_BASE_URL
  );
  return fontProvider(
    (face) => loadFontBytes(
      face,
      new URL(face.file, face.script?.startsWith("cjk-") ? cjkBase : base),
      3e4
    )
  );
}
export {
  createFontProvider
};
