# Painted book layers, revision 2

Three reusable neutral-leather book bases (classic, scholar, field) and eleven
independent painted metal emblems (blade, shield, focus, paired, spell,
universal, reaver, starseer, rogue, herald, feat).

All fourteen masters were made with OpenAI's built-in image generator,
referencing the project's original approved Shield Manual. Exact prompts and
generation locations are in `provenance.json`; PNG masters are under `masters/`.
No third-party artwork was used or third-party license claimed.

`export.mjs` regenerates 640px high-quality runtime layers at
`hd/assets/shop/painted/{covers,symbols}/`. The normal root
`tools/mobile-art.mjs` generates light twins and provenance; regenerate the
manifest afterward with `node tools/manifest.mjs --write`.

The game renderer recolors neutral leather across the complete binding,
including spine, back-cover edge and ribbon, while protecting warm brass and
parchment. Emblems preserve their tonal detail and have independently
selectable metal finish. The game's `src/content/bookArtPresets.js` owns the
recipes. Book Atelier in the game preview and in AshenedSpire-Editor edits
those same recipes. Cover and emblem layers are never flattened together.
