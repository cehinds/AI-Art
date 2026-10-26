#!/usr/bin/env python3
"""Install the source-faithful overhead projection for the Juicer weight crate."""
import hashlib, json, struct
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

PACK = Path(__file__).resolve().parents[2]
VIEWS = PACK / "reusable/views-additional"
OID = "concepts-boss-juicer-concept-crate"
VIEW = "top"
GEN_ID = "exec-45493bad-ee0c-4503-b574-cdc26db1bccd"
SRC = Path("/workspace/generated_images") / f"{GEN_ID}.png"
RAW = VIEWS / "raw"
RAW.mkdir(parents=True, exist_ok=True)
ATLAS = RAW / f"{GEN_ID}.png"
PROMPT = RAW / f"{GEN_ID}.prompt.txt"
PROMPT.write_text(
    "Targeted edit of the existing top view: preserve square crate footprint; "
    "show two dumbbell/bar bundles aligned vertically in the overhead projection "
    "(world Y), with paired weight plates at the top and bottom of each shaft. "
    "This matches FRONT/REAR circular plate ends and RIGHT/LEFT thin plate edges. "
    "Preserve dark wood and orange metal brace palette. Transparent strict orthographic view.\n",
    encoding="utf-8",
)
if not ATLAS.exists():
    ATLAS.write_bytes(SRC.read_bytes())

def sha(b):
    return hashlib.sha256(b).hexdigest()

atlas_bytes = ATLAS.read_bytes()
atlas = Image.open(ATLAS).convert("RGBA")
rgba = np.asarray(atlas)
alpha = rgba[:, :, 3]
# Select the single principal connected silhouette at alpha >= 16. Lower alpha
# antialiasing is retained inside its full bounds; disconnected transparent-RGB
# artifacts and isolated low-alpha specks are excluded.
labels, count = ndimage.label(alpha >= 16)
sizes = np.bincount(labels.ravel())
if count < 1:
    raise SystemExit("No alpha component in retained generated atlas")
label = int(np.argmax(sizes[1:]) + 1)
ys, xs = np.where(labels == label)
box = (int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1))
crop = atlas.crop(box)

target = Image.open(VIEWS / f"{OID}.{VIEW}.png").convert("RGBA")
target_box = target.getchannel("A").getbbox()
tw, th = target_box[2] - target_box[0], target_box[3] - target_box[1]
scale = min(tw / crop.width, th / crop.height)
nw, nh = round(crop.width * scale), round(crop.height * scale)
crop = crop.resize((nw, nh), Image.Resampling.LANCZOS)
canvas = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
anchor = (128, 128)
canvas.alpha_composite(crop, (anchor[0] - nw // 2, anchor[1] - nh // 2))

img_path = VIEWS / f"{OID}.{VIEW}.png"
meta_path = VIEWS / f"{OID}.{VIEW}.json"
original = img_path.read_bytes()
(RAW / f"{GEN_ID}.previous-approved.png").write_bytes(original)
canvas.save(img_path, optimize=False)
data = json.loads(meta_path.read_text(encoding="utf-8"))
png_bytes = img_path.read_bytes()
pixels = canvas.tobytes()
data["image"]["sha256"] = sha(png_bytes)
data["image"]["rgba_sha256"] = sha(struct.pack(">II", 256, 256) + pixels)
data["provenance"].update({
    "source_atlas": f"reusable/views-additional/raw/{GEN_ID}.png",
    "source_atlas_sha256": sha(atlas_bytes),
    "generation_recipe": f"reusable/views-additional/raw/{GEN_ID}.prompt.txt",
    "notes": "inferred orthographic view, not recovered pixels; two horizontal weight bundles are inferred from the visible gym-weight contents; unshown crate interior is not claimed recovered",
    "crop_bounds_px": {
        "alpha_threshold": 16,
        "alpha_bounds_global": list(box),
        "component_labels": [label],
        "resized_bounds_px": [nw, nh],
        "canvas_offset_px": [anchor[0] - nw // 2, anchor[1] - nh // 2],
        "shared_scale": scale,
        "normalization": "single largest connected alpha component; uniform scale to prior approved TOP footprint; centered at shared anchor",
    },
})
meta_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
index_path = PACK / "reusable/views-additional/set-index.json"
index = json.loads(index_path.read_text(encoding="utf-8"))
for asset in index["assets"]:
    if asset["id"] == data["id"]:
        asset.clear()
        asset.update(data)
        break
else:
    raise SystemExit(f"Missing asset in index: {data['id']}")
index_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
(RAW / f"{GEN_ID}.install.json").write_text(json.dumps({
    "object_id": OID, "view": VIEW, "atlas": ATLAS.relative_to(PACK).as_posix(),
    "atlas_sha256": sha(atlas_bytes), "previous_png_sha256": sha(original),
    "installed_png_sha256": sha(png_bytes), "component_bounds_xyxy": list(box),
    "alpha_component_threshold": 16, "target_approved_bounds": list(target_box),
    "uniform_scale": scale, "installed_bounds": list(canvas.getchannel("A").getbbox()),
}, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"id": data["id"], "crop_bounds_xyxy": box, "target": [tw, th],
                  "resized": [nw, nh], "scale": scale,
                  "installed_bbox": canvas.getchannel("A").getbbox(),
                  "image_sha256": data["image"]["sha256"]}, indent=2))
