"""Deterministically remove opaque black fill from open-arch apertures."""
from pathlib import Path
import hashlib, json, struct
import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent
PACK = HERE.parent.parent
INDEX = HERE / "set-index.json"
OBJECTS = ("room-kit--doors--door-open-ne", "room-kit--doors--door-open-nw")
VIEWS = ("front", "rear")
SEED_XY = (128, 128)
MAX_RGB = 20
ERODE_PIXELS = 2
index = json.loads(INDEX.read_text())
assets = {item["id"]: item for item in index["assets"]}
sets = {item["object_id"]: item for item in index["view_sets"]}
recipe = {"method": "center-seeded dark-aperture flood-fill with a 2px erosion to preserve stone outlines",
          "seed_xy": list(SEED_XY), "max_rgb": MAX_RGB, "erosion_pixels": ERODE_PIXELS,
          "inputs": {}, "outputs": {}}
for object_id in OBJECTS:
    for view in VIEWS:
        asset_id = f"{object_id}.{view}"
        meta = dict(assets[asset_id])
        source = HERE / "raw" / f"open-door-{object_id}-{view}-before-clean.png"
        source_bytes = source.read_bytes()
        image = Image.open(source).convert("RGBA")
        rgba = np.array(image)
        black = (rgba[:, :, :3].max(axis=2) < MAX_RGB) & (rgba[:, :, 3] > 0)
        labels, _ = ndimage.label(black, np.ones((3, 3), dtype=np.uint8))
        seed = labels[SEED_XY[1], SEED_XY[0]]
        if seed == 0:
            raise RuntimeError(f"{asset_id}: aperture seed is not in dark fill")
        aperture = labels == seed
        aperture = ndimage.binary_erosion(aperture, iterations=ERODE_PIXELS)
        rgba[aperture, 3] = 0
        corrected = Image.fromarray(rgba, "RGBA")
        output = PACK / meta["image"]["path"]
        corrected.save(output, optimize=True)
        meta["image"] = {"path": meta["image"]["path"], "width": 256, "height": 256,
            "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
            "rgba_sha256": hashlib.sha256(struct.pack(">II", 256, 256) + corrected.tobytes()).hexdigest()}
        meta["provenance"] = dict(meta.get("provenance", {}))
        meta["provenance"]["aperture_cleanup"] = {**recipe, "input_path": f"reusable/views-additional/raw/{source.name}",
            "input_sha256": hashlib.sha256(source_bytes).hexdigest(), "output_alpha_bbox": corrected.getchannel("A").getbbox()}
        sidecar = HERE / f"{asset_id}.json"
        meta["metadata_path"] = sidecar.relative_to(PACK).as_posix()
        sidecar.write_text(json.dumps(meta, indent=2) + "\n")
        assets[asset_id] = meta
        recipe["inputs"][asset_id] = hashlib.sha256(source_bytes).hexdigest()
        recipe["outputs"][asset_id] = meta["image"]["sha256"]
for object_id in OBJECTS:
    group = sets[object_id]
    group["complete"] = False
    group["geometry_qa"] = {"status": "pending-review", "views": list(VIEWS),
        "notes": "Opaque black doorway fill was removed from front/rear apertures; source-plus-six review pending.",
        "atlas_self_inspected": True}
    group["notes"] = "Front/rear open-arch aperture cleanup awaiting independent review."
index["assets"] = list(assets.values())
index["view_sets"] = list(sets.values())
INDEX.write_text(json.dumps(index, indent=2) + "\n")
(HERE / "raw" / "open-door-aperture-cleanup.recipe.json").write_text(json.dumps(recipe, indent=2) + "\n")
print(f"Cleaned {len(OBJECTS) * len(VIEWS)} doorway apertures.")
