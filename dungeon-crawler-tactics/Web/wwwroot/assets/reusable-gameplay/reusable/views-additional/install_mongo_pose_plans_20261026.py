#!/usr/bin/env python3
"""Install source-bound Mongo pose TOP/BOTTOM plans from retained atlases.

Each 6-cell atlas is split by its declared equal-width cells; every alpha pixel
inside the cell is retained. A uniform scale matches plan X to accepted front
width and plan Y to accepted profile length, centered on the shared anchor.
"""
from __future__ import annotations
import hashlib, json, os, struct
from pathlib import Path
from PIL import Image

PACK = Path(__file__).resolve().parents[2]
VIEWS = PACK / "reusable/views-additional"
RAW = VIEWS / "raw"
OBJECTS = [
    "revamp--characters--mongo",
    "revamp--characters--mongo--idle2",
    "revamp--characters--mongo--walk1",
    "revamp--characters--mongo--walk2",
    "revamp--characters--mongo--walk3",
    "revamp--characters--mongo--windup",
]
ATLASES = {
    "top": ("mongo-sixposes-top-single-20261026.png", "exec-81d350c1-6d79-4116-ab5e-092f5e7cfa80", "TOP atlas prompt, retained beside source atlas"),
    "bottom": ("mongo-sixposes-bottom-single-20261026.png", "exec-0bb68376-df82-4e0b-9f4a-1434207b5d26", "BOTTOM atlas prompt, retained beside source atlas"),
}

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def image_hash(im: Image.Image) -> str:
    rgba = im.convert("RGBA")
    return sha(struct.pack(">II", *rgba.size) + rgba.tobytes())

idx_path = VIEWS / "set-index.json"
index = json.loads(idx_path.read_text())
records = {a["id"]: a for a in index["assets"]}
staged = []
for view, (atlas_name, request_id, prompt_note) in ATLASES.items():
    atlas_path = RAW / atlas_name
    atlas_bytes = atlas_path.read_bytes()
    atlas = Image.open(atlas_path).convert("RGBA")
    w, h = atlas.size
    if w % len(OBJECTS):
        raise ValueError(f"{atlas_name}: width is not evenly divisible into six cells")
    cell_w = w // len(OBJECTS)
    for i, oid in enumerate(OBJECTS):
        asset_id = f"{oid}.{view}"
        metadata_path = VIEWS / f"{asset_id}.json"
        output_path = VIEWS / f"{asset_id}.png"
        meta = json.loads(metadata_path.read_text())
        source_image = meta["provenance"]["source_image"]
        # Keep all views bound to this pose's canonical native source.
        primary = PACK / "reusable/native" / f"{oid}.png"
        if not primary.exists():
            raise FileNotFoundError(primary)
        if source_image != f"reusable/native/{oid}.png":
            raise ValueError(f"{asset_id}: noncanonical provenance source {source_image}")
        cell = atlas.crop((i * cell_w, 0, (i + 1) * cell_w, h))
        alpha = cell.getchannel("A")
        # Threshold 16 excludes transparent RGB fringes while retaining soft edges.
        mask = alpha.point(lambda x: 255 if x >= 16 else 0)
        bounds = mask.getbbox()
        if not bounds:
            raise ValueError(f"{atlas_name}: empty cell {i} ({oid})")
        crop = cell.crop(bounds)
        prior = Image.open(output_path).convert("RGBA")
        pb = prior.getchannel("A").getbbox()
        if not pb:
            raise ValueError(f"{asset_id}: existing view has no visible pixels")
        # A top-plan X span matches the front-view width; Y matches side-profile length.
        target_x = (Image.open(VIEWS / f"{oid}.front.png").convert("RGBA").getchannel("A").getbbox()[2]
                    - Image.open(VIEWS / f"{oid}.front.png").convert("RGBA").getchannel("A").getbbox()[0])
        side_boxes = [Image.open(VIEWS / f"{oid}.{v}.png").convert("RGBA").getchannel("A").getbbox() for v in ("right", "left")]
        target_y = sum(b[2] - b[0] for b in side_boxes) / 2
        scale = min(target_x / crop.width, target_y / crop.height)
        nw, nh = max(1, round(crop.width * scale)), max(1, round(crop.height * scale))
        resized = crop.resize((nw, nh), Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
        offset = (128 - nw // 2, 128 - nh // 2)
        canvas.alpha_composite(resized, offset)
        old_bytes = output_path.read_bytes()
        staged.append((asset_id, output_path, metadata_path, meta, old_bytes, canvas,
                       atlas_name, sha(atlas_bytes), request_id, i, cell_w, h,
                       bounds, (nw, nh), offset, scale, source_image, sha(primary.read_bytes())))

# All inputs and outputs have been staged before any production file is replaced.
for (asset_id, out_path, meta_path, meta, old_bytes, canvas, atlas_name, atlas_sha,
     request_id, cell_i, cell_w, cell_h, crop_box, resized, offset, scale,
     source_image, source_sha) in staged:
    tmp = out_path.with_suffix(".png.tmp")
    canvas.save(tmp, format="PNG", optimize=False)
    os.replace(tmp, out_path)
    new_bytes = out_path.read_bytes()
    meta["image"]["width"], meta["image"]["height"] = canvas.size
    meta["image"]["sha256"] = sha(new_bytes)
    meta["image"]["rgba_sha256"] = image_hash(canvas)
    meta["provenance"].update({
        "source_image": source_image,
        "source_image_sha256": source_sha,
        "source_atlas": f"reusable/views-additional/raw/{atlas_name}",
        "source_atlas_sha256": atlas_sha,
        "generation_request_id": request_id,
        "generation_recipe": f"reusable/views-additional/install_mongo_pose_plans_20261026.py",
        "notes": "Generated inferred orthographic plan for the exact source pose; broad skull/snout and differentiated tail are retained, with per-pose limb phase. Hidden underside surfaces are inferred, not recovered pixels.",
        "crop_bounds_px": {
            "coordinate_format": "xywh",
            "nominal_cell": {"bounds": [cell_i * cell_w, 0, cell_w, cell_h]},
            "alpha_threshold": 16,
            "alpha_bounds_global": [cell_i * cell_w + crop_box[0], crop_box[1], crop_box[2] - crop_box[0], crop_box[3] - crop_box[1]],
            "resized_bounds_px": list(resized),
            "canvas_offset_px": list(offset),
            "shared_anchor_px": [128, 128],
            "uniform_scale": scale,
            "normalization": "uniform isotropic scale matching accepted front X span and right/left profile Y span, centered at shared anchor",
        },
    })
    meta_path.write_text(json.dumps(meta, indent=2) + "\n")
    records[asset_id].clear(); records[asset_id].update(meta)
    (RAW / f"{asset_id}.install-20261026.json").write_text(json.dumps({
        "asset_id": asset_id,
        "source_image": source_image,
        "source_image_sha256": source_sha,
        "source_atlas": atlas_name,
        "source_atlas_sha256": atlas_sha,
        "generation_request_id": request_id,
        "cell_index": cell_i,
        "crop_bounds_xywh": [cell_i * cell_w + crop_box[0], crop_box[1], crop_box[2]-crop_box[0], crop_box[3]-crop_box[1]],
        "output_bbox_xywh": list(canvas.getchannel("A").getbbox()),
        "uniform_scale": scale,
        "old_png_sha256": sha(old_bytes),
        "new_png_sha256": sha(new_bytes),
    }, indent=2) + "\n")

index["assets"] = [records[a["id"]] for a in index["assets"]]
idx_path.write_text(json.dumps(index, indent=2) + "\n")
print(json.dumps({x[0]: {"bbox": list(x[5].getchannel("A").getbbox()), "scale": x[15]} for x in staged}, indent=2))
