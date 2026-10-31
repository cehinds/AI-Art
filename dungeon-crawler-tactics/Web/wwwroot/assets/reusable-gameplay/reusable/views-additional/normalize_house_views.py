"""Normalize a retained six-column house-object atlas into inferred view assets.

Usage: python normalize_house_views.py raw/<batch>.recipe.json
The recipe and atlas paths are pack-relative; all outputs are centered 256x256 PNGs.
"""
from pathlib import Path
import hashlib, json, struct, sys
import numpy as np
from PIL import Image
from scipy import ndimage

OUT = Path(__file__).resolve().parent
PACK = OUT.parents[1]
DIRECTIONS = ["front", "top", "right", "left", "bottom", "rear"]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def bounds_for_cell(labels, counts, boxes, cell, threshold_ratio):
    here = labels_by_cell[cell]
    if not here:
        raise RuntimeError(f"cell {cell}: no alpha components")
    main = max(here, key=lambda label: counts[label])
    keep = [label for label in here if label == main or counts[label] >= counts[main] * threshold_ratio]
    selected = [boxes[label] for label in keep]
    return (min(b[0] for b in selected), min(b[1] for b in selected),
            max(b[2] for b in selected), max(b[3] for b in selected)), keep


recipe_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
if recipe_path is None:
    raise SystemExit("usage: python normalize_house_views.py raw/<batch>.recipe.json")
if not recipe_path.is_absolute():
    recipe_path = OUT / recipe_path
recipe = json.loads(recipe_path.read_text())
atlas_path = PACK / recipe["raw_atlas"]
atlas = Image.open(atlas_path).convert("RGBA")
rgba = np.asarray(atlas)
alpha = rgba[:, :, 3]
threshold = int(recipe.get("alpha_threshold", 245))
labels, count = ndimage.label(alpha >= threshold, np.ones((3, 3), dtype=np.uint8))
counts = np.bincount(labels.ravel())
height, width = alpha.shape
cols, rows = int(recipe["grid"]["columns"]), int(recipe["grid"]["rows"])
if cols != 6:
    raise RuntimeError("House six-view atlas must have exactly six view columns")
centers = [((c + .5) * width / cols, (r + .5) * height / rows) for r in range(rows) for c in range(cols)]
labels_by_cell = {i: [] for i in range(cols * rows)}
boxes = {}
for label in range(1, count + 1):
    if counts[label] < 4:
        continue
    yy, xx = np.where(labels == label)
    cx, cy = float(xx.mean()), float(yy.mean())
    cell = min(range(cols * rows), key=lambda i: ((cx - centers[i][0]) / (width / cols)) ** 2 + ((cy - centers[i][1]) / (height / rows)) ** 2)
    labels_by_cell[cell].append(label)
    boxes[label] = [int(xx.min()), int(yy.min()), int(xx.max() + 1), int(yy.max() + 1)]

index_path = OUT / "set-index.json"
index = json.loads(index_path.read_text()) if index_path.exists() else {"assets": [], "view_sets": []}
asset_map = {a["id"]: a for a in index["assets"]}
set_map = {s["object_id"]: s for s in index["view_sets"]}
raw_hash = sha(atlas_path.read_bytes())
ratio = float(recipe.get("min_component_ratio", .01))
source_manifest = recipe.get("source_metadata", {})

# Compute one isotropic factor per object from the largest full silhouette across all views.
prepared = {}
for obj in recipe["objects"]:
    oid, row = obj["id"], int(obj["row"])
    if row < 0 or row >= rows:
        raise RuntimeError(f"{oid}: row {row} outside atlas")
    bboxes, kept = {}, {}
    selected_views = obj.get("views", DIRECTIONS)
    for view in selected_views:
        col = DIRECTIONS.index(view)
        cell = row * cols + col
        bounds, component_labels = bounds_for_cell(labels, counts, boxes, cell, ratio)
        x0, y0, x1, y1 = bounds
        # Never accept a silhouette cut by the outer atlas canvas.
        if x0 <= 0 or y0 <= 0 or x1 >= width or y1 >= height:
            raise RuntimeError(f"{oid}.{view}: alpha silhouette touches outer atlas edge: {bounds}")
        bboxes[view] = bounds
        kept[view] = component_labels
    max_dim = max(max(b[2] - b[0], b[3] - b[1]) for b in bboxes.values())
    scale = min(float(obj.get("shared_scale", 1.0)), 208.0 / max_dim)
    prepared[oid] = {"bboxes": bboxes, "kept": kept, "scale": scale,
        "views": selected_views, "rotations": obj.get("view_rotations_deg", {})}

for obj in recipe["objects"]:
    oid, row = obj["id"], int(obj["row"])
    srcmeta_path = PACK / "reusable" / "native" / f"{oid}.json"
    srcmeta = json.loads(srcmeta_path.read_text())
    source_rel = srcmeta["image"]["path"]
    source_path = PACK / source_rel
    source_sha = sha(source_path.read_bytes())
    scene_src = srcmeta.get("provenance", {}).get("source_image")
    scene_path = PACK / scene_src if scene_src else None
    scene_sha = sha(scene_path.read_bytes()) if scene_path and scene_path.is_file() else srcmeta.get("provenance", {}).get("source_sha256")
    category = srcmeta.get("category", "prop")
    kind = "tile" if category == "structure" or "rug" in oid else "sprite"
    set_views = dict(set_map.get(oid, {}).get("views", {}))
    per_object_scale = prepared[oid]["scale"]
    for view in prepared[oid]["views"]:
        col = DIRECTIONS.index(view)
        cell = row * cols + col
        x0, y0, x1, y1 = prepared[oid]["bboxes"][view]
        component_labels = prepared[oid]["kept"][view]
        local_mask = np.isin(labels[y0:y1, x0:x1], component_labels)
        piece = atlas.crop((x0, y0, x1, y1))
        piece.putalpha(Image.fromarray((local_mask * 255).astype("uint8")))
        rotation = int(prepared[oid]["rotations"].get(view, 0)) % 360
        if rotation:
            if rotation not in (90, 180, 270):
                raise RuntimeError(f"{oid}.{view}: rotation must be 90, 180, or 270 degrees")
            piece = piece.rotate(rotation, resample=Image.Resampling.NEAREST, expand=True)
        nw = max(1, round(piece.width * per_object_scale))
        nh = max(1, round(piece.height * per_object_scale))
        piece = piece.resize((nw, nh), Image.Resampling.NEAREST)
        frame = Image.new("RGBA", (256, 256))
        offset = (128 - nw // 2, 128 - nh // 2)
        frame.alpha_composite(piece, offset)
        aid = f"{oid}.{view}"
        rel = f"reusable/views-additional/{aid}.png"
        destination = PACK / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        frame.save(destination, optimize=True)
        mpath = OUT / f"{aid}.json"
        tags = list(dict.fromkeys(list(srcmeta.get("tags", [])) + ["inferred-view", view]))
        notes = srcmeta.get("provenance", {}).get("notes", "")
        inference_notes = (f"Inferred orthographic {view} view, not recovered pixels. "
            f"Source crop may include occlusion/context; unrelated context was excluded. "
            f"Unseen geometry/details are conservatively inferred. Source note: {notes}")
        meta = {
            "id": aid, "name": f"{obj.get('name', srcmeta.get('name', oid))} {view.title()}", "kind": kind,
            "tags": tags, "object_id": oid, "view": view,
            "image": {"path": rel, "width": 256, "height": 256,
                "sha256": sha(destination.read_bytes()),
                "rgba_sha256": sha(struct.pack(">II", 256, 256) + frame.tobytes())},
            "metadata_path": mpath.relative_to(PACK).as_posix(), "anchor_px": [128, 128],
            "provenance": {"method": "generated", "source_image": source_rel,
                "source_image_sha256": source_sha, "source_scene": scene_src,
                "source_scene_sha256": scene_sha,
                "source_rect": srcmeta.get("provenance", {}).get("source_rect"),
                "notes": inference_notes, "source_atlas": recipe["raw_atlas"],
                "source_atlas_sha256": raw_hash,
                "generation_recipe": recipe_path.relative_to(PACK).as_posix(),
                "crop_bounds_px": {"nominal_cell": {"cell_index": cell, "grid": [cols, rows],
                    "bounds": [round((cell % cols) * width / cols), round((cell // cols) * height / rows),
                               round((cell % cols + 1) * width / cols), round((cell // cols + 1) * height / rows)]},
                    "alpha_bounds_global": [x0, y0, x1, y1], "component_labels": component_labels,
                    "resized_bounds_px": [nw, nh], "canvas_offset_px": list(offset),
                    "shared_scale": per_object_scale, "projection_scale": 1.0,
                    "orientation_correction_degrees": rotation}},
        }
        mpath.write_text(json.dumps(meta, indent=2) + "\n")
        asset_map[aid] = meta
        set_views[view] = aid
    previous_set = set_map.get(oid, {})
    if previous_set:
        previous_set["views"] = set_views
        previous_set["complete"] = False
        previous_set["geometry_qa"] = {"status": "pending-review", "views": DIRECTIONS,
            "notes": "Generated or corrected views from canonical house crop; independent source-plus-six geometry review pending.",
            "atlas_self_inspected": True}
        set_map[oid] = previous_set
    else:
        set_map[oid] = {"object_id": oid, "views": set_views, "complete": False,
            "geometry_qa": {"status": "pending-review", "views": DIRECTIONS,
                "notes": "Six inferred orthographic views generated from canonical house crop; independent source-plus-six geometry review pending.",
                "atlas_self_inspected": True},
            "notes": "Source crop may be partially occluded; hidden surfaces and any clean geometry beyond the crop are inferred."}

index["assets"] = list(asset_map.values())
index["view_sets"] = list(set_map.values())
index_path.write_text(json.dumps(index, indent=2) + "\n")
print(f"Normalized {len(recipe['objects'])} house objects into {len(recipe['objects']) * 6} inferred view PNGs from {recipe['raw_atlas']}.")
