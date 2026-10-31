# World Seams V2 reference review

Status: refreshed against the latest static proof exports and visually inspected on 2026-10-31. This is an asset-sheet and assembly comparison, not gameplay/runtime verification.

## Reference and attribution

The supplied FFII Pixel Remaster route frames are associated with Vorxu's [Altair & Fynn walkthrough](https://vorxu.com/final-fantasy-2-pixel-remaster/walkthrough/altair-and-fynn), specifically its Altair-to-Gatrea and Gatrea-to-Fynn gameplay clips. Reference-only crops are copied byte-for-byte from `C:/repos/AI-Art-FF2/References/WorldLayerComparisonV1/crops/`. They are comparison references, not production art. No exact video timestamps were supplied.

## V1 baseline gaps

- The V1 river loop has channel/bank width drift at joins, especially the lower-right bend/straight connection.
- V1 river ends and cross openings visibly narrow or widen at joins; bank positions are not registered to one shared profile.
- Coast and river atlas grass differ in color/texture block; cross-family ground matching was not approved.
- V1 coast repeats coastline bulges and exposes texture-phase changes at some cell boundaries. Its nine-piece set has no concave land corners or one-cell islands.

## V2 visual findings

- Latest N/S and E/W river-mouth assemblies both show a consistent narrow blue core, cyan transition, and continuous cream bank at the displayed join. The winding-river sample has rounded bends and no visible ladder stripes. Approximate native source profile, as reported with the export: blue core 5–7 px, bank 1–2 px per side, outer fringe 0–1 px. These findings address the displayed assemblies only.
- The updated contact sheet shows the sixteen river mask topologies and coast components. It confirms atlas inventory presence, not gameplay behavior or all possible transitions.
- Concave inlet, peninsula, and small island examples are present. Thin cream shore is visible, but coast outlines remain mostly orthogonal and less naturally flowing than the PR reference.
- Coast and river greens are compatible in the mixed-mouth samples. V2 grass is brighter and more finely patterned than PR's broader, darker value patches.
- Static imagery cannot establish animated water phase continuity or game-scale/runtime readability. No blanket seamlessness claim is made.

## Included proof

The PNGs in `v2-proof/` are refreshed copies of the latest `AssetWork/WorldSeamsV2/Review/world-components-v2/` exports, including both mouth directions and the contact sheet. Review the native and 3× images side by side in [index.html](index.html).
