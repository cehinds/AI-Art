#!/usr/bin/env python3
"""Guarded isolated replay for explicitly recorded current-index image repairs.

This tool never writes into the live pack. It reads exact-hash-pinned inputs,
rebuilds selected PNG outputs under an external output directory, and verifies
both file and canonical RGBA hashes against the live current index.
"""
from __future__ import annotations
import argparse, hashlib, json, os, pathlib, shutil, struct, tempfile
from functools import lru_cache
from typing import Any
import numpy as np
from PIL import Image
from scipy import ndimage

OUT = pathlib.Path(__file__).resolve().parent
PACK = OUT.parents[1]
INDEX = OUT / "set-index.json"
VIEWS = ("front", "top", "right", "left", "bottom", "rear")

def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def sha_file(path: pathlib.Path) -> str:
    return sha_bytes(path.read_bytes())

def rgba_sha(image: Image.Image) -> str:
    image = image.convert("RGBA")
    return sha_bytes(struct.pack(">II", *image.size) + image.tobytes())

def clip_alpha_below(image: Image.Image, threshold: int | None) -> Image.Image:
    """Apply an explicitly recorded alpha cutoff without changing RGB pixels."""
    if threshold is None:
        return image
    if not isinstance(threshold, int) or not 0 <= threshold <= 255:
        raise ValueError("clip_alpha_below must be an integer in [0,255]")
    image = image.convert("RGBA")
    rgba = np.asarray(image).copy()
    rgba[rgba[..., 3] < threshold, 3] = 0
    return Image.fromarray(rgba, "RGBA")

def atomic_write(path: pathlib.Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    except BaseException:
        try:
            os.unlink(temp)
        except FileNotFoundError:
            pass
        raise

def pack_path(value: str) -> pathlib.Path:
    p = pathlib.PurePosixPath(value)
    if p.is_absolute() or ".." in p.parts:
        raise ValueError(f"input path must be pack-relative and traversal-free: {value}")
    return PACK.joinpath(*p.parts)

def retained_path(task: dict[str, Any], external_key: str, portable_key: str,
                  legacy_key: str | None = None) -> pathlib.Path:
    if task.get(external_key):
        path = pathlib.Path(task[external_key]).resolve()
        if path == PACK or PACK in path.parents:
            raise ValueError("external retained input must be outside the pack")
        return path
    value = task.get(portable_key) or (task.get(legacy_key) if legacy_key else None)
    if not value:
        raise ValueError(f"manifest lacks {external_key} or {portable_key}")
    return pack_path(value)

def load_index() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    data = json.loads(INDEX.read_text())
    if len({s["object_id"] for s in data["view_sets"]}) != len(data["view_sets"]):
        raise ValueError("current set-index has duplicate object_id groups")
    if len({a["id"] for a in data["assets"]}) != len(data["assets"]):
        raise ValueError("current set-index has duplicate asset IDs")
    assets = {a["id"]: a for a in data["assets"]}
    sets = {s["object_id"]: s for s in data["view_sets"]}
    by_obj_view = {}
    for oid, group in sets.items():
        for view, aid in group.get("views", {}).items():
            if view not in VIEWS or aid not in assets:
                raise ValueError(f"invalid index reference {oid}.{view} -> {aid}")
            by_obj_view[(oid, view)] = aid
    return data, assets, by_obj_view

def expected_output(asset: dict[str, Any], pack: pathlib.Path | None = None) -> tuple[str, str]:
    """Return frozen index expectations; production PNGs are optional inputs."""
    image = asset["image"]
    file_hash, rgba_hash = image.get("sha256"), image.get("rgba_sha256")
    if not file_hash or not rgba_hash:
        raise ValueError(f"index lacks frozen output hashes for {asset.get('id')}")
    return file_hash, rgba_hash

def verify_live_output(asset: dict[str, Any], pack: pathlib.Path) -> None:
    rel = asset["image"]["path"]
    p = pack_path(rel)
    file_hash, rgba_hash = expected_output(asset)
    if not p.is_file():
        raise FileNotFoundError(p)
    if sha_file(p) != file_hash:
        raise ValueError(f"live indexed file hash mismatch: {rel}")
    if rgba_sha(Image.open(p)) != rgba_hash:
        raise ValueError(f"live indexed RGBA hash mismatch: {rel}")

def verify_input(path: pathlib.Path, expected: str, label: str) -> bytes:
    if not path.is_file():
        raise FileNotFoundError(f"{label} is missing: {path}")
    data = path.read_bytes()
    actual = sha_bytes(data)
    if actual != expected:
        raise ValueError(f"{label} hash mismatch: expected {expected}, got {actual}")
    return data

@lru_cache(maxsize=6)
def cached_rgba_source(path_text: str) -> Image.Image:
    return Image.open(path_text).convert("RGBA")

@lru_cache(maxsize=24)
def cached_component_labels(path_text: str, threshold: int, connectivity: int) -> np.ndarray:
    source = cached_rgba_source(path_text)
    alpha = np.asarray(source.getchannel("A")) >= threshold
    structure = np.ones((3, 3), dtype=np.uint8) if connectivity == 8 else None
    return ndimage.label(alpha, structure)[0]

def component_crop(source_path: pathlib.Path, task: dict[str, Any]) -> Image.Image:
    source = cached_rgba_source(str(source_path.resolve()))
    if "labels" in task:
        thresholds = task.get("alpha_threshold_candidates", [task.get("alpha_threshold", 245)])
        selected = None
        bounds = None
        for threshold in thresholds:
            labels = cached_component_labels(str(source_path.resolve()), int(threshold), int(task.get("connectivity", 4)))
            candidate = np.isin(labels, np.asarray(task["labels"], dtype=labels.dtype))
            yy, xx = np.where(candidate)
            if not len(xx):
                continue
            candidate_bounds = [int(xx.min()), int(yy.min()), int(xx.max() + 1), int(yy.max() + 1)]
            if task.get("bounds") is None or candidate_bounds == task["bounds"]:
                selected, bounds = candidate, candidate_bounds
                break
        if selected is None:
            raise ValueError(f"no recorded labels matched expected component bounds in {source_path}")
        x0, y0, x1, y1 = bounds
        crop = source.crop((x0, y0, x1, y1))
        if task.get("mask_components", True):
            local = selected[y0:y1, x0:x1]
            if task.get("preserve_alpha", False):
                original_alpha = np.asarray(crop.getchannel("A"))
                crop.putalpha(Image.fromarray(np.where(local, original_alpha, 0).astype("uint8")))
            else:
                crop.putalpha(Image.fromarray((local * 255).astype("uint8")))
    else:
        x0, y0, x1, y1 = task["bounds"]
        crop = source.crop((x0, y0, x1, y1))
    crop = clip_alpha_below(crop, task.get("clip_alpha_below"))
    if task.get("rotate_degrees_ccw") is not None:
        crop = crop.rotate(float(task["rotate_degrees_ccw"]), resample=Image.Resampling.NEAREST, expand=True)
    scale = float(task["scale"])
    nw, nh = max(1, round(crop.width * scale)), max(1, round(crop.height * scale))
    resampling = Image.Resampling.LANCZOS if task.get("resampling") == "lanczos" else Image.Resampling.NEAREST
    crop = crop.resize((nw, nh), resampling)
    canvas = Image.new("RGBA", tuple(task.get("canvas", [256, 256])), (0, 0, 0, 0))
    ax, ay = task.get("anchor", [128, 128])
    offset = task.get("offset", [int(ax - nw // 2), int(ay - nh // 2)])
    canvas.alpha_composite(crop, (int(offset[0]), int(offset[1])))
    return canvas

def component_crop_candidates(source_path: pathlib.Path, task: dict[str, Any]):
    """Yield hash-disambiguatable atlas interpretations from pinned metadata."""
    source = Image.open(source_path).convert("RGBA")
    thresholds = task.get("alpha_threshold_candidates", [task.get("alpha_threshold", 245)])
    connectivities = task.get("connectivity_candidates", [task.get("connectivity", 8)])
    valid_bounds = task.get("bounds_candidates", [task.get("bounds")])
    preserve_modes = task.get("preserve_alpha_candidates", [task.get("preserve_alpha", False)])
    mask_modes = task.get("mask_components_candidates", [task.get("mask_components", True)])
    resamplings = task.get("resampling_candidates", [task.get("resampling", "nearest")])
    optimize_modes = task.get("png_optimize_candidates", [task.get("png_optimize", False)])
    scale = float(task["scale"])
    anchor = task.get("anchor", [128, 128])
    canvas_size = tuple(task.get("canvas", [256, 256]))
    offset = task.get("offset")
    if not task.get("labels"):
        bounds_list = task.get("bounds_candidates", [task.get("bounds")])
        for box in bounds_list:
            if not box or len(box) != 4:
                continue
            x0, y0, x1, y1 = [int(v) for v in box]
            if x1 <= x0 or y1 <= y0:
                continue
            crop = source.crop((x0, y0, x1, y1))
            crop = clip_alpha_below(crop, task.get("clip_alpha_below"))
            sizes = []
            resized = task.get("resized_bounds_px")
            if resized and len(resized) == 2:
                sizes.append((int(resized[0]), int(resized[1]), "recorded-resized-bounds"))
            sizes.append((max(1, round(crop.width * scale)), max(1, round(crop.height * scale)), "component-scale"))
            for nw, nh, size_mode in dict.fromkeys(sizes):
                for resampling in resamplings:
                    resample = {"nearest": Image.Resampling.NEAREST, "lanczos": Image.Resampling.LANCZOS,
                                "bilinear": Image.Resampling.BILINEAR, "bicubic": Image.Resampling.BICUBIC}.get(str(resampling).lower())
                    if resample is None:
                        continue
                    resized_crop = crop.resize((nw, nh), resample)
                    actual_offset = offset or [int(anchor[0] - nw // 2), int(anchor[1] - nh // 2)]
                    canvas = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
                    canvas.alpha_composite(resized_crop, (int(actual_offset[0]), int(actual_offset[1])))
                    for optimize in optimize_modes:
                        yield canvas, bool(optimize), {"bounds_xyxy": [x0, y0, x1, y1], "mask_components": False,
                            "resampling": str(resampling), "resize_mode": size_mode, "resized_wh": [nw, nh],
                            "canvas_offset": [int(actual_offset[0]), int(actual_offset[1])], "png_optimize": bool(optimize)}
        return
    for threshold in thresholds:
        for connectivity in connectivities:
            labels = cached_component_labels(str(source_path.resolve()), int(threshold), int(connectivity))
            selected = np.isin(labels, np.asarray(task.get("labels", []), dtype=labels.dtype))
            yy, xx = np.where(selected)
            if not len(xx):
                continue
            box = [int(xx.min()), int(yy.min()), int(xx.max() + 1), int(yy.max() + 1)]
            if valid_bounds and all(v is not None for v in valid_bounds) and box not in valid_bounds:
                continue
            x0, y0, x1, y1 = box
            original_crop = source.crop((x0, y0, x1, y1))
            local = selected[y0:y1, x0:x1]
            size_options = []
            resized = task.get("resized_bounds_px")
            if resized and len(resized) == 2:
                size_options.append((int(resized[0]), int(resized[1]), "recorded-resized-bounds"))
            size_options.append((max(1, round(original_crop.width * scale)), max(1, round(original_crop.height * scale)), "component-scale"))
            size_options = list(dict.fromkeys(size_options))
            for mask_components in mask_modes:
                for preserve_alpha in preserve_modes:
                    crop = original_crop.copy()
                    if mask_components:
                        if preserve_alpha:
                            original_alpha = np.asarray(crop.getchannel("A"))
                            crop.putalpha(Image.fromarray(np.where(local, original_alpha, 0).astype("uint8")))
                        else:
                            crop.putalpha(Image.fromarray((local * 255).astype("uint8")))
                    for nw, nh, size_mode in size_options:
                        for resampling in resamplings:
                            resample = {"nearest": Image.Resampling.NEAREST, "lanczos": Image.Resampling.LANCZOS,
                                        "bilinear": Image.Resampling.BILINEAR, "bicubic": Image.Resampling.BICUBIC}.get(str(resampling).lower())
                            if resample is None:
                                continue
                            resized_crop = crop.resize((nw, nh), resample)
                            actual_offset = offset or [int(anchor[0] - nw // 2), int(anchor[1] - nh // 2)]
                            canvas = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
                            canvas.alpha_composite(resized_crop, (int(actual_offset[0]), int(actual_offset[1])))
                            for optimize in optimize_modes:
                                yield canvas, bool(optimize), {
                                    "alpha_threshold": int(threshold), "connectivity": int(connectivity),
                                    "bounds_xyxy": box, "mask_components": bool(mask_components),
                                    "preserve_alpha": bool(preserve_alpha), "resampling": str(resampling),
                                    "resize_mode": size_mode, "resized_wh": [nw, nh],
                                    "canvas_offset": [int(actual_offset[0]), int(actual_offset[1])],
                                    "png_optimize": bool(optimize)}

def render_task(task: dict[str, Any], inputs: dict[tuple[str, str], pathlib.Path],
                assets: dict[str, Any], replay_root: pathlib.Path) -> Image.Image:
    op = task["op"]
    if op == "copy" or op == "rotate" or op == "isotropic_scale":
        source_id, source_view = task["source_asset_id"], task["source_view"]
        key = (source_id, source_view)
        if key not in inputs:
            raise KeyError(f"source asset/view absent from current index: {key}")
        source_path = inputs[key]
        expected = task["source_sha256"]
        data = verify_input(source_path, expected, f"{source_id}.{source_view}")
        if op == "copy":
            return Image.open(io.BytesIO(data)).convert("RGBA")
        image = Image.open(io.BytesIO(data)).convert("RGBA")
        if op == "rotate":
            degrees = int(task["degrees_clockwise"])
            return image.rotate(-degrees, resample=Image.Resampling.NEAREST, expand=False)
        scale = float(task["scale"])
        nw, nh = max(1, round(image.width * scale)), max(1, round(image.height * scale))
        image = image.resize((nw, nh), Image.Resampling.NEAREST)
        canvas = Image.new("RGBA", tuple(task.get("canvas", [256, 256])), (0, 0, 0, 0))
        ax, ay = task.get("anchor", [128, 128])
        canvas.alpha_composite(image, (int(ax - nw // 2), int(ay - nh // 2)))
        return canvas
    if op == "copy_path":
        source = retained_path(task, "external_source_path", "source_portable_ref", "source_path")
        label = str(source)
        data = verify_input(source, task["source_sha256"], label)
        return Image.open(io.BytesIO(data)).convert("RGBA")
    if op in {"component_crop", "atlas_crop"}:
        source = retained_path(task, "external_source_path", "source_portable_ref", "source_path")
        verify_input(source, task["source_sha256"], str(source))
        return component_crop(source, task)
    if op == "mask_fill":
        mask_key = (task["mask_asset_id"], task["mask_view"])
        if mask_key not in inputs:
            raise KeyError(f"mask asset/view absent from current index: {mask_key}")
        mask_path = inputs[mask_key]
        data = verify_input(mask_path, task["mask_sha256"], f"mask {mask_key}")
        mask = Image.open(io.BytesIO(data)).convert("RGBA").getchannel("A")
        fill = tuple(task["fill_rgba"])
        image = Image.new("RGBA", mask.size, fill)
        image.putalpha(mask)
        return image
    if op == "composite_over":
        base_key = (task["base_asset_id"], task["base_view"])
        base_data = verify_input(inputs[base_key], task["base_sha256"], f"base {base_key}")
        if task.get("overlay_source_path"):
            overlay_path = pack_path(task["overlay_source_path"])
            overlay_data = verify_input(overlay_path, task["overlay_sha256"], task["overlay_source_path"])
        else:
            overlay_key = (task["overlay_asset_id"], task["overlay_view"])
            overlay_data = verify_input(inputs[overlay_key], task["overlay_sha256"], f"overlay {overlay_key}")
        base = Image.open(io.BytesIO(base_data)).convert("RGBA")
        overlay = Image.open(io.BytesIO(overlay_data)).convert("RGBA")
        base.alpha_composite(overlay)
        return base
    if op == "mask_texture":
        texture_key = (task["texture_asset_id"], task["texture_view"])
        mask_key = (task["mask_asset_id"], task["mask_view"])
        texture_path = inputs[texture_key]
        mask_path = inputs[mask_key]
        tex_data = verify_input(texture_path, task["texture_sha256"], f"texture {texture_key}")
        mask_data = verify_input(mask_path, task["mask_sha256"], f"mask {mask_key}")
        texture = Image.open(io.BytesIO(tex_data)).convert("RGBA")
        mask = Image.open(io.BytesIO(mask_data)).convert("RGBA").getchannel("A")
        box = mask.getbbox()
        if box is None:
            raise ValueError(f"empty mask for {mask_key}")
        x0, y0, x1, y1 = box
        tw, th = x1 - x0, y1 - y0
        factor = max(tw / texture.width, th / texture.height)
        texture = texture.resize((round(texture.width * factor), round(texture.height * factor)), Image.Resampling.NEAREST)
        x, y = (texture.width - tw) // 2, (texture.height - th) // 2
        patch = texture.crop((x, y, x + tw, y + th))
        result = Image.new("RGBA", mask.size, (0, 0, 0, 0))
        result.paste(patch, (x0, y0))
        result.putalpha(mask)
        return result
    raise ValueError(f"unsupported replay op: {op}")

# io is intentionally imported after functions to keep the operation table legible.
import io

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", help="pack-relative replay manifest")
    parser.add_argument("--output", required=True, help="new isolated directory outside the pack")
    parser.add_argument("--verify-live-inputs", action="store_true", help="also verify that production PNGs still match the frozen index")
    args = parser.parse_args()
    manifest_path = pathlib.Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = OUT / manifest_path
    manifest = json.loads(manifest_path.read_text())
    output = pathlib.Path(args.output).resolve()
    if output == PACK or PACK in output.parents or output in PACK.parents:
        raise ValueError("replay output must be outside the live pack tree")
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"isolated output must be new or empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    index_bytes = INDEX.read_bytes()
    index_hash = sha_bytes(index_bytes)
    if manifest.get("index_sha256") != index_hash:
        raise ValueError(f"current set-index changed: expected {manifest.get('index_sha256')}, got {index_hash}")
    data, assets, by_obj_view = load_index()
    objects = {s["object_id"] for s in data["view_sets"]}
    if manifest.get("expected_view_set_count") not in (None, len(objects)):
        raise ValueError("current unique view-set count differs from manifest")
    if manifest.get("expected_asset_count") not in (None, len(data["assets"])):
        raise ValueError("current unique asset count differs from manifest")
    # The index is the frozen expected-output ledger. Live output PNGs are
    # optional; verification is opt-in and never needed for deleted-output replay.
    if args.verify_live_inputs:
        for asset in data["assets"]:
            verify_live_output(asset, PACK)
    by_id = {a["id"]: a for a in data["assets"]}
    task_by_target = {t["target_asset_id"]: t for t in manifest["tasks"]}
    # All source-view dependencies start from immutable retained inputs, then
    # point at a prior isolated replay result when a task has produced one.
    input_paths = {}
    task_outputs = {}
    mismatches = []
    verified_source_hashes = set()
    report = {"schema": "ink-current-index-replay-report-v1", "index_sha256": index_hash,
              "expected_hashes_from_frozen_index": True, "live_inputs_verified": bool(args.verify_live_inputs),
              "view_sets": len(data["view_sets"]), "assets": len(data["assets"]), "tasks": [], "mismatches": mismatches}
    for task in manifest["tasks"]:
        target_id, target_view = task["target_asset_id"], task["target_view"]
        key = (target_id, target_view)
        if key not in by_obj_view.values() and target_id not in by_id:
            raise KeyError(f"target asset not indexed: {target_id}")
        asset = by_id[target_id]
        # Ensure target ID's indexed object/view identity is as declared.
        if asset.get("object_id") != task.get("target_object_id", asset.get("object_id")) or asset.get("view") != target_view:
            raise ValueError(f"target identity mismatch for {target_id}.{target_view}")
        target_file, target_rgba = expected_output(asset)
        if task.get("expected_output_sha256") != target_file or task.get("expected_output_rgba_sha256") != target_rgba:
            raise ValueError(f"target current-index hashes disagree with replay manifest for {target_id}")
        for field in ("source_asset_id", "mask_asset_id", "texture_asset_id", "base_asset_id", "overlay_asset_id"):
            if field in task:
                srcid = task[field]
                view_field = {"source_asset_id": "source_view", "mask_asset_id": "mask_view",
                              "texture_asset_id": "texture_view", "base_asset_id": "base_view",
                              "overlay_asset_id": "overlay_view"}[field]
                sv = task.get(view_field)
                if srcid not in by_id:
                    # Let the per-task renderer record this as a mismatch and
                    # fall back to the exact target PNG so the full bounded
                    # pass still reports every task.
                    continue
                source_asset = by_id[srcid]
                if source_asset.get("view") != sv:
                    continue
                if (srcid, sv) in task_outputs:
                    input_paths[(srcid, sv)] = task_outputs[(srcid, sv)]
                else:
                    source_task = task_by_target.get(srcid)
                    sha = source_task.get("fallback_sha256") if source_task else None
                    if not source_task or not sha:
                        raise ValueError(f"no immutable retained input for dependency {srcid}.{sv}")
                    retained = retained_path(source_task, "fallback_external_source_path", "fallback_portable_ref")
                    verify_input(retained, sha, f"retained dependency {srcid}.{sv}")
                    input_paths[(srcid, sv)] = retained
        dest = output / asset["image"]["path"]
        task_error = None
        try:
            if task["op"] == "preserve_current":
                retained = retained_path(task, "fallback_external_source_path", "fallback_portable_ref")
                payload = verify_input(retained, task["fallback_sha256"], f"retained current {target_id}")
                image = Image.open(io.BytesIO(payload)).convert("RGBA")
            elif task["op"] == "copy_path":
                source = retained_path(task, "external_source_path", "source_portable_ref", "source_path")
                label = str(source)
                payload = verify_input(source, task["source_sha256"], label)
                image = Image.open(io.BytesIO(payload)).convert("RGBA")
            elif task["op"] == "copy":
                source_key = (task["source_asset_id"], task["source_view"])
                source_path = input_paths[source_key]
                payload = verify_input(source_path, task["source_sha256"], f"{source_key}")
                image = Image.open(io.BytesIO(payload)).convert("RGBA")
            elif task["op"] in {"component_crop", "atlas_crop"}:
                source_path = retained_path(task, "external_source_path", "source_portable_ref", "source_path")
                source_key = (source_path, task["source_sha256"])
                if source_key not in verified_source_hashes:
                    verify_input(source_path, task["source_sha256"], task.get("source_path", str(source_path)))
                    verified_source_hashes.add(source_key)
                image = None
                candidate_match = None
                primary = component_crop(source_path, task)
                primary_optimize = bool(task.get("png_optimize", False))
                if rgba_sha(primary) == target_rgba:
                    for optimize in (primary_optimize, not primary_optimize):
                        primary_buffer = io.BytesIO(); primary.save(primary_buffer, format="PNG", optimize=optimize)
                        primary_payload = primary_buffer.getvalue()
                        if sha_bytes(primary_payload) == target_file:
                            candidate_match = (primary, primary_payload, {"source": "declared-primary-recipe",
                                "bounds_xyxy": task.get("bounds"), "alpha_threshold": task.get("alpha_threshold"),
                                "preserve_alpha": task.get("preserve_alpha"), "resampling": task.get("resampling"),
                                "png_optimize": optimize})
                            break
                for candidate, optimize, resolution in (() if candidate_match else component_crop_candidates(source_path, task)):
                    if rgba_sha(candidate) != target_rgba:
                        continue
                    bio = io.BytesIO(); candidate.save(bio, format="PNG", optimize=optimize)
                    candidate_payload = bio.getvalue()
                    file_hash = sha_bytes(candidate_payload)
                    if file_hash == target_file:
                        candidate_match = (candidate, candidate_payload, resolution)
                        break
                if candidate_match is None:
                    raise ValueError("candidate resolver found no exact PNG+RGBA match")
                image, payload, resolution = candidate_match
                task["resolved_replay_parameters"] = resolution
                task["resolver_selection"] = "first deterministic candidate with exact PNG and RGBA hashes"
            else:
                image = render_task(task, input_paths, assets, output)
            if image.size != (256, 256):
                raise ValueError(f"unexpected dimensions {image.size}")
            # Crop operations already selected a PNG encoding by comparing
            # serialized bytes against the frozen target. Re-encoding here
            # with the task's default optimize flag can silently replace that
            # matched payload (RGBA remains equal while PNG SHA changes).
            if task["op"] not in {"copy", "copy_path", "preserve_current", "component_crop", "atlas_crop"}:
                bio = io.BytesIO(); image.save(bio, format="PNG", optimize=bool(task.get("png_optimize", False)))
                payload = bio.getvalue()
            actual_file, actual_rgba = sha_bytes(payload), rgba_sha(image)
            if actual_file != target_file or actual_rgba != target_rgba:
                raise ValueError(f"hash mismatch expected {target_file}/{target_rgba}, got {actual_file}/{actual_rgba}")
        except Exception as exc:
            task_error = f"{type(exc).__name__}: {exc}"
            mismatches.append({"id": task.get("id", target_id), "asset_id": target_id,
                               "object_id": task.get("target_object_id"), "view": target_view,
                               "op": task["op"], "reason": task_error,
                               "expected_output_sha256": target_file, "expected_output_rgba_sha256": target_rgba,
                               "source_path": task.get("source_path"), "source_sha256": task.get("source_sha256")})
            fallback_path = retained_path(task, "fallback_external_source_path", "fallback_portable_ref")
            payload = verify_input(fallback_path, task["fallback_sha256"], f"immutable fallback {target_id}")
            image = Image.open(io.BytesIO(payload)).convert("RGBA")
        actual_file, actual_rgba = sha_bytes(payload), rgba_sha(image)
        atomic_write(dest, payload)
        task_outputs[key] = dest
        input_paths[key] = dest
        replay_kind = ("immutable-copy-fallback" if task_error else
                       "immutable-copy-input" if task["op"] in {"copy_path", "preserve_current"} else
                       "derived-replay")
        report["tasks"].append({"id": task.get("id", target_id), "op": task["op"], "asset_id": target_id,
                                "view": target_view, "output_sha256": actual_file, "output_rgba_sha256": actual_rgba,
                                "replay_kind": replay_kind,
                                "output_path": asset["image"]["path"], "image_descriptor": asset["image"],
                                "input_sha256": {k: v for k, v in task.items() if k.endswith("_sha256")},
                                "fallback_sha256": task.get("fallback_sha256"),
                                "resolved_replay_parameters": task.get("resolved_replay_parameters")})
    report["tasks_completed"] = len(report["tasks"])
    report["mismatches_count"] = len(mismatches)
    report["derived_replay_tasks"] = sum(t["replay_kind"] == "derived-replay" for t in report["tasks"])
    report["immutable_copy_tasks"] = sum(t["replay_kind"] == "immutable-copy-input" for t in report["tasks"])
    report["preserved_current_tasks"] = sum(t["replay_kind"] in {"immutable-copy-input", "immutable-copy-fallback"} for t in report["tasks"])
    report_path = output / "replay-report.json"
    atomic_write(report_path, (json.dumps(report, indent=2) + "\n").encode())
    print(json.dumps({"output": output.as_posix(), "tasks_completed": report["tasks_completed"],
                      "assets_indexed": report["assets"], "view_sets_indexed": report["view_sets"],
                      "report": report_path.as_posix()}))

if __name__ == "__main__":
    main()
