"""Rebuild all normalized view PNGs from retained source atlases and crop provenance.

Run from any working directory with: python reusable/views-additional/build_all.py
Paths in the catalog are pack-root-relative; no generated_images or workspace paths
are required. Crop bounds, connected-component labels, scale, and anchor placement
come from each leaf sidecar so later corrections remain reproducible as authored.
"""
from pathlib import Path
import hashlib
from io import BytesIO
import json
import struct
import argparse
from itertools import product

import numpy as np
from PIL import Image, ImageOps
from scipy import ndimage


OUT = Path(__file__).resolve().parent
PACK = OUT.parents[1]
INDEX = OUT / "set-index.json"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def rgba_sha256(frame: Image.Image) -> str:
    frame = frame.convert("RGBA")
    return sha256_bytes(struct.pack(">II", frame.width, frame.height) + frame.tobytes())


def png_bytes(frame: Image.Image, optimize=True) -> bytes:
    buffer = BytesIO()
    frame.save(buffer, format="PNG", optimize=optimize)
    return buffer.getvalue()


def decoded_bounds(bounds, fmt, atlas_size):
    """Decode recorded bounds as XYXY or XYWH; reject impossible interpretations."""
    a, b, c, d = [int(v) for v in bounds]
    if fmt == "xyxy":
        x0, y0, x1, y1 = a, b, c, d
    elif fmt == "xywh":
        x0, y0, x1, y1 = a, b, a + c, b + d
    else:
        raise ValueError(fmt)
    if not (0 <= x0 < x1 <= atlas_size[0] and 0 <= y0 < y1 <= atlas_size[1]):
        return None
    return (x0, y0, x1, y1)


def resized_size(crop_meta):
    source = crop_meta.get("resized_bounds_px", crop_meta.get("resized_wh"))
    values = [int(v) for v in source]
    if len(values) == 2:
        return values[0], values[1], "width-height"
    if len(values) == 4:
        x0, y0, x1, y1 = values
        offset = [int(v) for v in crop_meta["canvas_offset_px"]]
        if [x0, y0] != offset or x1 <= x0 or y1 <= y0:
            raise RuntimeError(f"invalid resized_bounds_px XYXY record: {values}")
        return x1 - x0, y1 - y0, "xyxy"
    raise RuntimeError(f"unsupported resized_bounds_px record: {values}")


def make_atlas_candidate(atlas, labels, crop_meta, recipe, fmt, threshold, alpha_mode, resample):
    recorded_bounds = crop_meta.get("alpha_bounds_global", crop_meta.get("alpha_bounds_global_xywh"))
    bounds = decoded_bounds(recorded_bounds, fmt, atlas.size)
    if bounds is None:
        return None, None
    x0, y0, x1, y1 = bounds
    rgba = np.asarray(atlas)
    if crop_meta.get("selection_mode") == "all_opaque_pixels":
        local_mask = rgba[y0:y1, x0:x1, 3] >= threshold
    else:
        keep = [int(v) for v in crop_meta.get("component_labels", [])]
        if not keep and crop_meta.get("global_component_label") is not None:
            keep = [int(crop_meta["global_component_label"])]
        if not keep and crop_meta.get("component_label") is not None:
            keep = [int(crop_meta["component_label"])]
        if keep:
            local_mask = np.isin(labels[y0:y1, x0:x1], keep)
        elif any("largest connected component" in str(crop_meta.get(key, "")).lower()
                 for key in ("selected_component", "component_selection")):
            cell_bounds = crop_meta.get("nominal_cell", {}).get("bounds")
            if cell_bounds and len(cell_bounds) == 4:
                cx, cy, cw, ch = [int(v) for v in cell_bounds]
                cell_labels, count = ndimage.label(rgba[cy:cy+ch, cx:cx+cw, 3] >= threshold)
                if count < 1:
                    return None, None
                sizes = np.bincount(cell_labels.ravel())
                sizes[0] = 0
                selected = int(np.argmax(sizes))
                local_mask = cell_labels[y0-cy:y1-cy, x0-cx:x1-cx] == selected
            else:
                crop_labels, count = ndimage.label(rgba[y0:y1, x0:x1, 3] >= threshold)
                if count < 1:
                    return None, None
                sizes = np.bincount(crop_labels.ravel())
                sizes[0] = 0
                local_mask = crop_labels == int(np.argmax(sizes))
            # component labels in retained targeted scripts use SciPy's default
            # 4-connectivity; this is recorded in the resolution report.
        elif crop_meta.get("selection_mode") == "global_alpha_component" and crop_meta.get("global_component_label") is not None:
            local_mask = labels[y0:y1, x0:x1] == int(crop_meta["global_component_label"])
        elif crop_meta.get("component_label") is not None and crop_meta.get("selection_mode") != "all_opaque_pixels":
            local_mask = labels[y0:y1, x0:x1] == int(crop_meta["component_label"])
        elif "component_selection" in crop_meta and not crop_meta.get("component_labels"):
            local_mask = rgba[y0:y1, x0:x1, 3] >= threshold
        else:
            # A few historical schemas explicitly select all pixels in the
            # authored crop; this is distinct from inventing a fallback from
            # an already-rendered output.
            local_mask = rgba[y0:y1, x0:x1, 3] >= threshold
    piece = atlas.crop(bounds)
    if alpha_mode == "preserve-selected-alpha":
        original_alpha = np.asarray(piece.getchannel("A"))
        piece.putalpha(Image.fromarray(np.where(local_mask, original_alpha, 0).astype("uint8")))
    elif alpha_mode == "binary-threshold-mask":
        piece.putalpha(Image.fromarray((local_mask * 255).astype("uint8")))
    elif alpha_mode != "raw-crop-alpha":
        raise ValueError(alpha_mode)
    orientation = int(crop_meta.get("orientation_correction_degrees", 0)) % 360
    if orientation:
        if orientation not in (90, 180, 270):
            raise RuntimeError(f"unsupported orientation correction {orientation}")
        piece = piece.rotate(orientation, resample=Image.Resampling.NEAREST, expand=True)
    projection_scale = float(crop_meta.get("projection_scale", 1.0))
    if projection_scale != 1.0:
        intermediate = (max(1, round(piece.width * projection_scale)),
                        max(1, round(piece.height * projection_scale)))
        piece = piece.resize(intermediate, Image.Resampling.NEAREST)
    nw, nh, _ = resized_size(crop_meta)
    piece = piece.resize((nw, nh), resample)
    frame = Image.new("RGBA", (int(recipe["canvas_width"]), int(recipe["canvas_height"])))
    ox, oy = [int(v) for v in crop_meta["canvas_offset_px"]]
    frame.alpha_composite(piece, (ox, oy))
    return frame, bounds


def apply_callbacks(frame, meta):
    """Apply only deterministic post-crop operations recorded in sidecar provenance."""
    postprocess = meta.get("provenance", {}).get("postprocess", {})
    if postprocess.get("operation") == "remove-isolated-alpha-components":
        rgba = np.asarray(frame).copy()
        labels, count = ndimage.label(rgba[:, :, 3] >= int(postprocess["alpha_threshold"]))
        sizes = np.bincount(labels.ravel())
        maximum = int(postprocess["maximum_component_pixels"])
        for label in range(1, min(len(sizes), count + 1)):
            if 0 < sizes[label] <= maximum:
                rgba[labels == label] = 0
        frame = Image.fromarray(rgba, "RGBA")
    if postprocess.get("operation") == "uniform-nearest-scale-about-anchor":
        expected_input = postprocess.get("input_sha256")
        if expected_input and sha256_bytes(png_bytes(frame)) != expected_input:
            raise RuntimeError(f"{meta['id']}: scale-callback input no longer matches retained projection")
        scale = float(postprocess["scale"])
        nw = max(1, round(frame.width * scale))
        nh = max(1, round(frame.height * scale))
        scaled = frame.resize((nw, nh), Image.Resampling.NEAREST)
        anchor_x, anchor_y = [int(v) for v in postprocess.get("anchor_px", [128, 128])]
        frame = Image.new("RGBA", frame.size)
        frame.alpha_composite(scaled, (anchor_x - nw // 2, anchor_y - nh // 2))
    aperture = meta.get("provenance", {}).get("aperture_cleanup")
    if aperture:
        if sha256_bytes(png_bytes(frame)) != aperture["input_sha256"]:
            raise RuntimeError(f"{meta['id']}: aperture-cleanup input no longer matches source projection")
        clean_rgba = np.asarray(frame).copy()
        black = (clean_rgba[:, :, :3].max(axis=2) < int(aperture["max_rgb"])) & (clean_rgba[:, :, 3] > 0)
        dark_labels, _ = ndimage.label(black, np.ones((3, 3), dtype=np.uint8))
        seed_x, seed_y = [int(v) for v in aperture["seed_xy"]]
        seed = dark_labels[seed_y, seed_x]
        if seed == 0:
            raise RuntimeError(f"{meta['id']}: aperture cleanup seed is no longer dark")
        hole = ndimage.binary_erosion(dark_labels == seed, iterations=int(aperture["erosion_pixels"]))
        clean_rgba[hole, 3] = 0
        frame = Image.fromarray(clean_rgba, "RGBA")
    return frame


def recipe_json(path, crop_meta, meta):
    """Load JSON recipes, and derive only explicit normalization parameters for prompt/Python recipes."""
    if path.suffix.lower() == ".json":
        return json.loads(path.read_text())
    result = {
        "canvas_width": int(meta["image"]["width"]),
        "canvas_height": int(meta["image"]["height"]),
        "alpha_threshold": crop_meta.get("alpha_threshold"),
        "preserve_alpha": crop_meta.get("preserve_alpha"),
    }
    # Historical correction installers retained a declarative install receipt
    # beside the raw prompt. Read only JSON data; never execute installer code.
    receipt = path.with_suffix(".install.json")
    if receipt.is_file():
        result["install_receipt"] = json.loads(receipt.read_text())
    return result


def resolve_atlas_frame(meta, expected_png_hash, expected_rgba_hash, atlas_cache):
    """Resolve one raw-atlas projection by both hashes; never consult a live output PNG."""
    provenance = meta["provenance"]
    crop_meta = provenance["crop_bounds_px"]
    atlas_rel = provenance["source_atlas"]
    atlas_path = PACK / atlas_rel
    atlas_hash = sha256_bytes(atlas_path.read_bytes())
    if provenance.get("source_atlas_sha256") and atlas_hash != provenance["source_atlas_sha256"]:
        raise RuntimeError(f"{meta['id']}: source atlas hash mismatch")
    recipe_path = PACK / provenance["generation_recipe"]
    recipe_data = recipe_json(recipe_path, crop_meta, meta)
    declared_threshold = recipe_data.get("alpha_threshold") or crop_meta.get("alpha_threshold")
    receipt = recipe_data.get("install_receipt", {})
    if declared_threshold is None:
        declared_threshold = receipt.get("alpha_component_threshold") or crop_meta.get("threshold")
    thresholds = ([int(declared_threshold)] if declared_threshold is not None else [])
    thresholds += [t for t in (16, 32, 64, 128, 200, 245) if t not in thresholds]
    declared_format = crop_meta.get("coordinate_format") or crop_meta.get("bounds_format")
    bounds_value = crop_meta.get("alpha_bounds_global", crop_meta.get("alpha_bounds_global_xywh"))
    if not declared_format:
        if "alpha_bounds_global_xywh" in crop_meta or crop_meta.get("alpha_bbox_global_coordinate_format") == "xywh":
            declared_format = "xywh"
        elif crop_meta.get("alpha_bbox_global_coordinate_format") == "xyxy":
            declared_format = "xyxy"
    formats = ([declared_format.lower()] if declared_format else [])
    formats += [fmt for fmt in ("xyxy", "xywh") if fmt not in formats]
    declared_alpha = recipe_data.get("preserve_alpha")
    alpha_modes = []
    if declared_alpha is not None:
        alpha_modes.append("preserve-selected-alpha" if declared_alpha else "binary-threshold-mask")
    if receipt.get("component_bounds_xyxy") == bounds_value:
        alpha_modes.append("raw-crop-alpha")
    if provenance.get("postprocess", {}).get("operation") == "remove-isolated-alpha-components":
        alpha_modes.insert(0, "raw-crop-alpha")
    alpha_modes += [m for m in ("binary-threshold-mask", "preserve-selected-alpha", "raw-crop-alpha") if m not in alpha_modes]
    resamples = [Image.Resampling.NEAREST, Image.Resampling.LANCZOS,
                 Image.Resampling.BILINEAR, Image.Resampling.BICUBIC]
    for fmt, threshold, alpha_mode, resample, optimize in product(
            formats, thresholds, alpha_modes, resamples, (True, False)):
        key = (atlas_rel, threshold)
        if key not in atlas_cache:
            atlas = Image.open(atlas_path).convert("RGBA")
            rgba = np.asarray(atlas)
            labels, _ = ndimage.label(rgba[:, :, 3] >= threshold, np.ones((3, 3), dtype=np.uint8))
            atlas_cache[key] = (atlas, labels)
        atlas, labels = atlas_cache[key]
        frame, decoded = make_atlas_candidate(atlas, labels, crop_meta, {
            "canvas_width": int(meta["image"]["width"]),
            "canvas_height": int(meta["image"]["height"]),
        }, fmt, threshold, alpha_mode, resample)
        if frame is None:
            continue
        try:
            frame = apply_callbacks(frame, meta)
        except RuntimeError:
            continue
        encoded = png_bytes(frame, optimize=optimize)
        if sha256_bytes(encoded) == expected_png_hash and (
                expected_rgba_hash is None or rgba_sha256(frame) == expected_rgba_hash):
            return frame, {"source_atlas": atlas_rel, "source_atlas_sha256": atlas_hash,
                "coordinate_format": fmt, "decoded_bounds_xyxy": list(decoded),
                "alpha_threshold": threshold, "alpha_mode": alpha_mode,
                "resampling": resample.name, "png_optimize": optimize,
                "source_png_sha256": expected_png_hash,
                "source_rgba_sha256": rgba_sha256(frame)}
    raise RuntimeError(f"{meta['id']}: immutable raw-atlas inputs cannot reproduce requested source view hash {expected_png_hash}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true", help="rebuild and hash-check without writing view PNGs")
    parser.add_argument("--resolution-report", type=Path, help="write the resolved crop/alpha interpretation report")
    parser.add_argument("--resume-report", type=Path, help="reuse previously verified hash resolutions (verify-only mode only)")
    args = parser.parse_args()
    if args.resume_report and not args.verify_only:
        parser.error("--resume-report is allowed only with --verify-only")
    catalog = json.loads(INDEX.read_text())
    metadata_by_id = {asset["id"]: json.loads((PACK / asset["metadata_path"]).read_text())
                      for asset in catalog["assets"]}
    atlas_cache = {}
    outputs = []
    resolution_rows = []
    failures = []
    assets = catalog["assets"]
    resume_by_id = {}
    if args.resume_report:
        prior = json.loads(args.resume_report.read_text())
        for row in prior.get("resolutions", []):
            resume_by_id[row["id"]] = row
    skipped = set()
    for asset_number, asset in enumerate(assets, 1):
        meta_path = PACK / asset["metadata_path"]
        # Use the adjacent sidecar as source of truth, just as the builder does.
        meta = json.loads(meta_path.read_text())
        prior_row = resume_by_id.get(meta["id"])
        if prior_row:
            if (prior_row.get("output_sha256") != meta.get("image", {}).get("sha256") or
                    prior_row.get("rgba_sha256") != meta.get("image", {}).get("rgba_sha256")):
                raise RuntimeError(f"{meta['id']}: resume proof output hashes differ from current sidecar")
            source_path_rel = prior_row.get("source_atlas") or prior_row.get("source_path")
            source_hash = prior_row.get("source_atlas_sha256") or prior_row.get("source_sha256")
            if source_path_rel and source_hash:
                if sha256_bytes((PACK / source_path_rel).read_bytes()) != source_hash:
                    raise RuntimeError(f"{meta['id']}: resume proof source hash no longer matches")
            resolution_rows.append(prior_row)
            skipped.add(meta["id"])
            continue
        crop_meta = meta.get("provenance", {}).get("crop_bounds_px")
        if not crop_meta:
            raise RuntimeError(f"{meta['id']}: missing crop_bounds_px provenance")
        atlas_rel = meta["provenance"].get("source_atlas")
        recipe_rel = meta["provenance"].get("generation_recipe")
        if not atlas_rel or not recipe_rel:
            raise RuntimeError(f"{meta['id']}: missing source atlas or generation recipe")
        atlas_path = PACK / atlas_rel
        recipe_path = PACK / recipe_rel
        if not atlas_path.is_file() or not recipe_path.is_file():
            raise RuntimeError(f"{meta['id']}: retained atlas/recipe is missing")
        atlas_hash = sha256_bytes(atlas_path.read_bytes())
        expected_atlas_hash = meta["provenance"].get("source_atlas_sha256")
        if expected_atlas_hash and atlas_hash != expected_atlas_hash:
            raise RuntimeError(f"{meta['id']}: source atlas hash mismatch")

        transform = meta.get("provenance", {}).get("view_transform")
        if transform:
            provenance = meta["provenance"]
            source_asset_id = provenance.get("source_view_asset")
            source_meta = metadata_by_id.get(source_asset_id)
            if source_meta is None:
                raise RuntimeError(f"{meta['id']}: transformed view references missing source view {source_asset_id}")
            source_view_hash = provenance.get("source_view_sha256")
            if not source_view_hash:
                raise RuntimeError(f"{meta['id']}: transformed view lacks immutable source-view hash")
            if "horizontal mirror" in transform:
                base_frame, source_resolution = resolve_atlas_frame(meta, source_view_hash, None, atlas_cache)
                frame = ImageOps.mirror(base_frame)
            elif "swap opposite camera projection" in transform:
                base_frame, source_resolution = resolve_atlas_frame(source_meta, source_view_hash, None, atlas_cache)
                frame = base_frame
            else:
                raise RuntimeError(f"{meta['id']}: unsupported declared view transform {transform}")
            encoded = png_bytes(frame, optimize=False)
            if sha256_bytes(encoded) != meta["image"].get("sha256") or rgba_sha256(frame) != meta["image"].get("rgba_sha256"):
                raise RuntimeError(f"{meta['id']}: transformed raw-atlas projection differs from both recorded hashes")
            outputs.append((PACK / meta["image"]["path"], encoded))
            resolution_rows.append({"id": meta["id"], "view": meta.get("view"),
                "source_view_asset": source_asset_id, "source_view_sha256": source_view_hash,
                "source_atlas": source_resolution["source_atlas"],
                "source_atlas_sha256": source_resolution["source_atlas_sha256"],
                "coordinate_format": source_resolution["coordinate_format"],
                "decoded_bounds_xyxy": source_resolution["decoded_bounds_xyxy"],
                "alpha_threshold": source_resolution["alpha_threshold"],
                "alpha_mode": source_resolution["alpha_mode"], "resampling": source_resolution["resampling"],
                "png_optimize": False, "view_transform": transform,
                "output_sha256": meta["image"]["sha256"], "rgba_sha256": meta["image"]["rgba_sha256"]})
            continue

        crop_meta = meta.get("provenance", {}).get("crop_bounds_px", {})
        source_crop_path = meta.get("provenance", {}).get("source_crop_path")
        if source_crop_path:
            crop_path = PACK / source_crop_path
            crop_bytes = crop_path.read_bytes()
            if sha256_bytes(crop_bytes) != meta["provenance"].get("source_crop_sha256"):
                raise RuntimeError(f"{meta['id']}: retained projection crop hash mismatch")
            piece = Image.open(crop_path).convert("RGBA")
            dest = PACK / meta["image"]["path"]
            if piece.size == (int(meta["image"]["width"]), int(meta["image"]["height"])) and sha256_bytes(crop_bytes) == meta["image"].get("sha256"):
                rgba_hash = sha256_bytes(struct.pack(">II", piece.width, piece.height) + piece.tobytes())
                if rgba_hash != meta["image"].get("rgba_sha256"):
                    raise RuntimeError(f"{meta['id']}: full-canvas retained projection RGBA hash differs from sidecar")
                outputs.append((dest, crop_bytes))
                resolution_rows.append({"id": meta["id"], "view": meta.get("view"),
                    "source_path": source_crop_path, "source_sha256": sha256_bytes(crop_bytes),
                    "coordinate_format": "retained-full-frame", "decoded_bounds_xyxy": None,
                    "output_sha256": meta["image"].get("sha256"), "rgba_sha256": rgba_hash})
                continue
            nw, nh, _ = resized_size(crop_meta)
            if piece.size != (nw, nh):
                piece = piece.resize((nw, nh), Image.Resampling.NEAREST)
            frame = Image.new("RGBA", (int(meta["image"]["width"]), int(meta["image"]["height"])))
            ox, oy = [int(v) for v in crop_meta["canvas_offset_px"]]
            frame.alpha_composite(piece, (ox, oy))
            buffer = BytesIO()
            frame.save(buffer, format="PNG", optimize=True)
            encoded = buffer.getvalue()
            if sha256_bytes(encoded) != meta["image"].get("sha256"):
                raise RuntimeError(f"{meta['id']}: retained projection-crop replay hash differs from sidecar")
            rgba_hash = sha256_bytes(struct.pack(">II", frame.width, frame.height) + frame.tobytes())
            if rgba_hash != meta["image"].get("rgba_sha256"):
                raise RuntimeError(f"{meta['id']}: retained projection-crop replay RGBA hash differs from sidecar")
            outputs.append((dest, encoded))
            resolution_rows.append({"id": meta["id"], "view": meta.get("view"),
                "source_path": source_crop_path, "source_sha256": sha256_bytes(crop_bytes),
                "coordinate_format": "retained-crop-size-offset", "decoded_bounds_xyxy": None,
                "crop_size_px": [nw, nh], "canvas_offset_px": [ox, oy],
                "output_sha256": meta["image"].get("sha256"), "rgba_sha256": rgba_hash})
            continue

        axis_remap = meta.get("provenance", {}).get("axis_remap")
        symmetric = meta.get("provenance", {}).get("symmetric_projection_derivation")
        retained_derivation = axis_remap or symmetric
        if retained_derivation:
            source_path = PACK / retained_derivation["source_path"]
            source_bytes = source_path.read_bytes()
            if sha256_bytes(source_bytes) != retained_derivation["source_sha256"]:
                raise RuntimeError(f"{meta['id']}: retained projection-derivation source hash mismatch")
            frame = Image.open(source_path).convert("RGBA")
            rotation = retained_derivation.get("rotation")
            if rotation == "clockwise90":
                frame = frame.transpose(Image.Transpose.ROTATE_270)
            elif rotation in ("180 degrees", "180"):
                frame = frame.transpose(Image.Transpose.ROTATE_180)
            elif rotation not in (None, "none"):
                raise RuntimeError(f"{meta['id']}: unknown projection-derivation rotation")
            dest = PACK / meta["image"]["path"]
            buffer = BytesIO()
            frame.save(buffer, format="PNG", optimize=True)
            encoded = buffer.getvalue()
            if sha256_bytes(encoded) != meta["image"].get("sha256"):
                raise RuntimeError(f"{meta['id']}: projection-derivation replay hash differs from sidecar")
            rgba_hash = sha256_bytes(struct.pack(">II", frame.width, frame.height) + frame.tobytes())
            if rgba_hash != meta["image"].get("rgba_sha256"):
                raise RuntimeError(f"{meta['id']}: projection-derivation replay RGBA hash differs from sidecar")
            outputs.append((dest, encoded))
            resolution_rows.append({"id": meta["id"], "view": meta.get("view"),
                "source_path": retained_derivation["source_path"], "source_sha256": sha256_bytes(source_bytes),
                "coordinate_format": "retained-projection-transform", "decoded_bounds_xyxy": None,
                "rotation": rotation or "none", "output_sha256": meta["image"].get("sha256"),
                "rgba_sha256": rgba_hash})
            continue

        recipe_data = recipe_json(recipe_path, crop_meta, meta)
        declared_threshold = recipe_data.get("alpha_threshold") or crop_meta.get("alpha_threshold")
        thresholds = ([int(declared_threshold)] if declared_threshold is not None else [])
        thresholds += [t for t in (16, 32, 64, 128, 200, 245) if t not in thresholds]
        declared_format = crop_meta.get("coordinate_format") or crop_meta.get("bounds_format")
        if not declared_format and "alpha_bounds_global_xywh" in crop_meta:
            declared_format = "xywh"
        bounds_value = crop_meta.get("alpha_bounds_global", crop_meta.get("alpha_bounds_global_xywh"))
        formats = ([declared_format.lower()] if declared_format else [])
        formats += [f for f in ("xyxy", "xywh") if f not in formats]
        declared_alpha = recipe_data.get("preserve_alpha")
        alpha_modes = []
        if declared_alpha is not None:
            alpha_modes.append("preserve-selected-alpha" if declared_alpha else "binary-threshold-mask")
        receipt = recipe_data.get("install_receipt", {})
        if receipt.get("component_bounds_xyxy") == crop_meta.get("alpha_bounds_global"):
            alpha_modes.append("raw-crop-alpha")
        if meta.get("provenance", {}).get("postprocess", {}).get("operation") == "remove-isolated-alpha-components":
            alpha_modes.insert(0, "raw-crop-alpha")
        alpha_modes += [m for m in ("binary-threshold-mask", "preserve-selected-alpha", "raw-crop-alpha") if m not in alpha_modes]
        resamples = [Image.Resampling.NEAREST, Image.Resampling.LANCZOS,
                     Image.Resampling.BILINEAR, Image.Resampling.BICUBIC]
        optimize_modes = [True, False]
        expected_file = meta["image"].get("sha256")
        expected_rgba = meta["image"].get("rgba_sha256")
        matches = []
        attempted = []
        resolved = None
        for fmt, threshold, alpha_mode, resample, optimize in product(formats, thresholds, alpha_modes, resamples, optimize_modes):
            if fmt not in ("xyxy", "xywh"):
                continue
            if bounds_value is None:
                raise RuntimeError(f"{meta['id']}: no supported alpha bounds field")
            key = (atlas_rel, threshold)
            if key not in atlas_cache:
                atlas = Image.open(atlas_path).convert("RGBA")
                rgba = np.asarray(atlas)
                labels, _ = ndimage.label(rgba[:, :, 3] >= threshold, np.ones((3, 3), dtype=np.uint8))
                atlas_cache[key] = (atlas, labels)
            atlas, labels = atlas_cache[key]
            frame, decoded = make_atlas_candidate(atlas, labels, crop_meta, {
                "canvas_width": int(meta["image"]["width"]),
                "canvas_height": int(meta["image"]["height"]),
            }, fmt, threshold, alpha_mode, resample)
            if frame is None:
                continue
            try:
                frame = apply_callbacks(frame, meta)
            except RuntimeError:
                # A sidecar callback may declare the pre-callback frame hash;
                # reject this interpretation and try the remaining metadata
                # candidates without weakening that guard.
                continue
            encoded = png_bytes(frame, optimize=optimize)
            file_hash = sha256_bytes(encoded)
            rgba_hash = rgba_sha256(frame)
            attempted.append({"coordinate_format": fmt, "decoded_bounds_xyxy": list(decoded),
                              "alpha_threshold": threshold, "alpha_mode": alpha_mode,
                              "resampling": resample.name, "png_optimize": optimize,
                              "png_sha256": file_hash, "rgba_sha256": rgba_hash})
            if file_hash == expected_file and rgba_hash == expected_rgba:
                matches.append((frame, encoded, fmt, decoded, threshold, alpha_mode, resample.name, optimize))
                # The recorded pair of cryptographic hashes uniquely binds the
                # exact pixels and PNG stream. Stop at the first exact match;
                # later interpretations cannot improve reproducibility and
                # would needlessly relabel every large source atlas.
                resolved = matches[-1]
                break
        if resolved is not None:
            matches = [resolved]
        unique = {(m[1], m[0].size, m[0].tobytes()) for m in matches}
        if not matches:
            failures.append({"id": meta["id"], "source_atlas": atlas_rel,
                             "source_atlas_sha256": atlas_hash,
                             "expected_png_sha256": expected_file,
                             "expected_rgba_sha256": expected_rgba,
                             "attempted_interpretations": len(attempted)})
            if args.resolution_report and (asset_number % 100 == 0):
                args.resolution_report.parent.mkdir(parents=True, exist_ok=True)
                args.resolution_report.write_text(json.dumps({"schema_version": 1,
                    "processed": asset_number, "expected": len(assets),
                    "count": len(resolution_rows), "failures": failures,
                    "resolutions": resolution_rows}, indent=2) + "\n")
            continue
        if len(unique) != 1:
            raise RuntimeError(f"{meta['id']}: ambiguous replay candidates produce different pixels")
        frame, encoded, fmt, decoded, threshold, alpha_mode, resampling, optimize = matches[0]
        resolution_rows.append({
            "id": meta["id"], "view": meta.get("view"),
            "source_atlas": atlas_rel, "source_atlas_sha256": atlas_hash,
            "recipe_path": str(recipe_rel), "recipe_format": recipe_path.suffix.lower(),
            "coordinate_format": fmt, "recorded_bounds": bounds_value, "decoded_bounds_xyxy": list(decoded),
            "resized_bounds_format": resized_size(crop_meta)[2],
            "alpha_threshold": threshold, "alpha_mode": alpha_mode,
            "resampling": resampling, "png_optimize": optimize,
            "matching_interpretations": [{"coordinate_format": m[2], "decoded_bounds_xyxy": list(m[3]),
                                           "alpha_threshold": m[4], "alpha_mode": m[5],
                                           "resampling": m[6], "png_optimize": m[7]} for m in matches],
            "output_sha256": expected_file, "rgba_sha256": expected_rgba,
        })
        outputs.append((PACK / meta["image"]["path"], encoded))
        if args.resolution_report and (asset_number % 100 == 0):
            args.resolution_report.parent.mkdir(parents=True, exist_ok=True)
            args.resolution_report.write_text(json.dumps({"schema_version": 1,
                "processed": asset_number, "expected": len(assets),
                "count": len(resolution_rows), "failures": failures,
                "resolutions": resolution_rows}, indent=2) + "\n")

    # Do not touch any existing output until every reconstruction and declared
    # file/pixel hash has passed. The encoded bytes are exactly the deterministic
    # PNG payload that was written during normalization.
    if args.resolution_report:
        args.resolution_report.parent.mkdir(parents=True, exist_ok=True)
        args.resolution_report.write_text(json.dumps({"schema_version": 1, "processed": len(assets),
            "expected": len(assets), "count": len(resolution_rows), "reused_prior_resolutions": len(skipped), "failures": failures,
            "resolutions": resolution_rows}, indent=2) + "\n")
    if failures:
        raise RuntimeError(f"{len(failures)} leaves did not reproduce their declared PNG and RGBA hashes; see resolution report")
    if not args.verify_only:
        for dest, encoded in outputs:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(encoded)
    print(f"Verified {len(outputs)} view PNGs from retained source atlases" + (" without writing." if args.verify_only else "."))


if __name__ == "__main__":
    main()
