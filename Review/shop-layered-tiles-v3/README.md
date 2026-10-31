# Layered shop tiles V3

Separate assets-only modular review. RoomAssemblyReviewV2 is frozen and untouched. Sources are independent generated structures and fixture overlays. Exports preserve source RGBA; alpha bounds only locate clean cell crops. Layer, footprint and side compatibility metadata describes inspected uses, not arbitrary all-direction seamlessness.

## Construction and limitations

34 reusable PNG exports: 21 structural slices and 13 fixture/rack layer exports. Blank masters have no baked dishes, tools or stock. Mounted weapons, hooks, dish, anvil and hammer are independently removable overlays. The generated final tool cell was a sword, exported honestly as single-upright-sword.

The empty rack is split into back and front-crossbar slices. Stock renders between those actual PNG layers. Tabletop versus apron/legs, counter surface versus front, cream wall band versus timber trim/wainscot, stone worktop versus brick face, and half-wall cap versus lower bands are independently exported. Cream inset and timber post crops are optional reusable samples. The stone structure is a bare worktop/brick base; it does not claim a firebox opening or animated forge fire.

Visible source slices do not reconstruct hidden surfaces. Standalone bands preserve only the visible artwork; no new back faces, concealed legs, missing wall sides or invented counter corners are claimed. The right counter elbow exists in the generated master; other corner orientations are not supplied. Side tags describe intended source-partition neighbors, not proven universal tile seams. Horizontal wall repetition is displayed for inspection. Own-kit 16px normalization and 8px details are authored scale choices, not retail measurements.

Rebuild: `node export.cjs`, `node build-review.cjs`, `node verify.cjs`. Sources and prompt records remain under sources/. No RoomAssemblyReviewV2 file was changed.

Chest/cabinet addition: five exports partition only closed visible source pixels. Latch removal and cabinet-frame removal leave transparent cutouts; they do not invent art hidden behind hardware or doors. Existing red-floor-swatch.png is preserved from ShopInteriorsV2 (16x16); separate timber-boundary is cropped from generated wall lower trim and demonstrates only a north run. Bow currently has no rendered string; retained as a candidate limitation. Bed layer ordering is delivered by a separate kit, leaving Scott's frozen room untouched.

Bookcase addition: independent empty frame/back, four front shelf rails, four stock rows and blue/white jug. Stock layers render before front shelf rails. Exact source partition reconstruction is verified for chest, cabinet and bookcase; no missing hidden face is painted. Four generated masters plus one preserved floor source currently supply 51 exports. Dialogue bubble source crop is provided separately for BedLayersV1; it is interface art and not a shop wall fixture.

## Final stock variants

81 reusable PNG exports total: 51 structure/weapon/furniture/book/floor exports plus 9 armor, 9 item and 12 magic exports. Seven generated masters and one preserved existing floor swatch are recorded by SHA-256. Weapon, armor, item and magic examples reuse the same structural template; they are layout proposals, not pixel-exact retail room reproductions. Armor signs/helmets/cuirasses/shields/pennant/mannequin, item bottles/scrolls/parcels/sack/jar/sign and magic sigils/tomes/book-stock/orbs/wizard remain separate assets. Full baked mounted-orb sources are not exported: visible sphere crops pair with the independently generated clean empty stand. No concealed orb surface is reconstructed.

Each armor/item/magic example includes all actual transparent layers plus placement metadata in shop-variants.json. Verification checks hashes, source crops/cutouts, exact delivered-layer reconstruction, visible furniture partitions, each variant reconstruction and real shelf stock/rail pixel overlap (stock behind front rails). Visual scale, palette and silhouettes remain candidates. Bow lacks a string. Stone worktop is not an open furnace/firebox.

Final rebuild: `npm run build`; verify: `npm run verify`. The review gallery has layer visibility toggles for the primary structure example and separate stock contact sheets for all three shop variants.

## Reference wall-stock comparison

wall-stock-comparison.png compares the three locked user-reference excerpts against new components at annotated stock anchors and scale: armor485x62, item517x67, magic500x76. Blank cream panels, posts and top/base trim remain independent of stock. Metadata and preserved references are self-contained under wall-comparisons/ and wall-reference-scenes.json. Armor repeats the steel helmet; item repeats parcel stacks and substitutes the shared blue/gold pennant for the orange/gold reference; potion shelves/trays are not supplied. Magic short shelf groups reuse bare frame samples and separate book rows, with different symbols/book counts. These are cropped wall comparisons, not reference-matched whole maps. The large shop images are component assembly proofs. Final asset count remains frozen at81.
