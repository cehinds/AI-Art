# Layered manuals, spellbooks and class books

Source: AshenSpire PR #1521 (`codex/manual-shop-assets`).

This package contains original OpenAI-generated painted book masters and
Codex-authored editable SVG symbol/trim layers. The transparent base paintings
have three styles; ten symbols have solid, line and seal variants. Thirty
transparent composition previews illustrate the ten book identities using
each cover style. No third-party art is included.

The game's Book Atelier and shared renderer are maintained in AshenSpire at
`art/manual-shop-2026-10-02/layers/` and `src/ui/components/bookArt.js`.
The recipe module there configures cover, leather color, symbol, treatment,
ink color and trim per book. These files are artwork only and grant no XP or
gameplay abilities themselves.

Original generation prompts and source references are retained in
`provenance.json` and `layers/provenance.json`. Runtime files are under
`hd/assets/shop/`; the repository's own mobile-art tool generates their
light twins and provenance. Existing canonical assets and policies are retained.

To regenerate authored layers, run layers/export.mjs with Sharp and cwebp 1.6.0 available, then run the repository's tools/mobile-art.mjs and tools/manifest.mjs --write to refresh canonical light provenance and the release manifest.

