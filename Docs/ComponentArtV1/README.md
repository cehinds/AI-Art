# Component Art V1 review catalog

This is a combined, asset-only review index. It groups the Altair building kit, opening-region sprites, world component candidates, interior/UI pack, WorldComponentsV2 seam corrections, InteriorComponentsV2 room components, InteriorDetailsV3 reference refinements, InteriorDetailsV4 wall and rug revisions, TerrainComponentsV3, and ShopInteriorsV1. The page reads each pack manifest so counts and previews can be refreshed as assets arrive.

## Status

**Candidate art only; game integration is on hold.** These previews do not establish playability, retail parity, legal rights, or Unity import behavior. Do not treat any image in this catalog as approved runtime content.

WorldComponentsV1 has known visual limitations: the coast set is a continuous island atlas with grass in its center, rather than an open-water-centered atlas; repeated coast edges show texture/shape phase changes; coast and river grass differ; and river bank widths change at joins. Bridge endpoints and mountain ridge behavior remain review candidates. No WFC, seamless tiling, or certified edge compatibility is claimed. See the [world component visual review](../WorldComponentsV1/visual-review.md) and [reference comparison](../WorldLayerComparisonV1/README.md).

Altair building facades and roofs are separated as transparent, same-canvas layers; assembled previews are included for checking the full forms. Signs and terrain props are included from the Altair manifest. This catalog is an inventory view, not an approval of every building detail against the PR map.

Interior previews group separately exported layers and nine-slice cells beneath their owning component. The current manifest has **21 top-level components and 109 unique PNG outputs**: 21 base images plus 16 layer images and 72 slice images. The combined index counts unique PNG paths across packs separately from top-level manifest entries; the current pack totals are 35 AltairKitV1, 4 OpeningWorldV1, 38 WorldComponentsV1, 109 InteriorComponentsV1, 68 WorldComponentsV2, 166 InteriorComponentsV2, 9 InteriorDetailsV3, 5 InteriorDetailsV4, 55 TerrainComponentsV3, and 50 ShopInteriorsV1 (539 unique production PNG paths total, including reused components and layered room proofs).

## Refresh

From the `AI-Art-FF2` repository root, run:

```powershell
node Review/component-art-v1/build-catalog.cjs
```

The script reads manifests from `Assets/Art/Production/{AltairKitV1,OpeningWorldV1,WorldComponentsV1,InteriorComponentsV1}` and writes only `Review/component-art-v1/index.html`. A pack without a manifest is reported as missing; rerun after its export to include its assets. Preview images link directly to the manifest-declared production PNGs and render over a checkerboard to make alpha visible. Interior child previews enumerate each manifest `layers` and `slices` file without counting them as additional top-level components.

## Related reviews

- [AltairKitV1 building and sign gallery](../../Review/altair-kit-v1/index.html)
- [OpeningWorldV1 contact sheet](../../Review/opening-world-v1/contact-sheet.png)
- [WorldComponentsV1 gallery](../../Review/world-components-v1/index.html)
- [InteriorComponentsV1 gallery](../../Review/interior-components-v1/index.html), when exported
- [World-layer reference comparison](../../Review/world-layer-comparison-v1/index.html)


## WorldComponentsV2 — 2026-10-31

The [revised terrain gallery](../../Review/world-components-v2/index.html) adds 47 coast masks, 16 river masks, ocean fill, and four river mouths. V1 remains available for comparison. Matching four-pixel boundary bands pass 648 compatibility checks and 700 joins across the proof layouts; this verifies static asset connectivity, not runtime integration or animated water. The [Pixel Remaster comparison](../../References/WorldComponentsV2/Comparison/index.html) records the remaining brighter grass and more regular coast shapes. Game integration stays deferred.

## InteriorComponentsV2 — 2026-10-31

The [joined interior kit](../../Review/interior-components-v2/index.html) adds floors, separate wall faces and cutcaps, doorways, stairs, and three carpet palettes with inside and outside corners. [Room comparisons](../../References/InteriorComponentsV2/Comparison/index.html) use attributed FFII Pixel Remaster references. See the pack verification receipt for exact tested join classes; a wall/floor material boundary is not treated as identical artwork. Earlier components and approved cursor art are preserved. Game integration remains deferred.

## InteriorDetailsV3 — 2026-10-31

The [focused interior refinement](../../Review/interior-details-v3/index.html) contains seven primary designs across nine PNG exports: three patterned rugs, two north-wall styles at two resolutions, and two golden wooden counters. [Original-reference / new-asset boards](../../References/InteriorDetailsV3/Comparison/index.html) preserve actual screenshot crops on the left. Occluded rug regions are inferred continuations of visible patterns. These whole decorative assets preserve motif detail; the pack does not replace V2 autotiles or claim new arbitrary-size rug/counter joins. Game integration remains deferred.

## InteriorDetailsV4 — 2026-10-31

The [wall and rug revision](../../Review/interior-details-v4/index.html) contains five whole components: three rugs, Hilda's tall wall with dark overhead timber, and Scott's wide wall strip with unequal bays. [Original-reference / V4 comparisons](../../References/InteriorDetailsV4/Comparison/index.html) show authentic screenshot crops beside the new native exports. The pass reduces added rug grids and restores reference wall proportions. Occluded rug areas remain inferred, and the designs retain differences in motif density and color. No new seamless tiling or game integration is claimed. Earlier packs remain unchanged.

## Terrain and shop pass — 2026-10-31

[TerrainComponentsV3](../../Review/terrain-components-v3/index.html) supplies 55 PNGs: four ground materials, sixteen dirt-road masks, sixteen cobble-road masks, sixteen river masks, two city trees and one overworld forest field. Directional tags and source records accompany the tiles. Roads, rivers and declared floor boundaries have independent four-pixel join checks; forest boundaries are diagnostic only. The dirt roads are optional authored assets, not evidence that the sampled retail overworld route has roads.

[ShopInteriorsV1](../../Review/shop-interiors-v1/index.html) contains nine new components, sixteen byte-preserved reused components, and five layered room proposals (weapons, armor, items, combined magic, temple). Ordinary shops share their red floor, wall and counter kit; stock displays and NPCs vary. The temple uses a distinct stone/blue treatment. Static PNG attendants and proposed occupancy metadata do not implement game behavior. [Reference comparisons](../../References/TerrainShopPassV1/Comparison/index.html) distinguish observed retail details from proposals. Game integration remains on hold.
