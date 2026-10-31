#!/usr/bin/env python3
"""Build lossless Pocket Dungeon reuse metadata without changing source artwork.

Requires Pillow and numpy. All paths in published JSON are relative to pack root.
--check calculates the same outputs but writes nothing; --rebuild explicitly runs
(the default) reproducible generation. Existing external catalog entries and
reviewed six-view metadata survive rebuilding.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import io
import json
import struct
from pathlib import Path

import numpy as np
from PIL import Image
from validate_pocket_reusable import view_set_approved

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACK = ROOT / "dungeon-crawler-tactics/Web/wwwroot/assets/style-packs/pocket-dungeon"
MANAGER = "pocket-reusable-v1"
VIEWS = ("front", "top", "right", "left", "bottom", "rear")


def canonical_hash(image):
    image = image.convert("RGBA")
    return hashlib.sha256(struct.pack(">II", *image.size) + image.tobytes()).hexdigest()


def file_hash(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()


def image_bytes(image):
    stream = io.BytesIO()
    image.save(stream, format="PNG", optimize=True)
    return stream.getvalue()


def read_json(path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


def unique_records(records, key, source):
    result = {}
    for record in records:
        identity = record.get(key)
        if not isinstance(identity, str) or not identity:
            raise ValueError(f"Missing {key} in {source}")
        if identity in result:
            raise ValueError(f"Duplicate {key} {identity!r} in {source}")
        result[identity] = record
    return result


def default_views(category):
    if category in {"ui", "effect", "portrait", "reconstruction_patch", "composition_layer"}:
        return {"applicable": False, "complete": True,
                "reason": "Screen-space graphic, effect, illustration, or reconstruction pixels; six physical object views do not apply."}
    return {"applicable": True, "complete": False,
            **{view: {"status": "missing", "asset_id": None} for view in VIEWS}}


def kind_for(category):
    return {"terrain": "tile", "structure": "sprite", "equipment": "icon",
            "prop": "sprite", "actor": "sprite", "effect": "effect", "ui": "ui",
            "loot": "icon", "portrait": "portrait"}.get(category, category)


class Builder:
    def __init__(self, pack):
        self.pack = pack
        self.outputs = {}
        self.assets = {}
        self.residuals = {}
        self.maps = []
        self.existing_index = read_json(pack / "reusable/index.json", {})
        self.manifest = read_json(pack / "manifest.json")
        unique_records(self.manifest["assets"], "id", "manifest.json")
        unique_records(self.existing_index.get("assets", []), "id", "reusable/index.json")
        unique_records(self.existing_index.get("view_sets", []), "object_id", "reusable/index.json")
        self.pixel_inventory = {}
        # Existing source PNGs are never edited or re-encoded.
        for path in sorted((pack / "components").glob("*.png")):
            with Image.open(path) as image:
                self.pixel_inventory.setdefault(canonical_hash(image), path.relative_to(pack).as_posix())

    def metadata(self, asset):
        path = asset["metadata_path"]
        self.outputs[path] = json_bytes(asset)
        self.assets[asset["id"]] = asset
        return asset

    def read_record(self, path, default=None):
        relative = path.relative_to(self.pack).as_posix()
        return json.loads(self.outputs[relative]) if relative in self.outputs else read_json(path, default)

    def open_image(self, path):
        source = io.BytesIO(self.outputs[path]) if path in self.outputs else self.pack / path
        return Image.open(source).convert("RGBA")

    def image_info(self, path, image=None, raw=None):
        if image is None:
            image = self.open_image(path)
        if raw is None:
            raw = self.outputs[path] if path in self.outputs else (self.pack / path).read_bytes()
        return {"path": path, "width": image.width, "height": image.height,
                "sha256": file_hash(raw), "rgba_sha256": canonical_hash(image)}

    def existing_components(self):
        for original in self.manifest["assets"]:
            asset_id = original["id"]
            metadata_path = str(Path(original["file"]).with_suffix(".json"))
            old = read_json(self.pack / metadata_path, {})
            category = original["category"]
            sheet = original["source"]["sheet"]
            source_sheet = self.manifest["sheets"][sheet]
            bounds = original["source"]["bounds"]
            asset = {**old, "schema_version": 1, "managed_by": MANAGER,
                "id": asset_id, "name": original["label"], "kind": kind_for(category),
                "category": category,
                "tags": sorted(set([self.manifest.get("id", self.pack.name), "existing", category, sheet, original["layer"], *asset_id.split("-")])),
                "image": self.image_info(original["file"]), "metadata_path": metadata_path,
                "provenance": {"method": "existing", "original_generation": "imagegen",
                    "source_image": source_sheet["file"], "source_sha256": source_sheet["sha256"],
                    "source_rect": [bounds[k] for k in ("x", "y", "width", "height")],
                    "extraction": original["source"], "padding_px": 4,
                    "license_record": "README.md",
                    "notes": "Unmodified pre-existing native-pixel extraction; original provenance retained in manifest.json. Repository inclusion does not establish a new licence."},
                "anchor_px": [original["anchor"]["x"], original["anchor"]["y"]],
                "object_id": old.get("object_id", asset_id), "view": old.get("view", "source"),
                "footprint_tiles": [original["logicalFootprint"]["width"], original["logicalFootprint"]["height"]],
                "procedural": old.get("procedural", {"eligible": False, "reason": "Concept extraction; seam, collision, and directional review required."}),
                "reuse_constraints": ["Preserve native pixels and existing alpha.", "Logical footprint is placement guidance, not a collision shape.", "Physical objects are not six-view complete unless explicitly reviewed."],
                "views": old.get("views", default_views(category))}
            self.metadata(asset)

    def residual(self, patch, source, rect):
        digest = canonical_hash(patch)
        # Deduplicate equal pixel content across concept images and atlas locations.
        if digest in self.residuals:
            asset = self.residuals[digest]
            occurrence = {"source_image": source, "source_rect": rect}
            if occurrence not in asset["provenance"]["occurrences"]:
                asset["provenance"]["occurrences"].append(occurrence)
            return asset
        if digest in self.pixel_inventory:
            existing_path = self.pixel_inventory[digest]
            for existing in self.assets.values():
                if existing["image"]["path"] == existing_path:
                    return existing
        asset_id = f"residual-{digest[:20]}"
        image_path = f"reusable/residuals/{digest[:20]}.png"
        existing_file = self.pack / image_path
        if existing_file.exists():
            try:
                cached = Image.open(existing_file).convert("RGBA")
                raw = existing_file.read_bytes() if canonical_hash(cached) == digest else image_bytes(patch)
            except (OSError, ValueError):
                raw = image_bytes(patch)
        else:
            raw = image_bytes(patch)
        self.outputs[image_path] = raw
        asset = {"schema_version": 1, "managed_by": MANAGER, "id": asset_id,
            "name": f"Reconstruction residual {digest[:12]}", "kind": "reconstruction_patch",
            "category": "reconstruction", "tags": [self.manifest.get("id", self.pack.name), "residual", "lossless", "reconstruction-only"],
            "image": self.image_info(image_path, patch, raw),
            "metadata_path": image_path.removesuffix(".png") + ".json",
            "provenance": {"method": "residual", "source_image": source, "source_rect": rect,
                "occurrences": [{"source_image": source, "source_rect": rect}],
                "license_record": "README.md", "notes": "Exact source RGBA, including invisible RGB. Covered semantic pixels are zeroed. This is not an isolated gameplay object or a seamless procedural tile."},
            "anchor_px": [0, 0], "procedural": {"eligible": False, "reason": "Residual source pixels only."},
            "reuse_constraints": ["Use only with its reconstruction map; not a semantic dungeon tile."],
            "views": default_views("reconstruction_patch")}
        self.residuals[digest] = asset
        self.assets[asset_id] = asset
        return asset

    def map_from_source(self, map_id, label, path, semantic, kind):
        source_image = self.open_image(path)
        original = np.array(source_image)
        assembled = np.zeros_like(original)
        coverage = np.zeros(original.shape[:2], dtype=bool)
        semantic_coverage = np.zeros(original.shape[:2], dtype=bool)
        placements = []
        for asset, x, y in semantic:
            pixels = np.array(self.open_image(asset["image"]["path"]))
            h, w = pixels.shape[:2]
            # Padding can extend past an atlas edge. Clip only the canvas-facing
            # view; retain the original PNG and original integer placement.
            left, top = max(0, x), max(0, y)
            right, bottom = min(source_image.width, x+w), min(source_image.height, y+h)
            if left >= right or top >= bottom:
                raise ValueError(f"Semantic placement outside {map_id}: {asset['id']}")
            clipped = pixels[top-y:bottom-y, left-x:right-x]
            mask = clipped[:, :, 3] > 0
            region = original[top:bottom, left:right]
            if np.any(clipped[mask] != region[mask]):
                raise ValueError(f"Semantic pixels differ from source: {map_id}/{asset['id']}")
            assembled[top:bottom, left:right][mask] = clipped[mask]
            coverage[top:bottom, left:right] |= mask
            role = "residual" if asset["kind"] == "reconstruction_patch" else "semantic"
            if role == "semantic":
                semantic_coverage[top:bottom, left:right] |= mask
            placements.append({"asset_id": asset["id"], "path": asset["image"]["path"],
                "x": x, "y": y, "rotation_deg": 0, "scale": 1,
                "blend": "masked-replace", "role": role})
        remaining = original.copy()
        remaining[coverage] = 0
        residual_placements = []
        for y in range(0, source_image.height, 64):
            for x in range(0, source_image.width, 64):
                pixels = remaining[y:y+64, x:x+64]
                if not np.any(pixels):
                    continue
                patch = Image.fromarray(pixels, "RGBA")
                asset = self.residual(patch, path, [x, y, patch.width, patch.height])
                residual_placements.append({"asset_id": asset["id"], "path": asset["image"]["path"],
                    "x": x, "y": y, "rotation_deg": 0, "scale": 1, "blend": "replace", "role": "residual"})
        layers = residual_placements + placements
        for z, layer in enumerate(layers):
            layer["z"] = z
        total_visible = int(np.count_nonzero(original[:, :, 3]))
        semantic_visible = int(np.count_nonzero(semantic_coverage))
        doc = {"schema_version": 1, "managed_by": MANAGER, "id": map_id, "label": label,
            "kind": kind, "source": self.image_info(path, source_image),
            "canvas": {"width": source_image.width, "height": source_image.height, "mode": "RGBA", "background": [0, 0, 0, 0]},
            "coordinate_system": "Pixels; top-left origin; x right, y down; integer placement. Rotation clockwise, then place transformed top-left at x,y.",
            "blend_modes": {"replace": "Copy full rectangle, including alpha-zero RGB.", "masked-replace": "Copy exact RGBA only where asset alpha > 0; binary mask, no alpha compositing.", "source-over": "Pillow Image.alpha_composite RGBA."},
            "layers": layers, "pixel_exact": True,
            "verification": {"rgba_sha256": canonical_hash(source_image), "differing_pixels": 0},
            "statistics": {"semantic_placement_count": sum(p["role"] == "semantic" for p in placements), "residual_placement_count": len(residual_placements) + sum(p["role"] == "residual" for p in placements),
                "semantic_visible_pixel_count": semantic_visible, "residual_visible_pixel_count": total_visible-semantic_visible,
                "source_visible_pixel_count": total_visible, "semantic_visible_coverage": round(semantic_visible / total_visible, 6) if total_visible else 0},
            "notes": "Residual patches preserve exact original pixels and are not procedural dungeon tiles. Hidden RGB is retained for byte-exact decoded RGBA reconstruction."}
        self.add_map(doc)

    def add_map(self, doc):
        map_path = f"reusable/maps/{doc['id']}.json"
        self.outputs[map_path] = json_bytes(doc)
        self.maps.append({"id": doc["id"], "label": doc["label"], "file": map_path,
                          "source": doc["source"]["path"], "kind": doc["kind"],
                          "statistics": doc["statistics"]})

    def preview_map(self):
        placements = []
        for z, original in enumerate(self.manifest["preview"]["layers"]):
            asset_id = f"preview-layer-{original['id']}"
            path = original["file"]
            metadata_path = str(Path(path).with_suffix(".json"))
            asset = {"schema_version": 1, "managed_by": MANAGER, "id": asset_id,
                "name": f"Preview {original['label']} layer", "kind": "composition_layer",
                "category": "composition", "tags": [self.manifest.get("id", self.pack.name), "preview", "layer", original["id"]],
                "image": self.image_info(path), "metadata_path": metadata_path,
                "provenance": {"method": "existing", "source_image": "preview.png", "license_record": "README.md",
                    "notes": "Unmodified existing preview layer, as listed in original manifest.json."},
                "anchor_px": [0, 0], "views": default_views("composition_layer"),
                "procedural": {"eligible": False, "reason": "Illustrative full-canvas layer."}}
            self.metadata(asset)
            placements.append({"asset_id": asset_id, "path": path, "x": 0, "y": 0, "z": z,
                "rotation_deg": 0, "scale": 1, "blend": "source-over", "role": "semantic"})
        source = self.image_info("preview.png")
        self.add_map({"schema_version": 1, "managed_by": MANAGER, "id": "preview", "label": "Layered component preview",
            "kind": "composition", "source": source,
            "canvas": {"width": source["width"], "height": source["height"], "mode": "RGBA", "background": [0, 0, 0, 0]},
            "coordinate_system": "Pixels, top-left origin; layers in increasing z order.", "layers": placements,
            "pixel_exact": True, "verification": {"rgba_sha256": source["rgba_sha256"], "differing_pixels": 0},
            "statistics": {"semantic_placement_count": 7, "residual_placement_count": 0},
            "notes": "Reuses all seven existing layer PNGs in original manifest order."})

    def finalize_outputs(self):
        from asset_attachment_tags import enrich_document, enrich_library, style_of
        index = json.loads(self.outputs["reusable/index.json"])
        enrich_library(self.pack, index)
        physical = [asset for asset in index["assets"] if asset.get("views", {}).get("applicable")]
        index.setdefault("statistics", {}).update({
            "physical_reference_count": len(physical),
            "canonical_physical_object_count": len({a.get("object_id", a["id"]) for a in physical}),
            "canonical_physical_objects_missing_six_views": len({a.get("object_id", a["id"]) for a in physical if not a["views"].get("complete")})})
        self.outputs["reusable/index.json"] = json_bytes(index)
        by_id = {asset["id"]: asset for asset in index["assets"]}
        for path, raw in list(self.outputs.items()):
            if path.endswith(".json"):
                self.outputs[path] = json_bytes(enrich_document(json.loads(raw), style_of(self.pack), by_id))
        index = json.loads(self.outputs["reusable/index.json"])
        recipe = index.get("procedural", {}).get("recipe")
        if recipe and recipe in self.outputs:
            index["procedural"]["recipe_sha256"] = file_hash(self.outputs[recipe])
        if getattr(self, "readonly_views", False):
            snapshots = getattr(self, "original_view_assets", {})
            index["assets"] = [snapshots.get(asset["id"], asset) for asset in index["assets"]]
            for asset in snapshots.values():
                self.outputs.pop(asset["metadata_path"], None)
        self.outputs["reusable/index.json"] = json_bytes(index)
        return self.outputs

    def build(self):
        self.existing_components()
        for sheet, record in self.manifest["sheets"].items():
            semantic = []
            for original in self.manifest["assets"]:
                if original["source"]["sheet"] == sheet:
                    bounds = original["source"]["bounds"]
                    semantic.append((self.assets[original["id"]], bounds["x"]-4, bounds["y"]-4))
            self.map_from_source(f"atlas-{sheet}", f"{sheet.title()} source atlas", record["file"], semantic, "atlas")
        from register_existing_derivatives import register_existing_derivatives
        register_existing_derivatives(self)
        # Current extension manifests are authoritative for their own directories.
        # Updating a prior catalog entry is valid; two active extensions claiming
        # the same asset/object id is a collision, never last-writer-wins.
        extension_paths = sorted((self.pack / "reusable").glob("views-*/set-index.json"))
        scene_path = self.pack / "reusable/scene-assets/index.json"
        if scene_path.exists() or "reusable/scene-assets/index.json" in self.outputs:
            extension_paths.append(scene_path)
        prefixes = tuple(path.parent.relative_to(self.pack).as_posix() + "/" for path in extension_paths)
        external_assets = {a["id"]: a for a in self.existing_index.get("assets", [])
                           if a.get("managed_by") != MANAGER and not a["image"]["path"].startswith(prefixes)}
        previous_assets = {a["id"]: a for a in self.existing_index.get("assets", [])}
        view_sets = {}
        for group in self.existing_index.get("view_sets", []):
            references = [ref.get("asset_id") if isinstance(ref, dict) else ref for ref in group.get("views", {}).values()]
            if not any(previous_assets.get(ref, {}).get("image", {}).get("path", "").startswith(prefixes) for ref in references):
                view_sets[group["object_id"]] = group
        asset_owners, object_owners = {}, {}
        for extension_path in extension_paths:
            label = extension_path.relative_to(self.pack).as_posix()
            extension = self.read_record(extension_path)
            incoming_assets = unique_records(extension.get("assets", []), "id", label)
            incoming_sets = unique_records(extension.get("view_sets", []), "object_id", label)
            for asset_id, asset in incoming_assets.items():
                if asset_id in asset_owners or asset_id in self.assets or asset_id in external_assets:
                    raise ValueError(f"Asset id collision {asset_id!r}: {label} and {asset_owners.get(asset_id, 'another catalog source')}")
                asset_owners[asset_id] = label
                external_assets[asset_id] = asset
            for object_id, group in incoming_sets.items():
                if object_id in object_owners or object_id in view_sets:
                    raise ValueError(f"View-set collision {object_id!r}: {label} and {object_owners.get(object_id, 'another catalog source')}")
                if set(group.get("views", {})) != set(VIEWS):
                    raise ValueError(f"View set must declare exactly six principal keys: {object_id}")
                object_owners[object_id] = label
                view_sets[object_id] = group
        scene = self.read_record(scene_path, {})
        extras = read_json(self.pack / "reusable/semantic-placements.json", {"sources": {}})
        for path in self.manifest.get("conceptFiles", []):
            semantic = []
            stem = Path(path).stem
            declarations = list(extras.get("sources", {}).get(path, []))
            scene_placements = scene.get("placements", {})
            declarations.extend(scene_placements.get(f"source-{stem}", scene_placements.get(path, [])))
            for item in declarations:
                if "metadata_path" in item:
                    asset = read_json(self.pack / item["metadata_path"])
                else:
                    asset = external_assets[item["asset_id"]]
                if asset["id"] in external_assets and external_assets[asset["id"]] != asset:
                    raise ValueError(f"Conflicting semantic-placement metadata: {asset['id']}")
                external_assets[asset["id"]] = asset
                semantic.append((asset, item["x"], item["y"]))
            self.map_from_source(f"concept-{stem}", f"{stem.title()} concept", path, semantic, "concept")
        if self.manifest.get("preview", {}).get("layers"):
            self.preview_map()
        for asset in self.residuals.values():
            self.metadata(asset)
        self.original_view_assets = {asset_id: copy.deepcopy(asset) for asset_id, asset in external_assets.items() if asset["image"]["path"].startswith("reusable/views-")}
        for asset_id, asset in external_assets.items():
            if asset_id not in self.assets:
                self.assets[asset_id] = asset
        for object_id, view_set in view_sets.items():
            original = self.assets.get(object_id)
            if original is None or original.get("managed_by") != MANAGER:
                continue
            declared = view_set.get("views", {})
            resolved = {}
            for view in VIEWS:
                target_id = declared.get(view)
                if isinstance(target_id, dict):
                    target_id = target_id.get("asset_id")
                target = self.assets.get(target_id)
                valid = target is not None and target.get("view") == view and target.get("object_id") == object_id
                resolved[view] = {"status": target.get("provenance", {}).get("method", "generated") if valid else "missing", "asset_id": target_id if valid else None}
            original["views"] = {"applicable": True, "complete": view_set_approved(view_set) and all(r["asset_id"] for r in resolved.values()), **resolved}
            if not view_set_approved(view_set):
                original["views"]["reason"] = "Principal views exist but the set remains unapproved or unfinished."
            for qa_field in ("quality_status", "geometry_qa", "quality_review"):
                if qa_field in view_set:
                    original["views"][qa_field] = view_set[qa_field]
            self.metadata(original)
        own_map_ids = {m["id"] for m in self.maps}
        self.maps.extend(m for m in self.existing_index.get("maps", []) if m["id"] not in own_map_ids)
        procedural = self.existing_index.get("procedural", {"status": "pending", "note": "Reconstruction patches are not procedural tiles."})
        sample_path = self.pack / "reusable/procedural/sample.json"
        if sample_path.exists() and (self.pack / "reusable/procedural/sample.png").exists():
            sample = read_json(sample_path)
            procedural = {**procedural, "status": "sample-available", "recipe": "reusable/procedural/sample.json",
                "preview": "reusable/procedural/sample.png", "seed": sample["seed"], "grid": sample["grid"],
                "generator": "python " + sample["generator"], "generator_working_directory": "AI-Art repository root",
                "rotation_convention": sample.get("rotation_convention", "counterclockwise"),
                "validation": sample.get("validation", {}), "limitations": sample["limitations"],
                "recipe_sha256": file_hash(sample_path.read_bytes()),
                "preview_sha256": file_hash((self.pack / "reusable/procedural/sample.png").read_bytes())}
            procedural.pop("note", None)
        index = {**self.existing_index, "schema_version": 1, "base": "..",
            "title": self.manifest.get("title", "Pocket Dungeon") + " reusable asset library", "assets": list(self.assets.values()), "maps": self.maps,
            "view_sets": list(view_sets.values()),
            "procedural": procedural,
            "statistics": {"existing_components_reused": len(self.manifest["assets"]),
                "existing_component_pngs_modified": 0, "existing_preview_layers_reused": len(self.manifest.get("preview", {}).get("layers", [])),
                "unique_residual_patches": len(self.residuals), "residual_placements": sum(m["statistics"].get("residual_placement_count",0) for m in self.maps),
                "map_count": len(self.maps), "asset_count": len(self.assets),
                "physical_assets_missing_six_views": sum(a.get("views", {}).get("applicable", False) and not a["views"].get("complete", False) for a in self.assets.values())},
            "limitations": ["Physical views marked missing remain unfinished; never infer completion from PNG count.", "Residual patches preserve source images but are not seamless gameplay tiles.", "Newly designed unseen views are inferred artwork, not recoverable original pixels."]}
        # Attachment rules enrich every canonical and generated asset identically.
        try:
            from asset_attachment_tags import enrich_library
        except ImportError:
            enrich_library = None
        if enrich_library is not None:
            enrich_library(self.pack, index)
            for asset in index["assets"]:
                self.outputs[asset["metadata_path"]] = json_bytes(asset)
        self.outputs["reusable/index.json"] = json_bytes(index)
        return self.finalize_outputs()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, default=DEFAULT_PACK)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Compare generated outputs without writing")
    mode.add_argument("--rebuild", action="store_true", help="Generate metadata and reconstruction residuals (default)")
    args = parser.parse_args()
    builder = Builder(args.pack.resolve())
    outputs = builder.build()
    obsolete = []
    # Remove only unchanged outputs from our previous catalog, never unknown or
    # locally edited files. Semantic cutouts can make earlier residuals obsolete.
    for previous in builder.existing_index.get("assets", []):
        metadata_path = previous.get("metadata_path", "")
        if previous.get("managed_by") != MANAGER or previous.get("kind") != "reconstruction_patch" or metadata_path in outputs:
            continue
        png_path = previous["image"]["path"]
        if not png_path.startswith("reusable/residuals/") or not metadata_path.startswith("reusable/residuals/"):
            raise ValueError("Refusing to remove an output outside managed residuals")
        existing_json = read_json(args.pack / metadata_path)
        existing_png = args.pack / png_path
        if existing_json != previous or not existing_png.exists() or file_hash(existing_png.read_bytes()) != previous["image"]["sha256"]:
            raise ValueError(f"Preserving locally modified obsolete output: {metadata_path}")
        obsolete.extend([metadata_path, png_path])
    changed = []
    for relative, data in outputs.items():
        path = args.pack / relative
        if not path.exists() or path.read_bytes() != data:
            changed.append(relative)
            if not args.check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
    if not args.check:
        for relative in obsolete:
            (args.pack / relative).unlink()
    print(json.dumps({"mode": "check" if args.check else "rebuild", "outputs": len(outputs),
                      "changed": len(changed), "obsolete": len(obsolete), "examples": changed[:20]}, indent=2))
    return 1 if args.check and (changed or obsolete) else 0


if __name__ == "__main__":
    raise SystemExit(main())
