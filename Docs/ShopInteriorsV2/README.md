# Tobul weapon-shop anchor, V2

V2 replaces V1's spacious invented layout with a generated reconstruction aligned to the actual Tobul weapon-shop screenshot. It retains the dense north wall, left L-counter, green merchant, chest, paired racks, furnace, narrow east workbench, stools, red floor, and large cream/lilac lower rug. The two visiting customers and speech bubble are intentionally removed in the approved generated source. Three selected variants change stock and clerk while retaining that layout: armor, item, and combined magic. Those are Tobul-layout adaptations, not verified Altair1:1 interiors.

## Reference and dimensions

Retail reference: [Vorxu Tobul screenshot](https://cdn.vorxu.com/images/final-fantasy-2-pixel-remaster/walkthrough/salamand-and-semitt-falls/tobul-960w.webp), full screenshot960x540. The chosen inner comparison rectangle is `(213,0,534,440)`. This excludes the outer room framing used in the reference agent's separate604x474 crop. It is a crop-scope difference, not an alternate retail room.

The approved generated master is1382x1138. Working export is356x294, roughly twice the inferred underlying retail logical density; this is an export convention, not a verified engine resolution. The alternate proof is534x441. The reference board uses the explicitly adjusted nearest-neighbor534x440 proof. No claim is made that imagegen reproduced retail pixels exactly. All positions come from the approved scene; no V1 room grid is used.

## What is reusable

| Asset family | Count | Contract |
|---|---:|---|
| Four shop scenes | 24PNG | Each composite plus floor/wall/rug/fixtures/merchant visible-pixel layers at356x294, all origins(0,0). Each set of five layers partitions every pixel exactly once. |
| Context/material crops | 28PNG | Seven per shop: whole decorated-wall strip, one wall-pane/timber sample, counter context, chest context, racks/stock context, visible lower rug, unobstructed red-floor sample. Exact crop rectangles are in manifest. |
| Transparent atlas props | 7PNG | Complete generated L-counter, chest, two separate racks, furnace, narrow workbench, stool. Alpha128, trimmed then nearest aspect-fit; bottom-center anchors. |

Total59 production PNGs. The atlas props are independent generated extractions with small shape differences from the scene. The scene's226x97 counter-context rectangle includes the merchant/chest/background; it is not a movable counter sprite. The isolated atlas counter is225x116 because its taller L is preserved without distortion. The contact sheet intentionally shows both.

## Layers and limits

Scene layers are **visible-pixel partitions**, not reconstructed independent room pieces. Occluded floor, merchant body, furniture backs, and wall behind mounted objects do not exist in these files. Polygon selections can include a narrow contextual fringe; use the whole scene at fixed coordinates for exact reconstruction. Collision is not inferred from those contextual masks. Atlas props can be placed independently, with any gameplay collision authored separately after approval.

The red-floor swatch is a clean visible16x16 material sample with an8x8 repeat proof. Its seams have not been repaired or guaranteed seamless. The wall strip remains a whole decorated strip: weapons are baked in, no new wall autotile/junction contract. The rug touches the bottom viewport edge; it is a visible crop, not a complete rug or a nine-slice/repeat asset. These labels prevent presenting one flattened scene as a finished modular tile kit.

Armor/item/magic are reviewed generated adaptations with no retail interior-match claim. No temple reconstruction is included; the previous cool-stone/blue temple remains an unverified art-direction proposal outside this package. Existing approved cursor option10 is untouched.

## Review and verification

- `Review/shop-interiors-v2/rooms/weapon-reference-matched-534x440.png`: exact board dimensions.
- `Review/shop-interiors-v2/rooms/weapon-534x441.png`: alternate agreed proof.
- `Review/shop-interiors-v2/four-shop-contact-sheet.png`: all four normalized rooms, equal viewport and scale.
- `Review/shop-interiors-v2/component-contact-sheet.png`: all35 component/material outputs.
- `Review/shop-interiors-v2/index.html`: scene, five alpha layers, component gallery.
- `Review/shop-interiors-v2/red-floor-repeat.png`: unchanged sample repetition.
- `Docs/ShopInteriorsV2/alpha-audit.json`: removed low-alpha/retained opaque source pixel counts per island.
- `Docs/ShopInteriorsV2/verification.json`: current exact reconstruction/hash receipt.

Run `node Tools/shop-interiors-v2/build.cjs verify` from the asset repository root. This is an assets-only export, with no game build, runtime binding, or collision integration.

Selected raw bytes and the five exact prompt records are preserved under `ArtSource/ShopInteriorsV2`. `source-lineage.json` maps every selected record's original `generatedFile` to its preserved filename and SHA256. All five copies matched their original generated files at export. The filtered prompt snapshot also retains the SHA256 of the parent's complete generation record; unrelated terrain prompts are not duplicated here.

Rebuild uses these preserved masters and selected records first, so an exported/published pack does not require the staging-only root `Incoming` directory or combined generation record. A final export launched from `C:\` reproduced the same production manifest hash. `Tools/shop-interiors-v2/README.md` contains the standalone dependency and reproduction commands.
