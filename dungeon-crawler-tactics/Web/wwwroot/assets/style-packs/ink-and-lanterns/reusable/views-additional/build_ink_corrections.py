"""Install isolated view corrections from retained imagegen cells for Ink style assets.

Offline command: python3 reusable/views-additional/build_ink_corrections.py --recipe reusable/views-additional/raw/<recipe>.json
"""
from __future__ import annotations
import argparse, hashlib, json, os, struct
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

OUT = Path(__file__).resolve().parent
PACK = OUT.parent.parent
INDEX = OUT / "set-index.json"

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def install(recipe_path: Path):
    recipe = json.loads(recipe_path.read_text())
    atlas_path = PACK / recipe["source_atlas"]
    atlas = Image.open(atlas_path).convert("RGBA")
    index = json.loads(INDEX.read_text())
    assets = {a["id"]: a for a in index["assets"]}
    view_sets = {s["object_id"]: s for s in index["view_sets"]}
    for target in recipe["targets"]:
        asset_id = target["asset_id"]
        asset = assets[asset_id]
        x0, y0, x1, y1 = target["cell_bounds"]
        cell = atlas.crop((x0, y0, x1, y1))
        rgba = np.asarray(cell).copy()
        labels, _ = ndimage.label(rgba[:, :, 3] > int(recipe.get("alpha_threshold", 32)))
        parts = []
        for label, sl in enumerate(ndimage.find_objects(labels), 1):
            if sl is None:
                continue
            ys, xs = sl
            area = int(np.count_nonzero(labels[sl] == label))
            if area < int(recipe.get("min_component_area", 24)):
                continue
            bbox = (xs.start, ys.start, xs.stop, ys.stop)
            touches = xs.start <= 1 or ys.start <= 1 or xs.stop >= cell.width - 1 or ys.stop >= cell.height - 1
            parts.append({"label": label, "area": area, "bbox": bbox, "touches": touches})
        if not parts:
            raise ValueError(f"{asset_id}: no visible components in {target['cell_bounds']}")
        largest = max(p["area"] for p in parts)
        chosen = [p for p in parts if not p["touches"] and p["area"] >= largest * float(recipe.get("component_area_ratio", 0.005))]
        if not chosen:
            chosen = [max(parts, key=lambda p: p["area"])]
        xlo = min(p["bbox"][0] for p in chosen); ylo = min(p["bbox"][1] for p in chosen)
        xhi = max(p["bbox"][2] for p in chosen); yhi = max(p["bbox"][3] for p in chosen)
        mask = np.isin(labels, [p["label"] for p in chosen])
        crop = Image.fromarray(np.where(mask[:, :, None], rgba, 0).astype(np.uint8), "RGBA").crop((xlo, ylo, xhi, yhi))
        cal = float(target.get("isotropic_calibration", 1.0))
        crop = crop.resize((max(1, round(crop.width * cal)), max(1, round(crop.height * cal))), Image.Resampling.NEAREST)
        maxdim = int(target.get("max_output_dimension", 200))
        scale = min(1.0, maxdim / max(crop.width, crop.height))
        nw, nh = round(crop.width * scale), round(crop.height * scale)
        if nw > 256 or nh > 256:
            raise ValueError(f"{asset_id}: normalized output clips ({nw}x{nh})")
        resized = crop.resize((nw, nh), Image.Resampling.NEAREST)
        canvas = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
        ox, oy = (256 - nw) // 2, (256 - nh) // 2
        canvas.alpha_composite(resized, (ox, oy))
        image_path = PACK / asset["image"]["path"]
        metadata_path = PACK / asset["metadata_path"]
        image_path.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(image_path, optimize=True)
        raw_rgba = canvas.tobytes()
        asset["image"]["width"] = 256; asset["image"]["height"] = 256
        asset["image"]["sha256"] = sha(image_path)
        asset["image"]["rgba_sha256"] = hashlib.sha256(struct.pack(">II", 256, 256) + raw_rgba).hexdigest()
        asset["provenance"].update({
            "method": "generated",
            "source_atlas": recipe["source_atlas"],
            "source_atlas_sha256": sha(atlas_path),
            "generation_recipe": str(recipe_path.relative_to(PACK)),
            "prompt_path": recipe["prompt_path"],
            "prompt_sha256": recipe["prompt_sha256"],
            "reference_images": recipe["reference_images"],
            "source_contact_sheet": recipe["source_contact_sheet"],
            "source_contact_sheet_sha256": recipe["source_contact_sheet_sha256"],
            "geometry_guide": recipe.get("geometry_guide"),
            "geometry_guide_sha256": recipe.get("geometry_guide_sha256"),
            "crop_bounds_px": {
                "nominal_cell": {"bounds": [x0, y0, x1 - x0, y1 - y0]},
                "alpha_bounds_global": [x0 + xlo, y0 + ylo, xhi - xlo, yhi - ylo],
                "component_labels": [p["label"] for p in chosen],
                "component_areas": [p["area"] for p in chosen],
                "resized_bounds_px": [nw, nh],
                "canvas_offset_px": [ox, oy],
                "isotropic_calibration": cal,
                "shared_scale": scale,
            },
            "notes": recipe["provenance_notes"],
        })
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.write_text(json.dumps(asset, indent=2) + "\n")
        oid = asset["object_id"]
        s = view_sets[oid]
        old = s.get("geometry_qa", {})
        history = list(old.get("history", []))
        if old.get("reviewed_at") or old.get("reviewer"):
            history.append({"status": old.get("status"), "reviewed_at": old.get("reviewed_at"),
                            "reviewer": old.get("reviewer"), "notes": old.get("notes", [])})
        s["complete"] = False
        s["geometry_qa"] = {"status": "pending-review", "reviewer": "independent-visual-review",
                             "changed_views": [asset["view"]], "history": history,
                             "notes": ["Corrective imagegen view installed; current-hash independent review required."]}
        s["notes"] = "Corrective inferred view installed; pending current-hash review."
    temp = INDEX.with_suffix(".json.tmp")
    temp.write_text(json.dumps(index, indent=2) + "\n")
    os.replace(temp, INDEX)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--recipe", required=True, help="Pack-root-relative recipe path")
    args = parser.parse_args()
    install(PACK / args.recipe)
