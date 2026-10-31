# Drainage channel expansion

This directory is separate from the frozen seven-library release. The expansion includes three new objects and 21 generated views. All 21 exported views have a qualified independent review and root approval, recorded by exact hashes in `catalog.json`, `review.json`, and immutable `source/review-decisions.json`. Visible grid seams, modest port offsets and illustrative geometry remain explicit qualifications. No pixel-seamless or runtime collision claim is made.

`source/*-corrected-sheet.png` are unchanged original image-generation outputs. Each JSON sidecar preserves the exact request prompt and source hash; matching prompt text files are byte-hashed by the view provenance. The original failed tee candidate remains separately retained as `source/tee-sheet.png` with its candid source sidecar. It is not an exported reusable view.

The focused builder expects `source/recipe.json` with `exports`: 21 entries each containing `shape` (`straight`, `corner`, `tee`), `view` (`isometric`, `front`, `rear`, `left`, `right`, `top`, `bottom`), expansion-relative `source`, and `[x,y,width,height]` `crop`. Optional `normalization` specifies `canvas_px`, `target_width_px`, and the recorded bounds alpha threshold; nearest-neighbor scaling centers the crop on a transparent canvas. Side/isometric views preserve aspect ratio; top/bottom views explicitly fit 384×384 square content using `target_height_px`, a documented stretch rather than a lossless crop. Alpha 1–15 is set to 0 and secondary 8-connected components no larger than 4 source pixels are removed; the largest and all larger components are preserved. Sidecars record exact cleanup counts. Raw source PNGs remain unchanged. Export sidecars retain both crop and normalization for exact replay. Crop rectangles must be reviewed against the raw image; nominal grid cells are not proof of complete separated objects. Retain all object prompts alongside their sheets.

From the AI-Art root:

```sh
python tools/drainage_expansion.py
python tools/drainage_expansion.py --check
python tools/drainage_expansion.py --render /tmp/drainage-rebuilt.png
python -m unittest discover -s tools -p test_drainage_expansion.py
```

The builder creates deterministic PNG crops/normalized exports, 21 JSON sidecars, a separate catalog, hash-bound review records, and a deterministic top-view example map with exact RGBA replay validation. Clockwise quarter turns apply to logical edges; only top-view rasters are rotated. Image center anchors and one-cell footprints are authored layout assumptions qualified by the recorded rendered fit review. The example validates logical neighboring edges, not pixel seams or gameplay collision.

The art-lab expansion module reads this standalone catalog without adding an eighth entry to the frozen release registry. Root integration owns master indexing, review approval, asset delivery, commits and publication.

`maps/alignment-report.json` reports bounded dark-teal overlap samples for the eight joins. All overlap at the sample lines; the minimum overlap is 76% of the narrower span and maximum center offset is 7 pixels at 128-pixel tile rendering. These heuristic measurements support visual review and do not prove exact border continuity. Dark grid outlines and local channel width/offset differences remain visible.

Reviewed replay uses immutable `source/review-decisions.json`: all 21 accepted asset hashes and the map hash must match, and `root_approval.status` must be `approved-qualified`. A staged build rejects stale decisions before replacing existing outputs. Accepted decisions produce `qualified-reviewed` catalog/asset status and remain part of the deterministic ZIP. The decision record has no generated current timestamp.
