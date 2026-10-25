# Full card portrait library

237 individually identified paintings cover 220 canonical AshenSpire cards and
17 equipment profiles. The 215 upgrade definitions reuse their base artwork.
`inventory.json` records the roster and source game commit; each `receipts/` entry
records its exact prompt, built-in OpenAI image generator provenance, dimensions
and SHA-256. PNG masters are 1024 x 1536 with extended scenery for mouse cropping.

These are first-party generated artworks based on the owner's approved game
references. No third-party asset license is claimed. Frames, cost symbols, names
and rules are rendered separately by the game and the Card Assembler.

Desktop images live in `hd/assets/cards/extended/`, with 1024px and 512px-wide
exports per subject. Mobile twins are generated from those high files by
`node tools/mobile-art.mjs`; do not copy independently encoded light images into
the release. The game pins the resulting art release normally.

The Editor's optional Card artwork library uses the 1024px-wide WebPs. It imports
only the selected image into a saved composition and keeps its original pixels
available for reversible mouse trimming. Eight additional choices have sources
in `../card-variants-2026-10-06/`.
