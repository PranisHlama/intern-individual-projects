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
function resolveDigitAdvance(family, bold = false, italic = false) {
  const style = bold ? italic ? "boldItalic" : "bold" : italic ? "italic" : "regular";
  return resolveWidthMatchedSubstitute(family)?.digitAdvances[style];
}
function maxDigitWidth(family, sizePx, measure, bold = false, italic = false) {
  const advance = resolveDigitAdvance(family, bold, italic);
  if (advance !== void 0) return Math.round(advance * sizePx);
  return Math.max(...[..."0123456789"].map((digit) => Math.round(measure(digit))));
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

// src/index.ts
var FONT_ASSET_URLS = {
  "Caladea-Bold.ttf": () => new URL("../assets/Caladea-Bold.ttf", import.meta.url),
  "Caladea-BoldItalic.ttf": () => new URL("../assets/Caladea-BoldItalic.ttf", import.meta.url),
  "Caladea-Italic.ttf": () => new URL("../assets/Caladea-Italic.ttf", import.meta.url),
  "Caladea-Regular.ttf": () => new URL("../assets/Caladea-Regular.ttf", import.meta.url),
  "Carlito-Bold.ttf": () => new URL("../assets/Carlito-Bold.ttf", import.meta.url),
  "Carlito-BoldItalic.ttf": () => new URL("../assets/Carlito-BoldItalic.ttf", import.meta.url),
  "Carlito-Italic.ttf": () => new URL("../assets/Carlito-Italic.ttf", import.meta.url),
  "Carlito-Regular.ttf": () => new URL("../assets/Carlito-Regular.ttf", import.meta.url),
  "ComicRelief-Bold.ttf": () => new URL("../assets/ComicRelief-Bold.ttf", import.meta.url),
  "ComicRelief-Regular.ttf": () => new URL("../assets/ComicRelief-Regular.ttf", import.meta.url),
  "DMSans-Bold.ttf": () => new URL("../assets/DMSans-Bold.ttf", import.meta.url),
  "DMSans-BoldItalic.ttf": () => new URL("../assets/DMSans-BoldItalic.ttf", import.meta.url),
  "DMSans-Italic.ttf": () => new URL("../assets/DMSans-Italic.ttf", import.meta.url),
  "DMSans-Regular.ttf": () => new URL("../assets/DMSans-Regular.ttf", import.meta.url),
  "DMSerifDisplay-Italic.ttf": () => new URL("../assets/DMSerifDisplay-Italic.ttf", import.meta.url),
  "DMSerifDisplay-Regular.ttf": () => new URL("../assets/DMSerifDisplay-Regular.ttf", import.meta.url),
  "Gelasio-Bold.ttf": () => new URL("../assets/Gelasio-Bold.ttf", import.meta.url),
  "Gelasio-BoldItalic.ttf": () => new URL("../assets/Gelasio-BoldItalic.ttf", import.meta.url),
  "Gelasio-Italic.ttf": () => new URL("../assets/Gelasio-Italic.ttf", import.meta.url),
  "Gelasio-Regular.ttf": () => new URL("../assets/Gelasio-Regular.ttf", import.meta.url),
  "Heebo-Bold.ttf": () => new URL("../assets/Heebo-Bold.ttf", import.meta.url),
  "Heebo-Regular.ttf": () => new URL("../assets/Heebo-Regular.ttf", import.meta.url),
  "Inter-Bold.ttf": () => new URL("../assets/Inter-Bold.ttf", import.meta.url),
  "Inter-BoldItalic.ttf": () => new URL("../assets/Inter-BoldItalic.ttf", import.meta.url),
  "Inter-Italic.ttf": () => new URL("../assets/Inter-Italic.ttf", import.meta.url),
  "Inter-Regular.ttf": () => new URL("../assets/Inter-Regular.ttf", import.meta.url),
  "LiberationMono-Bold.ttf": () => new URL("../assets/LiberationMono-Bold.ttf", import.meta.url),
  "LiberationMono-BoldItalic.ttf": () => new URL("../assets/LiberationMono-BoldItalic.ttf", import.meta.url),
  "LiberationMono-Italic.ttf": () => new URL("../assets/LiberationMono-Italic.ttf", import.meta.url),
  "LiberationMono-Regular.ttf": () => new URL("../assets/LiberationMono-Regular.ttf", import.meta.url),
  "LiberationSans-Bold.ttf": () => new URL("../assets/LiberationSans-Bold.ttf", import.meta.url),
  "LiberationSans-BoldItalic.ttf": () => new URL("../assets/LiberationSans-BoldItalic.ttf", import.meta.url),
  "LiberationSans-Italic.ttf": () => new URL("../assets/LiberationSans-Italic.ttf", import.meta.url),
  "LiberationSans-Regular.ttf": () => new URL("../assets/LiberationSans-Regular.ttf", import.meta.url),
  "LiberationSerif-Bold.ttf": () => new URL("../assets/LiberationSerif-Bold.ttf", import.meta.url),
  "LiberationSerif-BoldItalic.ttf": () => new URL("../assets/LiberationSerif-BoldItalic.ttf", import.meta.url),
  "LiberationSerif-Italic.ttf": () => new URL("../assets/LiberationSerif-Italic.ttf", import.meta.url),
  "LiberationSerif-Regular.ttf": () => new URL("../assets/LiberationSerif-Regular.ttf", import.meta.url),
  "Montserrat-Bold.ttf": () => new URL("../assets/Montserrat-Bold.ttf", import.meta.url),
  "Montserrat-BoldItalic.ttf": () => new URL("../assets/Montserrat-BoldItalic.ttf", import.meta.url),
  "Montserrat-Italic.ttf": () => new URL("../assets/Montserrat-Italic.ttf", import.meta.url),
  "Montserrat-Regular.ttf": () => new URL("../assets/Montserrat-Regular.ttf", import.meta.url),
  "NotoNaskhArabic-Regular.ttf": () => new URL("../assets/NotoNaskhArabic-Regular.ttf", import.meta.url),
  "NotoSansArabic-Bold.ttf": () => new URL("../assets/NotoSansArabic-Bold.ttf", import.meta.url),
  "NotoSansArabic-Regular.ttf": () => new URL("../assets/NotoSansArabic-Regular.ttf", import.meta.url),
  "NotoSansHebrew-Bold.ttf": () => new URL("../assets/NotoSansHebrew-Bold.ttf", import.meta.url),
  "NotoSansHebrew-Regular.ttf": () => new URL("../assets/NotoSansHebrew-Regular.ttf", import.meta.url),
  "OpenSans-Bold.ttf": () => new URL("../assets/OpenSans-Bold.ttf", import.meta.url),
  "OpenSans-BoldItalic.ttf": () => new URL("../assets/OpenSans-BoldItalic.ttf", import.meta.url),
  "OpenSans-Italic.ttf": () => new URL("../assets/OpenSans-Italic.ttf", import.meta.url),
  "OpenSans-Regular.ttf": () => new URL("../assets/OpenSans-Regular.ttf", import.meta.url),
  "Oswald-Bold.ttf": () => new URL("../assets/Oswald-Bold.ttf", import.meta.url),
  "Oswald-Regular.ttf": () => new URL("../assets/Oswald-Regular.ttf", import.meta.url),
  "Poppins-Bold.ttf": () => new URL("../assets/Poppins-Bold.ttf", import.meta.url),
  "Poppins-BoldItalic.ttf": () => new URL("../assets/Poppins-BoldItalic.ttf", import.meta.url),
  "Poppins-Italic.ttf": () => new URL("../assets/Poppins-Italic.ttf", import.meta.url),
  "Poppins-Regular.ttf": () => new URL("../assets/Poppins-Regular.ttf", import.meta.url),
  "Roboto-Bold.ttf": () => new URL("../assets/Roboto-Bold.ttf", import.meta.url),
  "Roboto-BoldItalic.ttf": () => new URL("../assets/Roboto-BoldItalic.ttf", import.meta.url),
  "Roboto-Italic.ttf": () => new URL("../assets/Roboto-Italic.ttf", import.meta.url),
  "Roboto-Regular.ttf": () => new URL("../assets/Roboto-Regular.ttf", import.meta.url),
  "Selawik-Bold.ttf": () => new URL("../assets/Selawik-Bold.ttf", import.meta.url),
  "Selawik-Light.ttf": () => new URL("../assets/Selawik-Light.ttf", import.meta.url),
  "Selawik-Regular.ttf": () => new URL("../assets/Selawik-Regular.ttf", import.meta.url),
  "Selawik-Semibold.ttf": () => new URL("../assets/Selawik-Semibold.ttf", import.meta.url),
  "Selawik-Semilight.ttf": () => new URL("../assets/Selawik-Semilight.ttf", import.meta.url),
  "SourceSans3-Bold.ttf": () => new URL("../assets/SourceSans3-Bold.ttf", import.meta.url),
  "SourceSans3-BoldItalic.ttf": () => new URL("../assets/SourceSans3-BoldItalic.ttf", import.meta.url),
  "SourceSans3-Italic.ttf": () => new URL("../assets/SourceSans3-Italic.ttf", import.meta.url),
  "SourceSans3-Regular.ttf": () => new URL("../assets/SourceSans3-Regular.ttf", import.meta.url)
};
var cjkAssetUrls;
var MissingCjkAddonError = class extends Error {
};
var UNRESOLVED_CJK_ADDON = /^(?:Cannot find (?:module|package)|Failed to resolve module specifier|Error resolving module specifier|The specifier|Module name,) ["'“]@betteroffice\/fonts-cjk["'”]/;
async function importCjkAssetUrls() {
  let addon;
  try {
    addon = await import("@betteroffice/fonts-cjk");
  } catch (error) {
    const message = error?.message;
    if (typeof message !== "string" || !UNRESOLVED_CJK_ADDON.test(message)) {
      throw error;
    }
    return void 0;
  }
  const urls = addon.CJK_FONT_ASSET_URLS;
  if (urls === null || typeof urls !== "object") {
    throw new TypeError("Invalid CJK_FONT_ASSET_URLS export from @betteroffice/fonts-cjk");
  }
  return urls;
}
function loadCjkAssetUrls() {
  if (cjkAssetUrls === void 0) {
    const promise = importCjkAssetUrls();
    promise.then(
      (urls) => {
        if (urls === void 0 && cjkAssetUrls === promise)
          cjkAssetUrls = void 0;
      },
      () => {
        if (cjkAssetUrls === promise) cjkAssetUrls = void 0;
      }
    );
    cjkAssetUrls = promise;
  }
  return cjkAssetUrls;
}
function assetBase(baseUrl) {
  const href = typeof baseUrl === "string" ? baseUrl : baseUrl.href;
  return href.endsWith("/") ? href : `${href}/`;
}
function resolvedAssetBase(baseUrl) {
  const base = assetBase(baseUrl);
  try {
    return typeof location === "undefined" ? new URL(base) : new URL(base, location.href);
  } catch {
    throw new TypeError(
      `Font baseUrl must be absolute when no browser location exists: ${base}`
    );
  }
}
var CJK_FILES = new Set(
  BUNDLED_FONTS.filter((face) => face.script?.startsWith("cjk-")).map((face) => face.file)
);
async function assetUrl({ file, script }, baseUrl) {
  if (baseUrl !== void 0) return new URL(file, baseUrl);
  const local = FONT_ASSET_URLS[file];
  if (local) return local();
  if (script?.startsWith("cjk-") || CJK_FILES.has(file)) {
    const cjk = await loadCjkAssetUrls();
    const resolveCjk = cjk?.[file];
    if (resolveCjk) return resolveCjk();
    if (!cjk) {
      throw new MissingCjkAddonError(
        `Bundled font ${file} needs the optional CJK add-on — install @betteroffice/fonts-cjk`
      );
    }
  }
  throw new Error(`Unknown bundled font asset: ${file}`);
}
function loadBundledFontBytes(face, options) {
  const baseUrl = options?.baseUrl === void 0 ? void 0 : resolvedAssetBase(options.baseUrl);
  const bytes = assetUrl(face, baseUrl).then((url) => loadFontBytes(face, url));
  if (baseUrl !== void 0 || !CJK_FILES.has(face.file)) return bytes;
  return bytes.catch((error) => {
    if (!(error instanceof MissingCjkAddonError)) throw error;
    return loadBundledFontBytes(
      resolveMetricCompatFace(
        face.family.includes("Serif") ? "Times New Roman" : "Arial",
        face.weight === 700,
        face.style === "italic"
      )
    );
  });
}
var registeredFaces = /* @__PURE__ */ new Map();
function registerBundledFontFace(face, cssFamily, options) {
  if (typeof document === "undefined" || typeof FontFace === "undefined" || document.fonts === void 0) {
    return Promise.resolve();
  }
  const family = cssFamily ?? face.family;
  const key = `${family}|${face.weight}|${face.style}`;
  const existing = registeredFaces.get(key);
  if (existing) return existing;
  const promise = (async () => {
    const bytes = await loadBundledFontBytes(face, options);
    const fontFace = new FontFace(family, bytes, {
      weight: String(face.weight),
      style: face.style
    });
    await fontFace.load();
    document.fonts.add(fontFace);
  })();
  promise.catch(() => {
    if (registeredFaces.get(key) === promise) registeredFaces.delete(key);
  });
  registeredFaces.set(key, promise);
  return promise;
}
function createFontProvider(options) {
  const resolvedOptions = options?.baseUrl === void 0 ? void 0 : { baseUrl: resolvedAssetBase(options.baseUrl) };
  return fontProvider((face) => loadBundledFontBytes(face, resolvedOptions));
}
export {
  BUNDLED_FONTS,
  WORD_FAMILY_ALIASES,
  createFontProvider,
  loadBundledFontBytes,
  maxDigitWidth,
  registerBundledFontFace,
  resolveBundledFamilyFace,
  resolveDigitAdvance,
  resolveGlyphFallbackFace,
  resolveLastResortChoice,
  resolveLastResortFace,
  resolveMetricCompatFace,
  resolveMetricCompatFamily,
  resolveScriptFallbackFace
};
