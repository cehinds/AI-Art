"""Replace generated fronts with source sprites and calibrate other projections to native scale."""
from pathlib import Path
import hashlib, json, sys
import numpy as np
from PIL import Image
from scipy import ndimage

OUT = Path(__file__).resolve().parent
PACK = OUT.parents[1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: python prepare_native_fronts.py <recipe.json>")
    recipe_path = Path(sys.argv[1])
    if not recipe_path.is_absolute():
        recipe_path = OUT / recipe_path
    recipe = json.loads(recipe_path.read_text())
    atlas_path = PACK / recipe["raw_atlas"]
    generated_path = PACK / recipe["generated_original_atlas"]
    atlas = Image.open(generated_path).convert("RGBA")
    pixels = np.asarray(atlas).copy()
    height, width = pixels.shape[:2]
    columns, rows = recipe["grid"]["columns"], recipe["grid"]["rows"]
    threshold = recipe.get("alpha_threshold", 245)
    min_ratio = recipe.get("min_component_ratio", .025)
    labels, count = ndimage.label(pixels[:, :, 3] >= threshold, np.ones((3, 3), dtype=np.uint8))
    counts = np.bincount(labels.ravel())
    centers = [((col + .5) * width / columns, (row + .5) * height / rows)
               for row in range(rows) for col in range(columns)]
    assigned = {i: [] for i in range(columns * rows)}
    boxes = {}
    for label in range(1, count + 1):
        if counts[label] < 4:
            continue
        yy, xx = np.where(labels == label)
        cx, cy = float(xx.mean()), float(yy.mean())
        cell = min(range(columns * rows), key=lambda i:
            ((cx - centers[i][0]) / (width / columns)) ** 2 +
            ((cy - centers[i][1]) / (height / rows)) ** 2)
        assigned[cell].append(label)
        boxes[label] = [int(xx.min()), int(yy.min()), int(xx.max() + 1), int(yy.max() + 1)]

    source_records = []
    for obj in recipe["objects"]:
        row = int(obj["row"])
        front_cell = row * columns
        source_path = PACK / obj.get("native_front", obj["source_image"])
        source = Image.open(source_path).convert("RGBA")
        native_size = list(source.size)
        source_mask = np.asarray(source)[:, :, 3] >= threshold
        sy, sx = np.where(source_mask)
        if not len(sx):
            raise RuntimeError(f"{obj['id']}: empty native source front")
        source_height = int(sy.max() + 1 - sy.min())
        native_front_bounds = [int(sx.min()), int(sy.min()), int(sx.max() + 1), int(sy.max() + 1)]

        # Remove generated front components and place the exact native source.
        for label in assigned[front_cell]:
            pixels[labels == label] = 0
        cell_x0, cell_x1 = round(0 * width / columns), round(width / columns)
        cell_y0, cell_y1 = round(row * height / rows), round((row + 1) * height / rows)
        front_input_scale = min(1.0, (cell_x1 - cell_x0) / source.width,
                                (cell_y1 - cell_y0) / source.height)
        if front_input_scale < 1.0:
            source = source.resize((max(1, round(source.width * front_input_scale)),
                                    max(1, round(source.height * front_input_scale))),
                                   Image.Resampling.NEAREST)
            source_mask = np.asarray(source)[:, :, 3] >= threshold
            sy, sx = np.where(source_mask)
            source_height = int(sy.max() + 1 - sy.min())
        front_offset = (cell_x0 + (cell_x1 - cell_x0 - source.width) // 2,
                        cell_y0 + (cell_y1 - cell_y0 - source.height) // 2)
        canvas = Image.fromarray(pixels, "RGBA")
        canvas.alpha_composite(source, front_offset)
        pixels = np.asarray(canvas).copy()

        # Match the native front's maximum projected extent using one common
        # downscale for all five generated directions. The source PNG stays intact.
        records = []
        maximum_inferred_height = 0
        for col in range(1, columns):
            cell = row * columns + col
            labels_here = assigned[cell]
            if not labels_here:
                raise RuntimeError(f"{obj['id']}: no components in generated view cell {cell}")
            main = max(labels_here, key=lambda label: counts[label])
            keep = [label for label in labels_here if label == main or counts[label] >= counts[main] * min_ratio]
            bounds = [min(boxes[label][0] for label in keep), min(boxes[label][1] for label in keep),
                      max(boxes[label][2] for label in keep), max(boxes[label][3] for label in keep)]
            maximum_inferred_height = max(maximum_inferred_height, bounds[3] - bounds[1])
            records.append((cell, labels_here, keep, bounds))
        shared_pre_scale = min(1.0, source_height / maximum_inferred_height) if maximum_inferred_height else 1.0
        view_records = []
        for cell, labels_here, keep, (x0, y0, x1, y1) in records:
            for label in labels_here:
                pixels[labels == label] = 0
            local_labels = labels[y0:y1, x0:x1]
            crop = atlas.crop((x0, y0, x1, y1))
            crop.putalpha(Image.fromarray(np.isin(local_labels, keep).astype("uint8") * 255))
            nw = max(1, round(crop.width * shared_pre_scale))
            nh = max(1, round(crop.height * shared_pre_scale))
            crop = crop.resize((nw, nh), Image.Resampling.NEAREST)
            col = cell % columns
            c0, c1 = round(col * width / columns), round((col + 1) * width / columns)
            r0, r1 = round(row * height / rows), round((row + 1) * height / rows)
            offset = (c0 + (c1 - c0 - nw) // 2, r0 + (r1 - r0 - nh) // 2)
            canvas = Image.fromarray(pixels, "RGBA")
            canvas.alpha_composite(crop, offset)
            pixels = np.asarray(canvas).copy()
            view_records.append({"cell_index": cell, "kept_components": keep,
                                 "source_crop_bounds_px": [x0, y0, x1, y1],
                                 "pre_normalization_scale": shared_pre_scale,
                                 "resized_bounds_px": [nw, nh], "atlas_offset_px": list(offset)})
        source_records.append({"object_id": obj["id"], "source_image": obj["source_image"],
                               "native_front": obj.get("native_front", obj["source_image"]),
                               "source_sha256": sha256(source_path), "native_source_size": native_size,
                               "native_front_atlas_scale": front_input_scale,
                               "placed_front_size": list(source.size),
                               "native_source_alpha_bounds_px": native_front_bounds,
                               "front_atlas_offset_px": list(front_offset),
                               "native_source_height_px": source_height,
                               "inferred_max_front/side_z_height_px": maximum_inferred_height,
                               "inferred_view_common_pre_scale": shared_pre_scale,
                               "inferred_views": view_records})

    Image.fromarray(pixels, "RGBA").save(atlas_path, optimize=True)
    report = {"generated_original_atlas": recipe["generated_original_atlas"],
              "generated_original_sha256": sha256(generated_path),
              "processed_atlas": recipe["raw_atlas"], "processed_atlas_sha256": sha256(atlas_path),
              "processing": "Replaced each generated front with the exact native RGBA source sprite. Applied one isotropic nearest-neighbor downscale shared by all five inferred views, calibrated from native-front height versus the tallest inferred front/side/rear Z extent. Top/bottom naturally keep their different projected extents. Source PNGs remain unchanged.",
              "objects": source_records}
    report_path = recipe_path.with_name(recipe_path.stem + ".front-reuse.json")
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(f"Prepared and scale-calibrated {len(source_records)} native fronts: {report_path.relative_to(OUT)}")


if __name__ == "__main__":
    main()
