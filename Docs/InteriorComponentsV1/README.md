# InteriorComponentsV1

Asset-only generation/normalization package. Game integration is explicitly deferred. This package never writes game C#, scenes, Unity metadata, existing assets, or approved cursor pixels.

## Production contract

- World tile scale: 32 native pixels per tile.
- Tall north wall face: 32Ã—64, opaque, horizontal repeat, bottom at wall/floor junction.
- Opaque floor/carpet cells: 32Ã—32 unless a component explicitly declares a larger rug canvas.
- Furniture: normally 64Ã—64 transparent canvases; regular atlas cells, alpha threshold 128, aspect-preserving nearest fit, bottom-center base anchor.
- UI panels/tabs: explicit component dimensions and nine-slice metadata, no text baked in.
- Cursor option 10: existing `BattleUiV4/menu-hand-right.png` and `target-hand-down.png` are hash-checked references only. Do not regenerate, modify or replace them.

See the [independent component breakdown](../InteriorCityUiComparisonV1/README.md) and [prioritized contracts](../InteriorCityUiComparisonV1/component-contracts.json).

## Source preservation

Raw generated PNG masters live in `ArtSource/InteriorComponentsV1/sources/`. Import keeps the exact source bytes and records SHA-256, dimensions and original path. A source ID is frozen: a changed master requires a new versioned ID. Generation prompts/tool/date must be retained separately with the batch's generation record; the normalizer does not infer licensing or invent provenance.

```powershell
python Tools/interior-components-v1/export.py import-master north-wall C:/absolute/path/to/generated-master.png
```

`Tools/interior-components-v1/components.json` selects the source, group/output path, native size, alpha contract and optional crop or regular grid/cell. Atlas labels and rectangles must be visually confirmed from the actual generated master; do not guess their order.

Examples:

```json
{"id":"bed","source":"furniture-atlas","grid":[4,2],"cell":[1,0],"output":"props/bed.png","size":[64,64],"alpha":"cutout"}
```

```json
{"id":"north-wall-center","source":"north-wall","output":"walls/north-center.png","size":[32,64],"alpha":"opaque","repeat":"horizontal"}
```

Rectangles use `[x,y,width,height]` source pixels. Cutout trimming considers alpha â‰¥128 opaque and makes output alpha binary. Opaque tiles keep their whole declared crop, preserving repeating edges; transparent pixels in an opaque crop cause a failure. Cutout cells require real transparency, so an opaque checkerboard background cannot silently be treated as a sprite cutout.

## Export and verify

```powershell
python Tools/interior-components-v1/export.py self-test
python Tools/interior-components-v1/export.py export --source north-wall
python Tools/interior-components-v1/export.py export
python Tools/interior-components-v1/export.py verify
```

A filtered export supports reviewing one master while other components remain pending. The manifest reports exported/configured counts and pending IDs. The read-only verifier checks configured completeness, source/output SHA-256, dimensions, alpha, furniture base anchors and approved cursor references. It fails if configured outputs remain missing.

Production PNGs go under `Assets/Art/Production/InteriorComponentsV1/`. Existing differing PNG bytes are preserved; choose a new versioned output/source ID for a revision. Only this package's derived manifest/gallery/contact sheet is refreshed. The [review gallery](../../Review/interior-components-v1/index.html) and [contact sheet](../../Review/interior-components-v1/contact-sheet.png) appear after the first successful export.

Validation establishes exact source/crop/export bookkeeping and asset encoding/anchor contracts. It does not establish retail parity, repeating-edge quality, legal rights, Unity import or runtime behavior. Every batch still needs visual inspection against its accepted reference components. No reference screenshot pixels may be used as production sprites.

## Frozen V1 export

**21 primary components / 109 production PNG files / 5 preserved generated masters.** The file count includes 21 complete components, 16 full-canvas frame/fill or border/field layers, and 72 individual nine-slice pieces. The two approved option-10 cursors are references only and are not included in these generated PNG counts. [Validation receipt](validation.json).

The components are: one 32×64 north wall; four 32×32 floor/carpet fields; eight furniture cutouts at their declared native canvases; four blank UI objects; and four complete rugs. UI layer pairs use `*-frame.png`/`*-fill.png`; rugs use `*-border.png`/`*-field.png`. Their nine-slice pieces use `-nw/-n/-ne/-w/-center/-e/-sw/-s/-se.png`. Every derivative path, size and SHA-256 is listed under its parent component in the production manifest.

Furniture extraction uses four column bands and explicit row bands `0..530` / `530..887`: the generated top-row objects extend below the nominal half-height. Equal row crops would amputate them. UI/rug rectangles are also explicit and disjoint; every accepted silhouette has transparent margin before alpha trimming. The surface atlas alone uses an exact 2×2 grid. UI and rug cutouts are normalized to their requested complete canvas dimensions; furniture keeps its aspect ratio and bottom-center placement.

### Visual review and limits

- [Contact sheet](../../Review/interior-components-v1/contact-sheet.png): all 21 native components inspected; no clipped furniture or checkerboard baked into output.
- [Three-size UI panel proof](../../Review/interior-components-v1/panel-nine-slice-proofs.png): fixed eight-pixel corner regions at 192×96, 320×128 and 480×200.
- [Rug border proof](../../Review/interior-components-v1/rug-nine-slice-proof.png): fixed corners, native-density repeated border/field at three extents. This is a composition study, not a seamlessness claim for every possible size.
- Five native/4× repeat proofs under `Review/interior-components-v1/repeats/` cover the wall and all four floor fields. The single variants still have recognizable repeated motifs; this batch does not add randomized material variants.
- The accepted empty gauge has a warm dark-brown track, whereas the inspected PR status reference uses a navy track. This style gap is recorded rather than silently recoloring the source. Separate frame/fill layers allow a later deliberate choice.
- The cream/lilac **floor** tile and cream/lilac **shop rug** are distinct generated components. No floor swatch is mislabeled as the patterned rug.
- These are reference-informed generated assets, not original retail pixel assets. Pixel-perfect fidelity, future placement/collision, font treatment, Unity import and rendered gameplay remain unverified. No integration is performed in this asset phase.

Read-only verification passed after freezing: all source/output hashes, exact native dimensions, binary alpha and base anchors, exact layer reconstruction, complete 109-PNG inventory, and the unchanged approved cursor hashes. Do not re-export different pixels into these frozen V1 names; use a new versioned source/output for a revision.


### Authorized derivative correction

Final rug border masks/slices use **12px**, separating the full inner gold/cream border from the plain center. An earlier 8px decomposition let border pixels repeat inside the field; the expanded proof caught it. The root agent explicitly authorized refreshing only these new derived PNGs while preserving existing GUIDs. All 21 accepted full-component SHA-256 values and raw-master bytes stayed unchanged. The final expanded proof has no internal gold grid. Normal exports still refuse changed PNG bytes; `--refresh-derived` is the explicit, narrowly scoped maintenance option for layer/slice outputs only.
