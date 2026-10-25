# Card art authoring library

60 artworks: 12 designs with five colors each. Physical and Magical
categories each contain Attack, Smash, Counter, Evade, Sweep and Defend. Each
five-image family uses variant 01 as its canonical design; variants 02–05 change
the color palette and aura while retaining that design.

The latest revision updates 49 masters: all 48 color variants and Physical Sweep
01. The other 11 canonical masters remain unchanged from commit
4cea7dd1d609083992c68562a04ed6070eb2b28f. Physical Sweep uses user-selected
Option 14: variant 01 is an exact copy of the selected image, with four color-only
variants of the same pose. This selection replaces only the five Physical Sweep
images from the previous working revision; the other 55 remain unchanged.
Counter artwork retains a shield and sword.

These authoring sources now supply 120 runtime image IDs in
assets/cards/library/. This adds art choices without adding playable cards or
changing card mechanics. Existing runtime images remain available unchanged.
See RUNTIME.md for the source mapping and repeatable integration procedure.

- masters/: 60 individual 1024 × 1536 PNG sources.
- exports/: 120 WebP previews, 512 × 768 and 1024 × 1536.
- shards/: current generation records with full prompts and prior provenance.
- manifest.json: roster, counts, source/export hashes, encoder versions and the
  twelve current design families. Each changed record preserves its complete
  previousRevision, including earlier nested history.
- export.mjs: reproduces the WebP files and verifies their exact bytes.

Physical colors: Steel / blue, Bronze / amber, Iron / crimson, Copper / teal,
Blackened steel / violet. Magical colors: Frost / cyan, Ember / orange,
Lightning / gold, Arcane / violet, Verdant / green.

designFamilies records each family's current variant-01 ID and SHA-256.
An asset's templateId and templateSha256 (or original templateSha field) record
the actual input used for its generation. All five Physical Sweep records refer
to selected Option 14; variant 01 retains its original prompt and generation
source, and selectedOption marks it as an exact copy. Original
generation paths identify sessions; masters/ contains the portable source files.

All artwork was generated with OpenAI image generation under human direction.
The existing AshenSpire shield guided the simple subjects, worn materials and
restrained auras. No third-party licence is claimed or inferred.

The masters, source exports and provenance remain under art/ in
cehinds/AshenSpire-art, excluded from runtime packs. Byte-identical copies of
the 120 exports live under hd/assets/cards/library/; their generated light
twins and art-manifest.json entries are included in runtime packs.
The earlier three-card pilot is separate and is not included.

Reproduce and verify with Node.js, Sharp 0.35.5 and WebP 1.6.0:
node export.mjs --sharp /path/to/node_modules/sharp

Verification covers 60 unique masters, 120 exact export hashes and dimensions,
twelve groups of five, gallery filters, image enlargement, keyboard dismissal
and mobile layout. Runtime integration is checked separately as described in
RUNTIME.md; game assignments and release pins are managed in the game repository.
