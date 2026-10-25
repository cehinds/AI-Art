# Remaster expansion pipeline

## World Builder Expansion 02

`worldbuilder-expansion02.cjs` builds an additive review collection after the standard exporter has processed its five source sheets. It preserves and verifies the SHA-256 hashes of all 1,202 preexisting production PNGs and their 1,202 metadata files against `worldbuilder-expansion02-baseline.json`. The helper never generates or repaints artwork.

```powershell
node Tools/remaster-expansion/worldbuilder-expansion02.cjs --preservation-only
node Tools/remaster-expansion/export.cjs --check-only
node Tools/remaster-expansion/export.cjs
node Tools/remaster-expansion/verify.cjs
node Tools/remaster-expansion/worldbuilder-expansion02.cjs
```

The helper checks 24 transparent 128×128 props and 32 opaque 64×64 tiles at 64 PPU, copies their exact native PNG bytes into the portable review folder, and emits row-major native contacts, an HTML gallery and a source/native hash inventory. Exact crop rectangles and sprite registration are retained from the exporter manifest. Sprite normalization uses the existing shared-sheet scale; tiles use whole-cell nearest-neighbor normalization. Optional `proof-layouts.json` next to the new source descriptor supplies explicit `key`, `owner`, `columns`, row-major tile `cells`, and optional `props` with `owner`, `name`, `x`, `y` pixel coordinates. These produce actual native tile/prop map composites at 64 PPU. Assemblies expose join quality; they do not certify seamlessness or Unity runtime behavior.

Review output: [World Builder Expansion 02](../../Review/remaster-expansion/worldbuilder-expansion02/index.html). New 64px tile owners use `world-tiles` so the earlier 32px tile proof renderer retains its original contract.

Run `export.cjs`, `verify.cjs`, and `coverage.cjs` with Node from the repository root. The scripts use installed `sharp` or the bundled Codex Node package. They are offline mechanical asset processing; ImageGen source generation is separate.

Sources and descriptors live recursively under `ArtSource/RemasterExpansion/`. A `sheets.json` can be an array or an object with `sheets`; exclusions can be `excludedSources` or a neighboring `excluded-sources.json` array/object. Every PNG must be exported or explicitly excluded. Output PNGs are isolated under `Assets/Art/Production/RemasterExpansion`; review GIFs, HTML, source/native contacts and tile assemblies stay outside Unity imports.

Each sheet requires `key`, `source`, `columns`, `rows`, `target:[width,height]`, `kind`, `group`, `owner`, `ppu`, `pivot`, and row-major `frameNames` for sprites or `names` for tiles. Names and IDs use lowercase hyphenated keys. IDs are `remaster:<group>.<owner>.<frame>`. Optional `region` and source-pixel `cellRects` record inspected overrides. Tile cells use whole-cell normalization, never sprite alpha bounding-box fitting; non-square source tile cells are rejected.

A `clip` supplies `name`, `loop`, and `durationsMs`, using all sheet frames unless `frames` explicitly chooses their order. `clips` can declare multiple named timelines over one sheet. Timing is explicit and must be at least 20 ms in 10 ms steps so GIF timing is exact. Reusing the same frame ID in a walk timeline is intentional; distinct native state names containing identical poses are rejected.

Sprite normalization uses one scale per source strip, grounded lower-body alpha centroids, fixed destination anchors and recorded offsets. Battle attack/cast sources share the frozen humanoid body-height cohort recorded in preservation-baseline.json (60.177966570489886 pixels). New sources must fit that height within their native canvas without clipping; they cannot shrink earlier heroes. A first-pose central body projection avoids treating the full weapon box as body height. `bodyReferenceFrame`, `bodyHeightNative`, `frameAnchors` (global source pixels) and `padding` can record explicit registration choices. No pose is independently resized. Sparse overlapping atlas rectangles can be separated by exact 8-connected alpha components assigned to measured source anchors; ambiguous assignments fail.

`verify.cjs` reconstructs every native PNG from source pixels, validates metadata/inventories/clip declarations, decodes each GIF, checks frame count/timing/loop flags and exact silhouette disposal, and compares decoded RGB against both its intended native frame and all alternative timeline frames. Only reuse of identical source state pixels permits a tie. RGB palette error is bounded; native PNGs remain authoritative. None of these file checks establishes anatomical quality, seamless tiles, Unity import or runtime behavior.

`RemasterArtReview.cs` provides scoped PPU/pivot import declarations, an imported-sprite validation menu, and a create-missing-only Unity AnimationClip generator. It does not overwrite existing clips or wire gameplay. No browser file-URL QA is performed; native/3× GIFs and actual PNG assembly evidence provide review artifacts.

## Incremental integration and preservation

Before the first incremental delivery, `node Tools/remaster-expansion/preservation.cjs` captured the existing 168 native PNG SHA-256 hashes, their metadata hashes, content IDs/paths, and the established battle body-height cohort in `preservation-baseline.json`. The snapshot is immutable during ordinary export. `Review/remaster-expansion/preservation.json` records the after-integration comparison; the current pass preserves all 168 PNGs and all 168 metadata files byte for byte while adding 114 PNGs.

Use the read-only preflight while sources are being prepared:

```powershell
node Tools/remaster-expansion/export.cjs --check-only
```

This decodes and plans the registered source sheets, reports maximum safe body height for every battle strip, checks frozen cohort compatibility and existing output hashes, and writes no assets, manifest or review artifacts. A source that cannot fit fails before output writes and reports its maximum supported body height. Compact or revise that new source, or obtain an explicit different-canvas policy; do not lower the existing cohort. Gordon and Ricard source candidates were compacted before their first export to meet this requirement.

Ordinary export refuses to change an already exported PNG at an existing path/ID. Existing metadata is never overwritten, and stale files are never deleted automatically. Retain existing source descriptors and IDs when extending the library. Strict verification also checks that preserved production files remain registered; removing a descriptor does not remove its PNG and produces an orphan-output finding.

For an intentional revision after a candidate has been exported, add a separately named source and descriptor rather than replacing the old asset. Use a unique sheet key, versioned frame IDs such as `attack-v2-01` through `attack-v2-06`, and a versioned clip name such as `attack-v2`. Keep the earlier descriptor, source, PNGs and clip declarations alongside it. This creates reviewable new PNG/clip IDs and allows Unity's create-missing-only menu to preserve existing animation assets. Changing the immutable preservation baseline or retiring old production IDs requires an explicit maintenance decision; the normal exporter does neither.
