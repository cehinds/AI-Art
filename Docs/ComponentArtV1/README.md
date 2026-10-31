# Component Art V1 review catalog

This is a combined, asset-only review index. It groups the Altair building kit, opening-region sprites, world component candidates, and interior/UI pack. The page reads each pack manifest so counts and previews can be refreshed as assets arrive.

## Status

**Candidate art only; game integration is on hold.** These previews do not establish playability, retail parity, legal rights, or Unity import behavior. Do not treat any image in this catalog as approved runtime content.

WorldComponentsV1 has known visual limitations: the coast set is a continuous island atlas with grass in its center, rather than an open-water-centered atlas; repeated coast edges show texture/shape phase changes; coast and river grass differ; and river bank widths change at joins. Bridge endpoints and mountain ridge behavior remain review candidates. No WFC, seamless tiling, or certified edge compatibility is claimed. See the [world component visual review](../WorldComponentsV1/visual-review.md) and [reference comparison](../WorldLayerComparisonV1/README.md).

Altair building facades and roofs are separated as transparent, same-canvas layers; assembled previews are included for checking the full forms. Signs and terrain props are included from the Altair manifest. This catalog is an inventory view, not an approval of every building detail against the PR map.

Interior previews group separately exported layers and nine-slice cells beneath their owning component. The current manifest has **21 top-level components and 109 unique PNG outputs**: 21 base images plus 16 layer images and 72 slice images. The combined index counts unique PNG paths across packs separately from top-level manifest entries; the current pack totals are 35 AltairKitV1, 4 OpeningWorldV1, 38 WorldComponentsV1, and 109 InteriorComponentsV1 (186 unique PNGs total).

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

