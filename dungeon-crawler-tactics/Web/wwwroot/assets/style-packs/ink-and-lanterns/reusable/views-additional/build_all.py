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

import numpy as np
from PIL import Image
from scipy import ndimage


OUT = Path(__file__).resolve().parent
PACK = OUT.parents[1]
INDEX = OUT / "set-index.json"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def replay_single_view_atlas_cell(meta: dict, recipe_data: dict, recipe_path: Path,
                                  atlas: Image.Image, atlas_rel: str, atlas_hash: str):
    """Replay the explicit per-view generated-atlas crop/resize recipe.

    This handler is intentionally limited to the v1 recipe emitted for the
    floor-hatch R/L correction. Unlike the legacy component-mask renderer, the
    source alpha inside the recorded component bbox is preserved as-is.
    """
    if recipe_data.get("method") != "single-view-atlas-cell-isotropic-normalization":
        return None
    provenance = meta.get("provenance", {})
    if provenance.get("generation_recipe") != recipe_path.relative_to(PACK).as_posix():
        raise RuntimeError(f"{meta['id']}: single-view recipe path differs from provenance")
    recipe_sha = sha256_bytes(recipe_path.read_bytes())
    expected_recipe_sha = provenance.get("generation_recipe_sha256")
    if expected_recipe_sha and recipe_sha != expected_recipe_sha:
        raise RuntimeError(f"{meta['id']}: single-view normalization recipe hash mismatch")
    if (recipe_data.get("object_id") != meta.get("object_id")
            or provenance.get("source_atlas") != atlas_rel
            or recipe_data.get("generated_atlas_path") != atlas_rel
            or recipe_data.get("generated_atlas_sha256") != atlas_hash
            or provenance.get("source_atlas_sha256") != atlas_hash):
        raise RuntimeError(f"{meta['id']}: single-view atlas/object binding mismatch")
    source_path = provenance.get("source_image")
    source_rows = [item for item in recipe_data.get("input_references", [])
                   if item.get("path") == source_path and item.get("role") == "native source identity and handle location"]
    if len(source_rows) != 1:
        raise RuntimeError(f"{meta['id']}: single-view canonical source path mismatch")
    source = source_rows[0]
    source_file = PACK / source_path
    if not source_file.is_file() or sha256_bytes(source_file.read_bytes()) != source.get("sha256"):
        raise RuntimeError(f"{meta['id']}: single-view canonical source hash mismatch")
    if (provenance.get("source_sha256") or provenance.get("source_image_sha256")) not in (None, source.get("sha256")):
        raise RuntimeError(f"{meta['id']}: single-view canonical source hash differs from provenance")
    request_path = recipe_data.get("generation_request_path")
    request_hash = recipe_data.get("generation_request_sha256")
    if (request_path != provenance.get("generation_request")
            or request_hash != provenance.get("generation_request_sha256")):
        raise RuntimeError(f"{meta['id']}: single-view generation-request binding mismatch")
    request_file = PACK / request_path
    if not request_file.is_file() or sha256_bytes(request_file.read_bytes()) != request_hash:
        raise RuntimeError(f"{meta['id']}: single-view generation request hash mismatch")

    view = meta.get("view")
    rows = [row for row in recipe_data.get("views", [])
            if row.get("object_id") == meta.get("object_id") and row.get("view") == view]
    if len(rows) != 1:
        raise RuntimeError(f"{meta['id']}: single-view recipe row missing or ambiguous")
    row = rows[0]
    crop_meta = provenance.get("crop_bounds_px", {})
    normalization = provenance.get("normalization", {})
    nominal = crop_meta.get("nominal_cell", {})
    if (row.get("atlas_path") != atlas_rel or row.get("atlas_sha256") != atlas_hash
            or nominal.get("bounds") != row.get("cell_xyxy")
            or crop_meta.get("alpha_bounds_global") != row.get("component_bounds_xyxy")
            or crop_meta.get("resized_bounds_px") != row.get("resized_dimensions_px")
            or crop_meta.get("canvas_offset_px") != row.get("canvas_offset_px")
            or crop_meta.get("alpha_threshold") != row.get("alpha_threshold")
            or crop_meta.get("shared_scale") != row.get("uniform_scale")
            or normalization.get("uniform_scale") != row.get("uniform_scale")
            or normalization.get("resized_dimensions_px") != row.get("resized_dimensions_px")
            or normalization.get("canvas_offset_px") != row.get("canvas_offset_px")
            or normalization.get("canvas_size_px") != row.get("canvas_size_px")):
        raise RuntimeError(f"{meta['id']}: sidecar crop/scale fields disagree with single-view recipe")

    x0, y0, x1, y1 = [int(v) for v in row["component_bounds_xyxy"]]
    cx0, cy0, cx1, cy1 = [int(v) for v in row["cell_xyxy"]]
    if (x0 < cx0 or y0 < cy0 or x1 > cx1 or y1 > cy1
            or x1 <= x0 or y1 <= y0 or cx1 > atlas.width or cy1 > atlas.height):
        raise RuntimeError(f"{meta['id']}: single-view crop/cell bounds are invalid")
    scale = float(row["uniform_scale"])
    if not np.isfinite(scale) or scale <= 0:
        raise RuntimeError(f"{meta['id']}: invalid single-view scale")
    piece = atlas.crop((x0, y0, x1, y1))
    expected_dimensions = [max(1, round(piece.width * scale)), max(1, round(piece.height * scale))]
    if expected_dimensions != row.get("resized_dimensions_px"):
        raise RuntimeError(f"{meta['id']}: single-view isotropic scale arithmetic mismatch")
    if row.get("resampling") != "nearest-neighbor":
        raise RuntimeError(f"{meta['id']}: unsupported single-view resampling method")
    piece = piece.resize(tuple(expected_dimensions), Image.Resampling.NEAREST)
    canvas_size = tuple(int(v) for v in row["canvas_size_px"])
    canvas = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    canvas.alpha_composite(piece, tuple(int(v) for v in row["canvas_offset_px"]))
    rgba_sha = sha256_bytes(struct.pack(">II", *canvas.size) + canvas.tobytes())
    if rgba_sha != row.get("candidate_rgba_sha256") or rgba_sha != meta.get("image", {}).get("rgba_sha256"):
        raise RuntimeError(f"{meta['id']}: single-view exact PNG/RGBA output mismatch")
    encoded = None
    encoding = None
    # The recipe predates an explicit PNG encoder field. Resolve only among
    # Pillow's bounded optimize/compression settings and require an exact
    # candidate SHA; never accept RGBA-only equality or a fallback.
    for optimize in (False, True):
        for compression in range(10):
            buffer = BytesIO()
            canvas.save(buffer, format="PNG", optimize=optimize, compress_level=compression)
            candidate = buffer.getvalue()
            candidate_sha = sha256_bytes(candidate)
            if candidate_sha == row.get("candidate_sha256") == meta.get("image", {}).get("sha256"):
                encoded = candidate
                encoding = {"optimize": optimize, "compress_level": compression}
                break
        if encoded is not None:
            break
    if encoded is None:
        raise RuntimeError(f"{meta['id']}: single-view exact PNG encoder match not found")
    return canvas, encoded, {"asset_id": meta["id"], "method": recipe_data["method"],
        "recipe_path": provenance["generation_recipe"], "recipe_sha256": recipe_sha,
        "source_atlas": atlas_rel, "source_atlas_sha256": atlas_hash,
        "cell_xyxy": row["cell_xyxy"], "crop_bounds_xyxy": row["component_bounds_xyxy"],
        "alpha_threshold": row["alpha_threshold"], "uniform_scale": scale,
        "resized_dimensions_px": expected_dimensions, "canvas_offset_px": row["canvas_offset_px"],
        "png_sha256": candidate_sha, "rgba_sha256": rgba_sha, "png_encoding": encoding}


def main() -> None:
    catalog = json.loads(INDEX.read_text())
    atlas_cache = {}
    outputs = []
    coordinate_resolutions = []
    for asset in catalog["assets"]:
        meta_path = PACK / asset["metadata_path"]
        # Use the adjacent sidecar as source of truth, just as the builder does.
        meta = json.loads(meta_path.read_text())
        replay_rel = meta.get("provenance", {}).get("replay_source")
        if replay_rel:
            replay_path = PACK / replay_rel
            if not replay_path.is_file():
                raise RuntimeError(f"{meta['id']}: retained replay source is missing")
            encoded = replay_path.read_bytes()
            replay_hash = sha256_bytes(encoded)
            expected_replay_hash = meta["provenance"].get("replay_source_sha256")
            if expected_replay_hash and replay_hash != expected_replay_hash:
                raise RuntimeError(f"{meta['id']}: retained replay source hash mismatch")
            replay_image = Image.open(BytesIO(encoded)).convert("RGBA")
            if replay_image.size != (int(meta["image"]["width"]), int(meta["image"]["height"])):
                raise RuntimeError(f"{meta['id']}: retained replay dimensions differ from metadata")
            rgba_hash = sha256_bytes(struct.pack(">II", replay_image.width, replay_image.height) + replay_image.tobytes())
            if replay_hash != meta["image"].get("sha256") or rgba_hash != meta["image"].get("rgba_sha256"):
                raise RuntimeError(f"{meta['id']}: retained replay source differs from declared image hashes")
            outputs.append((PACK / meta["image"]["path"], encoded))
            continue
        axis_remap = meta.get("provenance", {}).get("axis_remap")
        if axis_remap:
            source_path = PACK / axis_remap["source_path"]
            source_bytes = source_path.read_bytes()
            if sha256_bytes(source_bytes) != axis_remap["source_sha256"]:
                raise RuntimeError(f"{meta['id']}: retained axis-remap source hash mismatch")
            frame = Image.open(BytesIO(source_bytes)).convert("RGBA")
            rotation = axis_remap["rotation"]
            if rotation == "none":
                pass
            elif rotation == "clockwise90":
                frame = frame.transpose(Image.Transpose.ROTATE_270)
            elif rotation == "counterclockwise90":
                frame = frame.transpose(Image.Transpose.ROTATE_90)
            elif rotation in ("180", "180 degrees"):
                frame = frame.transpose(Image.Transpose.ROTATE_180)
            else:
                raise RuntimeError(f"{meta['id']}: unsupported retained axis-remap rotation")
            buffer = BytesIO(); frame.save(buffer, format="PNG", optimize=True); encoded = buffer.getvalue()
            file_hash = sha256_bytes(encoded)
            rgba_hash = sha256_bytes(struct.pack(">II", frame.width, frame.height) + frame.tobytes())
            if file_hash != meta["image"].get("sha256") or rgba_hash != meta["image"].get("rgba_sha256"):
                raise RuntimeError(f"{meta['id']}: retained axis-remap output differs from sidecar")
            outputs.append((PACK / meta["image"]["path"], encoded))
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

        key = (atlas_rel, int(json.loads(recipe_path.read_text()).get("alpha_threshold", 245)))
        if key not in atlas_cache:
            threshold = key[1]
            atlas = Image.open(atlas_path).convert("RGBA")
            rgba = np.asarray(atlas)
            mask = rgba[:, :, 3] >= threshold
            labels, _ = ndimage.label(mask, np.ones((3, 3), dtype=np.uint8))
            atlas_cache[key] = (atlas, labels)
        atlas, labels = atlas_cache[key]

        values = [int(v) for v in crop_meta["alpha_bounds_global"]]
        x, y, c, d = values
        bbox_options = [("xyxy", x, y, c, d), ("xywh", x, y, x + c, y + d)]
        recipe_data = json.loads(recipe_path.read_text())
        single_view_result = replay_single_view_atlas_cell(
            meta, recipe_data, recipe_path, atlas, atlas_rel, atlas_hash)
        if single_view_result is not None:
            frame, encoded, resolution = single_view_result
            outputs.append((PACK / meta["image"]["path"], encoded))
            coordinate_resolutions.append(resolution)
            continue
        threshold = int(recipe_data.get("alpha_threshold", 245))
        cell_options = [("global8", None, None, None, None)]
        nominal = crop_meta.get("nominal_cell", {}).get("bounds")
        if nominal:
            cx, cy, cc, cd = [int(v) for v in nominal]
            for encoding, cx0, cy0, cx1, cy1 in [("xyxy", cx, cy, cc, cd), ("xywh", cx, cy, cx + cc, cy + cd)]:
                cell_options.extend([(f"local8-{encoding}", cx0, cy0, cx1, cy1), (f"local4-{encoding}", cx0, cy0, cx1, cy1)])
        chosen = None
        base_threshold = int(recipe_data.get("alpha_threshold", 245))
        threshold_options = [base_threshold, base_threshold + 1, base_threshold - 1, base_threshold + 2, base_threshold - 2]
        alpha_options = [bool(recipe_data.get("preserve_alpha", False)), not bool(recipe_data.get("preserve_alpha", False))]
        for bbox_encoding, x0, y0, x1, y1 in bbox_options:
            if x0 < 0 or y0 < 0 or x1 <= x0 or y1 <= y0 or x1 > atlas.width or y1 > atlas.height:
                continue
            for cell_encoding, cx0, cy0, cx1, cy1 in cell_options:
                if not cell_encoding.startswith("global") and (cx0 < 0 or cy0 < 0 or cx1 <= cx0 or cy1 <= cy0 or cx1 > atlas.width or cy1 > atlas.height):
                    continue
                for alpha_threshold in threshold_options:
                    if alpha_threshold <= 0:
                        continue
                    if cell_encoding.startswith("global"):
                        label_source = labels
                        mx0, my0 = x0, y0
                    else:
                        cell = atlas.crop((cx0, cy0, cx1, cy1))
                        binary = np.asarray(cell)[:, :, 3] >= alpha_threshold
                        if cell_encoding.startswith("local4"):
                            label_source, _ = ndimage.label(binary)
                        else:
                            label_source, _ = ndimage.label(binary, np.ones((3, 3), dtype=np.uint8))
                        mx0, my0 = x0 - cx0, y0 - cy0
                        if mx0 < 0 or my0 < 0 or mx0 + (x1-x0) > label_source.shape[1] or my0 + (y1-y0) > label_source.shape[0]:
                            continue
                    if crop_meta.get("selection_mode") == "all_opaque_pixels":
                        alpha_crop = np.asarray(atlas)[y0:y1, x0:x1, 3]
                        local_mask = alpha_crop >= int(crop_meta.get("alpha_threshold", 245))
                    else:
                        keep = [int(v) for v in crop_meta["component_labels"]]
                        local_mask = np.isin(label_source[my0:my0+(y1-y0), mx0:mx0+(x1-x0)], keep)
                    piece_base = atlas.crop((x0, y0, x1, y1))
                    for preserve_alpha in alpha_options:
                        piece = piece_base.copy()
                        if preserve_alpha:
                            original_alpha = np.asarray(piece.getchannel("A"))
                            piece.putalpha(Image.fromarray(np.where(local_mask, original_alpha, 0).astype("uint8")))
                        else:
                            piece.putalpha(Image.fromarray((local_mask * 255).astype("uint8")))
                        projection_scale = float(crop_meta.get("projection_scale", 1.0))
                        if projection_scale != 1.0:
                            projected_size = (max(1, round(piece.width * projection_scale)), max(1, round(piece.height * projection_scale)))
                            piece = piece.resize(projected_size, Image.Resampling.NEAREST)
                        nw, nh = [int(v) for v in crop_meta["resized_bounds_px"]]
                        piece = piece.resize((nw, nh), Image.Resampling.NEAREST)
                        candidate = Image.new("RGBA", (int(meta["image"]["width"]), int(meta["image"]["height"])))
                        ox, oy = [int(v) for v in crop_meta["canvas_offset_px"]]
                        candidate.alpha_composite(piece, (ox, oy))
                        buffer = BytesIO(); candidate.save(buffer, format="PNG", optimize=True); candidate_bytes = buffer.getvalue()
                        candidate_file_sha = sha256_bytes(candidate_bytes)
                        candidate_rgba_sha = sha256_bytes(struct.pack(">II", candidate.width, candidate.height) + candidate.tobytes())
                        if candidate_file_sha == meta["image"].get("sha256") and candidate_rgba_sha == meta["image"].get("rgba_sha256"):
                            chosen = (bbox_encoding, cell_encoding, candidate, candidate_bytes, alpha_threshold, preserve_alpha)
                            break
                    if chosen:
                        break
                if chosen:
                    break
            if chosen:
                break
        matches = [chosen] if chosen else []
        if not matches:
            raise RuntimeError(f"{meta['id']}: no coordinate interpretation matches both declared hashes")
        # If multiple interpretations match, their exact pixel/file hashes are
        # necessarily identical; retain deterministic XYXY/global-first ordering.
        bbox_encoding, cell_encoding, frame, encoded, alpha_threshold, preserve_alpha = matches[0]
        coordinate_resolutions.append({"asset_id": meta["id"], "bounds_encoding": bbox_encoding, "nominal_cell_encoding": cell_encoding, "connectivity": "4-connected" if cell_encoding.startswith("local4") else "8-connected", "decoded_crop_xyxy": [x0, y0, x1, y1], "alpha_threshold": alpha_threshold, "preserve_alpha": preserve_alpha, "source_atlas": atlas_rel, "source_atlas_sha256": atlas_hash, "png_sha256": meta["image"]["sha256"], "rgba_sha256": meta["image"]["rgba_sha256"]})
        dest = PACK / meta["image"]["path"]
        outputs.append((dest, encoded))

    # Do not touch any existing output until every reconstruction and declared
    # file/pixel hash has passed. The encoded bytes are exactly the deterministic
    # PNG payload that was written during normalization.
    for dest, encoded in outputs:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(encoded)
    (OUT / "build_all_coordinate_resolution.json").write_text(json.dumps({"resolved_assets": coordinate_resolutions}, indent=2) + "\n")
    print(f"Rebuilt and verified {len(outputs)} view PNGs from retained raw atlases.")


if __name__ == "__main__":
    main()
