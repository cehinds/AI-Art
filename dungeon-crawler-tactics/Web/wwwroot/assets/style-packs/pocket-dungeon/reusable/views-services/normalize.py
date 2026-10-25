#!/usr/bin/env python3
"""Normalize retained six-view atlas generations. No artwork is drawn here."""
from pathlib import Path
import hashlib, json, struct
from datetime import datetime, timezone

import numpy as np
from PIL import Image
from scipy import ndimage

OUT = Path(__file__).resolve().parent
PACK = OUT.parents[1]
VIEWS = ["front", "top", "right", "left", "bottom", "rear"]
MANIFEST = OUT / "generation.json"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def rgba_sha(im):
    im = im.convert("RGBA")
    return hashlib.sha256(struct.pack(">II", *im.size) + im.tobytes()).hexdigest()

def atomic_json(path, obj):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")
    tmp.replace(path)

def auxiliary_meta(path, kind, provenance):
    im = Image.open(path).convert("RGBA")
    meta = path.with_suffix(".json")
    atomic_json(meta, {"id": path.stem, "name": path.stem.replace("-", " ").title(), "kind": kind,
                       "reusable": False, "tags": ["pipeline-artifact"],
                       "image": {"path": path.relative_to(PACK).as_posix(), "width": im.width, "height": im.height,
                                 "sha256": sha(path), "rgba_sha256": rgba_sha(im)},
                       "metadata_path": meta.relative_to(PACK).as_posix(), "anchor_px": [0,0],
                       "views": {"applicable": False, "complete": True,
                                 "reason": "Pipeline atlas or preview sheet, not a placed physical object."},
                       "provenance": provenance})

def main_component_group(im, row, col, rows):
    """Choose whole components by centroid cell; include nearby detached details.

    This intentionally does not crop at nominal cell edges, so a component that
    drifts across a grid line remains intact. Alpha <245 is treated as glow/fringe.
    """
    arr = np.asarray(im.convert("RGBA"))
    mask = arr[:, :, 3] >= 245
    labels, n = ndimage.label(mask, np.ones((3, 3), dtype=np.uint8))
    h, w = mask.shape
    cell_w, cell_h = w / 6, h / rows
    comps = []
    for k, slc in enumerate(ndimage.find_objects(labels), start=1):
        if slc is None:
            continue
        local_y, local_x = np.nonzero(labels[slc] == k)
        area = len(local_x)
        if area < 18:
            continue
        y0, y1 = slc[0].start, slc[0].stop
        x0, x1 = slc[1].start, slc[1].stop
        comps.append({"label": k, "area": area, "cx": float(x0 + local_x.mean()), "cy": float(y0 + local_y.mean()),
                      "bbox": [x0, y0, x1, y1]})
    in_cell = [c for c in comps if int(c["cy"] / cell_h) == row and int(c["cx"] / cell_w) == col]
    if not in_cell:
        raise RuntimeError(f"no alpha component for atlas cell {row},{col}")
    main = max(in_cell, key=lambda c: c["area"])
    x0, y0, x1, y1 = main["bbox"]
    # Keep nearby disconnected spikes, glints, mushrooms, and ground chips.
    selected = [main]
    for c in in_cell:
        if c is main or c["area"] < 45:
            continue
        a, b, d, e = c["bbox"]
        dx = max(x0 - d, a - x1, 0)
        dy = max(y0 - e, b - y1, 0)
        if (dx * dx + dy * dy) ** .5 <= 34:
            selected.append(c)
    x0 = min(c["bbox"][0] for c in selected); y0 = min(c["bbox"][1] for c in selected)
    x1 = max(c["bbox"][2] for c in selected); y1 = max(c["bbox"][3] for c in selected)
    keep = np.isin(labels[y0:y1, x0:x1], [c["label"] for c in selected])
    crop = im.crop((x0, y0, x1, y1)).convert("RGBA")
    crop.putalpha(Image.fromarray((keep * 255).astype(np.uint8), "L"))
    edge_touch = x0 == 0 or y0 == 0 or x1 == w or y1 == h
    return crop, [x0, y0, x1-x0, y1-y0], [c["label"] for c in selected], edge_touch

def main():
    batches = json.loads(MANIFEST.read_text())
    assets, sets = [], []
    created = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    for batch in batches:
        raw = OUT / batch["raw"]
        atlas = Image.open(raw).convert("RGBA")
        if atlas.width % 6 or atlas.height % len(batch["objects"]):
            raise ValueError(f"atlas dimensions do not match 6 x object rows: {raw.name} {atlas.size}")
        rows = len(batch["objects"])
        atlas_sha = sha(raw)
        auxiliary_meta(raw, "generated_atlas", {"method": "generated", "generated_at": created,
                       "generation_parameters": {"tool": "image_gen.imagegen", "transparent_background": True,
                                                  "prompt": batch["prompt"],
                                                  "reference_images": [(PACK / "components" / f"{oid}.png").relative_to(PACK).as_posix() for oid in batch["objects"]]},
                       "notes": "Unmodified raw generation retained for review and reproducibility."})
        recipe_objects = []
        for row, oid in enumerate(batch["objects"]):
            source_meta = json.loads((PACK / "components" / f"{oid}.json").read_text())
            crops, rects, labels, edge_touches = [], [], [], []
            for col in range(6):
                crop, rect, component_labels, edge = main_component_group(atlas, row, col, rows)
                crops.append(crop); rects.append(rect); labels.append(component_labels); edge_touches.append(edge)
            scale = 220 / max(max(c.size) for c in crops)
            view_ids = {}
            for col, (view, crop) in enumerate(zip(VIEWS, crops)):
                size = [max(1, round(crop.width * scale)), max(1, round(crop.height * scale))]
                frame = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
                frame.alpha_composite(crop.resize(size, Image.Resampling.NEAREST), ((256-size[0])//2, 248-size[1]))
                aid = f"{oid}.{view}"; path = OUT / f"{aid}.png"; frame.save(path)
                meta_path = path.with_suffix(".json")
                rel = path.relative_to(PACK).as_posix()
                source_path = PACK / "components" / f"{oid}.png"
                d = {
                    "id": aid, "name": f"{source_meta['name']} {view}", "kind": source_meta["kind"],
                    "tags": sorted(set(source_meta.get("tags", [])) | {"isolated", "orthographic", "inferred-view", view}),
                    "object_id": oid, "view": view, "reusable": True,
                    "image": {"path": rel, "width": 256, "height": 256, "sha256": sha(path), "rgba_sha256": rgba_sha(frame)},
                    "metadata_path": meta_path.relative_to(PACK).as_posix(), "anchor_px": [128, 248],
                    "views": {"applicable": False, "complete": True, "reason": "Directional member of a generated six-view object set."},
                    "provenance": {
                        "method": "generated", "source_image": source_path.relative_to(PACK).as_posix(),
                        "source_image_sha256": sha(source_path), "generated_atlas": raw.relative_to(PACK).as_posix(),
                        "generated_atlas_sha256": atlas_sha,
                        "generation_parameters": {"tool": "image_gen.imagegen", "transparent_background": True,
                                                   "prompt": batch["prompt"], "reference_images": [(PACK / "components" / f"{ref_id}.png").relative_to(PACK).as_posix() for ref_id in batch["objects"]]},
                        "normalization": {"cell_centroid_assignment": [row, col], "alpha_threshold": 245,
                                          "component_labels": labels[col], "component_policy": "largest centroid-assigned component plus nearby detached alpha components within 34 px; whole component bounds, not nominal cell crop",
                                          "cell_rect": rects[col], "atlas_edge_touch": edge_touches[col],
                                          "shared_scale": scale, "render_size_px": size, "canvas": [256,256],
                                          "resampling": "NEAREST", "anchor_px": [128,248]},
                        "notes": "Generated directional reconstruction with inferred hidden surfaces; not recovered source geometry. Low alpha glow and fringe were removed by alpha thresholding."
                    }
                }
                atomic_json(meta_path, d); assets.append(d); view_ids[view] = aid
            sets.append({"object_id": oid, "views": view_ids, "complete": True,
                         "notes": "Six generated principal views; inferred hidden surfaces. Same shared normalization scale across all directions."})
            recipe_objects.append({"object_id": oid, "row": row, "view_crop_rects": rects,
                                   "component_labels_by_view": labels, "atlas_edge_touch_by_view": edge_touches,
                                   "shared_scale": scale})
        atomic_json(raw.with_suffix(".recipe.json"), {"atlas_sha256": atlas_sha, "objects": recipe_objects,
                                                       "normalizer": "reusable/views-services/normalize.py"})
        atomic_json(OUT / "set-index.json", {"assets": assets, "view_sets": sets})
        print(f"persisted {len(sets)} complete sets ({len(assets)} views) through {batch['raw']}", flush=True)
    # Preview sheet of normalized assets, six columns per object.
    preview = Image.new("RGBA", (6*256, len(sets)*256))
    for r, s in enumerate(sets):
        for c, view in enumerate(VIEWS):
            preview.alpha_composite(Image.open(OUT / f"{s['views'][view]}.png").convert("RGBA"), (c*256, r*256))
    preview_path = OUT / "preview.png"; preview.save(preview_path)
    auxiliary_meta(preview_path, "contact_sheet", {"method": "composed",
                   "source_images": [a["image"]["path"] for a in assets]})
    print(f"complete: {len(sets)} sets, {len(assets)} views, preview={preview_path}")

if __name__ == "__main__":
    main()
