#!/usr/bin/env python3
"""Rebuild the isolated lower-edge candidate without mutating the live view set."""
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
OBJ = "broadcast-portals-studio-partition-closed-doorway"
ATLAS = HERE / "raw" / f"{OBJ}-bottom-v1-atlas.png"
REQUEST = HERE / "raw" / f"{OBJ}-bottom-v1.request.json"
CONTACT = HERE / "qa-broadcast-closed-door-source-six-v1.png"
SOURCE = PACK / "broadcast-portals" / "components" / f"{OBJ}.png"
CANDIDATE = HERE / "raw" / f"{OBJ}-bottom-v1-candidate.png"
RECIPE = HERE / "raw" / f"{OBJ}-bottom-v1-candidate.recipe.json"
QA = HERE / f"qa-{OBJ}-bottom-v1-candidate-source-six.png"
VIEWS = ("front", "top", "right", "left", "bottom", "rear")
TARGET_WIDTH = 232


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic(path, data):
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


def png_bytes(image):
    import io
    stream = io.BytesIO()
    image.save(stream, "PNG", optimize=True)
    return stream.getvalue()


def main():
    req = json.loads(REQUEST.read_text().removesuffix("\\n"))
    assert req["object_id"] == OBJ and req["view"] == "bottom"
    assert req["status"] == "generated-atlas-ready-for-normalization"
    assert sha(ATLAS) == req["generated_atlas_sha256"]
    assert sha(SOURCE) == req["reference_inputs"][0]["sha256"]
    assert sha(CONTACT) == req["reference_inputs"][1]["sha256"]

    image = Image.open(ATLAS).convert("RGBA")
    alpha = np.asarray(image)[:, :, 3]
    labels, count = ndimage.label(alpha >= 245)
    comps = []
    for label in range(1, count + 1):
        ys, xs = np.nonzero(labels == label)
        if len(xs) >= 50:
            comps.append((len(xs), label, (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)))
    if not comps:
        raise RuntimeError("No substantial alpha component")
    comps.sort(reverse=True)
    main_area = comps[0][0]
    keep = [c for c in comps if c[0] >= main_area * .02]
    x0 = min(c[2][0] for c in keep); y0 = min(c[2][1] for c in keep)
    x1 = max(c[2][2] for c in keep); y1 = max(c[2][3] for c in keep)
    crop = image.crop((x0, y0, x1, y1))
    scale = TARGET_WIDTH / crop.width
    size = (TARGET_WIDTH, max(1, round(crop.height * scale)))
    crop = crop.resize(size, Image.Resampling.NEAREST)
    offset = ((256 - size[0]) // 2, (256 - size[1]) // 2)
    canvas = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    canvas.alpha_composite(crop, offset)
    candidate_bytes = png_bytes(canvas)
    atomic(CANDIDATE, candidate_bytes)
    live = [HERE / f"{OBJ}.{v}.png" for v in VIEWS]
    before = {v: sha(p) for v, p in zip(VIEWS, live)}
    recipe = {
        "schema_version": 1,
        "status": "candidate-ready-for-independent-review",
        "object_id": OBJ,
        "direction": "bottom",
        "request_path": "reusable/views-additional/raw/" + REQUEST.name,
        "request_sha256": sha(REQUEST),
        "source_atlas": "reusable/views-additional/raw/" + ATLAS.name,
        "source_atlas_sha256": sha(ATLAS),
        "canonical_source": "broadcast-portals/components/" + SOURCE.name,
        "canonical_source_sha256": sha(SOURCE),
        "contact_reference": "reusable/views-additional/" + CONTACT.name,
        "contact_reference_sha256": sha(CONTACT),
        "operation": "retain alpha-connected components >=2% of largest at alpha>=245; crop full union; isotropic nearest-neighbor scale to target horizontal extent; center on transparent 256x256",
        "alpha_threshold": 245,
        "component_labels": [c[1] for c in keep],
        "component_bounds_xyxy_px": [x0, y0, x1, y1],
        "crop_dimensions_px": [x1 - x0, y1 - y0],
        "scale": scale,
        "resized_dimensions_px": list(size),
        "canvas_offset_xy_px": list(offset),
        "target_width_px": TARGET_WIDTH,
        "candidate_path": "reusable/views-additional/raw/" + CANDIDATE.name,
        "candidate_sha256": hashlib.sha256(candidate_bytes).hexdigest(),
        "preinstall_view_hashes": before,
        "preserved_views": ["front", "top", "right", "left", "rear"],
        "inference_note": "Inferred straight-up principal view; not recovered pixels or calibrated 3D.",
    }
    atomic(RECIPE, (json.dumps(recipe, indent=2) + "\n").encode())

    source = Image.open(SOURCE).convert("RGBA")
    views = [canvas if v == "bottom" else Image.open(p).convert("RGBA") for v, p in zip(VIEWS, live)]
    sheet = Image.new("RGBA", (7 * 184, 216), (239, 235, 226, 255))
    draw = ImageDraw.Draw(sheet)
    for col, (im, label) in enumerate(zip([source] + views, ["source", *VIEWS])):
        x = col * 184
        draw.text((x + 4, 22), label, fill=(15, 15, 15, 255))
        im.thumbnail((168, 168), Image.Resampling.LANCZOS)
        sheet.alpha_composite(im, (x + 8 + (168 - im.width) // 2, 42 + (168 - im.height) // 2))
    atomic(QA, png_bytes(sheet))
    print(json.dumps({"candidate": str(CANDIDATE), "candidate_sha256": recipe["candidate_sha256"], "recipe_sha256": sha(RECIPE), "qa_contact": str(QA), "bbox": [x0, y0, x1, y1], "size": size, "scale": scale}, indent=2))


if __name__ == "__main__":
    main()
