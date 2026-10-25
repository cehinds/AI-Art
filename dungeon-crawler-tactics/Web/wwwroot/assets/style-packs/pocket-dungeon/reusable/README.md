# Pocket Dungeon reusable artwork

This package extends the existing 360-component Pocket Dungeon collection without
repainting or replacing those PNGs. The canonical files live in `cehinds/AI-Art`
on the `dungeon-crawler` branch. The game's art-lab page is a browser for this data.

## What the files mean

- `index.json` lists assets, per-item JSON paths, reconstruction maps, view sets,
  downloadable archives and measured coverage. All image and metadata paths in
  these JSON files are relative to the **Pocket Dungeon pack root**, one directory
  above this file.
- Existing `components/*.png` are reused. Their new adjacent `.json` files add
  tags, source/extraction provenance, dimensions, hashes and view references.
- `scene-assets/` contains native UI regions, floor samples, and explicitly
  labelled scene fragments. A portrait card or labelled button can retain its
  cream background. A scene fragment with a baked floor is a
  `reconstruction_patch`, not an isolated character sprite.
- `maps/` records every placement's asset, pixel position, layer order, rotation
  and blend rule. The three concept scenes, sixteen source atlases and layered
  preview have independent reconstruction maps.
- `residuals/` preserves remaining source pixels in small, deduplicated patches.
  These are needed for lossless reconstruction; do not use them as procedural
  dungeon tiles. Atlas images can contain RGB data even under fully transparent
  pixels, and that data is retained too.
- `views-*/` contains six-view illustrations and retained generation sources.
  Front, top, right, left, bottom and rear are newly inferred views. They are not
  recovered photographs of hidden surfaces, nor a calibrated 3D model. Each set
  shares a source identity and normalization recipe. Original art remains the
  source of truth for exact reconstruction.
- `procedural/` contains a seeded connected-grid example with walkability,
  neighbor connections, tile positions, rotations and object placements. Floor
  interior samples may show visible repeat seams. The example does not change
  the playable game's collision or map-generation rules.

Flat UI, portraits and visual effects explicitly declare that principal physical
views do not apply. Generated view files reference their parent object and view;
they do not recursively require another six views.

## Reconstruct an original image

From the **AI-Art repository root**, using Python 3 with Pillow and NumPy:

```sh
python3 -m pip install -r tools/pocket-requirements.txt
python3 tools/render_pocket_map.py --list
python3 tools/render_pocket_map.py --map concept-original --output /tmp/pocket-original.png
python3 tools/render_pocket_map.py --map concept-new --output /tmp/pocket-market.png
python3 tools/render_pocket_map.py --map concept-combat --output /tmp/pocket-combat.png
python3 tools/validate_pocket_reusable.py --self-test --require-six-views --report /tmp/pocket-validation.json
```

For an exported archive, pass `--pack` pointing to its Pocket Dungeon pack root.
Use the archive's instructions for the included script locations. Rendering
refuses to overwrite the retained source or any asset.

Exactness is defined as equality of **decoded RGBA pixels**, not identical PNG
compression bytes. The validator compares every pixel independently. Canonical
RGBA hashes are SHA-256 over big-endian unsigned 32-bit width and height followed
by the RGBA bytes. Separate file hashes detect changed PNG files.

## Placement conventions

Coordinates use pixels, origin at the top-left, x increasing right and y down.
`x` and `y` place the image's top-left; `z` is back-to-front order. Lossless maps
use unit scale and integer right-angle rotations (clockwise). `replace` copies
all four channels, `masked-replace` copies RGBA only where source alpha is
nonzero, and `source-over` performs alpha compositing. Do not substitute alpha
compositing for either replacement operation.

Browser canvases may normalize color data underneath transparency. Use the
offline renderer and validator for exact RGBA comparisons. The page's manual
remix exporter separately declares a center anchor; procedural recipes specify
their cell and pixel coordinates explicitly.

## Regenerate derived metadata and examples

```sh
python3 tools/build_pocket_scene_assets.py --seed 23
python3 tools/build_pocket_reusable.py --rebuild
python3 tools/build_pocket_reusable.py --check
python3 tools/validate_pocket_reusable.py --self-test --require-six-views
```

Extraction and normalization also use SciPy; tested dependency versions are in
`tools/pocket-requirements.txt`. View normalization helpers in `views-*/` use retained raw generations. Their
recorded crop, scale and anchor parameters permit offline reconstruction of the
derived PNGs. Re-running an image-generation model is not expected to reproduce
the same pixels. Do not replace retained generation sources or claim regenerated
art is an extraction from the original scenes.

Download archives omit large raw view-generation atlases when recorded in
`archive-provenance.json`; those remain in the canonical art repository. Archive
manifests identify included files and hashes. ZIP downloads on the art-lab page
come from the pinned art-repository revision, while interactive PNGs and JSON
remain on the website.

Preserve existing attribution and licence records. This is an unofficial fan-art
library; these exports do not grant new rights to characters, settings or other
underlying material.
