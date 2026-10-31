# Scene decomposition V1 — reference analysis only

Open `index.html` for the four-step review. `tobul/labeled.png` and `scott/labeled.png` provide numbered scene labels; the matching contact sheets and `isolated/` directories contain reference-only rectangular crops.

This is a manually seeded annotation dataset plus an automated exporter, **not a general automatic detector**. Boxes describe approximate visible extents, overlap deliberately and retain the original background/occluding objects. They are not transparent masks, object cutouts, generated artwork or production-ready sprites. The whole-room floor crop also includes furnishings; it is a context observation, not a recovered floor layer.

`scenes.json` is the editable data contract: crop-relative rectangles, logical layers, parent IDs, foreground→background occlusion edges, observed status and unresolved inferred hidden fields. Existing generated counterparts are candidate mappings only, including an actor proxy rather than verified Scott artwork. Several counterpart files combine more than one component. The geometry of concealed backs, undersides and interrupted patterns remains null. Interpolation requires a later explicit generation/reconstruction pass and review; this package does not claim to have recovered unseen reference pixels.

The inventory covers major visible furnishings and structural regions. Texture details, tiny fixtures, lighting and clipped/external regions remain unmodeled; `semanticExhaustiveness` is false. This is a reviewable starting inventory, not proof that every semantic component was identified. Fixed room crops intentionally exclude the minimap and most perimeter/exterior pixels.

Rebuild from the checked-in annotation data:

```
node AssetWork/SceneDecompositionV1/export.cjs
node AssetWork/SceneDecompositionV1/verify.cjs
```

`seed.cjs` recreates the initial two-scene annotations; running it replaces edits to `scenes.json`, so use it only intentionally. The exporter uses the installed Codex-runtime Sharp package, with an absolute Windows path currently recorded in both scripts. Source references remain in the separate local art checkout. `manifest.json` pins source and per-crop SHA-256 hashes. Verification independently regenerates every reference crop, checks bounds and relationship endpoints and confirms mapped candidate paths exist. Verification does not establish semantic completeness, mask accuracy or correctness of inferred geometry.

No original-reference pixels are written into production assets. No existing generated counterpart is modified. Source artwork remains reference material with its existing rights and attribution; these exports make no licensing claim.

The package also preserves 15 user-provided armor, item and magic reference snippets under `sources/`, with byte hashes in the manifest. These have no asserted remote origin. Their scene IDs begin `armor-`, `item-`, or `magic-`. Small stock rows use approximate manually seeded per-slot bounds: adjoining books or tiny bottles may share a crop boundary or include neighbors. These require finer human annotation before any semantic-mask claim. Shared wall/rack/counter structure is recorded separately from swappable stock overlays and the wizard NPC.

`append-snippets.cjs` recreates those snippet annotations from the original temporary clipboard files if they remain available; ordinary rebuilds use preserved sources and `scenes.json` directly and do not require those temporary files. `refine-annotations.cjs` records the initial room upright/rack correction; ordinary edits belong in `scenes.json`.

Twelve additional city/town excerpts are preserved under `sources/city-*`. Family names are descriptive annotation categories, not claims of source game/version. Each building placement stays separate, with approximate roof/facade/opening regions. Small door/window subdivisions use family-relative seeded bounds and require human semantic review: they are crops of observed pixels, not established object masks. Purple/orange geometry reuse is explicitly `proposed-not-observed-equivalence` in scene metadata. Distinct roofs and silhouettes remain visible rather than being normalized into an assumed identical kit. Castle turrets, bridge/water/parapets, church tower, grass and trees have separate family labels. `append-city.cjs` recreates these annotations from the clipboard originals; ordinary rebuilds use preserved files.

All31 original user/reference images are now preserved under `sources/` and scene source paths are relative to this package. Ordinary export/verification no longer reads the art checkout or clipboard directories. Historical seed/recreation scripts retain their original input paths and should not be run when replaying the portable frozen data.
