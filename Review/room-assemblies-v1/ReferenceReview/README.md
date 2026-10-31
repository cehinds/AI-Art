# Room Assembly Review V1

Reference-only comparison package for three static rooms assembled from existing production components. It keeps original captures, exact source crops, proof composites and rebuild scripts together. It does not claim gameplay, character, dialogue, animation or complete room-layout fidelity.

## Reference crops

- **Tobul weapon shop:** 960×540 Vorxu capture; crop `(213,0,534,440)`. This is the locked room viewport used by the prior matched-scale review.
- **Scott refuge:** 960×540 Vorxu capture; crop `(69,0,534,390)`. It shows the cream/timber wall, stone floor, rug, bed, bookcase and room furnishings. The crop ends above the lower outer border and cuts some foreground crates at the viewport edge.
- **Hilda throne room:** 1920×1080 RPGFan capture; crop `(430,355,1380,463)`. It begins below the top dialogue panel and ends before the lower dialogue/menu overlay. The crop retains the throne, red carpet, side chairs, party and attendant.

`reference-manifest.json` records each archived source, source URL, dimensions, exact crop rectangle and SHA-256 hash. Crops are literal source pixels; no retouch or rescaling is applied.

## Comparison rules

- Candidate composites must be supplied at the exact reference crop dimensions: Tobul 534×440, Scott 534×390, Hilda 1380×463.
- The board builder rejects mismatched dimensions and does not resize or crop candidate proofs. Both sides are placed at the same native pixel size (1×). The Hilda board is deliberately wide; the HTML scales the preview to fit, and its linked PNG preserves the native 1× comparison.
- Label each candidate as a static assembly. Original captures may show transient characters and dialogue; differences remain visible and documented.
- These crops and side-by-side boards do not prove exact retail room layouts or gameplay behavior.

## Current review

The Tobul board is ready at `boards/tobul-side-by-side.png`. Its 534×440 reference and candidate are displayed 1× with no resizing or crop. In this first static assembly, the clerk position, wall/display bays, L-counter footprint, rug footprint and right-side fixtures align closely. Remaining differences are the counter surface/ornament detail and small bench/stool proportions. The original screenshot also has two customers and a dialogue bubble, which the static candidate omits.

All three exact-size boards are available. Scott’s floor grain was enlarged in the final composite and now reads closer to the reference square-stone pitch. Three red/white seat-like objects along the reference wall-floor seam still differ in silhouette/detail; their exact identity is uncertain. The rug is somewhat narrower and the bed proportions differ slightly. Hilda has a documented style delta in carpet border and wall color; its major object centers align reasonably. Details are in `review-findings.json`.

## Build

Place final normalized room composites at `room-proofs/tobul.png`, `room-proofs/scott.png`, and `room-proofs/hilda.png`. Run `make-reference-crops.cjs` to recreate reference crops, then `boards/build-room-comparisons.cjs` to produce one PNG per room and `room-proof-manifest.json`. Run `verify.cjs` to check reference/proof hashes, dimensions, and local HTML links. The board builder uses only local crop/proof files and requires exact dimensions.

At handoff, any room without a normalized candidate proof remains explicitly pending in the manifest and HTML.
