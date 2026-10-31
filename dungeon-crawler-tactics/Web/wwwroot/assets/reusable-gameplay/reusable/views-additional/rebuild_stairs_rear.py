"""Rebuild the inferred rear elevation from its retained generated atlas."""
from pathlib import Path
import hashlib, json, struct
import numpy as np
from PIL import Image

OUT = Path(__file__).resolve().parent
PACK = OUT.parents[1]
asset_id = "room-kit--props--stairs.rear"
raw_rel = "reusable/views-additional/raw/stairs-rear-correction-atlas.png"
raw_path = PACK / raw_rel
atlas = Image.open(raw_path).convert("RGBA")
a = np.asarray(atlas)
mask = a[:, :, 3] >= 245
ys, xs = np.where(mask)
if len(xs) == 0:
    raise RuntimeError("no opaque source pixels")
bounds = [int(xs.min()), int(ys.min()), int(xs.max()+1), int(ys.max()+1)]
crop = atlas.crop(bounds)
local = np.asarray(crop).copy()
local[:, :, 3] = (local[:, :, 3] >= 245).astype(np.uint8) * 255
crop = Image.fromarray(local, "RGBA")
scale = 147 / crop.height
nw, nh = round(crop.width*scale), 147
crop = crop.resize((nw, nh), Image.Resampling.NEAREST)
frame = Image.new("RGBA", (256, 256))
offset = (128 - nw//2, 128 - nh//2)
frame.alpha_composite(crop, offset)
dest = PACK / f"reusable/views-additional/{asset_id}.png"
frame.save(dest, optimize=True)
meta_path = OUT / f"{asset_id}.json"
meta = json.loads(meta_path.read_text())
meta["image"].update({"path": f"reusable/views-additional/{asset_id}.png", "width": 256, "height": 256, "sha256": hashlib.sha256(dest.read_bytes()).hexdigest(), "rgba_sha256": hashlib.sha256(struct.pack(">II", 256, 256)+frame.tobytes()).hexdigest()})
meta["provenance"].update({
    "method": "generated",
    "source_image": "reusable/native/room-kit--props--stairs.png",
    "native_front": "reusable/native/room-kit--props--stairs.png",
    "native_front_sha256": hashlib.sha256((PACK / "reusable/native/room-kit--props--stairs.png").read_bytes()).hexdigest(),
    "notes": "Inferred orthographic rear elevation generated from the canonical stair sprite; unseen rear surfaces are not recovered source pixels.",
    "source_atlas": raw_rel,
    "source_atlas_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
    "generation_recipe": "reusable/views-additional/raw/stairs-rear-correction.recipe.json",
    "crop_bounds_px": {"alpha_threshold": 245, "alpha_bounds_global": bounds, "resized_bounds_px": [nw,nh], "canvas_offset_px": list(offset), "uniform_scale": scale, "target_height_px": nh}
})
meta_path.write_text(json.dumps(meta, indent=2)+"\n")
index_path = OUT / "set-index.json"
index = json.loads(index_path.read_text())
for item in index["assets"]:
    if item.get("id") == asset_id:
        item.clear(); item.update(meta); break
else:
    index["assets"].append(meta)
for group in index["view_sets"]:
    if group.get("object_id") == "room-kit--props--stairs":
        group["complete"] = False
        group["geometry_qa"] = {"status":"pending-review", "views":["rear"], "notes":"Rear stair correction generated and locally inspected; awaiting independent review.", "atlas_self_inspected":True}
        group["notes"] = "Targeted rear elevation correction awaiting independent review."
        break
index_path.write_text(json.dumps(index, indent=2)+"\n")
print(json.dumps({"bounds":bounds,"size":[nw,nh],"offset":offset,"scale":scale,"image_sha256":meta['image']['sha256']}))
