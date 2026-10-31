# City layered icons V1

Assets-only staging. `kit.json` is the editable crop/size/layer recipe; `export.cjs` writes only this directory. No game map or production asset is changed.

```
node AssetWork/CityLayeredIconsV1/export.cjs
node AssetWork/CityLayeredIconsV1/verify.cjs
```

Sources are generated art, not reference screenshot pixels. Existing grass/floor sources are copied without modification. The registered grass phase proof reconstructs the copied64 material from its four32px tiles exactly. It demonstrates that one specified arrangement; arbitrary variants are not guaranteed seamless.

New generated city icons can be added as entries with `id`, `source`, `crop:[x,y,w,h]`, optional nearest-neighbor `size:[w,h]`, tags and optional `layers:[{id,band:[y,height],tags}]`. Visible bands preserve original RGBA and placement, and the verifier requires complete, nonoverlapping coverage and exact pixel reconstruction. These are useful visible roof/facade/deck/parapet partitions, not recovered concealed surfaces; unseen backs and undersides remain unresolved. Crops must be selected after viewing the source. A band that cuts through sloping geometry is a technical partition, not a semantic mask, and should be named accordingly.

The local exporter/verifier currently use the installed Codex-runtime Sharp package at its absolute Windows path. Recipe sources within this directory travel with the package.

The first city source supplies twelve distinct icons. Object contours use reviewed manual source-coordinate polygon masks, binary alpha and nearest-neighbor normalization; these masks are candidates rather than automatic segmentation. Roof/facade partitions are intentionally named visible bands because sloping roofs cross the split. Bridge partitions instead use west parapet, middle deck and east parapet columns; a column can include neighboring outline pixels. All visible partitions exactly reconstruct their parent. Hidden wall tops, rear faces, roof undersides and complete independent rear structures remain unresolved.

`node AssetWork/CityLayeredIconsV1/contact.cjs` writes `city-contact.png`. The contact sheet has been visually inspected; it is review evidence and does not demonstrate runtime integration.

Three representative houses (purple gable, purple large/L house and orange gable) now have semantic roof polygon overlays plus facade backings extended behind the roof. Each extension repeats a known white-plaster patch from this GENERATED city atlas only; the separate concealed-inference mask identifies every invented pixel. The verifier checks roof-over-facade composition exactly equals the original isolated icon. This validates occluded candidate reconstruction, not historical correctness of hidden reference architecture.

New grass, earth and stone paving use opaque64px material crops from the generated ground/wall master, with four registered32px phases each. Removing source alpha makes these ground planes opaque. Straight/end, L-corner and arched-gate walls are manually outlined, normalized and split into cap/face visible bands and32px grid tiles. The gate opening has an explicitly inferred transparent hole mask. Registered wall grid reconstructions are pixel-exact; arbitrary end-to-middle or ground repeat seams remain unverified. Seven declared reconstruction proofs are included.
