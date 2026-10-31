# Interior Details V3 — Reference Review

Original FFII Pixel Remaster screenshot crops are compared beside new V3 art in three PNG boards under `boards/`. Boards are 1120 px wide. The screenshot crops are preserved source imagery; most are displayed at source size, while the tall Hilda red-rug crop is reduced proportionally with nearest-neighbor scaling so the full border and caption fit. New assets are enlarged with nearest-neighbor sampling; displayed scale can vary to fit the comparison panels.

## Sources

- Hilda audience room: [RPGFan, Final Fantasy II Pixel Remaster Screenshot 005](https://www.rpgfan.com/wp-content/uploads/2021/06/Final-Fantasy-II-Pixel-Remaster-Screenshot-005.jpg).
- Scott refuge: [Vorxu, Altair & Fynn](https://vorxu.com/final-fantasy-2-pixel-remaster/walkthrough/altair-and-fynn).
- Tobul smithy: [Vorxu, Salamand & Semitt Falls](https://vorxu.com/final-fantasy-2-pixel-remaster/walkthrough/salamand-and-semitt-falls).

Exact screenshot paths, source URLs, crop rectangles, source/crop SHA-256 values, and occlusion notes are recorded in [`source-crops/source-crops.json`](source-crops/source-crops.json). Crop files are PNG crops of preserved captures with no retouch or redraw; references are not production art.

## Board inventory

- [`walls`](boards/wall-floor-original-vs-v3.png): Hilda wall crop vs Hilda repeated V3 wall; Scott wall crop vs Scott repeated V3 wall. The Hilda crop is fully visible at source proportions and separated from its caption. Both wall styles are represented. The floor context row was removed to keep the board focused on V3 changes.
- [`rugs`](boards/rugs-original-vs-v3.png): Hilda, Scott, and Tobul original captures/crops vs each complete V3 rug. Scott's full crop is explicitly labeled as occluded by bed, party, and speech bubble; an inset shows an unobscured original rug fragment. Hilda uses a partial corner crop rather than implying the full retail rug is visible.
- [`Tobul counter and shop`](boards/counter-shop-original-vs-v3.png): source screenshot crop vs V3 straight and L-corner counter exports. Display items remain visible in the original capture and are not included in the new counter art.

All seven primary components are represented: three rugs, two wall styles, and straight/L-corner counter. Production export paths and native dimensions are listed in [`v3-production-manifest.json`](v3-production-manifest.json); review registrations are in [`v3-proof-manifest.json`](v3-proof-manifest.json). No floor asset changed in V3.

## Rebuilding the boards

[`build-boards.js`](build-boards.js) rebuilds all three PNGs from this folder's `source-crops/` and the staging sibling `../Assets/Art/Production/InteriorDetailsV3/`. It requires Node.js and Sharp (`npm install sharp` in an appropriate local environment, or make Sharp available through `NODE_PATH`). Run `node build-boards.js` from this directory. The script uses nearest-neighbor scaling for comparisons and does not modify source crops or production assets.

## Independent visual review

- Hilda red/gold border repeats the original checker/triangle fringe; its reference panel is a clear corner crop with no characters.
- Scott blue/cream uses the exposed lattice motif; the screenshot's bed, characters, and speech bubble cover the center of the full rug. The board keeps that occlusion visible.
- Tobul lilac/cream uses an interlocking diamond treatment similar to the original visible crop.
- Hilda and Scott wall assets preserve separate lower wood-panel and vertical-slat variants. Repeat preview strips are horizontally assembled from V3 native exports.
- Counter straight and L corner use a consistent gold top and patterned wood face. Original counter fixtures are not baked into the new assets.
- The V3 motifs are regularized and are not claimed to be retail 1:1. The panels compare components, not complete room layouts or runtime placements.

No game code, build, integration, or publishing change was made in this subtask.

