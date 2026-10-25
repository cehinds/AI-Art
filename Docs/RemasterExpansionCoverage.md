# Remaster expansion: animation and environment coverage

**575 total expansion native PNGs, 63 selected source sheets, 39 timed animation clips, and 78 individual native/3× GIFs.** Existing Batch 01 and Campaign assets are preserved. 29 superseded source candidates remain on disk with explicit exclusion reasons; 0 source PNGs are unregistered.

| Group | Exported PNGs | Native pixels | Pixels per Unity unit |
| --- | ---: | --- | --- |
| animated-tiles | 16 | 32x32 | 32 |
| animated-props | 4 | 64x64 | 32 |
| tiles | 260 | 32x32 | 32 |
| world-tiles | 85 | 64x64 | 64 |
| field | 48 | 64x64 | 32 |
| world-props | 56 | 128x128, 64x64 | 64, 32 |
| battle | 90 | 128x128 | 64 |
| world-vehicles | 16 | 128x128 | 32 |

This expansion covers 9 party members (Firion, Maria, Guy, Leon, Minwu, Josef, Gordon, Leila, Ricard), each with six attack frames and four cast frames; 48 directional field walk states across 4 characters; 25 environment families with ten-tile and sixteen-tile sets; sixteen animated water/lava tiles; and four torch frames. It is a new candidate set rather than a higher-resolution replacement of every old campaign sprite or an audit of all original maps.

## World Builder 100 — current pass

Exactly **100 new 32×32 tiles in ten biome sets** plus **32 static world sprites** (16 vehicle direction views, 8 trees, 8 mountain/cave landmarks) add 132 PNGs while preserving all 282 pre-request PNGs and metadata. No animation clips were added; vehicle directions are static choices.

[Gallery](../Review/remaster-expansion/worldbuilder100/index.html), [construction guide](../Review/remaster-expansion/worldbuilder100/construction-guide.md), [100-tile contact](../Review/remaster-expansion/worldbuilder100/tiles-100-contact.png), [32-object contact](../Review/remaster-expansion/worldbuilder100/objects-32-contact.png), [native 320×320 atlas](../Review/remaster-expansion/worldbuilder100/tiles-100-native-atlas.png), and [coordinate/ID map](../Review/remaster-expansion/worldbuilder100/atlas-coordinates.json) isolate the new collection from older assets. Every packed atlas cell reconstructs its actual native RGBA pixels exactly. Older coast, deep/shallow-water, lava, dock and snow kits are complementary reuse, not counted in the new 100.

The initial batch was archived with all 132 PNGs, metadata and proofs before explicitly authorized correction of natural-biome dividers and mountain edge endcaps. Selected source revisions passed independent native-size review; texture density, repetition and cross-biome joins remain candidates. Inner/concave corners, full transition combinations, multi-level ramps/slopes, autotiling and runtime collision setup remain missing. The fantasy propeller-plane is an optional extension.

## Actual motion artifacts

- [Main-party attack review loop](../Review/remaster-expansion/party-attacks-review-3x.gif): actual exported PNGs side by side, with a clearly labeled review loop. The original attack duration is 640 ms; an additional 600 ms recovery hold makes the review cycle 1240 ms. Production attacks remain nonlooping.
- Individual clips live under Review/remaster-expansion as group-owner-clip-native.gif and group-owner-clip-3x.gif. Attacks use 100/120/70/90/110/150 ms; casts use 160/180/100/200 ms and remain nonlooping. Walks deliberately reuse the middle passing state in a four-entry timeline at 120/80/120/80 ms. Water/lava and torch loop with their declared timing.
- [Offline motion controls](../Review/remaster-expansion/index.html) provide play/pause, step, replay and exact timing. No browser file-URL check was performed for this expansion because an earlier tool denied that URL policy. File and GIF checks are separate evidence.

There are 158 unique native states referenced by 174 timeline entries. Repeated walk timeline entries reuse the same source state intentionally; distinct state names cannot hide identical exported poses because verification rejects them. Pixel differences alone are not proof of readable action. See [independent source/sequence QA](RemasterAnimationSources.md).

## Incremental preservation

[Preservation record](../Review/remaster-expansion/preservation.json) verifies all 282 pre-expansion PNG hashes and metadata hashes unchanged. This pass adds 293 PNGs. The 60.18-pixel battle body cohort is locked by Tools/remaster-expansion/preservation-baseline.json; a new strip that cannot fit fails before any output write rather than resizing older heroes.

## Body registration and pixel density

Battle frames are **128×128 canvases at 64 PPU**, with an approximately **60.18-pixel reference body height**. The remaining canvas preserves complete weapons, capes, wind-up, strike and recovery silhouettes. Canvas resolution is not body height.

Attack and cast strips are normalized together using a first-pose central-body alpha projection and the worst complete weapon/cape extent. Every pose in a strip uses one shared scale. Source lower-body centroids and ground baselines map to a fixed destination anchor; poses are not independently centered on their weapon-inclusive bounding boxes or resized individually. Exact source crops, source/body anchors, shared scale, destination anchor and per-frame offsets are recorded in the manifest. The global body fit is constrained by Leon's full attack silhouette. Independent contact-sequence QA found the previous attack/cast scale pop materially corrected, with grounded baselines and coherent pose order; final perceived smoothness and source anatomical consistency need in-engine review.

The [guest-party attack review loop](../Review/remaster-expansion/guest-attacks-review-3x.gif) shows Minwu, Josef, Gordon, Leila and Ricard with the same review-only recovery hold. [Next art pass](ArtNextPass.md) tracks remaining idle/hit/critical/victory/KO states, other field walks, tile-join repairs and Unity integration.

## Actual tile assembly evidence

[Environment test layout](../Review/remaster-expansion/environment-overview.png) is a compact 2×2 mechanical composition of actual exported assets: a town roof on cobble, a cave room with floor in the center, a shoreline pond with its original small island and sand surround, and repeated grass with the actual Firion field sprite. The field canvas and tiles both use 32 PPU, so their relative scale is explicit. No map pixels or tile edges were painted to make these proofs.

The shoreline uses its named NW/N/NE, W/center/E, SW/S/SE tiles; the original shore-center island is retained because substituting the unrelated deepwater tile produced a stronger rectangular mismatch. The cave room uses floor-01 in its center; wall-center remains available separately. [Tile assembly identities](../Review/remaster-expansion/tile-assemblies.json) and [overview identities](../Review/remaster-expansion/environment-overview.json) record each actual PNG placement.

**Visible texture repetition and joins remain cleanup work**, especially cobble/snow repetition and shoreline center texture changes. These are illustrative test layouts rather than reconstructed original maps, seamlessness claims, or visually repaired concept images. [Environment source/QA ledger](RemasterEnvironmentSources.md) and [online reference evidence](../References/PixelRemaster/README.md) distinguish inspected images from discovery-only sources.

The [extra-family test layout](../Review/remaster-expansion/environment-extras-overview.png) assembles named snow/ice, desert ruins, dock/water and dungeon pieces from actual exports. [Placement records](../Review/remaster-expansion/environment-extras-proofs.json) identify every tile. The dungeon test uses floor at its center; the freestanding open-arch tile remains a separate exported candidate. These tests reveal joins and are not claims of compatible or seamless transitions. The [snow center comparison](../Review/remaster-expansion/snow-center-comparison.png) labels both actual center IDs: the original center retains a snow island, while frozen-ice-01 removes it but adds a rectangular highlight boundary. The accepted overview is preserved; neither variant is claimed seamless.

## Reproduce and verify

```powershell
node Tools/remaster-expansion/export.cjs
node Tools/remaster-expansion/verify.cjs
node Tools/remaster-expansion/coverage.cjs
```

Descriptors are discovered recursively under ArtSource/RemasterExpansion/**/sheets.json; excluded-sources.json preserves rejected revisions. Tile pixels are resampled from entire fixed grid cells to their declared 32×32 or 64×64 targets without visible-object bounding-box fitting. Sprite pixels use exact crop/component selection, a binary alpha threshold and nearest-neighbor resampling only. Existing edited PNGs are protected, existing .meta files are preserved, and no stale assets are automatically deleted.

Strict file validation is **PASS** for all 575 PNGs and 78 individual GIFs: native dimensions, source/config/output hashes, reconstructed source pixels, complete clip order/durations, PPU/pivots, IDs/GUIDs, alpha and source inventories. Decoded GIF alpha matches every native silhouette with no previous-frame trails. Decoded GIF RGB is closest to the intended native frame among all distinct timeline alternatives, including fully opaque animated tiles. Maximum observed mean RGB palette error is **2.2622 /255** against an 18/255 bound. GIF palettes are limited; native PNGs remain authoritative.

## Unity setup and limits

The existing production importer routes RemasterExpansion through RemasterArtReview.ApplyImportSettings. It reads manifest PPU and pivot and sets PPU on both TextureImporter and TextureImporterSettings before settings are applied. Old 16 PPU assets retain their existing scope.

After licensing/import is available, reimport the expansion and run **FF2 > Art > Validate Remaster Expansion Imports**, then **FF2 > Art > Create Missing Remaster Animation Clips**. The generator creates missing .anim files only under Assets/Art/Production/RemasterExpansion/Animations, using actual SpriteRenderer sprite keys, cumulative manifest durations, terminal hold keys and loop flags. Existing .anim files are preserved. No .anim files are claimed to exist until this Unity menu runs. Scene/controller wiring and gameplay remain separate.

The editor helper compiled against installed Unity API assemblies with zero warnings/errors. This is not Unity Editor import, Play mode or a playable build; those were not run for this expansion. No commit, push or publication is performed by the pipeline.
