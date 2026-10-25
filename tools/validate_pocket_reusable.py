#!/usr/bin/env python3
"""Validate Pocket Dungeon metadata, deduplication, and exact reconstructions.

Run with --self-test for independent renderer/error-detection fixtures. --report
writes explicit current-run evidence outside the source images. Missing six-view
coverage is reported separately and becomes fatal only with --require-six-views.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import struct
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACK = ROOT / "dungeon-crawler-tactics/Web/wwwroot/assets/style-packs/pocket-dungeon"
VIEWS = ("front", "top", "right", "left", "bottom", "rear")


def view_set_approved(group):
    qa = group.get("geometry_qa", {})
    status = qa.get("status") if isinstance(qa, dict) else None
    return bool(group.get("complete")) and (status is None or status in {"passed", "approved", "accepted", "verified"})


def contained(root, relative):
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise ValueError(f"Unsafe pack-relative path: {relative!r}")
    path = root / relative
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Path escapes pack: {relative}")
    return path


def digest(image):
    rgba = image.convert("RGBA")
    return hashlib.sha256(struct.pack(">II", rgba.width, rgba.height) + rgba.tobytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text())


def unique_records(records, key, label):
    result = {}
    for record in records:
        value = record.get(key)
        if not isinstance(value, str) or not value:
            raise ValueError(f"Missing {key} in {label}")
        if value in result:
            raise ValueError(f"Duplicate {key} {value!r} in {label}")
        result[value] = record
    return result


def view_reference(value):
    return value.get("asset_id") if isinstance(value, dict) else value


def check_rectangle(rectangle, size, label, xywh=False):
    if not isinstance(rectangle, (list, tuple)) or len(rectangle) != 4 or not all(isinstance(v, (int, float)) for v in rectangle):
        raise ValueError(f"Malformed rectangle: {label}")
    x, y, right, bottom = rectangle
    if xywh:
        right, bottom = x + right, y + bottom
    if x < 0 or y < 0 or right <= x or bottom <= y or right > size[0] or bottom > size[1]:
        raise ValueError(f"Rectangle outside image: {label}: {rectangle} within {size}")


def check_asset_geometry(pack, asset, image, source_sizes):
    anchor = asset.get("anchor_px")
    if isinstance(anchor, dict):
        anchor = [anchor.get("x"), anchor.get("y")]
    if not isinstance(anchor, list) or len(anchor) != 2 or not all(isinstance(v, (int, float)) for v in anchor):
        raise ValueError(f"Missing or malformed anchor: {asset['id']}")
    if not (0 <= anchor[0] <= image.width and 0 <= anchor[1] <= image.height):
        raise ValueError(f"Anchor outside PNG: {asset['id']}")
    provenance = asset["provenance"]
    calibration = provenance.get("source_cell_calibration")
    if asset.get("view") in VIEWS and calibration is not None:
        if (not isinstance(calibration, list) or len(calibration) != 2
                or not all(isinstance(value, (int, float)) and math.isfinite(value) and value > 0 for value in calibration)):
            raise ValueError(f"Malformed source cell calibration: {asset['id']}")
        if not math.isclose(calibration[0], calibration[1], rel_tol=1e-9, abs_tol=1e-12):
            raise ValueError(f"Anisotropic principal-view normalization: {asset['id']}")
    source = provenance.get("source_image")
    rectangle = provenance.get("source_rect")
    if isinstance(rectangle, list) and source and contained(pack, source).is_file():
        if source not in source_sizes:
            with Image.open(contained(pack, source)) as source_image:
                source_sizes[source] = source_image.size
        check_rectangle(rectangle, source_sizes[source], f"{asset['id']}/source_rect", xywh=True)
    atlas = provenance.get("source_atlas") or provenance.get("generated_atlas")
    if atlas and contained(pack, atlas).is_file():
        if atlas not in source_sizes:
            with Image.open(contained(pack, atlas)) as source_image:
                source_sizes[atlas] = source_image.size
        size = source_sizes[atlas]
        normalization = provenance.get("normalization", {})
        crop = provenance.get("crop_bounds_px", {})
        if normalization.get("cell_rect"):
            check_rectangle(normalization["cell_rect"], size, f"{asset['id']}/cell_rect", xywh=True)
        if isinstance(rectangle, dict):
            for key in ("alpha_bounds", "cell"):
                if rectangle.get(key):
                    check_rectangle(rectangle[key], size, f"{asset['id']}/{key}", xywh=True)
            for key in ("alpha_component_bounds_atlas_px", "cell_px"):
                if rectangle.get(key):
                    check_rectangle(rectangle[key], size, f"{asset['id']}/{key}")
        if isinstance(crop, dict) and crop.get("alpha_bounds_global"):
            check_rectangle(crop["alpha_bounds_global"], size, f"{asset['id']}/alpha_bounds_global")
        for component in normalization.get("component_groups", []):
            if component.get("bbox"):
                check_rectangle(component["bbox"], size, f"{asset['id']}/component bbox")
    normalization = provenance.get("normalization", {})
    for key in ("frame_size", "canvas", "canvas_px"):
        if key in normalization and tuple(normalization[key]) != image.size:
            raise ValueError(f"Normalization {key} does not match PNG: {asset['id']}")
    bbox = image.getchannel("A").getbbox()
    if asset.get("view") in VIEWS and bbox is None:
        raise ValueError(f"Empty generated principal view: {asset['id']}")
    return bbox


def image_info(root, info):
    path = contained(root, info["path"])
    image = Image.open(path).convert("RGBA")
    if (image.width, image.height) != (info["width"], info["height"]):
        raise ValueError(f"Dimension mismatch: {info['path']}")
    if "sha256" in info and hashlib.sha256(path.read_bytes()).hexdigest() != info["sha256"]:
        raise ValueError(f"PNG byte hash mismatch: {info['path']}")
    if "rgba_sha256" in info and digest(image) != info["rgba_sha256"]:
        raise ValueError(f"RGBA hash mismatch: {info['path']}")
    return image


def render(root, document, assets):
    canvas_spec = document["canvas"]
    canvas = Image.new("RGBA", (canvas_spec["width"], canvas_spec["height"]), tuple(canvas_spec.get("background", [0,0,0,0])))
    z_values = [layer["z"] for layer in document["layers"]]
    if z_values != sorted(z_values) or len(z_values) != len(set(z_values)):
        raise ValueError(f"Unordered or duplicate z values: {document['id']}")
    for layer in document["layers"]:
        asset = assets[layer["asset_id"]]
        if layer["path"] != asset["image"]["path"]:
            raise ValueError(f"Placement path does not match asset: {layer['asset_id']}")
        tile = Image.open(contained(root, layer["path"])).convert("RGBA")
        rotation = layer["rotation_deg"]
        if not isinstance(rotation, int) or rotation % 90:
            raise ValueError("Only integer right-angle rotations are lossless")
        if layer.get("scale", 1) != 1:
            raise ValueError("Exact reconstruction disallows resampling")
        if rotation % 360:
            tile = tile.rotate(-rotation, expand=True)
        x, y = layer["x"], layer["y"]
        if not isinstance(x, int) or not isinstance(y, int) or x >= canvas.width or y >= canvas.height or x+tile.width <= 0 or y+tile.height <= 0:
            raise ValueError(f"Out-of-bounds or noninteger placement: {layer['asset_id']}")
        blend = layer["blend"]
        if blend == "replace":
            canvas.paste(tile, (x,y))
        elif blend == "masked-replace":
            # Binary alpha ownership: preserve partial alpha and RGB exactly.
            mask = tile.getchannel("A").point(lambda alpha: 255 if alpha else 0)
            canvas.paste(tile, (x,y), mask)
        elif blend == "source-over":
            canvas.alpha_composite(tile, (x,y))
        else:
            raise ValueError(f"Unknown blend mode: {blend}")
    return canvas


def validate_procedural(pack, settings, assets):
    if not settings.get("recipe"):
        return {"status": "not-present"}
    recipe_path = contained(pack, settings["recipe"])
    preview_path = contained(pack, settings["preview"])
    for path, field in ((recipe_path, "recipe_sha256"), (preview_path, "preview_sha256")):
        if settings.get(field) and hashlib.sha256(path.read_bytes()).hexdigest() != settings[field]:
            raise ValueError(f"Procedural {field} mismatch")
    recipe = read_json(recipe_path)
    grid = recipe["grid"]
    width, height, size = grid["width"], grid["height"], grid["cell_size_px"]
    cells = {(cell["x"], cell["y"]): cell for cell in recipe["cells"]}
    if len(cells) != width * height or len(recipe["cells"]) != width * height:
        raise ValueError("Procedural grid has missing or duplicate cells")
    walkable = {point for point,cell in cells.items() if cell["walkable"]}
    entry, exit_cell = tuple(recipe["entry"]), tuple(recipe["exit"])
    reached = {entry}; pending = [entry]
    if entry not in walkable or exit_cell not in walkable:
        raise ValueError("Procedural entry/exit is not walkable")
    directions = {"north":(0,-1), "east":(1,0), "south":(0,1), "west":(-1,0)}
    while pending:
        x,y = pending.pop()
        for dx,dy in directions.values():
            neighbor = x+dx,y+dy
            if neighbor in walkable and neighbor not in reached:
                reached.add(neighbor); pending.append(neighbor)
    if reached != walkable:
        raise ValueError("Procedural walkable cells are disconnected")
    canvas = Image.new("RGBA", (width*size,height*size), tuple(recipe.get("background_rgba", [20,18,35,255])))
    convention = recipe.get("rotation_convention", settings.get("rotation_convention", "counterclockwise"))
    if convention not in {"clockwise", "counterclockwise"}:
        raise ValueError("Unknown procedural rotation convention")
    for (x,y),cell in cells.items():
        if x < 0 or y < 0 or x >= width or y >= height:
            raise ValueError("Procedural cell outside declared grid")
        expected = [name for name,(dx,dy) in directions.items() if (x+dx,y+dy) in walkable] if cell["walkable"] else []
        if set(expected) != set(cell["connections"]):
            raise ValueError(f"Procedural connection mismatch: {(x,y)}")
        if not cell["walkable"]:
            continue
        asset = assets[cell["asset_id"]]
        if cell["path"] != asset["image"]["path"] or cell["position_px"] != [x*size,y*size]:
            raise ValueError("Procedural tile reference or position mismatch")
        tile = Image.open(contained(pack,cell["path"])).convert("RGBA")
        if tile.size != (size,size) or cell["rotation_deg"] not in (0,90,180,270):
            raise ValueError("Procedural tile dimensions or rotation invalid")
        angle = cell["rotation_deg"] * (-1 if convention == "clockwise" else 1)
        canvas.alpha_composite(tile.rotate(angle), (x*size,y*size))
    for item in recipe.get("objects", []):
        if tuple(item["cell"]) not in walkable or item["path"] != assets[item["asset_id"]]["image"]["path"]:
            raise ValueError("Procedural object placement is invalid")
        if item.get("resampling") != "nearest" or item.get("rotation_deg") != 0:
            raise ValueError("Unsupported procedural object transform")
        image = Image.open(contained(pack,item["path"])).convert("RGBA")
        image = image.resize(tuple(item["render_size_px"]), Image.Resampling.NEAREST)
        canvas.alpha_composite(image,tuple(item["position_px"]))
    original = Image.open(preview_path).convert("RGBA")
    if canvas.size != original.size or canvas.tobytes() != original.tobytes():
        raise ValueError("Procedural sample does not match its recorded recipe")
    return {"status": "passed", "seed": recipe["seed"], "walkable_cells": len(walkable),
        "all_walkable_cells_connected": True, "entry_reaches_exit": True,
        "differing_pixels": 0, "rgba_sha256": digest(canvas), "limitations": recipe["limitations"]}


def validate(pack, require_views=False):
    index = read_json(pack / "reusable/index.json")
    from view_review_contract import load_review, POLICY
    review_report = load_review(pack, index,
        required=require_views and index.get('view_review_policy') == POLICY)
    legacy_review_report = load_review(pack, index, legacy=True,
        required=require_views and index.get('legacy_view_review_policy') == POLICY)
    assets = {}
    provenance_record = index.get("archive", {}).get("external_provenance_manifest")
    external_provenance = {}
    if provenance_record:
        external_provenance = {item["path"]: item for item in read_json(contained(pack, provenance_record)).get("external_provenance", [])}
    verified_provenance = {}
    source_sizes = {}
    view_sets = unique_records(index.get("view_sets", []), "object_id", "catalog view_sets")
    for object_id, group in view_sets.items():
        if set(group.get("views", {})) != set(VIEWS):
            raise ValueError(f"View set must declare exactly six principal keys: {object_id}")
        if group.get("complete") and not view_set_approved(group):
            raise ValueError(f"False geometry approval: {object_id}")
    image_paths = {}
    metadata_paths = {}
    pixel_hashes = {}
    visible_hashes = {}
    missing_views = []
    warnings = []
    boundary_findings = []
    for asset in index["assets"]:
        asset_id = asset["id"]
        if asset_id in assets:
            raise ValueError(f"Duplicate asset id: {asset_id}")
        assets[asset_id] = asset
        if not asset.get("name") or not asset.get("tags"):
            raise ValueError(f"Missing name/tags: {asset_id}")
        if not asset.get("provenance", {}).get("method"):
            raise ValueError(f"Missing provenance: {asset_id}")
        for field, hash_field in (("source_image", "source_sha256"), ("source_atlas", "source_atlas_sha256"), ("generated_atlas", "generated_atlas_sha256")):
            reference = asset["provenance"].get(field)
            if not reference:
                continue
            source_path = contained(pack, reference)
            expected_hash = asset["provenance"].get(hash_field)
            if field == "source_image":
                expected_hash = expected_hash or asset["provenance"].get("source_image_sha256")
            if not source_path.is_file():
                external = external_provenance.get(reference)
                if external is None or (expected_hash and external.get("sha256") != expected_hash):
                    raise ValueError(f"Missing undeclared provenance source: {reference}")
            elif expected_hash:
                if reference not in verified_provenance:
                    verified_provenance[reference] = hashlib.sha256(source_path.read_bytes()).hexdigest()
                if verified_provenance[reference] != expected_hash:
                    raise ValueError(f"Provenance hash mismatch: {reference}")
        for source in asset["provenance"].get("referenced_source_images", []):
            reference = source["path"]
            source_path = contained(pack, reference)
            if not source_path.is_file():
                external = external_provenance.get(reference)
                if external is None or external.get("sha256") != source.get("sha256"):
                    raise ValueError(f"Missing referenced generation source: {reference}")
            elif source.get("sha256"):
                if reference not in verified_provenance:
                    verified_provenance[reference] = hashlib.sha256(source_path.read_bytes()).hexdigest()
                if verified_provenance[reference] != source["sha256"]:
                    raise ValueError(f"Referenced generation source hash mismatch: {reference}")
        image = image_info(pack, asset["image"])
        bbox = check_asset_geometry(pack, asset, image, source_sizes)
        if asset.get("view") in VIEWS:
            if bbox and (bbox[0] == 0 or bbox[1] == 0 or bbox[2] == image.width or bbox[3] == image.height):
                boundary_findings.append({"id": asset_id, "alpha_bounds": bbox, "reason": "Visible alpha touches frame boundary; review for clipped geometry."})
            visible = np.array(image)
            visible[visible[:, :, 3] == 0] = 0
            visible_hashes[asset_id] = digest(Image.fromarray(visible, "RGBA"))
        expected_sidecar = str(Path(asset["image"]["path"]).with_suffix(".json"))
        metadata_path = asset.get("metadata_path", expected_sidecar)
        sidecar = read_json(contained(pack, metadata_path))
        if sidecar != asset:
            raise ValueError(f"Sidecar/catalog mismatch: {asset_id}")
        if asset["image"]["path"] in image_paths:
            raise ValueError(f"Multiple asset ids claim one PNG: {asset_id} and {image_paths[asset['image']['path']]}")
        if metadata_path in metadata_paths:
            raise ValueError(f"Multiple asset ids claim one sidecar: {asset_id}")
        image_paths[asset["image"]["path"]] = asset_id
        metadata_paths[metadata_path] = asset_id
        pixel_hashes.setdefault(digest(image), []).append(asset_id)
        if asset["kind"] == "reconstruction_patch" and asset.get("procedural",{}).get("eligible"):
            raise ValueError(f"Residual incorrectly advertised as procedural: {asset_id}")
        views = asset.get("views", {})
        if asset.get("view") in VIEWS and asset.get("object_id"):
            group = view_sets.get(asset["object_id"], {})
            reference = view_reference(group.get("views", {}).get(asset["view"]))
            if reference != asset_id:
                raise ValueError(f"Generated leaf view is absent from its view set: {asset_id}")
            if not views:
                continue
        if views.get("applicable"):
            absent = [v for v in VIEWS if views.get(v, {}).get("status") in {None,"missing"} or not views.get(v,{}).get("asset_id")]
            if absent or not views.get("complete"):
                missing_views.append({"id": asset_id, "missing": absent,
                    "reason": views.get("reason", "Missing or unapproved principal views.")})
                if absent and views.get("complete"):
                    raise ValueError(f"False six-view completeness: {asset_id}")
        elif not views.get("reason"):
            raise ValueError(f"Non-applicable views need a reason: {asset_id}")
    for asset in assets.values():
        views = asset.get("views", {})
        if views.get("applicable"):
            for view in VIEWS:
                ref = views.get(view,{}).get("asset_id")
                if ref and ref not in assets:
                    raise ValueError(f"Missing {view} asset {ref} for {asset['id']}")
                if ref:
                    target = assets[ref]
                    if target.get("view") != view:
                        raise ValueError(f"Wrong view label for {ref}: expected {view}")
                    if target.get("object_id") != asset.get("object_id", asset["id"]):
                        raise ValueError(f"Principal-view reference changes object identity: {asset['id']} -> {ref}")
    view_aliases = []
    for object_id, group in view_sets.items():
        hashes = {}
        scales = []
        if object_id not in assets:
            raise ValueError(f"View set lacks its source object: {object_id}")
        for view in VIEWS:
            ref = view_reference(group["views"][view])
            if group.get("complete") and (ref not in assets or assets[ref].get("view") != view):
                raise ValueError(f"Incomplete or mismatched view set: {object_id}/{view}")
            if ref:
                if ref not in assets or assets[ref].get("view") != view or assets[ref].get("object_id") != object_id:
                    raise ValueError(f"View child belongs to the wrong object or direction: {object_id}/{view}")
                hashes.setdefault(visible_hashes[ref], []).append(view)
                provenance = assets[ref]["provenance"]
                normalization = provenance.get("normalization", {})
                scale = normalization.get("scale", normalization.get("shared_scale", normalization.get("shared_scale_per_object")))
                if scale is None and isinstance(provenance.get("crop_bounds_px"), dict):
                    scale = provenance["crop_bounds_px"].get("shared_scale")
                if scale is not None:
                    scales.append(float(scale))
        if scales and max(scales) - min(scales) > 1e-9:
            raise ValueError(f"Principal views use inconsistent normalization scales: {object_id}")
        absent = [view for view in VIEWS if not view_reference(group["views"][view])]
        if (absent or not view_set_approved(group)) and not any(item["id"] == object_id for item in missing_views):
            missing_views.append({"id": object_id, "missing": absent, "reason": "View set is not marked complete."})
        for same_views in hashes.values():
            if len(same_views) > 1:
                declarations = group.get("symmetry", [])
                declared = next((item for item in declarations if isinstance(item, dict) and set(same_views).issubset(item.get("views", [])) and item.get("reason")), None)
                view_aliases.append({"object_id": object_id, "views": same_views, "declared_symmetry": bool(declared), "reason": declared.get("reason") if declared else "Identical visible pixels across directions need review."})
    duplicate_groups = [ids for ids in pixel_hashes.values() if len(ids) > 1]
    # Pre-existing aliases are reported, not rewritten; newly generated duplicate
    # residuals are a build defect because they should share one asset reference.
    for group in duplicate_groups:
        new_residuals = [i for i in group if assets[i]["kind"] == "reconstruction_patch" and assets[i].get("provenance", {}).get("method") == "residual"]
        if len(new_residuals) > 1:
            raise ValueError(f"Duplicate residual PNGs: {new_residuals}")
    results = []
    map_ids = set()
    for entry in index["maps"]:
        document = read_json(contained(pack, entry["file"]))
        if entry["id"] != document["id"] or entry["source"] != document["source"]["path"] or entry["kind"] != document["kind"]:
            raise ValueError(f"Map entry/document mismatch: {entry['id']}")
        if document["id"] in map_ids:
            raise ValueError(f"Duplicate map id: {document['id']}")
        map_ids.add(document["id"])
        if not document.get("pixel_exact"):
            warnings.append(f"Non-exact layout skipped for pixel comparison: {document['id']}")
            continue
        original = image_info(pack, document["source"])
        reconstructed = render(pack, document, assets)
        if original.size != reconstructed.size:
            raise ValueError(f"Source/canvas dimensions differ: {document['id']}")
        different = int(np.count_nonzero(np.any(np.asarray(original) != np.asarray(reconstructed), axis=2)))
        if different:
            raise ValueError(f"Reconstruction mismatch: {document['id']}: {different} pixels")
        expected = document.get("verification",{}).get("rgba_sha256")
        if expected and expected != digest(reconstructed):
            raise ValueError(f"Map verification hash mismatch: {document['id']}")
        semantic_count = sum(layer["role"] == "semantic" for layer in document["layers"])
        residual_count = sum(layer["role"] == "residual" for layer in document["layers"])
        if semantic_count + residual_count != len(document["layers"]):
            raise ValueError(f"Unknown reconstruction layer role: {document['id']}")
        if any(layer["role"] == "semantic" and assets[layer["asset_id"]]["kind"] == "reconstruction_patch" for layer in document["layers"]):
            raise ValueError(f"Residual patch mislabeled as semantic: {document['id']}")
        statistics = document.get("statistics",{})
        if statistics.get("semantic_placement_count",semantic_count) != semantic_count or statistics.get("residual_placement_count",residual_count) != residual_count:
            raise ValueError(f"Inaccurate placement statistics: {document['id']}")
        if document["kind"] != "composition":
            for layer in document["layers"]:
                if layer["role"] == "residual":
                    info = assets[layer["asset_id"]]["image"]
                    if assets[layer["asset_id"]].get("provenance", {}).get("method") == "residual" and (info["width"] > 64 or info["height"] > 64):
                        raise ValueError(f"Oversized generated residual tile: {document['id']}")
                    if info["width"] >= original.width and info["height"] >= original.height:
                        patch = Image.open(contained(pack, info["path"])).convert("RGBA")
                        # A source smaller than64px can have a single disjoint
                        # remainder patch. Reject a complete visible source copy,
                        # while allowing invisible RGB and genuinely uncovered pixels.
                        source_pixels = np.asarray(original)
                        patch_pixels = np.asarray(patch)[:original.height,:original.width]
                        visible = source_pixels[:,:,3] > 0
                        if np.any(visible) and np.array_equal(patch_pixels[visible], source_pixels[visible]):
                            raise ValueError(f"Whole-image/background residual shortcut: {document['id']}")
        results.append({"id": document["id"], "source": document["source"]["path"],
            "map_sha256": hashlib.sha256(contained(pack, entry["file"]).read_bytes()).hexdigest(),
            "rgba_sha256": digest(reconstructed), "differing_pixels": different,
            "semantic_placements": semantic_count, "residual_placements": residual_count})
    if require_views and missing_views:
        raise ValueError(f"{len(missing_views)} physical assets still lack six principal views")
    undeclared_aliases = [finding for finding in view_aliases if not finding["declared_symmetry"]]
    if undeclared_aliases:
        warnings.append(f"{len(undeclared_aliases)} principal-view pixel aliases require symmetry review.")
        if require_views:
            raise ValueError(f"Undeclared identical principal views: {undeclared_aliases}")
    if boundary_findings:
        warnings.append(f"{len(boundary_findings)} generated views touch frame boundaries; review clipping.")
    procedural = validate_procedural(pack, index.get("procedural", {}), assets)
    return {"status": "passed", "schema_version": 1, "assets_checked": len(assets), "procedural_validation": procedural,
        "independent_view_review": review_report['statistics'] if review_report else None,
        "targeted_legacy_view_review": legacy_review_report['statistics'] if legacy_review_report else None,
        "maps_pixel_exact": len(results), "maps": results,
        "duplicate_pixel_groups": duplicate_groups, "missing_six_view_count": len(missing_views),
        "view_pixel_aliases": view_aliases, "view_boundary_findings": boundary_findings,
        "missing_six_views": missing_views, "warnings": warnings,
        "limitations": "Pixel fidelity and metadata validity do not certify inferred hidden surfaces or procedural seam quality."}


def self_test():
    checks = []
    with tempfile.TemporaryDirectory(prefix="pocket-reconstruct-test-") as directory:
        root = Path(directory)
        base = Image.new("RGBA", (3,2), (33,44,55,0))
        base.save(root/"base.png")
        sprite = Image.new("RGBA", (1,1), (101,102,103,17))
        sprite.save(root/"sprite.png")
        assets = {"base":{"image":{"path":"base.png"}},"sprite":{"image":{"path":"sprite.png"}}}
        document = {"id":"fixture", "canvas":{"width":3,"height":2},"layers":[
            {"asset_id":"base","path":"base.png","x":0,"y":0,"z":0,"rotation_deg":0,"scale":1,"blend":"replace"},
            {"asset_id":"sprite","path":"sprite.png","x":1,"y":1,"z":1,"rotation_deg":0,"scale":1,"blend":"masked-replace"}]}
        result = render(root, document, assets)
        assert result.getpixel((0,0)) == (33,44,55,0), "Invisible RGB must survive replace"
        assert result.getpixel((1,1)) == (101,102,103,17), "Partial alpha must not blend twice"
        checks += ["hidden-alpha RGB preservation", "partial-alpha masked replacement"]
        document["layers"][1]["blend"] = "source-over"
        expected = base.copy(); expected.alpha_composite(sprite,(1,1))
        assert render(root,document,assets).tobytes() == expected.tobytes()
        checks.append("source-over compositing")
        asymmetric = Image.new("RGBA",(2,1)); asymmetric.putdata([(1,2,3,255),(4,5,6,255)]); asymmetric.save(root/"sprite.png")
        document["layers"][1].update(x=2,y=0,rotation_deg=90,blend="replace")
        rotated = render(root,document,assets)
        assert rotated.getpixel((2,0)) == (1,2,3,255) and rotated.getpixel((2,1)) == (4,5,6,255)
        checks.append("clockwise right-angle rotation")
        for change in ({"x":3},{"rotation_deg":45},{"scale":2}):
            saved = document["layers"][1].copy(); document["layers"][1].update(change)
            try:
                render(root,document,assets)
            except ValueError:
                pass
            else:
                raise AssertionError(f"Invalid placement accepted: {change}")
            document["layers"][1] = saved
        checks.append("invalid bounds, rotation, and resampling rejected")
        try:
            contained(root,"../outside.png")
        except ValueError:
            pass
        else:
            raise AssertionError("Traversal was accepted")
        checks.append("path traversal rejected")
        try:
            image_info(root,{"path":"base.png","width":3,"height":2,"sha256":"0"*64})
        except ValueError:
            pass
        else:
            raise AssertionError("Corrupted hash accepted")
        checks.append("tampered PNG hash rejected")
        fixture_assets = []
        for number, name in enumerate(("object", *VIEWS)):
            image = Image.new("RGBA", (3, 3))
            image.putpixel((1, 1), (number + 1, 20, 30, 255))
            image.save(root / f"{name}.png")
            asset = {"id": name, "name": name, "kind": "sprite", "tags": ["fixture"],
                     "image": {"path": f"{name}.png", "width": 3, "height": 3},
                     "metadata_path": f"{name}.json", "anchor_px": [1, 1],
                     "provenance": {"method": "generated", "source_image": "object.png"}}
            if name == "object":
                asset["views"] = {"applicable": True, "complete": True,
                    **{view: {"status": "generated", "asset_id": view} for view in VIEWS}}
            else:
                asset.update(object_id="object", view=name)
            fixture_assets.append(asset)
        fixture_index = {"assets": fixture_assets, "maps": [], "view_sets": [{"object_id": "object", "complete": True, "views": {view: view for view in VIEWS}}]}
        (root / "reusable").mkdir()

        def save_fixture():
            for asset in fixture_assets:
                (root / asset["metadata_path"]).write_text(json.dumps(asset))
            (root / "reusable/index.json").write_text(json.dumps(fixture_index))

        save_fixture()
        validate(root, require_views=True)
        saved_ref = fixture_index["view_sets"][0]["views"].pop("rear")
        save_fixture()
        try:
            validate(root)
        except ValueError as exc:
            assert "six principal keys" in str(exc)
        else:
            raise AssertionError("Incomplete view key list accepted")
        fixture_index["view_sets"][0]["views"]["rear"] = saved_ref
        fixture_assets[1]["object_id"] = "wrong-object"
        save_fixture()
        try:
            validate(root)
        except ValueError:
            pass
        else:
            raise AssertionError("Wrong child object identity accepted")
        fixture_assets[1]["object_id"] = "object"
        (root / "rear.png").write_bytes((root / "front.png").read_bytes())
        save_fixture()
        aliases = validate(root)["view_pixel_aliases"]
        assert len(aliases) == 1 and not aliases[0]["declared_symmetry"]
        try:
            validate(root, require_views=True)
        except ValueError as exc:
            assert "Undeclared identical" in str(exc)
        else:
            raise AssertionError("Undeclared symmetric view alias accepted in strict mode")
        fixture_index["view_sets"][0]["symmetry"] = [{"views": ["front", "rear"], "reason": "Synthetic symmetric fixture"}]
        save_fixture()
        assert validate(root, require_views=True)["view_pixel_aliases"][0]["declared_symmetry"]
        checks += ["six principal view keys required", "view object identity enforced", "identical directions require declared symmetry in strict mode"]
    return checks


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack",type=Path,default=DEFAULT_PACK)
    parser.add_argument("--report",type=Path)
    parser.add_argument("--self-test",action="store_true")
    parser.add_argument("--require-six-views",action="store_true")
    args=parser.parse_args()
    tests=self_test() if args.self_test else []
    result=validate(args.pack.resolve(),args.require_six_views)
    result["renderer_self_tests"]=tests
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k not in {"maps","missing_six_views"}},indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
