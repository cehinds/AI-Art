# FFII Pixel Remaster World Layer Comparison V1

This document compares supplied Final Fantasy II Pixel Remaster route frames with the current-game capture explicitly labeled **BEFORE ocean fix**, and shows four new `OpeningWorldV1` art candidates. The candidates are AI-Art assets only and are not integrated into the game.

## Review files

- [Annotated crop catalog](../../Review/world-layer-comparison-v1/index.html)
- [Side-by-side contact sheet](../../Review/world-layer-comparison-v1/comparison-contact-sheet.png)
- [All supplied source frames](../../Review/world-layer-comparison-v1/source-contact-sheet.png)
- [Source URLs and SHA-256 values](../../References/WorldLayerComparisonV1/sources.json)
- [Exact crop rectangles and layer recommendations](../../References/WorldLayerComparisonV1/crop-catalog.json)
- [OpeningWorldV1 four-asset contact sheet](../../Review/opening-world-v1/contact-sheet.png)

The source captures are copied byte-for-byte under `References/WorldLayerComparisonV1/source-frames/`. Each crop is an exact PNG rectangle under `References/WorldLayerComparisonV1/crops/`; the contact sheet scales crops for display, but the crop files retain their original pixels. None of these images or crops are production art, and nothing is copied to `Assets/`.

The Pixel Remaster route frames are associated with the [Vorxu Altair-to-Gatrea and Gatrea-to-Fynn gameplay clips](https://vorxu.com/final-fantasy-2-pixel-remaster/walkthrough/altair-and-fynn). [Pro Game Guides](https://progameguides.com/final-fantasy/final-fantasy-2-pixel-remaster-walkthrough/) independently describes leaving Altair west, crossing the bridge north to Gatrea, then continuing to Fynn. Local capture timestamps were not supplied, so this catalog identifies the source frame filenames and exact crop coordinates without claiming video timecodes. The sixth Gatrea-to-Fynn image is a black frame and is excluded from the comparisons.

## Layer findings and production gaps

| Layer | Pixel Remaster reference | Current BEFORE capture | Stable asset contract / gap |
| --- | --- | --- | --- |
| Ground | Fine, dense grass texture with broader value patches. | Bright, high-frequency speckle. | Candidate `OpeningWorldV1/grass.png` is 32×32, low-noise, and repeats on all four edges. It is not game-integrated; compare it with a post-fix capture. |
| Ocean | Continuous blue surface with small light ripples. | The supplied old capture has regular grid/streak artifacts. | Existing `deepwater-01..03` contains a left-shore fragment; the frozen, unbuilt renderer binding crops x=3..31. Do not treat the BEFORE image as post-fix evidence. A 32×32 four-frame ocean component is planned separately. |
| Coast | Narrow irregular tan fringe at water edge. | Broad square beach steps. | Existing directional `shore-*` tiles are present. New coast art is planned under `WorldComponentsV1`; target contract keeps water base and a 20% shore-edge band separate. No native post-fix QA yet. |
| Forest | Dense individual dark conifers over a separate floor. | A single mottled hedge-like mass. | Candidate `OpeningWorldV1/conifer.png` is 32×48. The renderer contract places two staggered conifers per logical cell and keeps town hedge canopy separate. Candidate art is not game-integrated; compare density and crown silhouette visually. |
| Mountains | Repeating triangular peaks with crisp light facets and dark separations. | Only a thin strip is visible in the supplied screenshot, partly adjacent to HUD. | Existing `mountain-01..04` tiles are recorded in the crop catalog. New variants are planned under `WorldComponentsV1`; proposed tile scale is 32×32 with cardinal/diagonal edge variants. |
| River | Narrow winding blue channel, thin continuous banks, small highlights. | Chunkier stepped blue path and brown/orange border. | Existing `river-expansion02` connectivity masks cover straights, bends, tees, and cross. New river-edge components are planned under `WorldComponentsV1`; keep water ports N/E/S/W and banks separate. |
| Bridge | Small gray stone deck with squared abutments. | The visible bridge is brown wood and partly covered by the top HUD. | Existing coast bridge tiles are wood, not stone. A new 32×32 stone NS/EW pair is planned, with road ports at both ends and river continuing underneath. |
| Settlement | Walled compound with clustered blue roofs and a central keep. | No walled settlement is visible in this viewport. | Candidates `altair-town.png` (160×128, 5×4) and `fynn-town.png` (160×192, 5×6) have bottom-center anchors above the south gate. They are not game-integrated. |
| Actors | Small party-leader sprite rendered independently over terrain. | Larger clustered avatar. | Existing directional `field/firion/{down,left,right,up}-01..03` art is recorded in the crop catalog. Keep actor and foot anchor independent from terrain. The screenshot comparison does not establish a replacement need. |
| UI | Top-right minimap is overlaid in screen space. | Title/objective/menu bars above and control bar below. | Keep minimap and HUD in a viewport-space layer, outside terrain, shore, river, settlement, and actor passes. |

## Recommended draw order

1. Ground base and forest floor.
2. Ocean/river water surfaces.
3. Coast and river-bank overlays.
4. Terrain overlays: mountains, individual forest canopies, and walled settlements.
5. Bridges and actors.
6. Screen-space minimap and HUD.

The bridge deck must draw over the river while retaining visible water on both sides. Settlement walls and gate openings should remain in their own layer so road access and collision can follow the active world map plan rather than a flattened screenshot crop.

## Scope limits

- The current capture predates the ocean fix. The current renderer binding is frozen/unbuilt; no post-fix native screenshot was supplied.
- The supplied frames show route landmarks, not a complete world-map tileset or exact pixel-art source sheet.
- Screenshot zoom differs between the reference captures and current window. Visual similarity findings cover texture, silhouette, edge width, and layering, not exact color values or one-to-one pixel dimensions.
- A renderer contract or generated candidate does not prove native visual fidelity. Compare a fresh in-game screenshot after the renderer and assets are assembled.
- PR screenshots and the derived crops remain reference-only. Do not use them as runtime sprites or claim a license grant.
