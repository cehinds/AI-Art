"""Replay NW wall camera remap from retained pre-remap image sources."""
from pathlib import Path
import hashlib
import json
import struct
from PIL import Image

HERE = Path(__file__).resolve().parent
PACK = HERE.parents[1]
RAW = HERE / "raw" / "room-wall-nw-before-axis-remap"
INDEX = HERE / "set-index.json"
OBJECTS = ("room-kit--concept--wall-nw", "room-kit--walls--wall-nw")
MAPPING = {
    "front": ("right", None),
    "right": ("rear", None),
    "left": ("front", None),
    "rear": ("left", None),
    "top": ("top", "clockwise90"),
    "bottom": ("bottom", "clockwise90"),
}
index = json.loads(INDEX.read_text())
assets = {item["id"]: item for item in index["assets"]}
sets = {item["object_id"]: item for item in index["view_sets"]}
recipe = {"method": "long-X to long-Y axis remap; elevations re-keyed, plans rigidly rotated clockwise 90 degrees",
          "objects": {}, "mapping": MAPPING}
for object_id in OBJECTS:
    recipe["objects"][object_id] = {}
    for destination_view, (source_view, rotation) in MAPPING.items():
        asset_id = f"{object_id}.{destination_view}"
        source_path = RAW / f"{object_id}.{source_view}.png"
        source_bytes = source_path.read_bytes()
        image = Image.open(source_path).convert("RGBA")
        if rotation == "clockwise90":
            image = image.transpose(Image.Transpose.ROTATE_270)
        target_meta = dict(assets[asset_id])
        output_path = PACK / target_meta["image"]["path"]
        image.save(output_path, optimize=True)
        target_meta["image"] = {
            "path": target_meta["image"]["path"],
            "width": 256,
            "height": 256,
            "sha256": hashlib.sha256(output_path.read_bytes()).hexdigest(),
            "rgba_sha256": hashlib.sha256(struct.pack(">II", 256, 256) + image.tobytes()).hexdigest(),
        }
        target_meta["anchor_px"] = [128, 128]
        target_meta["metadata_path"] = (HERE / f"{asset_id}.json").relative_to(PACK).as_posix()
        provenance = dict(target_meta.get("provenance", {}))
        provenance.update({
            "method": "generated",
            "source_image": f"reusable/native/{object_id}.png",
            "notes": "Inferred orthographic view for the canonical long-Y NW wall; derived by rigid camera remap from retained source projection, not recovered pixels.",
            "axis_remap": {
                "recipe": "reusable/views-additional/repair_room_wall_nw_axes.py",
                "source_asset_id": f"{object_id}.{source_view}",
                "source_path": f"reusable/views-additional/raw/room-wall-nw-before-axis-remap/{object_id}.{source_view}.png",
                "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
                "rotation": rotation,
            },
        })
        target_meta["provenance"] = provenance
        sidecar = HERE / f"{asset_id}.json"
        sidecar.write_text(json.dumps(target_meta, indent=2) + "\n")
        assets[asset_id] = target_meta
        recipe["objects"][object_id][destination_view] = {
            "source_view": source_view,
            "rotation": rotation,
            "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
            "output_sha256": target_meta["image"]["sha256"],
        }
    group = sets[object_id]
    group["complete"] = False
    group["geometry_qa"] = {
        "status": "pending-review",
        "views": list(MAPPING),
        "notes": "NW wall changed from duplicate long-X to long-Y; source-plus-six review pending.",
        "atlas_self_inspected": True,
    }
    group["notes"] = "Targeted NW wall axis remap awaits independent review."
index["assets"] = list(assets.values())
index["view_sets"] = list(sets.values())
INDEX.write_text(json.dumps(index, indent=2) + "\n")
(HERE / "raw" / "room-wall-nw-axis-remap.recipe.json").write_text(json.dumps(recipe, indent=2) + "\n")
print(f"Remapped six views for {len(OBJECTS)} NW wall projections.")
