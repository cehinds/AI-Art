"""Rebuild one views-additional batch from its retained raw atlas and recipe JSON."""
from pathlib import Path
import hashlib, json, struct, sys, os, tempfile
import numpy as np
from PIL import Image
from scipy import ndimage

OUT = Path(__file__).resolve().parent
PACK = OUT.parents[1]
recipe_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
if recipe_path is None:
    raise SystemExit("usage: python normalize_batch.py <recipe.json relative to this folder>")
if not recipe_path.is_absolute():
    recipe_path = OUT / recipe_path
recipe = json.loads(recipe_path.read_text())
raw = PACK / recipe["raw_atlas"]
atlas = Image.open(raw).convert("RGBA")
rgba = np.asarray(atlas)
mask = rgba[:, :, 3] >= recipe.get("alpha_threshold", 245)
labels, n = ndimage.label(mask, np.ones((3, 3), dtype=np.uint8))
counts = np.bincount(labels.ravel())
height, width = mask.shape
columns, rows = recipe["grid"]["columns"], recipe["grid"]["rows"]
centers = [((x + 0.5) * width / columns, (y + 0.5) * height / rows) for y in range(rows) for x in range(columns)]
assign = {i: [] for i in range(columns * rows)}
props = {}
for label in range(1, n + 1):
    if counts[label] < 4:
        continue
    yy, xx = np.where(labels == label)
    cx, cy = float(xx.mean()), float(yy.mean())
    cell = min(range(columns * rows), key=lambda i: ((cx - centers[i][0]) / (width / columns)) ** 2 + ((cy - centers[i][1]) / (height / rows)) ** 2)
    assign[cell].append(label)
    props[label] = [int(xx.min()), int(yy.min()), int(xx.max() + 1), int(yy.max() + 1)]
all_views = ["front", "top", "right", "left", "bottom", "rear"]
views = recipe.get("views", all_views)
if columns != len(views):
    raise ValueError(f"recipe grid has {columns} columns but {len(views)} views are configured")
old_index = OUT / "set-index.json"
old_data = json.loads(old_index.read_text()) if old_index.exists() else {"assets": [], "view_sets": []}
old_sets = {s["object_id"]: s for s in old_data["view_sets"]}
# Fail closed: never overwrite an existing view unless the recipe explicitly
# whitelists exactly the directions being rebuilt for that object.
for obj in recipe["objects"]:
    if obj.get("status", "accepted") != "accepted":
        continue
    oid = obj["id"]
    if oid in old_sets:
        allowed = set(obj.get("replace_views", []))
        if not allowed or set(views) - allowed:
            raise ValueError(f"{oid}: already indexed; recipe must explicitly whitelist every replaced view")
assets, view_sets = [], []
raw_hash = hashlib.sha256(raw.read_bytes()).hexdigest()
for obj in recipe["objects"]:
    if obj.get("status", "accepted") != "accepted":
        continue
    row, oid = obj["row"], obj["id"]
    refs = dict(old_sets.get(oid, {}).get("views", {}))
    pieces = []
    for col, view in enumerate(views):
        labels_here = assign[row * columns + col]
        if not labels_here:
            continue
        main = max(labels_here, key=lambda label: counts[label])
        keep = [label for label in labels_here if label == main or counts[label] >= counts[main] * recipe.get("min_component_ratio", 0.02)]
        boxes = [props[label] for label in keep]
        x0, y0 = min(b[0] for b in boxes), min(b[1] for b in boxes)
        x1, y1 = max(b[2] for b in boxes), max(b[3] for b in boxes)
        local_labels = labels[y0:y1, x0:x1, None]
        local = (local_labels == np.asarray(keep)[None, None, :]).any(axis=2)
        crop = atlas.crop((x0, y0, x1, y1))
        crop.putalpha(Image.fromarray((local * 255).astype("uint8")))
        pieces.append((view, crop, [x0, y0, x1, y1], col, keep))
    if len(pieces) != len(views):
        raise RuntimeError(f"{oid}: expected {len(views)} nonempty views, got {len(pieces)}")
    scale = recipe.get("shared_scale_override", min(208 / max(max(piece.size) for _, piece, *_ in pieces), 1.0))
    for view, piece, bounds, col, keep in pieces:
        nw, nh = max(1, round(piece.width * scale)), max(1, round(piece.height * scale))
        piece = piece.resize((nw, nh), Image.Resampling.NEAREST)
        frame = Image.new("RGBA", (256, 256))
        offset = (128 - nw // 2, 128 - nh // 2)
        frame.alpha_composite(piece, offset)
        asset_id = f"{oid}.{view}"
        rel = f"reusable/views-additional/{asset_id}.png"
        dest = PACK / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        frame.save(dest, optimize=True)
        meta_path = OUT / f"{asset_id}.json"
        metadata = {
            "id": asset_id,
            "name": f"{obj['name']} {view.title()}",
            "kind": obj["kind"],
            "tags": [*obj.get("tags", []), "inferred-view", view],
            "object_id": oid,
            "view": view,
            "image": {
                "path": rel,
                "width": 256,
                "height": 256,
                "sha256": hashlib.sha256(dest.read_bytes()).hexdigest(),
                "rgba_sha256": hashlib.sha256(struct.pack(">II", 256, 256) + frame.tobytes()).hexdigest(),
            },
            "metadata_path": meta_path.relative_to(PACK).as_posix(),
            "anchor_px": [128, 128],
            "provenance": {
                "method": "generated",
                "source_image": obj["source_image"],
                **({"scene_source": obj["scene_source"]} if obj.get("scene_source") is not None else {}),
                **({"scene_source_rect": obj["scene_source_rect"]} if obj.get("scene_source_rect") is not None else {}),
                "notes": "inferred orthographic view, not recovered pixels",
                "source_atlas": recipe["raw_atlas"],
                "source_atlas_sha256": raw_hash,
                "generation_recipe": recipe_path.relative_to(PACK).as_posix(),
                "crop_bounds_px": {
                    "nominal_cell": {"column": col, "row": row, "bounds": [round(col * width / columns), round(row * height / rows), round((col + 1) * width / columns), round((row + 1) * height / rows)]},
                    "alpha_bounds_global": bounds,
                    "component_labels": keep,
                    "resized_bounds_px": [nw, nh],
                    "canvas_offset_px": list(offset),
                    "shared_scale": scale,
                },
            },
        }
        meta_path.write_text(json.dumps(metadata, indent=2) + "\n")
        assets.append(metadata)
        refs[view] = asset_id
    set_entry = dict(old_sets.get(oid, {}))
    set_entry.update({"object_id": oid, "views": refs, "complete": all(v in refs for v in all_views), "notes": "Six generated orthographic views; unseen surfaces conservatively inferred."})
    if obj.get("geometry_qa") is not None:
        set_entry["geometry_qa"] = obj["geometry_qa"]
    if set_entry.get("geometry_qa", {}).get("status") in {"pending-correction", "pending-review"}:
        set_entry["complete"] = False
    view_sets.append(set_entry)
index_path = OUT / "set-index.json"
old = old_data
by_id = {a["id"]: a for a in old["assets"] if (PACK / a["image"]["path"]).exists()}
by_id.update({a["id"]: a for a in assets})
sets_by_id = {s["object_id"]: s for s in old["view_sets"]}
sets_by_id.update({s["object_id"]: s for s in view_sets})
payload = json.dumps({"assets": list(by_id.values()), "view_sets": list(sets_by_id.values())}, indent=2) + "\n"
fd, tmp_name = tempfile.mkstemp(prefix="set-index.", suffix=".tmp", dir=OUT)
os.close(fd)
Path(tmp_name).write_text(payload)
os.replace(tmp_name, index_path)
print(f"Rebuilt {len(view_sets)} sets / {len(assets)} views from {recipe['raw_atlas']}.")
