// ============================================================================
// data/palettes.js — semantic color palettes (single source of truth for color)
// ----------------------------------------------------------------------------
// Pure data. No raw hex appears in character/equipment/spell definitions — they
// reference the semantic token names below, and palette-service resolves them.
//
// PSP-era (Dawn of Souls / Anniversary) shading style: each MATERIAL is a 5-stop
// ramp so forms read as rounded rather than flat NES blocks:
//   outline  - darkest, the 1px border around a form
//   shadow   - core shadow / underside
//   base     - the main local color
//   light    - lit surface
//   highlight- brightest specular touch
//
// Biological colors (skin/hair/eyes) are also ramps where it helps shading.
//
// Loaded before sprite-gen-service. Shares the global scope (no import/export).
// ============================================================================

var PALETTES = {
  // ── Skin tones (outline, shadow, base, light, highlight) ──
  skin: {
    fair:   ["#6b4733", "#b07a55", "#d99a6c", "#f0bd8e", "#ffe0c0"],
    tan:    ["#5a3a26", "#8f5a38", "#bd7c4e", "#dba072", "#f3c79a"],
    dark:   ["#3a2418", "#5e3b26", "#83563a", "#a87554", "#caa07a"],
    pale:   ["#7a5a4a", "#bd9484", "#e0baa8", "#f2d4c6", "#fff0e6"],
    elf:    ["#5a5a4a", "#9a9a7a", "#c2c2a0", "#dcdcbe", "#f2f2e0"]
  },

  // ── Hair colors (outline, shadow, base, light, highlight) ──
  hair: {
    dark_brown: ["#1d130c", "#3a2a20", "#574033", "#7a5c46", "#9c7a5e"],
    black:      ["#0d0d12", "#1c1c24", "#2e2e3a", "#454556", "#5e5e72"],
    blonde:     ["#7a5c1e", "#a8862e", "#d8c070", "#ecdc96", "#fbf2c6"],
    red:        ["#5a1e10", "#8a3018", "#b8482a", "#d66a44", "#ee9468"],
    silver:     ["#5a5a66", "#8a8a96", "#b4b4c0", "#d4d4de", "#f2f2f8"],
    white:      ["#7a7a86", "#a8a8b4", "#cacad4", "#e6e6ee", "#ffffff"]
  },

  // ── Eye colors (single accent + a darker rim) ──
  eyes: {
    ice_blue:  ["#2a5a7a", "#7ab8e0"],
    brown:     ["#3a2414", "#8a5a32"],
    green:     ["#1e4a2a", "#4aa05a"],
    amber:     ["#6a4410", "#d89a30"],
    grey:      ["#3a3a44", "#9a9aa8"]
  },

  // ── Materials (outline, shadow, base, light, highlight) ──
  materials: {
    iron:    ["#2a2e36", "#454c59", "#697283", "#9aa4b4", "#cdd4df"],
    steel:   ["#33373f", "#565d6b", "#828b9b", "#b3bcca", "#eef2f8"],
    leather: ["#2e1d12", "#4f3320", "#6f4a30", "#8f6644", "#b08a62"],
    hide:    ["#3a2c1a", "#5e472b", "#80623d", "#a08056", "#c0a276"],
    cloth:   ["#2a2438", "#453c5a", "#645a80", "#8a80a6", "#b4abcc"],
    gold:    ["#6a4a10", "#9a7320", "#caa53a", "#e6c960", "#fbea9c"],
    wood:    ["#3a2616", "#5c3e24", "#7e5836", "#a0764e", "#c0996e"],
    bronze:  ["#4a2e16", "#7a4e26", "#a8723e", "#caa05a", "#e6c684"]
  },

  // ── Generic accents used by effects / spell icons ──
  fx: {
    fire:    ["#7a1e0a", "#c44218", "#f07028", "#ffa850", "#ffe0a0"],
    frost:   ["#1e4a6a", "#3a7ab0", "#6ab0e0", "#a8dcf4", "#e0f6ff"],
    shock:   ["#5a4a0a", "#a88a1a", "#e0c83a", "#f4ec80", "#ffffc0"],
    healing: ["#1e5a2a", "#3a9a4a", "#6ad07a", "#a8eeb0", "#e0ffe6"],
    arcane:  ["#3a1e5a", "#6a3a9a", "#9a6ad0", "#c8a8ee", "#eee0ff"]
  }
};
