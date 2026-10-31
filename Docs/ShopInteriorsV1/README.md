# ShopInteriorsV1 - five layered starter interiors

Assets only, staged under `AssetWork/TerrainShopPassV1`. No game code, scene, Unity import/build or art-repository changes are made by this package. The five templates are **weapon, armor, item, combined magic, and temple**. Black/white magic are not presented as separate Altair shops.

## Review

- [Five-room contact sheet](../../Review/shop-interiors-v1/contact-sheet.png)
- [Room/layer gallery](../../Review/shop-interiors-v1/index.html)
- [Individual component sheet](../../Review/shop-interiors-v1/component-sheet.png)
- [NPC/altar alpha-edge proof](../../Review/shop-interiors-v1/alpha-edge-proof.png)
- [Original NPC style/scale references](../../Review/shop-interiors-v1/npc-reference-sheet.png)
- [Source/component inventory CSV](inventory.csv)

Every room has `floor.png`, `wall.png`, `npc.png`, `furniture.png`, and `composite.png` at **448x416 pixels /32PPU**, plus `placement.json`. Native and3x room views are provided. Ordered layer strips in `Review/shop-interiors-v1/layers/{id}-layers.png` show the construction over a checkerboard.

Composition order is **floor -> wall -> NPC -> furniture**. The counter can cover the bottom boot pixel of a clerk, while the face/torso remains visible. Attendants stand behind the service boundary; no character is painted into a fixture. The two-cell southern entrance and proposed customer service cells remain clear.

## Components and reuse

The kit owns **25 individual component PNGs:16 byte-identical approved reuses and9 newly normalized components**. One unchanged sibling TerrainComponentsV3 flagstone floor is referenced by hash, not copied into ShopInteriorsV1. Five room sets add25PNG layers/composites: **50 owned production PNGs total**.

Approved whole components reused:

- InteriorDetailsV4 Scott alternating wall bays and Tobul cream/lilac customer rug; temple uses the complete Scott blue/cream rug.
- InteriorDetailsV3 golden straight and L counter components. Their alpha padding is accounted for by placement overlap, joining the counter without repainting source pixels.
- InteriorComponentsV2 red floor, cool cream/lilac floor and dark cutaway wall-cap pieces.
- InteriorComponentsV1 bookshelf, chair and selected furnishings, plus the existing stone pillar. Unused inventoried components remain available individually; the manifest identifies actual room placements.
- Campaign shopkeeper for the weapon room; Campaign robed mage for the combined magic room. These approved sprites are copied unchanged.

Nine new components:

| Component | Native output | PPU | Use |
|---|---|---|---|
| weapon-display |64x64|32|Swords, spear and axe rack|
| armor-display |64x64|32|Helmet, chainmail and shield stand|
| item-display |64x64|32|Potions, bundled goods and small stock|
| magic-display |64x64|32|Tomes, open book and crystal|
| temple-altar |96x64|32|Stone altar with integral candles|
| temple-wall |64x64|32|Distinct cool limestone north face|
| item-clerk |32x48|64|Static apron-wearing item attendant|
| armorer |32x48|64|Static cap/apron armorer|
| temple-cleric |32x48|64|Distinct static white/blue cleric|

NPC density is deliberate: new32x48 sprites at64PPU have the same logical16x24 size as the approved Campaign NPCs at32PPU. Proofs enlarge through nearest-neighbor display only. No idle animation or movement strip is claimed. Minwu is preserved only as a style reference, not reused as the temple cleric.

## Floor and layout basis

Ordinary shops share a continuous **red textile floor**, approved cream/timber north wall, golden L counter and customer rug. The new flagstone appears **only at the entrance pad**. An earlier proof's flagstone stock band was removed after review; initial proof bytes are preserved under `ArtSource/ShopInteriorsV1/proof-iterations/`.

Weapon/smithy materials are grounded in the inspected FFII Pixel Remaster Tobul capture: red floor, pale patterned rug, golden counter and display stock. The precise starter-room arrangement is authored, not traced retail map data. Armor/item/magic variants share that template as an art-direction choice; their individual retail interiors were not visually verified in this pass. Magic uses one combined vendor/template.

The temple deliberately changes to cool stone, blue/cream rug, limestone north wall, altar, side seating and a cleric. **This is a proposed temple candidate, not a verified FFII retail temple match.** The other-town pale landmark capture is not relabeled as a temple reference.

The V4 decorative wall/rug pieces are whole authored components. This package does not invent a new seamless, autotile or nine-slice contract for them. Room proofs repeat/place the whole selected wall component at its declared density; no motif is repainted or repaired. Source NPCs and approved art are preserved byte-for-byte.

## Layer and placement metadata

The manifest records each component's source/dependency path, SHA-256, native size, PPU and logical size. Each room records layer hashes, canvas size, component rectangles/base anchors, layer order, shop type, proposed blocked cells, entrance cells and customer service approach cells.

Collision is **proposal metadata only**. The verifier checks a simple abstract occupancy grid from the entrance to the marked service cells. It does not establish engine collision, interaction range, navigation behavior or playable map integration. Counter service points are explicit authoring targets for later integration.

## Source preservation and alpha

Nine selected generated masters and the unselected first altar are preserved unchanged, with the root's ten exact generation prompts/tool/source records in `ArtSource/ShopInteriorsV1/generation-prompts.json`. The first altar remains at `iterations/temple-altar-first-pass.png` as edit provenance. All selected outputs are generated art, not screenshot crops.

Cutouts use alpha>=128, full bounding-box trim, nearest-neighbor aspect fit and two-pixel transparent padding. Invisible output RGB is zero. The temple wall is opaque. No local pixel painting, silhouette erosion, color replacement or reference-pixel extraction is performed.

The final NPC/altar masters contain soft low-alpha viewer glow. Alpha histograms and128/240 bounding comparisons are recorded in [source-alpha-audit.json](source-alpha-audit.json). The binary128 exports were inspected over a light/dark checkerboard: no opaque gray halo was visible outside the physical outlines. Generated cutout output alpha is strictly0/255.

## Reproduce and verify

From the staging root `AssetWork/TerrainShopPassV1`:

```powershell
& 'C:/Users/const/AppData/Local/Programs/Python/Python313/python.exe' Tools/shop-interiors-v1/build.py build
& 'C:/Users/const/AppData/Local/Programs/Python/Python313/python.exe' Tools/shop-interiors-v1/build.py verify
```

Pillow 12.3.0 is available in that interpreter. The pinned dependency is in `Tools/shop-interiors-v1/requirements.txt`; a different workstation can install it with `python -m pip install -r Tools/shop-interiors-v1/requirements.txt`. The same commands work from the art-repository root after publication because all kit paths are relative. Verification is read-only. It checks source/provenance and output hashes, exact layer reconstruction, complete owned-PNG inventory, generated alpha/invisible RGB, counter-face/torso clearance and abstract entrance/service routes. Rebuilding refuses changed individual component bytes; owned room-proof revisions are backed up before refresh. Existing production art and raw masters are never overwritten.

## Reference scope and attribution

Published reference destination: [crop register](../../References/TerrainShopPassV1/Comparison/crop-register.json) and [store-reference availability](../../References/TerrainShopPassV1/Comparison/shop-reference-status.json). During staging these files are in the sibling `ReferenceReview/` folder. They record exact source/crop rectangles, hashes and availability limits. Primary inspected shop image: [Vorxu Tobul/smithy screenshot](https://cdn.vorxu.com/images/final-fantasy-2-pixel-remaster/walkthrough/salamand-and-semitt-falls/tobul-960w.webp). [FFII shops reference](https://vorxu.com/final-fantasy-2-pixel-remaster/shops) supplies store context; it does not make the inferred room layouts visually verified. Screenshot references remain research outside production layers.

Generated art is reference-informed, not original retail imagery. Preserving references grants no new rights, endorsement or license. No runtime, animation, shop economy, dialogue, inventory, game-map or retail1:1 claim is made.
