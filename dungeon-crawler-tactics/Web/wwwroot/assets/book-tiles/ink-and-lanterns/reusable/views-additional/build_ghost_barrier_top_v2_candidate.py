#!/usr/bin/env python3
"""Rebuild an isolated TOP candidate from the retained road-barrier atlas."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = Path(__file__).resolve().parent
PACK = HERE.parents[1]
OBJ = "ghost-havana-ghost-traffic-road-barrier"
ATLAS = HERE / "raw" / f"{OBJ}-top-v2-atlas.png"
REQUEST = HERE / "raw" / f"{OBJ}-top-v2.request.json"
CANONICAL = PACK / "ghost-havana" / "components" / f"{OBJ}.png"
CONTACT = HERE / f"qa-{OBJ}-current-source-six-pre-repair.png"
CANDIDATE = HERE / "raw" / f"{OBJ}-top-v2-candidate.png"
RECIPE = HERE / "raw" / f"{OBJ}-top-v2-candidate.recipe.json"
QA = HERE / f"qa-{OBJ}-top-v2-candidate-source-six.png"
DIRECTIONS = ("front", "top", "right", "left", "bottom", "rear")
TARGET_WIDTH = 223


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic(path: Path, data: bytes) -> None:
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise


def png_bytes(im: Image.Image) -> bytes:
    import io
    stream = io.BytesIO()
    im.save(stream, format="PNG", optimize=True)
    return stream.getvalue()


def canonical_rgba_sha(im: Image.Image) -> str:
    rgba = im.convert("RGBA")
    return hashlib.sha256(rgba.width.to_bytes(4, "big") + rgba.height.to_bytes(4, "big") + rgba.tobytes()).hexdigest()


def main() -> None:
    req_text = REQUEST.read_text().removesuffix("\\n")
    req = json.loads(req_text)
    assert req["object_id"] == OBJ and req["view"] == "top"
    assert req["status"] == "generated-atlas-ready-for-normalization"
    assert sha(ATLAS) == req["generated_atlas_sha256"]
    assert sha(CANONICAL) == req["reference_inputs"][0]["sha256"]
    assert sha(CONTACT) == req["reference_inputs"][1]["sha256"]

    atlas = Image.open(ATLAS).convert("RGBA")
    alpha = np.asarray(atlas)[:, :, 3]
    labels, count = ndimage.label(alpha >= 245)
    components = []
    for label in range(1, count + 1):
        ys, xs = np.nonzero(labels == label)
        if len(xs) >= 50:
            components.append((len(xs), label, (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)))
    if not components:
        raise RuntimeError("No substantial opaque component in generated atlas")
    components.sort(reverse=True)
    area, main_label, bounds = components[0]
    x0, y0, x1, y1 = bounds
    crop = atlas.crop(bounds)
    scale = TARGET_WIDTH / crop.width
    out_size = (TARGET_WIDTH, max(1, round(crop.height * scale)))
    crop = crop.resize(out_size, Image.Resampling.NEAREST)
    xoff = (256 - out_size[0]) // 2
    yoff = (256 - out_size[1]) // 2
    canvas = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    canvas.alpha_composite(crop, (xoff, yoff))
    candidate_bytes = png_bytes(canvas)
    atomic(CANDIDATE, candidate_bytes)

    source_views = [PACK / f"reusable/views-additional/{OBJ}.{d}.png" for d in DIRECTIONS]
    old_hashes = {d: sha(p) for d, p in zip(DIRECTIONS, source_views)}
    recipe = {
        "schema_version": 1,
        "status": "candidate-ready-for-independent-review",
        "object_id": OBJ,
        "direction": "top",
        "request_path": "reusable/views-additional/raw/" + REQUEST.name,
        "request_sha256": sha(REQUEST),
        "source_atlas": "reusable/views-additional/raw/" + ATLAS.name,
        "source_atlas_sha256": sha(ATLAS),
        "canonical_source": "ghost-havana/components/" + CANONICAL.name,
        "canonical_source_sha256": sha(CANONICAL),
        "contact_reference": "reusable/views-additional/" + CONTACT.name,
        "contact_reference_sha256": sha(CONTACT),
        "operation": "extract largest alpha-connected component at alpha >= 245; crop complete component; isotropic nearest-neighbor scale to 223 px full plan span; center on transparent 256x256 canvas",
        "alpha_threshold": 245,
        "component_label": main_label,
        "component_area_px": area,
        "component_bounds_xyxy_px": list(bounds),
        "crop_dimensions_px": [x1 - x0, y1 - y0],
        "scale": scale,
        "resized_dimensions_px": list(out_size),
        "canvas_offset_xy_px": [xoff, yoff],
        "target_width_px": TARGET_WIDTH,
        "candidate_path": "reusable/views-additional/raw/" + CANDIDATE.name,
        "candidate_file_sha256": hashlib.sha256(candidate_bytes).hexdigest(),
        "candidate_rgba_sha256": canonical_rgba_sha(canvas),
        "preinstall_view_hashes": old_hashes,
        "preserved_views": ["front", "right", "left", "bottom", "rear"],
        "inference_note": "Orthographic inferred overhead illustration; not recovered pixels and not calibrated 3D.",
    }
    atomic(RECIPE, (json.dumps(recipe, indent=2) + "\n").encode())

    # Source plus all six current/candidate views on a neutral opaque ground.
    src = Image.open(CANONICAL).convert("RGBA")
    cells = [src] + [canvas if d == "top" else Image.open(p).convert("RGBA") for d, p in zip(DIRECTIONS, source_views)]
    sheet = Image.new("RGB", (7 * 256 + 6 * 12, 284), (112, 112, 112))
    draw = ImageDraw.Draw(sheet)
    labels_text = ["SOURCE", *[d.upper() for d in DIRECTIONS]]
    for i, (cell, label) in enumerate(zip(cells, labels_text)):
        x = i * 268
        draw.text((x + 6, 5), label, fill=(235, 235, 235))
        bg = Image.new("RGBA", (256, 256), (112, 112, 112, 255))
        bg.alpha_composite(cell, (0, 0))
        sheet.paste(bg.convert("RGB"), (x, 28))
    atomic(QA, png_bytes(sheet.convert("RGBA")))
    print(json.dumps({"candidate": str(CANDIDATE), "candidate_sha256": recipe["candidate_file_sha256"], "recipe_sha256": sha(RECIPE), "qa_contact": str(QA), "component_bounds": bounds, "dimensions": out_size, "scale": scale}, indent=2))


if __name__ == "__main__":
    main()
