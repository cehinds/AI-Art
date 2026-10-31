#!/usr/bin/env python3
"""Replay the three recorded dynamite-bundle cells to an explicit evidence directory.

This is a non-installing replay: it verifies the retained atlas and canonical
source hashes, writes only under --output-dir, and never touches active views or
indices. Pixel extraction and normalization intentionally mirror the original
installer's component-centroid selection and NEAREST resize.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

PACK = Path(__file__).resolve().parents[4]
INSTALL = PACK / "reusable/views-equipment/raw/targeted-repairs/legacy-dynamite-crossbow-v1-install.json"
TARGET = "arsenal-dynamite-bundle"
VIEWS = {"front", "top", "rear"}
TARGET_X = [192, 528, 900, 1273, 1633, 1980]
TARGET_Y = [219, 522]


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def rgba_sha(image: Image.Image) -> str:
    converted = image.convert("RGBA")
    return sha_bytes(struct.pack(">II", *converted.size) + converted.tobytes())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    out = args.output_dir.resolve()
    if out == PACK or PACK in out.parents:
        raise SystemExit("output directory must be outside the canonical pack")
    out.mkdir(parents=True, exist_ok=True)

    recipe = json.loads(INSTALL.read_text())
    atlas_path = PACK / recipe["atlas"]
    atlas_sha = sha_file(atlas_path)
    if atlas_sha != recipe["atlas_sha256"]:
        raise SystemExit("retained atlas SHA mismatch")
    source = recipe["objects"][TARGET]
    source_path = PACK / source["source"]
    source_sha = sha_file(source_path)
    if source_sha != source["source_sha256"]:
        raise SystemExit("canonical source SHA mismatch")

    atlas = Image.open(atlas_path).convert("RGBA")
    alpha = np.asarray(atlas)[:, :, 3]
    labels, _ = ndimage.label(alpha >= 245, structure=np.ones((3, 3), dtype=np.uint8))
    records = []
    for cell in recipe["cells"]:
        if cell["object_id"] != TARGET or cell["view"] not in VIEWS:
            continue
        view = cell["view"]
        target_x, target_y = TARGET_X[cell["col"]], TARGET_Y[cell["row"]]
        best = None
        for label, sl in enumerate(ndimage.find_objects(labels), 1):
            if sl is None:
                continue
            area = int((labels[sl] == label).sum())
            if area < 1000:
                continue
            yy, xx = ndimage.center_of_mass(labels == label)
            distance = ((xx - target_x) ** 2 + (yy - target_y) ** 2) ** 0.5
            if best is None or distance < best[0]:
                best = (distance, label, area, sl)
        if best is None or best[0] > 90:
            raise SystemExit(f"no selected atlas component for {TARGET}.{view}")
        _, label, area, sl = best
        y0, y1 = sl[0].start, sl[0].stop
        x0, x1 = sl[1].start, sl[1].stop
        pixels = np.asarray(atlas.crop((x0, y0, x1, y1))).copy()
        pixels[:, :, 3] = np.where(labels[y0:y1, x0:x1] == label, 255, 0).astype(np.uint8)
        body = Image.fromarray(pixels, "RGBA")
        scale = cell["scale"]
        size = (round(body.width * scale), round(body.height * scale))
        body = body.resize(size, Image.Resampling.NEAREST)
        canvas = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
        canvas.alpha_composite(body, (128 - size[0] // 2, 248 - size[1]))
        destination = out / f"{TARGET}.{view}.png"
        canvas.save(destination, optimize=True)
        records.append({
            "object_id": TARGET,
            "view": view,
            "scale": scale,
            "source_path": source["source"],
            "source_sha256": source_sha,
            "atlas_path": recipe["atlas"],
            "atlas_sha256": atlas_sha,
            "crop_bounds_xyxy": [x0, y0, x1, y1],
            "component_label": label,
            "component_area_px": area,
            "resized_dimensions_px": list(size),
            "replay_output_path": str(destination),
            "replay_output_sha256": sha_file(destination),
            "replay_output_rgba_sha256": rgba_sha(canvas),
        })
    if {record["view"] for record in records} != VIEWS:
        raise SystemExit("replay did not produce the exact three requested views")
    print(json.dumps({
        "schema_version": 1,
        "replay_status": "executed",
        "installer_recipe_path": INSTALL.relative_to(PACK).as_posix(),
        "installer_recipe_sha256": sha_file(INSTALL),
        "atlas_path": recipe["atlas"],
        "atlas_sha256": atlas_sha,
        "canonical_source_path": source["source"],
        "canonical_source_sha256": source_sha,
        "records": records,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
