# Wall components V4

Assets-only review staging. Existing stock and front overlay bytes remain identical to V3, with unchanged rendered positions. No game code changed.

- `comparison.png`: original / V3 / V4 at native resolution, cyan annotated measured reference post bounds.
- `components/`: independent clean, stock-free panels, posts, top molding and bottom timber for each room.
- `rooms/`: blank wall background, unchanged stock/front layers, assembled review strip.
- `manifest.json`: dimensions, SHA256, per-component coordinates and source declarations.
- `inputs/`: copied existing generated input textures, V3 layers and reference strips. Reference strips are REVIEW ONLY and never used by the production component path.

Run `node build.cjs` then `node verify.cjs`. Uses the installed Sharp runtime at the explicit path in the scripts. Build performs nearest-neighbor scaling and crops only of existing generated PNG texture assets; layered pink/pale plaster frames are procedural rectangles. No image generation.

Post bounds were manually measured in the supplied reference strips and checked against native pixels; precision approximately one pixel. Half-open x ranges are listed in the manifest. Bay widths vary by room rather than splitting the canvas into six equal sections. Top molding heights: armor 6px, item 9px, magic 14px. These are strip geometry measurements, not a claim of universal tile dimensions or verified arbitrary seams.

Verification checks every exported PNG hash and dimension, exact raw-pixel reassembly of the independent wall parts and exact raw-pixel assembly of wall + stock + front. It also checks that stock/front PNG files are byte-identical to copied V3 inputs. Source V3 stock anchor records are retained in `inputs/v3-placements.json`. Existing artwork differences (symbols, bottle silhouettes, shelf widths) remain.

Source: C:/repos/AI-Art-FF2/Review/shop-layered-tiles-v3. Existing generated wall textures came from `sources/structure-master.png` SHA256 `81074a35df2e79a7bc6ed34def7ee340652dc4664f73b64de36dc1b3e676214c`. The source V3 manifest is retained as `inputs/source-v3-manifest.json`; it records original crops and normalization. No new license or ownership claim is made.
