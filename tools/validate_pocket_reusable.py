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


def file_sha256(path, verified=None):
    path = Path(path)
    if verified is not None and path.as_posix() in verified:
        return verified[path.as_posix()]
    value = hashlib.sha256(path.read_bytes()).hexdigest()
    if verified is not None:
        verified[path.as_posix()] = value
    return value


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


def crop_alpha_bounds_xyxy(crop, label):
    """Return recorded alpha bounds as XYXY, honoring an explicit encoding.

    Historical crop records without a format declaration use XYXY. XYWH is
    accepted only when explicitly declared (or when the field name itself is
    alpha_bounds_global_xywh); this keeps legacy records stable and prevents
    guessing based on whether one interpretation happens to fit an atlas.
    """
    if "alpha_bounds_global_xywh" in crop:
        bounds = crop["alpha_bounds_global_xywh"]
        declared = crop.get("coordinate_format", "xywh")
        if declared != "xywh":
            raise ValueError(f"Conflicting alpha-bounds field and coordinate format: {label}")
        if (not isinstance(bounds, (list, tuple)) or len(bounds) != 4
                or not all(isinstance(value, (int, float)) for value in bounds)):
            raise ValueError(f"Malformed alpha bounds: {label}")
        x, y, width, height = bounds
        return [x, y, x + width, y + height]
    bounds = crop.get("alpha_bounds_global")
    if bounds is None:
        return None
    coordinate_format = crop.get("coordinate_format", "xyxy")
    if coordinate_format not in {"xyxy", "xywh"}:
        raise ValueError(f"Unknown alpha-bounds coordinate format for {label}: {coordinate_format!r}")
    if coordinate_format == "xywh":
        if (not isinstance(bounds, (list, tuple)) or len(bounds) != 4
                or not all(isinstance(value, (int, float)) for value in bounds)):
            raise ValueError(f"Malformed alpha bounds: {label}")
        x, y, width, height = bounds
        return [x, y, x + width, y + height]
    return bounds


def validate_normalization_records(records, source_size, label):
    """Validate the historical list-form candidate normalization manifest.

    This is evidence about earlier candidates, not the active output transform;
    candidate files may have been pruned after the generated atlas and emitted
    PNG were retained. Bounds and scale arithmetic remain checkable here.
    """
    if not isinstance(records, list):
        raise ValueError(f"Malformed normalization history: {label}")
    for number, record in enumerate(records):
        item_label = f"{label}/normalization[{number}]"
        if not isinstance(record, dict):
            raise ValueError(f"Malformed normalization history record: {item_label}")
        view = record.get("view")
        if view not in VIEWS:
            raise ValueError(f"Unknown normalization history view: {item_label}")
        check_rectangle(record.get("raw_bbox"), source_size, f"{item_label}/raw_bbox")
        raw_dimensions = record.get("raw_dimensions")
        render_size = record.get("render_size")
        for name, dimensions in (("raw_dimensions", raw_dimensions), ("render_size", render_size)):
            if (not isinstance(dimensions, list) or len(dimensions) != 2
                    or not all(isinstance(value, int) and not isinstance(value, bool) and value > 0
                               for value in dimensions)):
                raise ValueError(f"Malformed {name}: {item_label}")
        bbox = record["raw_bbox"]
        if raw_dimensions != [bbox[2] - bbox[0], bbox[3] - bbox[1]]:
            raise ValueError(f"Normalization raw dimensions disagree with bounds: {item_label}")
        scale = record.get("uniform_scale")
        if not isinstance(scale, (int, float)) or not math.isfinite(scale) or scale <= 0:
            raise ValueError(f"Malformed historical uniform scale: {item_label}")
        if any(abs(round(length * scale) - actual) > 1
               for length, actual in zip(raw_dimensions, render_size)):
            raise ValueError(f"Historical normalization scale disagrees with render size: {item_label}")
        threshold = record.get("threshold_alpha")
        if not isinstance(threshold, int) or isinstance(threshold, bool) or not 0 <= threshold <= 255:
            raise ValueError(f"Malformed historical alpha threshold: {item_label}")
        anchor = record.get("anchor_px")
        if (not isinstance(anchor, list) or len(anchor) != 2
                or not all(isinstance(value, int) and not isinstance(value, bool) for value in anchor)):
            raise ValueError(f"Malformed historical anchor: {item_label}")
        candidate_path = record.get("candidate_path")
        candidate_hash = record.get("candidate_sha256")
        if not isinstance(candidate_path, str) or not candidate_path:
            raise ValueError(f"Missing historical candidate path: {item_label}")
        if (not isinstance(candidate_hash, str) or len(candidate_hash) != 64
                or any(character not in "0123456789abcdef" for character in candidate_hash.lower())):
            raise ValueError(f"Malformed historical candidate hash: {item_label}")


def normalization_parameters(provenance, label):
    value = provenance.get("normalization", {})
    if isinstance(value, dict):
        return value
    if isinstance(value, list):
        # The list form is a historical per-candidate record, validated against
        # the source atlas separately; it is not an active parameter mapping.
        return {}
    raise ValueError(f"Malformed normalization metadata: {label}")


def normalization_input_group(pack, provenance, external_provenance, label):
    normalization = provenance.get("normalization", {})
    if not isinstance(normalization, dict) or "input_group" not in normalization:
        return None
    group = normalization["input_group"]
    required = {"schema_version", "method", "recipe_id", "source_atlas", "source_atlas_sha256",
        "cell_grid", "alpha_threshold_exclusive", "component_connectivity", "minimum_component_area_px",
        "edge_touch_margin_px", "component_selection", "cell_calibration", "shared_scale_formula", "resampling"}
    if not isinstance(group, dict) or set(group) != required:
        raise ValueError(f"Malformed normalization input_group schema: {label}")
    if (group["schema_version"] != 1
            or group["method"] != "process_object_local_cells_shared_scale"
            or group["recipe_id"] != "object-local-cell-alpha-components-shared-scale-v1"):
        raise ValueError(f"Unsupported normalization input_group method: {label}")
    atlas = provenance.get("generated_atlas") or provenance.get("source_atlas")
    if atlas != group["source_atlas"]:
        raise ValueError(f"Normalization input_group atlas does not match provenance: {label}")
    expected_hash = provenance.get("generated_atlas_sha256") or provenance.get("source_atlas_sha256")
    if expected_hash != group["source_atlas_sha256"]:
        raise ValueError(f"Normalization input_group atlas hash does not match provenance: {label}")
    atlas_path = contained(pack, atlas)
    actual_hash = (hashlib.sha256(atlas_path.read_bytes()).hexdigest() if atlas_path.is_file()
                   else external_provenance.get(atlas, {}).get("sha256"))
    if actual_hash != group["source_atlas_sha256"]:
        raise ValueError(f"Unverified normalization input_group atlas: {label}")
    calibration = provenance.get("source_cell_calibration")
    if calibration != group["cell_calibration"]:
        raise ValueError(f"Normalization input_group calibration does not match provenance: {label}")
    grid = group["cell_grid"]
    if (not isinstance(grid, dict) or set(grid) != {"columns", "rows", "row_index", "cell_size_px"}
            or grid["columns"] != 6 or grid["rows"] != 6 or grid["row_index"] not in {2, 3}
            or grid["cell_size_px"] != [256, 171]):
        raise ValueError(f"Unsupported normalization input_group cell grid: {label}")
    if (group["alpha_threshold_exclusive"] != 32 or group["component_connectivity"] != 4
            or group["minimum_component_area_px"] != 24 or group["edge_touch_margin_px"] != 1
            or group["component_selection"] != "non-edge-touching-at-least-1-percent-largest-fallback-largest"
            or group["cell_calibration"] != [1.0, 1.0]
            or group["shared_scale_formula"] != "204/max-width-or-height-of-all-six-extracted-cells-after-calibration"
            or group["resampling"] != "nearest"):
        raise ValueError(f"Unsupported normalization input_group parameters: {label}")
    # Full canonical contents form the comparison cohort. Per-set row_index is
    # stable across views; per-view cell column is intentionally absent.
    return ("declared-input-group", json.dumps(group, sort_keys=True, separators=(",", ":")))


def _matching_report_rows(document, asset):
    asset_id, object_id, view = asset.get("id"), asset.get("object_id"), asset.get("view")
    found = []
    def walk(node):
        if isinstance(node, dict):
            direct_id = node.get("asset_id", node.get("id"))
            identity_match = direct_id == asset_id or (node.get("object_id") == object_id
                and node.get("view", node.get("direction")) == view)
            has_report_fields = any(key in node for key in (
                "source_atlas", "source_atlas_sha256", "png_sha256", "output_sha256",
                "rgba_sha256", "decoded_crop_xyxy", "decoded_bounds_xyxy"))
            if identity_match and has_report_fields:
                found.append(node)
                return
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)
    walk(document)
    return found


def _check_hash_bound_report(pack, path_field, hash_field, expected_path, expected_hash,
                             verified_provenance, label):
    path = contained(pack, expected_path)
    if not path.is_file() or file_sha256(path, verified_provenance) != expected_hash:
        raise ValueError(f"Normalization execution report hash mismatch: {label}/{path_field}")
    return read_json(path)


def _check_executed_replay_binding(pack, evidence, asset, verified_provenance, label):
    report = _check_hash_bound_report(pack, "execution_report_path", "execution_report_sha256",
        evidence["execution_report_path"], evidence["execution_report_sha256"], verified_provenance, label)
    if report.get("failures") not in (None, []):
        raise ValueError(f"Normalization execution report contains failures: {label}")
    if all(key in report for key in ("processed", "expected", "count")) and not (
            report["processed"] == report["expected"] == report["count"]):
        raise ValueError(f"Normalization execution report is incomplete: {label}")
    rows = _matching_report_rows(report, asset)
    if len(rows) != 1:
        raise ValueError(f"Normalization execution report row missing or ambiguous: {label}")
    row = rows[0]
    checks = (("source_atlas", evidence["atlas_path"]),
              ("source_atlas_sha256", evidence["atlas_sha256"]))
    for key, expected in checks:
        if key in row and row[key] != expected:
            raise ValueError(f"Normalization execution report {key} mismatch: {label}")
    if row.get("source_atlas") is None or row.get("source_atlas_sha256") is None:
        raise ValueError(f"Normalization execution report lacks atlas binding: {label}")
    crop = row.get("decoded_crop_xyxy", row.get("decoded_bounds_xyxy", row.get("crop_bounds_xyxy")))
    if crop is not None and crop != evidence["crop_bounds_xyxy"]:
        raise ValueError(f"Normalization execution report crop mismatch: {label}")
    output_sha = row.get("png_sha256", row.get("output_sha256", row.get("active_output_sha256")))
    output_rgba = row.get("rgba_sha256", row.get("active_output_rgba_sha256"))
    if evidence.get("output_report_path"):
        output_report = _check_hash_bound_report(pack, "output_report_path", "output_report_sha256",
            evidence["output_report_path"], evidence["output_report_sha256"], verified_provenance, label)
        output_rows = _matching_report_rows(output_report, asset)
        if len(output_rows) != 1:
            raise ValueError(f"Normalization output report row missing or ambiguous: {label}")
        output_row = output_rows[0]
        output_sha = output_row.get("sha256", output_row.get("png_sha256", output_row.get("output_sha256")))
        output_rgba = output_row.get("rgba_sha256", output_row.get("active_output_rgba_sha256"))
    if output_sha != evidence["active_output_sha256"] or output_rgba != evidence["active_output_rgba_sha256"]:
        raise ValueError(f"Normalization execution report output hash mismatch: {label}")


def affine_calibration_basis(pack, asset, provenance, normalization, label, verified_provenance=None,
                             external_provenance=None):
    """Check an explicitly reviewed affine projection, never infer one.

    This is reserved for reviewed orthographic illustrations whose end and side
    axes were intentionally fitted independently. It verifies a hash-bound
    recipe row and current output/source/atlas bindings, then checks the exact
    per-axis resize arithmetic. Legacy assets remain in the strict shared-scale
    cohort unless this complete evidence object is present.
    """
    evidence = normalization.get("calibration_evidence")
    if evidence is None:
        return None
    fields = {"schema_version", "method", "recipe_path", "recipe_sha256", "object_id", "view",
        "source_path", "source_sha256", "atlas_path", "atlas_sha256", "active_output_sha256",
        "active_output_rgba_sha256", "crop_bounds_xyxy", "resized_dimensions_px", "scale_x", "scale_y",
        "target_dimensions_px", "review_record_path", "review_record_sha256", "review_status"}
    optional = {"source_recipe_path", "source_recipe_sha256", "final_uniform_scale",
        "final_canvas_bounds_xyxy", "purpose"}
    if (not isinstance(evidence, dict) or not fields.issubset(evidence)
            or set(evidence) - fields - optional):
        raise ValueError(f"Malformed affine calibration evidence: {label}")
    if (evidence["schema_version"] != 1 or evidence["method"] != "reviewed-axis-affine-v1"
            or evidence["object_id"] != asset.get("object_id") or evidence["view"] != asset.get("view")
            or evidence["review_status"] != "approved"):
        raise ValueError(f"Affine calibration evidence is not an approved asset/view match: {label}")
    recipe_path = contained(pack, evidence["recipe_path"])
    if not recipe_path.is_file() or file_sha256(recipe_path, verified_provenance) != evidence["recipe_sha256"]:
        raise ValueError(f"Unverified affine calibration recipe: {label}")
    recipe = read_json(recipe_path)
    review_path = contained(pack, evidence["review_record_path"])
    if (not review_path.is_file()
            or file_sha256(review_path, verified_provenance) != evidence["review_record_sha256"]):
        raise ValueError(f"Unverified affine calibration review record: {label}")
    if "source_recipe_path" in evidence or "source_recipe_sha256" in evidence:
        source_recipe_path = evidence.get("source_recipe_path")
        source_recipe_hash = evidence.get("source_recipe_sha256")
        if not isinstance(source_recipe_path, str) or not isinstance(source_recipe_hash, str):
            raise ValueError(f"Malformed affine source recipe reference: {label}")
        source_recipe_file = contained(pack, source_recipe_path)
        if (not source_recipe_file.is_file()
                or file_sha256(source_recipe_file, verified_provenance) != source_recipe_hash):
            raise ValueError(f"Affine source recipe hash mismatch: {label}")
    matching = []
    def visit(node):
        if isinstance(node, dict):
            if (node.get("object_id", node.get("id")) == evidence["object_id"]
                    and node.get("view", node.get("direction")) == evidence["view"]):
                matching.append(node)
            for child in node.values():
                visit(child)
        elif isinstance(node, list):
            for child in node:
                visit(child)
    visit(recipe)
    if len(matching) != 1:
        raise ValueError(f"Affine calibration recipe row is missing or ambiguous: {label}")
    row = matching[0]
    source_path = provenance.get("source_rect_image") or provenance.get("source_image")
    source_hash = (provenance.get("source_rect_image_sha256") if provenance.get("source_rect_image")
                   else provenance.get("source_sha256") or provenance.get("source_image_sha256"))
    atlas_path = provenance.get("generated_atlas") or provenance.get("source_atlas")
    atlas_hash = provenance.get("generated_atlas_sha256") or provenance.get("source_atlas_sha256")
    output_hash = asset.get("image", {}).get("sha256")
    if (evidence["source_path"] != source_path
            or (source_hash is not None and evidence["source_sha256"] != source_hash)
            or evidence["atlas_path"] != atlas_path or evidence["atlas_sha256"] != atlas_hash
            or evidence["active_output_sha256"] != output_hash):
        raise ValueError(f"Affine calibration source/output binding mismatch: {label}")
    for path_key, hash_key in (("source_path", "source_sha256"), ("atlas_path", "atlas_sha256")):
        ref = evidence[path_key]
        local = contained(pack, ref)
        external = None if local.is_file() else (external_provenance or {}).get(ref)
        actual = file_sha256(local, verified_provenance) if local.is_file() else external.get("sha256") if external else None
        if actual != evidence[hash_key]:
            raise ValueError(f"Unverified affine calibration {path_key}: {label}")
    output_path = contained(pack, asset["image"]["path"])
    if not output_path.is_file() or file_sha256(output_path, verified_provenance) != output_hash:
        raise ValueError(f"Unverified affine calibration output: {label}")
    with Image.open(output_path) as out:
        if digest(out) != evidence["active_output_rgba_sha256"]:
            raise ValueError(f"Affine calibration output RGBA mismatch: {label}")
    crop = provenance.get("crop_bounds_px", {})
    bounds = (normalization.get("component_bounds_xyxy_px")
        or normalization.get("alpha_component_bounds_atlas_px")
        or crop_alpha_bounds_xyxy(crop, label))
    if bounds is None:
        bounds = row.get("crop_bounds_xyxy")
    if bounds != evidence["crop_bounds_xyxy"]:
        raise ValueError(f"Affine calibration crop binding mismatch: {label}")
    resized = normalization.get("resized_dimensions_px", crop.get("resized_bounds_px"))
    if resized is None:
        resized = row.get("resized_dimensions_px")
    if resized != evidence["resized_dimensions_px"]:
        raise ValueError(f"Affine calibration target dimensions mismatch: {label}")
    sx, sy = evidence["scale_x"], evidence["scale_y"]
    if (not all(isinstance(x, (int, float)) and math.isfinite(x) and x > 0 for x in (sx, sy))
            or sx == sy):
        raise ValueError(f"Affine calibration must declare finite distinct axis factors: {label}")
    source_calibration = provenance.get("source_cell_calibration")
    if source_calibration != [sx, sy]:
        raise ValueError(f"Affine calibration disagrees with source cell calibration: {label}")
    dimensions = [bounds[2]-bounds[0], bounds[3]-bounds[1]]
    if any(not isinstance(x, int) or isinstance(x, bool) or x <= 0 for x in dimensions):
        raise ValueError(f"Affine calibration has malformed source crop dimensions: {label}")
    if (abs(round(dimensions[0]*sx)-resized[0]) > 1
            or abs(round(dimensions[1]*sy)-resized[1]) > 1):
        raise ValueError(f"Affine calibration factors disagree with target dimensions: {label}")
    if ("final_uniform_scale" in evidence
            and evidence["final_uniform_scale"] != normalization.get("scale")):
        raise ValueError(f"Affine final uniform scale disagrees with normalization: {label}")
    if "final_uniform_scale" in evidence and any(
            abs(round(length * evidence["final_uniform_scale"]) - target) > 1
            for length, target in zip(resized, evidence["target_dimensions_px"])):
        raise ValueError(f"Affine final uniform scale disagrees with target dimensions: {label}")
    if "final_canvas_bounds_xyxy" in evidence:
        final_bounds = evidence["final_canvas_bounds_xyxy"]
        if ([final_bounds[2]-final_bounds[0], final_bounds[3]-final_bounds[1]]
                != evidence["target_dimensions_px"]):
            raise ValueError(f"Affine final canvas bounds disagree with target dimensions: {label}")
        actual_bbox = Image.open(output_path).getchannel("A").getbbox()
        if actual_bbox != tuple(final_bounds):
            raise ValueError(f"Affine final canvas bounds disagree with active output: {label}")
    if ("final_canvas_bounds_xyxy" in evidence
            and (not isinstance(evidence["final_canvas_bounds_xyxy"], list)
                 or len(evidence["final_canvas_bounds_xyxy"]) != 4)):
        raise ValueError(f"Malformed affine final canvas bounds: {label}")
    if "purpose" in evidence and (not isinstance(evidence["purpose"], str) or not evidence["purpose"].strip()):
        raise ValueError(f"Missing affine calibration purpose: {label}")
    for key in fields - {"schema_version", "method", "recipe_path", "recipe_sha256",
                         "review_record_path", "review_record_sha256", "review_status"}:
        if key in row and row[key] != evidence[key]:
            raise ValueError(f"Affine calibration recipe row disagrees on {key}: {label}")
    return ("reviewed-axis-affine", evidence["recipe_sha256"], evidence["object_id"], evidence["view"])


def retained_snapshot_basis(pack, asset, normalization, label, verified_provenance=None):
    """Bind an irrecoverable historical render to a distinct lossless snapshot."""
    evidence = normalization.get("retained_snapshot_evidence")
    if evidence is None:
        return None
    required = {"schema_version", "method", "manifest_path", "manifest_sha256", "object_id", "view"}
    if not isinstance(evidence, dict) or set(evidence) != required:
        raise ValueError(f"Malformed retained-snapshot evidence: {label}")
    if (evidence["schema_version"] != 1 or evidence["method"] != "verified-retained-snapshot-v1"
            or evidence["object_id"] != asset.get("object_id") or evidence["view"] != asset.get("view")):
        raise ValueError(f"Retained-snapshot identity mismatch: {label}")
    manifest_path = contained(pack, evidence["manifest_path"])
    if (not manifest_path.is_file()
            or file_sha256(manifest_path, verified_provenance) != evidence["manifest_sha256"]):
        raise ValueError(f"Retained-snapshot manifest hash mismatch: {label}")
    manifest = read_json(manifest_path)
    rows = manifest.get("records")
    if not isinstance(rows, list):
        raise ValueError(f"Malformed retained-snapshot manifest records: {label}")
    matches = [row for row in rows if row.get("object_id") == evidence["object_id"]
               and row.get("view") == evidence["view"]]
    if len(matches) != 1:
        raise ValueError(f"Retained-snapshot row missing or ambiguous: {label}")
    row = matches[0]
    output = asset.get("image", {})
    output_path = output.get("path")
    if (row.get("active_output_path") != output_path
            or row.get("active_output_sha256") != output.get("sha256")):
        raise ValueError(f"Retained-snapshot active output binding mismatch: {label}")
    live_path = contained(pack, output_path)
    if not live_path.is_file() or file_sha256(live_path, verified_provenance) != output.get("sha256"):
        raise ValueError(f"Retained-snapshot live PNG hash mismatch: {label}")
    with Image.open(live_path) as live:
        live_size, live_rgba = live.size, digest(live)
    if row.get("active_output_rgba_sha256") != live_rgba:
        raise ValueError(f"Retained-snapshot live RGBA mismatch: {label}")
    snapshot_rel = row.get("snapshot_path")
    if not isinstance(snapshot_rel, str) or snapshot_rel == output_path:
        raise ValueError(f"Retained-snapshot input must be distinct from active output: {label}")
    snapshot_path = contained(pack, snapshot_rel)
    if not snapshot_path.is_file() or file_sha256(snapshot_path, verified_provenance) != row.get("snapshot_sha256"):
        raise ValueError(f"Retained-snapshot input hash mismatch: {label}")
    with Image.open(snapshot_path) as snapshot:
        if (snapshot.size != live_size or row.get("dimensions_px") != list(live_size)
                or digest(snapshot) != live_rgba or row.get("snapshot_rgba_sha256") != live_rgba):
            raise ValueError(f"Retained-snapshot input differs from active output: {label}")
    if not isinstance(row.get("claim"), str) or not row["claim"].strip() \
            or not isinstance(row.get("existing_explanation"), str) or not row["existing_explanation"].strip():
        raise ValueError(f"Retained-snapshot provenance explanation is missing: {label}")
    return ("verified-retained-snapshot", evidence["manifest_sha256"], evidence["object_id"], evidence["view"])


def per_view_normalization_basis(pack, asset, provenance, normalization, label, verified_provenance=None,
                                 external_provenance=None):
    policy = normalization.get("scale_policy")
    if policy is None:
        return None
    if policy != "per-view-uniform":
        raise ValueError(f"Unsupported normalization scale policy: {label}")
    evidence = normalization.get("scale_evidence")
    expected_fields = {"schema_version", "method", "recipe_path", "recipe_sha256", "object_id", "view",
        "source_path", "source_sha256", "atlas_path", "atlas_sha256", "active_output_sha256",
        "active_output_rgba_sha256", "crop_bounds_xyxy", "resized_dimensions_px", "scale", "projection_scale"}
    optional_fields = {"replay_status", "verification_basis", "rounding_model", "integer_rounding_model",
        "execution_report_path", "execution_report_sha256", "output_report_path", "output_report_sha256",
        "review_record_path", "review_record_sha256", "orientation_correction_degrees"}
    if (not isinstance(evidence, dict) or not expected_fields.issubset(evidence)
            or set(evidence) - expected_fields - optional_fields):
        raise ValueError(f"Malformed per-view normalization evidence: {label}")
    if (evidence["schema_version"] != 1 or evidence["method"] not in {
                "verified-per-view-isotropic-v1", "reviewed-current-output-isotropic-v1"}
            or evidence["object_id"] != asset.get("object_id")
            or evidence["view"] != asset.get("view")):
        raise ValueError(f"Per-view normalization identity mismatch: {label}")
    if (evidence["method"] == "reviewed-current-output-isotropic-v1"
            and evidence.get("replay_status") != "not-replayed"):
        raise ValueError(f"Unclear non-replayed scale evidence status: {label}")
    verification_basis = evidence.get("verification_basis")
    if verification_basis not in {"executed-replay", "producer-recorded-output", "reviewed-current-output"}:
        raise ValueError(f"Unsupported per-view verification basis: {label}")
    if (evidence["method"] == "reviewed-current-output-isotropic-v1"
            and verification_basis != "reviewed-current-output"):
        raise ValueError(f"Reviewed current output has conflicting verification basis: {label}")
    recipe_path = contained(pack, evidence["recipe_path"])
    if not recipe_path.is_file():
        raise ValueError(f"Missing per-view normalization recipe: {label}")
    if file_sha256(recipe_path, verified_provenance) != evidence["recipe_sha256"]:
        raise ValueError(f"Per-view normalization recipe hash mismatch: {label}")
    recipe = read_json(recipe_path)
    source_path = provenance.get("source_rect_image") or provenance.get("source_image")
    source_hash = (provenance.get("source_rect_image_sha256") if provenance.get("source_rect_image")
                   else provenance.get("source_sha256") or provenance.get("source_image_sha256"))
    # Some historical style records name a local source image but omit its
    # hash from provenance. Accept the evidence hash only after independently
    # hashing that contained source file below.
    if source_hash is None and evidence.get("source_path") == source_path:
        source_hash = evidence.get("source_sha256")
    crop = provenance.get("crop_bounds_px", {})
    scale = normalization.get("scale", normalization.get("shared_scale",
        normalization.get("shared_scale_per_object", crop.get("shared_scale"))))
    if not isinstance(scale, (int, float)) or not math.isfinite(scale) or scale <= 0:
        raise ValueError(f"Malformed per-view normalization scale: {label}")
    output_hash = asset.get("image", {}).get("sha256")
    if (evidence["source_path"] != source_path or evidence["source_sha256"] != source_hash
            or evidence["active_output_sha256"] != output_hash):
        raise ValueError(f"Per-view normalization source/output binding mismatch: {label}")
    source_file = contained(pack, source_path)
    external_source = None if source_file.is_file() else (external_provenance or {}).get(source_path)
    actual_source_hash = (file_sha256(source_file, verified_provenance) if source_file.is_file()
                          else external_source.get("sha256") if external_source else None)
    if actual_source_hash != source_hash:
        raise ValueError(f"Unverified per-view normalization source: {label}")
    image_path = contained(pack, asset["image"]["path"])
    if not image_path.is_file() or file_sha256(image_path, verified_provenance) != output_hash:
        raise ValueError(f"Unverified per-view normalization output: {label}")
    with Image.open(image_path) as active_image:
        if digest(active_image) != evidence["active_output_rgba_sha256"]:
            raise ValueError(f"Per-view normalization RGBA binding mismatch: {label}")
    atlas_path = evidence["atlas_path"]
    atlas_hash = evidence["atlas_sha256"]
    provenance_atlas = provenance.get("generated_atlas") or provenance.get("source_atlas")
    provenance_atlas_hash = provenance.get("generated_atlas_sha256") or provenance.get("source_atlas_sha256")
    if atlas_path != provenance_atlas or atlas_hash != provenance_atlas_hash:
        raise ValueError(f"Per-view normalization atlas binding mismatch: {label}")
    atlas_file = contained(pack, atlas_path)
    actual_atlas_hash = (file_sha256(atlas_file, verified_provenance) if atlas_file.is_file()
                         else (external_provenance or {}).get(atlas_path, {}).get("sha256"))
    if actual_atlas_hash != atlas_hash:
        raise ValueError(f"Unverified per-view normalization atlas: {label}")
    # Find exactly one scale row for this object/view in the immutable recipe.
    # Prior-view guard hashes are deliberately not treated as emitted outputs.
    recipe_rows = []
    def visit(node):
        if isinstance(node, dict):
            identity = node.get("object_id", node.get("id"))
            direction = node.get("view", node.get("direction"))
            if identity == evidence["object_id"] and direction == evidence["view"]:
                recipe_rows.append(node)
            for child in node.values():
                visit(child)
        elif isinstance(node, list):
            for child in node:
                visit(child)
    visit(recipe)
    if len(recipe_rows) != 1 or recipe_rows[0].get("scale") != scale:
        raise ValueError(f"Per-view normalization scale is not bound by the recipe: {label}")
    row = recipe_rows[0]
    required_row_fields = {"scale", "source_path", "source_sha256", "atlas_path", "atlas_sha256",
        "active_output_sha256", "active_output_rgba_sha256", "crop_bounds_xyxy",
        "resized_dimensions_px", "projection_scale"}
    if not required_row_fields.issubset(row):
        raise ValueError(f"Per-view normalization evidence row lacks active bindings: {label}")
    if row.get("verification_basis") != verification_basis:
        raise ValueError(f"Per-view evidence row verification basis mismatch: {label}")
    if verification_basis == "reviewed-current-output":
        if (evidence.get("replay_status") != "not-replayed" or row.get("replay_status") != "not-replayed"):
            raise ValueError(f"Reviewed current output must be explicitly marked not replayed: {label}")
        review_path = evidence.get("review_record_path")
        review_hash = evidence.get("review_record_sha256")
        if (not isinstance(review_path, str) or not isinstance(review_hash, str)
                or row.get("review_record_path") != review_path or row.get("review_record_sha256") != review_hash):
            raise ValueError(f"Reviewed current output lacks immutable review binding: {label}")
        review_file = contained(pack, review_path)
        if not review_file.is_file() or file_sha256(review_file, verified_provenance) != review_hash:
            raise ValueError(f"Reviewed current output review hash mismatch: {label}")
    elif verification_basis == "producer-recorded-output":
        original_recipe_path = row.get("original_recipe_path")
        original_recipe_hash = row.get("original_recipe_sha256")
        if (not isinstance(original_recipe_path, str) or not isinstance(original_recipe_hash, str)
                or row.get("original_recipe_output_match") is not True
                or row.get("original_recipe_output_sha256") != evidence["active_output_sha256"]):
            raise ValueError(f"Verified per-view evidence lacks exact original recipe output binding: {label}")
        original_path = contained(pack, original_recipe_path)
        if (not original_path.is_file()
                or file_sha256(original_path, verified_provenance) != original_recipe_hash):
            raise ValueError(f"Verified per-view original recipe hash mismatch: {label}")
    else:
        if (not isinstance(evidence.get("execution_report_path"), str)
                or not isinstance(evidence.get("execution_report_sha256"), str)
                or row.get("execution_report_path") != evidence["execution_report_path"]
                or row.get("execution_report_sha256") != evidence["execution_report_sha256"]):
            raise ValueError(f"Executed per-view output lacks replay report binding: {label}")
        if (row.get("output_report_path") != evidence.get("output_report_path")
                or row.get("output_report_sha256") != evidence.get("output_report_sha256")):
            raise ValueError(f"Executed per-view output report binding mismatch: {label}")
        _check_executed_replay_binding(pack, evidence, asset, verified_provenance, label)
    # Some normalizers record the active isolated component bounds under
    # normalization rather than the older atlas-cell crop record. Prefer those
    # explicit component fields; otherwise use the active crop bounds. A recipe
    # row may be the source only when it declares bounds under a recognized key.
    bounds = None
    for key in ("component_bounds_xyxy_px", "alpha_component_bounds_atlas_px"):
        value = normalization.get(key)
        if value is not None:
            bounds = value
            break
    if bounds is None:
        bounds = crop_alpha_bounds_xyxy(crop, label)
    row_bounds = row.get("crop_bounds_xyxy", row.get("component_bounds_xyxy_px"))
    if row_bounds is None and isinstance(row.get("crop_bounds_px"), dict):
        row_bounds = crop_alpha_bounds_xyxy(row["crop_bounds_px"], f"{label}/recipe-row")
    if bounds is None:
        bounds = row_bounds
    if bounds is None or bounds != evidence["crop_bounds_xyxy"]:
        raise ValueError(f"Per-view normalization crop binding mismatch: {label}")
    if row_bounds is not None and row_bounds != bounds:
        raise ValueError(f"Per-view normalization recipe crop mismatch: {label}")
    # Normalized evidence manifests duplicate the exact active bindings into
    # their unique row. When a legacy producer recipe itself is used directly,
    # it may only contain the scale cell; its hash still binds that historical
    # recipe while active image/crop facts are checked against the sidecar.
    for key in ("source_path", "source_sha256", "atlas_path", "atlas_sha256",
                "active_output_sha256", "active_output_rgba_sha256", "crop_bounds_xyxy",
                "resized_dimensions_px", "projection_scale", "verification_basis",
                "execution_report_path", "execution_report_sha256", "output_report_path",
                "output_report_sha256", "review_record_path", "review_record_sha256",
                "orientation_correction_degrees"):
        if key in row and row[key] != evidence[key]:
            raise ValueError(f"Per-view normalization recipe row disagrees on {key}: {label}")
    crop = provenance.get("crop_bounds_px", {})
    resized = normalization.get("resized_dimensions_px", crop.get("resized_bounds_px"))
    if resized is None:
        resized = row.get("resized_dimensions_px")
    projection = evidence["projection_scale"]
    if (evidence["scale"] != scale or evidence["resized_dimensions_px"] != resized):
        raise ValueError(f"Per-view normalization dimensions/scale binding mismatch: {label}")
    orientation = evidence.get("orientation_correction_degrees", crop.get("orientation_correction_degrees", 0))
    if orientation not in {0, 90, 180, 270}:
        raise ValueError(f"Unsupported per-view orientation correction: {label}")
    if (not isinstance(resized, list) or len(resized) != 2
            or not all(isinstance(value, int) and not isinstance(value, bool) and value > 0 for value in resized)
            or bounds is None or projection <= 0 or not math.isfinite(projection)):
        raise ValueError(f"Per-view normalization scale is not isotropic or disagrees with rendered dimensions: {label}")
    projected = [round(length * scale * projection)
        for length in (bounds[2]-bounds[0], bounds[3]-bounds[1])]
    if orientation in {90, 270}:
        projected.reverse()
    if any(abs(actual - expected) > 1 for actual, expected in zip(projected, resized)):
        raise ValueError(f"Per-view normalization scale is not isotropic or disagrees with rendered dimensions: {label}")
    if "orientation_correction_degrees" in evidence and orientation in {90, 270}:
        actual_box = Image.open(image_path).getchannel("A").getbbox()
        if (actual_box is None or [actual_box[2]-actual_box[0], actual_box[3]-actual_box[1]]
                != resized):
            raise ValueError(f"Per-view quarter-turn dimensions disagree with active PNG: {label}")
    return ("verified-per-view-scale", evidence["recipe_sha256"], evidence["object_id"], evidence["view"])


def check_asset_geometry(pack, asset, image, source_sizes, external_provenance=None, verified_provenance=None):
    external_provenance = external_provenance or {}
    verified_provenance = verified_provenance if verified_provenance is not None else {}
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
        normalization_meta = provenance.get("normalization", {})
        affine_declared = (isinstance(normalization_meta, dict)
            and isinstance(normalization_meta.get("calibration_evidence"), dict)
            and normalization_meta["calibration_evidence"].get("method") == "reviewed-axis-affine-v1")
        if (not math.isclose(calibration[0], calibration[1], rel_tol=1e-9, abs_tol=1e-12)
                and not affine_declared):
            raise ValueError(f"Anisotropic principal-view normalization: {asset['id']}")
    source = provenance.get("source_image")
    rectangle = provenance.get("source_rect")
    if rectangle is not None:
        explicit_rectangle_source = provenance.get("source_rect_image")
        if explicit_rectangle_source:
            rectangle_source = explicit_rectangle_source
        elif isinstance(rectangle, list):
            # In ordinary extraction records source_rect is relative to the
            # source scene when present; source_image may be a tight crop.
            rectangle_source = provenance.get("source_scene") or source
        elif isinstance(rectangle, dict):
            # Legacy generated-view records historically stored source_rect
            # coordinates against their generated/source atlas.
            rectangle_source = provenance.get("generated_atlas") or provenance.get("source_atlas")
        else:
            raise ValueError(f"Malformed source_rect: {asset['id']}")
        if not rectangle_source:
            raise ValueError(f"Missing source image for source_rect: {asset['id']}")
        rectangle_path = contained(pack, rectangle_source)
        external_rectangle = None if rectangle_path.is_file() else external_provenance.get(rectangle_source)
        if not rectangle_path.is_file() and external_rectangle is None:
            raise ValueError(f"Missing source_rect image: {asset['id']}: {rectangle_source}")
        expected_rectangle_hash = provenance.get("source_rect_image_sha256")
        if expected_rectangle_hash is None and isinstance(rectangle, dict):
            expected_rectangle_hash = rectangle.get("source_sha256")
        if expected_rectangle_hash is None:
            expected_rectangle_hash = (
                provenance.get("source_scene_sha256") if rectangle_source == provenance.get("source_scene") else
                provenance.get("source_sha256") if rectangle_source == provenance.get("source_image") else
                provenance.get("generated_atlas_sha256") if rectangle_source == provenance.get("generated_atlas") else
                provenance.get("source_atlas_sha256") if rectangle_source == provenance.get("source_atlas") else None)
        actual_rectangle_hash = (file_sha256(rectangle_path, verified_provenance)
            if rectangle_path.is_file() else external_rectangle.get("sha256"))
        if expected_rectangle_hash is not None and actual_rectangle_hash != expected_rectangle_hash:
            raise ValueError(f"source_rect image hash mismatch: {asset['id']}")
        if not rectangle_path.is_file() and (not expected_rectangle_hash or actual_rectangle_hash != expected_rectangle_hash):
            raise ValueError(f"Unverified external source_rect image: {asset['id']}")
        if rectangle_path.is_file():
            if rectangle_source not in source_sizes:
                with Image.open(rectangle_path) as source_image:
                    source_sizes[rectangle_source] = source_image.size
            size = source_sizes[rectangle_source]
        else:
            size = external_rectangle.get("size_px")
            if (not isinstance(size, list) or len(size) != 2
                    or not all(isinstance(value, int) and not isinstance(value, bool) and value > 0 for value in size)):
                raise ValueError(f"Missing source_rect image dimensions: {asset['id']}")
            declared_size = provenance.get("source_rect_image_size")
            if declared_size is None and isinstance(rectangle, dict):
                declared_size = rectangle.get("source_size")
            if declared_size is not None and declared_size != size:
                raise ValueError(f"External source_rect dimensions disagree with metadata: {asset['id']}")
        if isinstance(rectangle, list):
            coordinate_format = provenance.get("source_rect_coordinate_format", "xywh")
            if coordinate_format not in {"xyxy", "xywh"}:
                raise ValueError(f"Unknown source_rect coordinate format: {asset['id']}")
            check_rectangle(rectangle, size, f"{asset['id']}/source_rect", xywh=coordinate_format == "xywh")
        else:
            if rectangle.get("source_size") and rectangle["source_size"] != list(size):
                raise ValueError(f"source_rect dimensions do not match bound image: {asset['id']}")
            coordinate_format = rectangle.get("coordinate_format",
                provenance.get("source_rect_coordinate_format", "xywh"))
            if coordinate_format not in {"xyxy", "xywh"}:
                raise ValueError(f"Unknown source_rect coordinate format: {asset['id']}")
            for key in ("alpha_bounds", "cell"):
                if rectangle.get(key):
                    formats = rectangle.get("coordinate_formats", {})
                    if not isinstance(formats, dict) or any(name not in {"alpha_bounds", "cell"}
                            or coordinate_format not in {"xyxy", "xywh"}
                            for name, coordinate_format in formats.items()):
                        raise ValueError(f"Malformed source_rect coordinate_formats: {asset['id']}")
                    member_format = formats.get(key, coordinate_format)
                    if member_format not in {"xyxy", "xywh"}:
                        raise ValueError(f"Unknown source_rect coordinate format: {asset['id']}/{key}")
                    check_rectangle(rectangle[key], size, f"{asset['id']}/source_rect/{key}",
                        xywh=member_format == "xywh")
            for key in ("alpha_component_bounds_atlas_px", "cell_px"):
                if rectangle.get(key):
                    check_rectangle(rectangle[key], size, f"{asset['id']}/source_rect/{key}")
    atlas = provenance.get("source_atlas") or provenance.get("generated_atlas")
    if atlas:
        atlas_path = contained(pack, atlas)
        external_atlas = None if atlas_path.is_file() else external_provenance.get(atlas)
        if not atlas_path.is_file() and external_atlas is None:
            raise ValueError(f"Missing undeclared provenance atlas: {asset['id']}: {atlas}")
        expected_atlas_hash = provenance.get("generated_atlas_sha256") if atlas == provenance.get("generated_atlas") else provenance.get("source_atlas_sha256")
        actual_atlas_hash = (file_sha256(atlas_path, verified_provenance)
            if atlas_path.is_file() else external_atlas.get("sha256"))
        if expected_atlas_hash and expected_atlas_hash != actual_atlas_hash:
            raise ValueError(f"Provenance hash mismatch: {atlas}")
        if atlas_path.is_file():
            if atlas not in source_sizes:
                with Image.open(atlas_path) as source_image:
                    source_sizes[atlas] = source_image.size
            size = source_sizes[atlas]
        else:
            size = external_atlas.get("size_px")
            if (not isinstance(size, list) or len(size) != 2
                    or not all(isinstance(value, int) and not isinstance(value, bool) and value > 0 for value in size)):
                raise ValueError(f"Missing provenance atlas dimensions: {asset['id']}")
        adapter = provenance.get("normalization_adapter")
        alpha_bounds_size = size
        if isinstance(adapter, dict) and "extractor_atlas" in adapter:
            extractor = adapter.get("extractor_atlas")
            extractor_hash = adapter.get("extractor_sha256")
            if not isinstance(extractor, str) or not isinstance(extractor_hash, str):
                raise ValueError(f"Incomplete normalization adapter source: {asset['id']}")
            extractor_path = contained(pack, extractor)
            external_extractor = None if extractor_path.is_file() else external_provenance.get(extractor)
            if not extractor_path.is_file() and external_extractor is None:
                raise ValueError(f"Missing normalization adapter atlas: {asset['id']}")
            actual_extractor_hash = (file_sha256(extractor_path, verified_provenance)
                if extractor_path.is_file() else external_extractor.get("sha256"))
            if actual_extractor_hash != extractor_hash:
                raise ValueError(f"Normalization adapter atlas hash mismatch: {asset['id']}")
            if extractor_path.is_file():
                if extractor not in source_sizes:
                    with Image.open(extractor_path) as source_image:
                        source_sizes[extractor] = source_image.size
                alpha_bounds_size = source_sizes[extractor]
            else:
                size_px = external_extractor.get("size_px")
                if (not isinstance(size_px, list) or len(size_px) != 2
                        or not all(isinstance(value, int) and not isinstance(value, bool) and value > 0 for value in size_px)):
                    raise ValueError(f"Missing normalization adapter dimensions: {asset['id']}")
                alpha_bounds_size = size_px
        normalization_record = provenance.get("normalization", {})
        normalization = normalization_record if isinstance(normalization_record, dict) else {}
        crop = provenance.get("crop_bounds_px", {})
        if normalization.get("cell_rect"):
            check_rectangle(normalization["cell_rect"], size, f"{asset['id']}/cell_rect", xywh=True)
        if isinstance(crop, dict):
            alpha_bounds = crop_alpha_bounds_xyxy(crop, f"{asset['id']}/alpha_bounds_global")
            if alpha_bounds is not None:
                check_rectangle(alpha_bounds, alpha_bounds_size, f"{asset['id']}/alpha_bounds_global")
        for component in normalization.get("component_groups", []):
            if component.get("bbox"):
                check_rectangle(component["bbox"], size, f"{asset['id']}/component bbox")
        if isinstance(normalization_record, list):
            validate_normalization_records(normalization_record, size, asset["id"])
        elif not isinstance(normalization_record, dict):
            raise ValueError(f"Malformed normalization metadata: {asset['id']}")
    normalization = normalization_parameters(provenance, asset["id"])
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


def validate(pack, require_views=False, allow_recorded_blocks=False):
    index = read_json(pack / "reusable/index.json")
    from generation_block_contract import load_blocks, records as block_records
    block_report = load_blocks(pack, index)
    blocks = block_records(block_report) if allow_recorded_blocks else {}
    from view_review_contract import load_review, POLICY
    review_report = load_review(pack, index,
        required=require_views and index.get('view_review_policy') == POLICY,
        allow_recorded_blocks=allow_recorded_blocks)
    legacy_review_report = load_review(pack, index, legacy=True,
        required=require_views and index.get('legacy_view_review_policy') == POLICY,
        allow_recorded_blocks=allow_recorded_blocks)
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
        for field, hash_field in (("source_image", "source_sha256"), ("source_scene", "source_scene_sha256"),
                                  ("source_rect_image", "source_rect_image_sha256"),
                                  ("source_atlas", "source_atlas_sha256"), ("generated_atlas", "generated_atlas_sha256")):
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
        bbox = check_asset_geometry(pack, asset, image, source_sizes, external_provenance, verified_provenance)
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
    affine_calibrations = []
    for object_id, group in view_sets.items():
        hashes = {}
        scales = {}
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
                normalization = normalization_parameters(provenance, f"{object_id}/{view}")
                scale = normalization.get("scale", normalization.get("shared_scale", normalization.get("shared_scale_per_object")))
                if scale is None and isinstance(provenance.get("crop_bounds_px"), dict):
                    scale = provenance["crop_bounds_px"].get("shared_scale")
                if scale is not None:
                    effective = float(scale)
                    if not math.isfinite(effective) or effective <= 0:
                        raise ValueError(f'Invalid normalization factor: {object_id}/{view}')
                    crop = provenance.get('crop_bounds_px', {})
                    requested = normalization.get('requested_shared_scale', crop.get('requested_shared_scale'))
                    compared = effective
                    if requested is not None:
                        compared = float(requested)
                        if not math.isfinite(compared) or compared <= 0:
                            raise ValueError(f'Invalid requested normalization factor: {object_id}/{view}')
                        bounds = (normalization.get("component_bounds_xyxy_px")
                            or normalization.get("alpha_component_bounds_atlas_px")
                            or crop_alpha_bounds_xyxy(crop, f"{object_id}/{view}") or [])
                        resized = normalization.get("resized_dimensions_px", crop.get('resized_bounds_px', []))
                        projection = float(normalization.get('projection_scale', crop.get('projection_scale', 1)))
                        rendered_factor = effective * projection
                        if not math.isfinite(rendered_factor) or rendered_factor <= 0:
                            raise ValueError(f'Invalid projection normalization factor: {object_id}/{view}')
                        if (len(bounds) != 4 or len(resized) != 2
                                or not all(isinstance(n, int) and not isinstance(n, bool) and n > 0 for n in resized)
                                or bounds[2] <= bounds[0] or bounds[3] <= bounds[1]
                                or any(abs(round(length * rendered_factor) - actual) > 1
                                       for length, actual in zip((bounds[2]-bounds[0], bounds[3]-bounds[1]), resized))):
                            raise ValueError(f'Effective normalization factor disagrees with resized crop: {object_id}/{view}')
                    # Raw resize factors are comparable only for the same
                    # normalization input. A later isolated repair atlas may
                    # have a different pixel resolution and valid own factor.
                    label = f"{object_id}/{view}"
                    basis = per_view_normalization_basis(pack, assets[ref], provenance, normalization,
                        label, verified_provenance, external_provenance)
                    if basis is None:
                        basis = affine_calibration_basis(pack, assets[ref], provenance, normalization,
                            label, verified_provenance, external_provenance)
                        if basis is not None:
                            calibration = normalization["calibration_evidence"]
                            affine_calibrations.append({"object_id": object_id, "view": view,
                                "method": basis[0], "recipe_sha256": basis[1],
                                "scale_x": calibration["scale_x"], "scale_y": calibration["scale_y"],
                                "target_dimensions_px": calibration["target_dimensions_px"],
                                "review_status": calibration["review_status"]})
                    if basis is None:
                        basis = retained_snapshot_basis(pack, assets[ref], normalization,
                            label, verified_provenance)
                    if basis is None:
                        basis = normalization_input_group(pack, provenance, external_provenance, label)
                    if basis is None:
                        rect_image = provenance.get("source_rect_image")
                        if rect_image:
                            rect_hash = provenance.get("source_rect_image_sha256")
                            rect_path = contained(pack, rect_image)
                            if not rect_hash or not rect_path.is_file() or file_sha256(rect_path, verified_provenance) != rect_hash:
                                raise ValueError(f"Unverified normalization source rectangle: {label}")
                            basis = ("source-rect-image", rect_image, rect_hash)
                        else:
                            atlas = provenance.get('generated_atlas') or provenance.get('source_atlas')
                            basis = ('legacy-unqualified',)
                            if atlas:
                                raw = contained(pack, atlas)
                                raw_hash = (file_sha256(raw, verified_provenance) if raw.is_file()
                                            else external_provenance.get(atlas, {}).get('sha256'))
                                if not raw_hash:
                                    raise ValueError(f'Unverified normalization input: {object_id}/{view}')
                                basis = (atlas, raw_hash)
                    scales.setdefault(basis, []).append(compared)
        if any(max(values) - min(values) > 1e-9 for values in scales.values()):
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
    unexpected_missing = [item for item in missing_views
        if assets.get(item['id'], {}).get('object_id', item['id']) not in blocks]
    if require_views and unexpected_missing:
        raise ValueError(f"{len(unexpected_missing)} physical assets still lack six principal views")
    undeclared_aliases = [finding for finding in view_aliases if not finding["declared_symmetry"]]
    if undeclared_aliases:
        warnings.append(f"{len(undeclared_aliases)} principal-view pixel aliases require symmetry review.")
        unexpected_aliases = [finding for finding in undeclared_aliases if not any(
            set(alias) == set(finding['views']) for alias in
            blocks.get(finding['object_id'], {}).get('blocked_pixel_aliases', []))]
        if require_views and unexpected_aliases:
            raise ValueError(f"Undeclared identical principal views: {unexpected_aliases}")
    if boundary_findings:
        warnings.append(f"{len(boundary_findings)} generated views touch frame boundaries; review clipping.")
    procedural = validate_procedural(pack, index.get("procedural", {}), assets)
    return {"status": "passed", "schema_version": 1, "assets_checked": len(assets), "procedural_validation": procedural,
        "independent_view_review": review_report['statistics'] if review_report else None,
        "targeted_legacy_view_review": legacy_review_report['statistics'] if legacy_review_report else None,
        "maps_pixel_exact": len(results), "maps": results,
        "duplicate_pixel_groups": duplicate_groups, "missing_six_view_count": len(missing_views),
        "view_pixel_aliases": view_aliases, "view_boundary_findings": boundary_findings,
        "reviewed_affine_calibrations": affine_calibrations,
        "missing_six_views": missing_views, "warnings": warnings,
        "release_validation": "validated-with-recorded-generation-blocks" if blocks else "no-recorded-block-exceptions-used",
        "recorded_generation_blocks": [{"object_id": oid, "affected_views": row['affected_views'],
            "status": row['status'], "complete": False} for oid, row in sorted(blocks.items())],
        "recorded_blocked_set_count": len(blocks),
        "recorded_blocked_view_count": sum(len(row['affected_views']) for row in blocks.values()),
        "unexpected_incomplete_count": len(unexpected_missing),
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
    parser.add_argument("--allow-recorded-generation-blocks",action="store_true",
        help="Opt into exact hash-bound image-tool release blocks; does not approve affected views")
    args=parser.parse_args()
    tests=self_test() if args.self_test else []
    result=validate(args.pack.resolve(),args.require_six_views,args.allow_recorded_generation_blocks)
    result["renderer_self_tests"]=tests
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k not in {"maps","missing_six_views"}},indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
