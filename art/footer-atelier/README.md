# Footer Atelier components

The owner approved this modular footer on October 3, 2026 for implementation in AshenSpire. The five PNG masters were generated using OpenAI's built-in imagegen tool, with prompts recorded in `prompts.json`; no third-party artwork was imported. `source-manifest.json` retains the original Footer Atelier source hashes, including the separately published stamina components.

The new components are the blank End Turn plate, draw pile, spent-card pile, potion cradle and connector. Text is absent from these masters: labels, live values, text positions and font settings belong to the game/editor layout. `approved-layout.json` preserves the editor's assembled layout; its sample values are illustrative only. The matching stamina and mana art ships separately under `assets/ui/stamina-orb/`.

`export.mjs` crops only transparent margins, using alpha > 20 as in Footer Atelier. It keeps aspect ratios and alpha, scales the plate inside 768px and other components inside 512px, and writes runtime WebP at quality 90 / alpha quality 100 / effort 6. `export-receipt.json` records original hashes, exact crop rectangles and runtime dimensions. Original PNG masters remain intact.

Run `node art/footer-atelier/export.mjs <path-to-sharp>` from this repository, then `node tools/mobile-art.mjs` and `node tools/manifest.mjs --write`. Light twins use the repository's existing 5/16 scale, quality 35 / alpha quality 40 policy; these files and provenance must be generated, never edited manually.
