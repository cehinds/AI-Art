"""Replay the retained deterministic loose-brace edge crops without reading output views."""
from pathlib import Path
import hashlib
import json
import struct
from PIL import Image

HERE = Path(__file__).resolve().parent
PACK = HERE.parent.parent
INDEX = HERE / "set-index.json"
OBJECT = "concepts-boss-swine-concept-loose-metal-brace"
VIEWS = ("front", "rear", "right", "left")
index = json.loads(INDEX.read_text())
assets = {item["id"]: item for item in index["assets"]}
sets = {item["object_id"]: item for item in index["view_sets"]}
for view in VIEWS:
    asset_id = f"{OBJECT}.{view}"
    meta = dict(assets[asset_id])
    crop_path = HERE / "raw" / f"swine-loose-brace-{view}-crop.png"
    crop = Image.open(crop_path).convert("RGBA")
    frame = Image.new("RGBA", (256, 256))
    offset = (128 - crop.width // 2, 128 - crop.height // 2)
    frame.alpha_composite(crop, offset)
    image_path = PACK / meta["image"]["path"]
    image_path.parent.mkdir(parents=True, exist_ok=True)
    frame.save(image_path, optimize=True)
    meta["image"] = {
        "path": meta["image"]["path"],
        "width": 256,
        "height": 256,
        "sha256": hashlib.sha256(image_path.read_bytes()).hexdigest(),
        "rgba_sha256": hashlib.sha256(struct.pack(">II", 256, 256) + frame.tobytes()).hexdigest(),
    }
    meta["metadata_path"] = (HERE / f"{asset_id}.json").relative_to(PACK).as_posix()
    meta["anchor_px"] = [128, 128]
    sidecar = HERE / f"{asset_id}.json"
    sidecar.write_text(json.dumps(meta, indent=2) + "\n")
    assets[asset_id] = meta
index["assets"] = list(assets.values())
index["view_sets"] = list(sets.values())
INDEX.write_text(json.dumps(index, indent=2) + "\n")
print(f"Replayed {len(VIEWS)} brace edge crops from retained raw crop sources.")
