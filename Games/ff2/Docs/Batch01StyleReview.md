# Batch 01 Style Review

## Approval and scope

The visual direction represented by `Review/art/02-firion-study.png` and `Review/art/03-environment-kit.png` was approved on 2026-10-24. The approval authorizes production in that style. This review applies to visual consistency only; it does not approve exact FFII maps, screen layouts, mechanics, or historical source dimensions.

## Batch 01 plan

| Family | Planned content | Production target | Status |
|---|---:|---|---|
| Terrain | 16 cells | 16 x 16 px each | Exported review candidate |
| Structures | 16 cells | 16 x 16 px each | Exported review candidate |
| Firion field walk | 12 frames (4 directions x 3 frames) | 16 x 24 px per frame; bottom-centered to a 16 x 16 px ground footprint | Exported review candidate |

The frame and tile sizes are production conventions selected to retain the approved compact proportions, not assertions about original-game dimensions. The concept boards are reference material and must not be sliced or marked as production-ready assets.

## Six-point style acceptance

Review at native resolution and integer-scaled nearest-neighbor size. Accept a batch when all six checks pass:

1. **Silhouette and scale:** characters stay compact and recognizable, with Firion's approved bandana, light hair, blue clothing, and warm accents; terrain and structures retain readable 16 px cell boundaries.
2. **Pixel edges:** use intentional square clusters and stepped contours; no blur, filtering, antialiased edges, or stray semitransparent pixels in final opaque art.
3. **Palette discipline:** use restrained, coordinated color ramps with clear value separation; avoid gradients and isolated colors that do not support form or readability.
4. **Material consistency:** water, ground, stone, wood, roofs, and vegetation each use coherent texture and shading consistent with `03-environment-kit.png`.
5. **Gameplay readability:** tile seams, paths, walls, openings, and interactable shapes remain legible at native scale; character feet align to the shared ground footprint.
6. **Batch coherence:** frames and neighboring cells keep consistent outline weight, light direction, palette, scale, and pivot/anchor; no pose or tile looks like it came from a different visual style.

## Review status

`Assets/Art/Production/Batch01/manifest.json` lists 44 assets from three source sheets: 16 terrain tiles, 16 structure tiles, and 12 Firion frames. It reports dimensions, unique IDs, hashes, and sprite alpha as passing; its conservative edge diagnostic reports `MISMATCHES` and explicitly cautions that exact edge equality does not prove visual continuity. The review contact sheet and native atlases were inspected. The tile families share the approved crisp pixel style and material palette. Firion reads very compactly at 16 x 24 px; the alternating stride poses look similar, so legibility of face and walk animation merits particular attention in review.

The batch is **exported-review-candidate**, not accepted final gameplay art. Unity import defaults and the separate review-scene generator are implemented and compile against the installed Unity API; actual Editor import and runtime rendering remain unverified. Exact-source fidelity and final human style acceptance remain unverified. Re-check the manifest and proofs after any re-export before changing these statuses.

The coordinator inspected the final revised path, hut and town/dungeon assemblies after re-export: the earlier artificial dirt grid and central roof gable were removed. Texture repetition and corner/edge polish remain visible review items. A 32 x 48 Firion detail comparison is available outside the production directory; it does not change the native 16 x 24 contract or world footprint.
