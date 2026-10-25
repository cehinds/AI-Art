# World Builder Expansion 02

Created with built-in ImageGen, following the approved FFII environment study and existing world props. This is an additive candidate asset batch for the original Japanese Final Fantasy II project.

## Delivered

- 24 transparent, static world-object sprites at 128x128: village/farm furnishings, road/ferry fixtures, and camp/fortification objects.
- 32 opaque tiles at 64x64: 16 river pieces (straights, four bends, four T-junctions, crossing, spring, ford, stepping stones and fills) and 16 raised stone terrace pieces (outer edges/corners, four concave corners and fills).
- Individual PNGs with stable IDs and Unity .meta files, five selected source masters, full generation prompts, source crops/hashes, native contact sheets, actual tile/prop assemblies, and a portable review package.

All new files use 64 pixels per Unity unit. A tile occupies one world unit; a 128px prop canvas occupies two. Existing assets retain their original settings. These are 24 distinct static objects, not animation frames. No new animation clips were added.

## Files

- `ArtSource/RemasterExpansion/worldbuilder-expansion02/`: selected source PNGs, generation.json, sheets.json, and explicit map proof layouts.
- `Assets/Art/Production/RemasterExpansion/world-props/`: village-expansion02, road-expansion02 and camp-expansion02.
- `Assets/Art/Production/RemasterExpansion/world-tiles/`: river-expansion02 and terrace-expansion02.
- `Review/remaster-expansion/worldbuilder-expansion02/index.html`: standalone review gallery.
- `Review/worldbuilder-expansion02.zip`: portable review package.

The Unity project already points to this art checkout through its Assets/Art junction, so the new assets are visible at that location without copying over older artwork.

## Visual review and provenance

The selected masters retain the approved cream/gray stone, blue cloth and roof accents, ochre wood, green foliage and clustered pixel treatment. Native 128px prop contacts were inspected for eight distinct silhouettes per sheet, transparent margins and readable shapes. All 24 objects are present. Native 64px river and terrace contacts were inspected in row-major order.

The initial river master contained artificial dark divider lines; a targeted ImageGen edit removed them. The initial terrace master contained soil gutters between paving cells; its selected revision removes those interior gaps. Earlier masters remain preserved under `ArtSource/Revisions/worldbuilder-expansion02/`. Full initial and revision prompts are recorded in generation.json. No reference screenshot pixels were used as production exports.

Map proofs assemble the exported PNGs directly at their native sizes. They show a river crossing with road props, a raised terrace camp, and a concave-corner courtyard. No proof image was painted over to hide seams. Some repeated texture phases and small bank offsets remain visible; this is not a claim that every possible adjacency is seamless. The added furnishings are compatible expansion designs, not verified reconstructions of particular FFII map objects.

## Verification

The normal exporter and independent source-reconstruction verifier pass for all 470 RemasterExpansion PNGs, 470 unique IDs/GUIDs and the existing 27 timed clips/54 GIF previews. The new batch has 56 native PNGs from five selected source sheets. The batch helper verifies sizes, PPU, alpha contracts, native/source hashes, and preserves all 1,202 earlier production PNGs plus their 1,202 metadata files byte for byte.

Rebuild with `node Tools/remaster-expansion/export.cjs`, `node Tools/remaster-expansion/verify.cjs`, `node Tools/remaster-expansion/coverage.cjs`, and `node Tools/remaster-expansion/worldbuilder-expansion02.cjs`.

Unity Editor import, RuleTile setup, collision, and in-game rendering remain unverified. This batch does not claim a playable game or completed map coverage.
