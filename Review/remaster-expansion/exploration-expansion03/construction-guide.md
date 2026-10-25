# Exploration Expansion 03

An additive FFII candidate art batch matching the approved field-character and environment references. Generated with built-in ImageGen; no reference screenshot pixels are exported as production artwork.

## Contents

- 36 transparent 64x64 field frames: Maria, Guy and Leon, three poses in each of four directions, at 32 PPU.
- 12 looping walk definitions with native and 3x GIF previews. Each direction uses contact A, passing, contact B, passing at 120/80/120/80 ms.
- 16 transparent 128x128 props at 64 PPU: eight mine fixtures and eight crystal/rock formations.
- 16 opaque 64x64 cavern tiles at 64 PPU: outer walls/corners, four concave corners and four fills.

The mine fixtures include a shaft headframe, winch, ore bucket, ore chute, rail stop, tool rack, sorting table and ventilation bellows. Grotto props include sapphire, amethyst, emerald and amber clusters, an open geode, an iron-ore boulder, stalactites and stalagmites.

## Review and provenance

- `Review/remaster-expansion/exploration-expansion03/index.html`: standalone gallery, actual native exports, walk GIFs and tile/prop map assemblies.
- `Review/exploration-expansion03.zip`: portable review and asset package.
- `ArtSource/RemasterExpansion/exploration-expansion03/`: six selected masters, full prompts, exact crop descriptors and explicit proof layouts.
- `ArtSource/Revisions/exploration-expansion03/`: preserved earlier Maria, Leon and cavern masters.
- `Review/remaster-expansion/exploration-expansion03/inventory.json`: source/export hashes, IDs, crop rectangles, PPU, timings and measured character scale.

Maria keeps her violet hair, red scarf/headband and bow/quiver; Guy retains the green/ochre outfit and strapped axe; Leon retains dark armor, gold trim and cobalt cape. Leon's field weapon is completely stowed under his cape in the selected sheet to remove inconsistent sword placement. The cavern revision removes artificial atlas divider lines.

Each character sheet uses one shared scale, with measured crops and foot anchoring. Uneven source-row spacing required explicit crop boundaries; a uniform grid would have clipped boots and included neighboring poses. The corrected native silhouettes span 54-58 pixels high, compared with 57-58 for Firion; the front poses are slightly shorter. Characters at 32 PPU occupy a two-unit canvas; environment tiles at 64 PPU occupy one unit. The review includes the previous Firion idle sprite as a scale reference. Map proofs assemble actual exported PNGs without painting over their seams.

## Verification and limits

The batch helper checks 68 native PNGs, 12 walk clips, six source masters, dimensions, PPU, transparency and hashes, and verifies that all 1,258 earlier production PNGs and their metadata remain unchanged. Run the standard exporter, reconstruction verifier, coverage report and batch helper:

```text
node Tools/remaster-expansion/export.cjs
node Tools/remaster-expansion/verify.cjs
node Tools/remaster-expansion/coverage.cjs
node Tools/remaster-expansion/exploration-expansion03.cjs
```

These are candidate walk animations. Opposing foot contacts still need polish, particularly Maria's front/back and Leon's side views; distinct files and valid timing do not establish a convincing gait. Repeated texture phases and wall offsets can remain visible in assembled cavern rooms. No universal seamless adjacency, exact reconstruction of a named FFII location, or completed game is claimed.

Unity Editor import, animation playback, collision and RuleTile configuration remain unverified. The existing game-to-art junction makes the files accessible to the game checkout; it does not prove runtime integration.
