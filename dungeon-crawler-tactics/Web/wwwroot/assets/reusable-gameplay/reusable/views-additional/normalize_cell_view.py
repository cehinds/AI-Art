"""Rebuild partial principal-view correction atlas (one named view per occupied grid cell)."""
from pathlib import Path
import hashlib, json, struct, sys
import numpy as np
from PIL import Image
from scipy import ndimage

OUT = Path(__file__).resolve().parent
PACK = OUT.parents[1]
recipe_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
if recipe_path is None:
    raise SystemExit("usage: python normalize_cell_view.py <recipe.json relative to this folder>")
if not recipe_path.is_absolute():
    recipe_path = OUT / recipe_path
recipe = json.loads(recipe_path.read_text())
raw = PACK / recipe["raw_atlas"]
atlas = Image.open(raw).convert("RGBA")
rgba = np.asarray(atlas)
threshold = recipe.get("alpha_threshold", 245)
mask = rgba[:, :, 3] >= threshold
labels, count = ndimage.label(mask, np.ones((3, 3), dtype=np.uint8))
counts = np.bincount(labels.ravel())
height, width = mask.shape
cols, rows = recipe["grid"]["columns"], recipe["grid"]["rows"]
centers = [((c + .5) * width / cols, (r + .5) * height / rows) for r in range(rows) for c in range(cols)]
assigned = {i: [] for i in range(cols * rows)}
boxes = {}
for label in range(1, count + 1):
    if counts[label] < 4:
        continue
    yy, xx = np.where(labels == label)
    cx, cy = float(xx.mean()), float(yy.mean())
    cell = min(range(cols * rows), key=lambda i: ((cx - centers[i][0]) / (width / cols)) ** 2 + ((cy - centers[i][1]) / (height / rows)) ** 2)
    assigned[cell].append(label)
    boxes[label] = [int(xx.min()), int(yy.min()), int(xx.max() + 1), int(yy.max() + 1)]
index_path = OUT / "set-index.json"
index = json.loads(index_path.read_text()) if index_path.exists() else {"assets": [], "view_sets": []}
asset_map = {a["id"]: a for a in index["assets"]}
set_map = {s["object_id"]: s for s in index["view_sets"]}
raw_hash = hashlib.sha256(raw.read_bytes()).hexdigest()
view = recipe["view"]
for obj in recipe["objects"]:
    cell = obj["cell_index"]
    labels_here = assigned[cell]
    if not labels_here:
        raise RuntimeError(f"{obj['id']}: no alpha components in cell {cell}")
    main = max(labels_here, key=lambda label: counts[label])
    keep = [label for label in labels_here if label == main or counts[label] >= counts[main] * recipe.get("min_component_ratio", .02)]
    selected = [boxes[label] for label in keep]
    x0, y0 = min(b[0] for b in selected), min(b[1] for b in selected)
    x1, y1 = max(b[2] for b in selected), max(b[3] for b in selected)
    local_mask = np.isin(labels[y0:y1, x0:x1], keep)
    crop = atlas.crop((x0, y0, x1, y1))
    crop.putalpha(Image.fromarray((local_mask * 255).astype("uint8")))
    aid = f"{obj['id']}.{view}"
    old = asset_map.get(aid)
    if old is None:
        raise RuntimeError(f"{aid}: no existing principal view to correct")
    prior_scale = float(obj.get("normalization_scale",
        old.get("provenance", {}).get("crop_bounds_px", {}).get("shared_scale", 1.0)))
    projection_scale = float(obj.get("projection_scale", 1.0))
    if projection_scale != 1.0:
        adjusted = (max(1, round(crop.width * projection_scale)),
                    max(1, round(crop.height * projection_scale)))
        crop = crop.resize(adjusted, Image.Resampling.NEAREST)
    scale = min(float(prior_scale), 208 / max(crop.size))
    nw, nh = max(1, round(crop.width * scale)), max(1, round(crop.height * scale))
    crop = crop.resize((nw, nh), Image.Resampling.NEAREST)
    frame = Image.new("RGBA", (256, 256))
    offset = (128 - nw // 2, 128 - nh // 2)
    frame.alpha_composite(crop, offset)
    rel = old["image"]["path"]
    dest = PACK / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    frame.save(dest, optimize=True)
    metadata_path = OUT / f"{aid}.json"
    meta = dict(old)
    meta["image"] = {"path": rel, "width": 256, "height": 256,
        "sha256": hashlib.sha256(dest.read_bytes()).hexdigest(),
        "rgba_sha256": hashlib.sha256(struct.pack(">II", 256, 256) + frame.tobytes()).hexdigest()}
    meta["metadata_path"] = metadata_path.relative_to(PACK).as_posix()
    meta["anchor_px"] = [128, 128]
    prov = dict(meta.get("provenance", {}))
    prov.update({"method": "generated", "source_image": obj.get("source_image", prov.get("source_image")),
        "notes": obj.get("provenance_notes", "inferred orthographic view, not recovered pixels; targeted geometry corrected after review"),
        "source_atlas": recipe["raw_atlas"], "source_atlas_sha256": raw_hash,
        "generation_recipe": recipe_path.relative_to(PACK).as_posix(),
        "crop_bounds_px": {"nominal_cell": {"cell_index": cell, "grid": [cols, rows], "bounds": [round((cell % cols) * width / cols), round((cell // cols) * height / rows), round((cell % cols + 1) * width / cols), round((cell // cols + 1) * height / rows)]},
            "alpha_bounds_global": [x0, y0, x1, y1], "component_labels": keep,
            "resized_bounds_px": [nw, nh], "canvas_offset_px": list(offset), "shared_scale": scale,
            "projection_scale": projection_scale}})
    meta["provenance"] = prov
    metadata_path.write_text(json.dumps(meta, indent=2) + "\n")
    asset_map[aid] = meta
    group = dict(set_map[obj["id"]])
    prior_qa = group.get("geometry_qa", {})
    prior_pending = list(prior_qa.get("views", [])) if prior_qa.get("status") == "pending-correction" else []
    remaining = obj.get("remaining_pending_views", [v for v in prior_pending if v != view])
    if remaining:
        group["complete"] = False
        group["geometry_qa"] = {"status": "pending-correction", "views": remaining,
            "reason": obj.get("qa_reason", prior_qa.get("reason", "Targeted geometry correction remains.")), "atlas_self_inspected": True}
        group["notes"] = "Targeted principal-view geometry correction remains in progress."
    else:
        # A worker's own correction pass is not an independent geometry review.
        # Keep the set incomplete until a reviewer records a current-hash PASS.
        group["complete"] = False
        group["geometry_qa"] = {"status": "pending-review", "views": [view],
            "notes": obj.get("qa_notes", "Targeted view corrected and self-inspected; independent review pending."),
            "atlas_self_inspected": True}
        group["notes"] = "Targeted principal-view correction is awaiting independent review."
    set_map[obj["id"]] = group
index["assets"] = list(asset_map.values())
index["view_sets"] = list(set_map.values())
index_path.write_text(json.dumps(index, indent=2) + "\n")
print(f"Rebuilt {len(recipe['objects'])} {view} corrections from {recipe['raw_atlas']}.")
