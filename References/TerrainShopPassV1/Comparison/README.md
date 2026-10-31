# Terrain and Shop Reference Review V1

Reference-only research package for overworld/city terrain and shop/interior direction. Preserved reference frames and actual crops are under `source-frames/` and `crops/`; exact source dimensions, URLs, rectangles, and SHA-256 values are recorded in [`crop-register.json`](crop-register.json). These images are research references, not production assets and convey no new license grant.

## Concrete visual guidance

### Overworld terrain

- **Grass:** the Vorxu Altair-to-Gatrea captures show a broad bright green field with fine, dense variation and modest value patches. Trees/river/settlement are separate objects or edges over that base.
- **Rivers:** narrow vivid cobalt/blue channels wind through grass and forest. Their edges have a thin olive/yellow-green and brown bank with small white water highlights. Use the crossing crop to distinguish the gray stone bridge deck from the water and bank. These frames show a river and bridge, not a continuous dirt road.
- **Trees:** dense dark pointed conifers with visible individual crowns; forest edge leaves green floor/gaps visible. Avoid making the forest a single hedge mass.
- **Overland road:** no clear dirt-road layer appears in the sampled Altair-to-Gatrea route frames. The gray stone crossing is evidence for a bridge, not for paving the open field. Any new road network should be treated as an authoring choice until a clearer FFII PR road crop is found.

### City surfaces and buildings

- [`other-town-cobble-material.png`](crops/other-town-cobble-material.png) is from a Klardendum FFII PR screenshot whose town identity is unconfirmed. It shows warm gray-beige irregular stone paving with distinct block shapes and darker grout/shadows. Use only as material/color guidance; do not transfer its geography to Altair.
- [`other-town-shopfront-material.png`](crops/other-town-shopfront-material.png) shows blue tile roofing, pale stone facade and a sign. It is likewise material reference only.
- [`fynn-settlement-marker.png`](crops/fynn-settlement-marker.png) is a real FFII PR Fynn overworld marker, with a walled cluster, gate and blue-roof keep/houses. It is shape evidence for Fynn only; it does not establish Altair's exact color/material palette.
- [`altair-town-layout-sepia.png`](crops/altair-town-layout-sepia.png) is a sepia Altair automap. It can guide layout/topology only, not gameplay colors.

### Shops, NPCs, and temple evidence

- [`tobul-weapon-shop.png`](crops/tobul-weapon-shop.png) is a direct FFII PR Tobul smithy screenshot. It visibly has a merchant behind a substantial L-shaped counter, a red floor, wall-mounted weapon displays and other fixtures. This is the strongest local visual sample for a weapon shop interior.
- Vorxu also lists PR weapon, armor and item shop vendor images on [Weapons](https://vorxu.com/final-fantasy-2-pixel-remaster/weapons), [Armor](https://vorxu.com/final-fantasy-2-pixel-remaster/armor), and [Shops](https://vorxu.com/final-fantasy-2-pixel-remaster/shops). The web page identifies these as shop interiors, but its image CDN did not load through the research reader, so this package does not claim to have visually compared those images or crop them. See [`shop-reference-status.json`](shop-reference-status.json).
- The [Altair & Fynn walkthrough](https://vorxu.com/final-fantasy-2-pixel-remaster/walkthrough/altair-and-fynn) confirms Altair has a magic shop, but no magic-shop interior image was found in the inspected reference set. A distinct merchant/NPC design for magic should be treated as a proposal, not a sourced visual fact.
- No clearly identified FFII PR temple/sanctuary capture was found. [`other-town-pale-landmark.png`](crops/other-town-pale-landmark.png) is a pale stone landmark/statue-like feature from the unidentified-town image; its function is uncertain. Do not call it an exact temple reference.

## Source provenance

- Overworld route frames: local 640×360 screenshots preserved from the Vorxu [Altair & Fynn walkthrough](https://vorxu.com/final-fantasy-2-pixel-remaster/walkthrough/altair-and-fynn) gameplay clips. The capture bundle has no exact per-frame timestamp mapping; none is asserted. It is the accepted FFII PR source used by [`WorldLayerComparisonV1`](../../../References/WorldLayerComparisonV1/sources.json).
- Altair map: direct Vorxu image `altair-start-game.png`, saved locally as `pr-altair-map.png`; sepia layout only.
- Other-town city material: Klardendum screenshot `ff2pr1.jpg`, preserved locally as `pr-town-materials.jpg`; town identity unconfirmed.
- Weapon shop: direct Vorxu Tobul screenshot `tobul-960w.webp`, saved locally as `pr-smithy.webp`; platform/build unknown.
- Online shop page image endpoints and their inspection status are in `shop-reference-status.json`.

## Rebuilding this review

The board generators use the copied inputs under `comparison-inputs/`, so they remain usable after this folder is copied to `References/TerrainShopPassV1/Comparison`. Run them from the copied folder with `node boards/build-terrain-board.cjs`, `node boards/build-context-board.cjs`, or `node boards/build-shop-board.cjs`. They need the Node `sharp` package. `boards/update-terrain-snapshot-manifest.cjs` and `boards/update-shop-snapshot-manifest.cjs` resolve staged/repository source proofs when present and can record copied snapshots when source proofs are absent. Rebuilding original crops with `node make-reference-crops.js` also requires `sharp`; install it locally with `npm install --no-save --package-lock=false sharp` if it is not already resolvable.

## Current scope

This is a reference and attribution package. It contains preserved source crops and review-board snapshots, but no generated production art. It does not prove game integration or runtime behavior. Terrain and shop/temple comparison boards are included. The overworld forest-field proof is diagnostic-only and has no repeatability contract. Keep reference crops separate from production art.

## Preliminary candidate notes (not a final comparison)

Side-by-side boards for current V3 terrain candidates are in [`boards/`](boards/). The board generator scripts are beside them and use nearest-neighbor fitting without distortion. The proof inputs used by those boards are copied under [`comparison-inputs/terrain-v3/`](comparison-inputs/terrain-v3/) so this review folder can travel independently; production floor tiles are shown enlarged only for inspection. The forest proof is a diagnostic field with visible repeated crown groupings, not a map-ready forest composition.

Grass in the current V3 output reads darker and bluer/olive than the bright green route capture. City cobble is warm pale gray-beige and irregular like the separate Klardendum crop, though V3 appears paler and higher-contrast at the displayed tile scale. Shop flagstone reads as a darker warm brown block surface. The river core is narrow like the reference, but its cyan-green/orange fringe is more conspicuous and regular than the thin olive/earth PR banks. These are independent visual observations, not pass/fail or retail-parity claims.

For river comparison, prioritize the narrow cobalt channel, very thin olive/earth bank, and sparse light water pixels visible in the registered PR crops. For trees, compare individual pointed crowns and visible green gaps rather than only forest silhouette. No sampled route frame establishes an open-field dirt-road treatment. For shops, the Tobul screenshot is the only locally inspectable PR interior in this package: preserve the evidence of an L-counter, red floor and wall-mounted wares in the comparison; weapon/armor/item category images are page-listed but their CDN bytes were unavailable to inspect. Distinct magic-shop and temple designs therefore remain proposals unless additional attributed images are captured.

### Shop room comparison

[`boards/shop-and-temple-reference-vs-v1.png`](boards/shop-and-temple-reference-vs-v1.png) compares the actual Tobul smithy capture against the frozen weapon-room proposal, then shows armor, item, magic and temple proposals separately. The weapon proposal retains the observed red floor, wall-mounted wares and merchant behind an L-counter while using a different room layout and fixture art. All four ordinary-shop variants share the same floor/wall/counter plan but vary their displays and attendant sprites: armor stands, item shelves, spell books/blue-robed attendant. In each proof the attendant is behind the service front; placement metadata puts shop attendants at y=104 while the counter front begins at y=128. The temple proposal is clearly distinct in pale stone/blue palette, central altar, side chairs and cleric placement. These are art-direction candidates, not confirmed FFII PR interiors or exact room layouts. Proof input hashes are in [`comparison-inputs/shop-v1/snapshot-manifest.json`](comparison-inputs/shop-v1/snapshot-manifest.json).
