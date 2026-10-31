#!/usr/bin/env python3
"""Export deterministic, self-contained Pocket Dungeon reconstruction archives.

Default exports the whole catalog. Repeat --map ID to create smaller independent
collections. --plan lists size/count without writing. Raw generation atlases are
external provenance by default, recorded with their repository paths/hashes;
--include-raw includes them. Archives larger than --max-mib fail without replacing
an existing destination. Original sources used for pixel checks are included.
"""
from __future__ import annotations
import argparse
import sys
import copy
import hashlib
import json
import os
import tempfile
import zipfile
from pathlib import Path
from PIL import Image

sys.dont_write_bytecode = True

from validate_pocket_reusable import DEFAULT_PACK, VIEWS, contained, image_info, read_json, unique_records, view_reference

TOOLS = ("build_pocket_reusable.py", "validate_pocket_reusable.py", "render_pocket_map.py", "package_pocket_reusable.py", "export_pocket_collections.py", "assemble_archive_parts.py", "pocket-requirements.txt")


def encoded(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()


def raster_provenance_references(provenance):
    """Raw generation images and explicit crop-coordinate images, not outputs."""
    refs = [(provenance[field], provenance.get(field + '_sha256'))
            for field in ('source_atlas', 'generated_atlas', 'source_rect_image', 'replay_source', 'source_crop_path')
            if provenance.get(field)]
    # source_crop_path uses a historical hash-field spelling.
    if provenance.get('source_crop_path'):
        refs[-1] = (provenance['source_crop_path'], provenance.get('source_crop_sha256'))
    adapter = provenance.get('normalization_adapter')
    if isinstance(adapter, dict) and adapter.get('extractor_atlas'):
        refs.append((adapter['extractor_atlas'], adapter.get('extractor_sha256')))
    for key in ('axis_remap', 'symmetric_projection_derivation'):
        derivation = provenance.get(key)
        if isinstance(derivation, dict) and derivation.get('source_path'):
            refs.append((derivation['source_path'], derivation.get('source_sha256')))
    return refs


def asset_dependencies(index, selected):
    """Close a selection over canonical objects, their views and companions."""
    by_id = unique_records(index["assets"], "id", "source catalog assets")
    groups = unique_records(index.get("view_sets", []), "object_id", "source catalog view sets")
    asset_ids = set(selected)
    unknown = asset_ids - set(by_id)
    if unknown:
        raise ValueError(f"Unknown asset ids: {sorted(unknown)}")
    while True:
        previous = set(asset_ids)
        for asset_id in list(asset_ids):
            asset = by_id[asset_id]
            targets = [value["asset_id"] for value in asset.get("views", {}).values()
                       if isinstance(value, dict) and value.get("asset_id")]
            targets.extend(asset[field] for field in ("object_id", "canonical_asset_id")
                           if asset.get(field) in by_id)
            group = groups.get(asset_id)
            if group:
                targets.extend(filter(None, (view_reference(value) for value in group["views"].values())))
            for target in targets:
                if target not in by_id:
                    raise ValueError(f"Missing view dependency: {asset_id} -> {target}")
                asset_ids.add(target)
        asset_ids.update(a["id"] for a in index["assets"] if a.get("canonical_asset_id") in asset_ids)
        if asset_ids == previous:
            return asset_ids


def plan(pack, selected_maps=None, include_raw=False, selected_assets=None):
    folder = "pocket-dungeon" if pack.resolve() == DEFAULT_PACK.resolve() else "library"
    repository_location = "AI-Art repository dungeon-crawler branch, " + str(pack).split("Web/wwwroot/assets/")[-1]
    original = read_json(pack / "reusable/index.json")
    from generation_block_contract import load_blocks, project as project_blocks, reference as block_reference, evidence_files
    block_report = load_blocks(pack, original)
    from view_review_contract import load_review, project, expected_objects, reference as review_reference
    review_report = load_review(pack, original)
    legacy_review_report = load_review(pack, original, legacy=True)
    index = copy.deepcopy(original)
    by_id = unique_records(original["assets"], "id", "source catalog assets")
    map_index = unique_records(original["maps"], "id", "source catalog maps")
    groups = unique_records(original.get("view_sets", []), "object_id", "source catalog view sets")
    for object_id, group in groups.items():
        if set(group.get("views", {})) != set(VIEWS):
            raise ValueError(f"View set must declare exactly six principal keys: {object_id}")
    subset = selected_maps is not None or selected_assets is not None
    if subset:
        ids = set(selected_maps or [])
        unknown = ids - set(map_index)
        if unknown:
            raise ValueError(f"Unknown map ids: {sorted(unknown)}")
        index["maps"] = [m for m in original["maps"] if m["id"] in ids]
        asset_ids = set(selected_assets or [])
        unknown_assets = asset_ids - set(by_id)
        if unknown_assets:
            raise ValueError(f"Unknown asset ids: {sorted(unknown_assets)}")
        if not ids and not asset_ids:
            raise ValueError("A collection must select maps or assets")
        for entry in index["maps"]:
            asset_ids.update(layer["asset_id"] for layer in read_json(contained(pack, entry["file"]))["layers"])
        asset_ids = asset_dependencies(original, asset_ids)
        index["assets"] = [a for a in original["assets"] if a["id"] in asset_ids]
        index["view_sets"] = [v for v in groups.values() if v["object_id"] in asset_ids]
        index["procedural"] = {"status": "not-in-this-collection", "note": "Map collection; use the complete catalog for procedural examples."}
    else:
        asset_ids = set(by_id)
    files = set()
    external = {}
    provenance_hashes = {}
    provenance_sizes = {}
    evidence_seen = set()

    def retain_evidence(relative, expected_hash):
        path = contained(pack, relative)
        if not path.is_file():
            raise ValueError(f'Missing normalization evidence recipe: {relative}')
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected_hash:
            raise ValueError(f'Normalization evidence recipe hash mismatch: {relative}')
        files.add(relative)
        if relative in evidence_seen or path.suffix != '.json':
            return
        evidence_seen.add(relative)
        # Follow only validator-consumed proof links. Generation atlas and
        # candidate lineage remains separately declared external provenance.
        def visit(value):
            if isinstance(value, dict):
                for stem in ('original_recipe', 'execution_report', 'output_report', 'source_recipe', 'review_record'):
                    if value.get(stem + '_path'):
                        retain_evidence(value[stem + '_path'], value.get(stem + '_sha256'))
                for child in value.values():
                    visit(child)
            elif isinstance(value, list):
                for child in value:
                    visit(child)
        visit(json.loads(raw))

    for asset in index["assets"]:
        image_info(pack, asset["image"])
        files.add(asset["image"]["path"])
        metadata = asset.get("metadata_path", str(Path(asset["image"]["path"]).with_suffix(".json")))
        if read_json(contained(pack, metadata)) != asset:
            raise ValueError(f"Source sidecar/catalog mismatch: {asset['id']}")
        files.add(metadata)
        provenance = asset.get("provenance", {})
        normalization = provenance.get('normalization', {})
        for evidence_field in ('scale_evidence', 'calibration_evidence'):
            evidence = normalization.get(evidence_field) if isinstance(normalization, dict) else None
            if not isinstance(evidence, dict):
                continue
            references = [('recipe_path', 'recipe_sha256')]
            if evidence_field == 'calibration_evidence':
                references.append(('review_record_path', 'review_record_sha256'))
                if evidence.get('source_recipe_path'):
                    references.append(('source_recipe_path', 'source_recipe_sha256'))
            for path_field, hash_field in references:
                retain_evidence(evidence.get(path_field), evidence.get(hash_field))
        snapshot_evidence = normalization.get('retained_snapshot_evidence') if isinstance(normalization, dict) else None
        if isinstance(snapshot_evidence, dict):
            manifest_path = snapshot_evidence.get('manifest_path')
            retain_evidence(manifest_path, snapshot_evidence.get('manifest_sha256'))
            rows = read_json(contained(pack, manifest_path)).get('records', [])
            matching = [row for row in rows if row.get('object_id') == asset.get('object_id')
                        and row.get('view') == asset.get('view')]
            if len(matching) != 1:
                raise ValueError(f'Missing or ambiguous retained-snapshot row: {asset["id"]}')
            row = matching[0]
            retain_evidence(row.get('snapshot_path'), row.get('snapshot_sha256'))
        for source_field in ('source_image', 'source_scene'):
            source = provenance.get(source_field)
            if source and contained(pack, source).is_file():
                expected = provenance.get(source_field + '_sha256')
                if source_field == 'source_image':
                    expected = provenance.get('source_sha256') or expected
                if expected:
                    if source not in provenance_hashes:
                        provenance_hashes[source] = hashlib.sha256(contained(pack, source).read_bytes()).hexdigest()
                    if expected != provenance_hashes[source]:
                        raise ValueError(f"Original source hash mismatch: {source}")
                files.add(source)
            elif source:
                raise ValueError(f"Missing original provenance image: {source}")
        for reference in provenance.get("referenced_source_images", []):
            path = contained(pack, reference["path"])
            if not path.is_file():
                raise ValueError(f"Missing referenced generation source: {reference['path']}")
            if reference.get("sha256") and hashlib.sha256(path.read_bytes()).hexdigest() != reference["sha256"]:
                raise ValueError(f"Referenced source hash mismatch: {reference['path']}")
            files.add(reference["path"])
        for occurrence in provenance.get("occurrences", []):
            occurrence_source = occurrence.get("source_image")
            if occurrence_source and contained(pack, occurrence_source).is_file():
                files.add(occurrence_source)
            elif occurrence_source:
                raise ValueError(f"Missing residual provenance source: {occurrence_source}")
        for atlas, expected_hash in raster_provenance_references(provenance):
            path = contained(pack, atlas)
            if not path.is_file():
                raise ValueError(f"Missing raw provenance atlas: {atlas}")
            if atlas not in provenance_hashes:
                provenance_hashes[atlas] = hashlib.sha256(path.read_bytes()).hexdigest()
            actual_hash = provenance_hashes[atlas]
            if expected_hash and expected_hash != actual_hash:
                raise ValueError(f"Raw provenance atlas hash mismatch: {atlas}")
            if atlas not in provenance_sizes:
                with Image.open(path) as raster:
                    provenance_sizes[atlas] = list(raster.size)
            # The validator needs this exact raster to verify tight-input
            # normalization coordinates in an extracted collection. Other raw
            # generation atlases remain external unless --include-raw is set.
            if include_raw or atlas == provenance.get('source_rect_image'):
                files.add(atlas)
            else:
                external[atlas] = {"path": atlas, "sha256": actual_hash, "size_px": provenance_sizes[atlas],
                    "location": repository_location, "purpose": "Raw generated view provenance; not required for rendering exported PNGs"}
    for entry in index["maps"]:
        files.add(entry["file"])
        files.add(entry["source"])
    # Existing rebuild/source provenance is retained. Full export additionally
    # retains supplementary generators' extension manifests and procedural demos.
    files.add("README.md")
    if (pack / "reusable/README.md").is_file():
        files.add("reusable/README.md")
    if (pack / "reusable/library-guide.json").is_file():
        files.add("reusable/library-guide.json")
    legacy_manifest = pack / "manifest.json"
    external["manifest.json"] = {"path": "manifest.json", "sha256": hashlib.sha256(legacy_manifest.read_bytes()).hexdigest(),
        "location": repository_location,
        "purpose": "Legacy complete catalog references unrelated animations/contact sheets/ZIPs. Each exported PNG retains its own full extraction metadata; the legacy catalog is not needed to render this archive."}
    if not subset:
        for pattern in ("reusable/views-*/set-index.json", "reusable/scene-assets/index.json", "reusable/procedural/*", "reusable/semantic-placements.json"):
            files.update(p.relative_to(pack).as_posix() for p in pack.glob(pattern) if p.is_file())
    index["statistics"] = {**index.get("statistics", {}), "asset_count": len(index["assets"]), "map_count": len(index["maps"])}
    if subset:
        index["statistics"] = {
            "asset_count": len(index["assets"]), "map_count": len(index["maps"]),
            "existing_components_reused": sum(a["image"]["path"].startswith("components/") for a in index["assets"]),
            "existing_component_pngs_modified": 0,
            "existing_preview_layers_reused": sum(a["kind"] == "composition_layer" for a in index["assets"]),
            "unique_residual_patches": sum(a["kind"] == "reconstruction_patch" and a.get("managed_by") == "pocket-reusable-v1" for a in index["assets"]),
            "residual_placements": sum(m.get("statistics", {}).get("residual_placement_count", 0) for m in index["maps"]),
            "physical_assets_missing_six_views": sum(a.get("views", {}).get("applicable", False) and not a["views"].get("complete", False) for a in index["assets"]),
        }
    index["downloads"] = []
    catalog_content = {key: value for key, value in original.items() if key != "downloads"}
    index["archive"] = {"scope": "selected-maps-and-assets" if subset else "full-catalog",
        "source_catalog_content_sha256": hashlib.sha256(encoded(catalog_content)).hexdigest(),
        "catalog_hash_definition": "SHA-256 of canonical indented JSON with trailing newline, excluding downloads to avoid archive hash cycles",
        "external_provenance_manifest": "reusable/archive-provenance.json"}
    localized_rules = None
    registry_entry = None
    if index.get("attachment_rules"):
        rule_path = (pack / index["attachment_rules"]).resolve()
        assets_root = next((p for p in [pack, *pack.parents] if p.name == "assets"), None)
        if assets_root is None or not rule_path.is_relative_to(assets_root):
            raise ValueError("Attachment rules must remain inside the repository assets root")
        if not rule_path.is_file():
            raise ValueError("Build central attachment-rules.json before packaging")
        localized_rules = copy.deepcopy(read_json(rule_path))
        registry = read_json(assets_root / "reusable-library.json")
        entry = next((entry for entry in registry["libraries"] if (assets_root / entry["base"]).resolve() == pack.resolve()), None)
        if entry is None:
            raise ValueError("Pack is missing from the central library registry")
        registry_entry = {**entry, "base": folder, "index": f"{folder}/reusable/index.json"}
        qualified = {entry["id"] + "::" + asset_id for asset_id in asset_ids}
        localized_rules["tiles"] = [tile for tile in localized_rules["tiles"]
                                    if tile["id"] in qualified
                                    and tile.get("asset_id", tile["id"].split("::", 1)[-1]) in asset_ids]
        included_tiles = {tile["id"] for tile in localized_rules["tiles"]}
        wanted_groups = {a.get("attachment", {}).get("compatibility_group") for a in index["assets"]}
        localized_rules["groups"] = [group for group in localized_rules["groups"] if group["id"] in wanted_groups]
        for group in localized_rules["groups"]:
            group["tile_ids"] = [tile for tile in group["tile_ids"] if tile in included_tiles]
            group["preferred_tile_ids"] = [tile for tile in group.get("preferred_tile_ids", [])
                                           if tile in group["tile_ids"]]
            if not group["tile_ids"]:
                group["reason"] = "No compatible provider is included in this independent archive; consult the complete library for additional candidates."
        localized_rules["scope"] = "Attachment candidates projected to assets in this independent archive. Editorial compatibility only."
        index["attachment_rules"] = "reusable/attachment-rules.json"
    contents = {f"{folder}/{relative}": contained(pack,relative).read_bytes() for relative in sorted(files)}
    if review_report is not None:
        review_report = project(review_report, expected_objects(index))
        index['view_review'] = review_reference(review_report)
        contents[f"{folder}/reusable/view-review.json"] = encoded(review_report)
    if legacy_review_report is not None:
        legacy_review_report = project(legacy_review_report, expected_objects(index))
        index['legacy_view_review'] = review_reference(legacy_review_report, legacy=True)
        contents[f"{folder}/reusable/legacy-view-review.json"] = encoded(legacy_review_report)
    if block_report is not None:
        block_report = project_blocks(block_report, expected_objects(index))
        index['generation_blocks'] = block_reference(block_report)
        contents[f"{folder}/reusable/generation-blocks.json"] = encoded(block_report)
        for info in evidence_files(block_report):
            contents[f"{folder}/{info['path']}"] = contained(pack, info['path']).read_bytes()
    # Portable approval evidence closes over the actual reviewed crop, which may
    # be an exactly pixel-equivalent PNG copy outside normal catalog assets.
    for report in (review_report, legacy_review_report):
        for record in (report or {}).get('sets', []):
            evidence = (record.get('review') or {}).get('source_evidence', {})
            for info in (record.get('source'), record.get('primary_source'), evidence.get('reviewed_reference')):
                if info:
                    contents[f"{folder}/{info['path']}"] = contained(pack, info['path']).read_bytes()
    if localized_rules is not None:
        contents[f"{folder}/reusable/attachment-rules.json"] = encoded(localized_rules)
    if registry_entry is not None:
        contents["reusable-library.json"] = encoded({"schema_version": 1, "tags": ["metadata-document", "library-registry"], "libraries": [registry_entry]})
    contents[f"{folder}/reusable/index.json"] = encoded(index)
    contents[f"{folder}/reusable/archive-provenance.json"] = encoded({"tags": ["metadata-document", "external-provenance"], "external_provenance": list(external.values())})
    for filename in (*TOOLS, "build_reusable_library.py", "register_existing_derivatives.py", "asset_attachment_tags.py", "render_art_remix.py", "view_review_contract.py", "generation_block_contract.py", "merge_view_reviews.py", "legacy_view_review_targets.json"):
        if not (Path(__file__).resolve().parent / filename).is_file():
            continue
        contents[filename] = (Path(__file__).resolve().parent / filename).read_bytes()
    contents["usage.json"] = encoded({
        "schema_version": 1,
        "tags": ["metadata-document", "archive-usage", "reconstruction-instructions"],
        "title": original.get("title", "Reusable asset library"),
        "catalog_root": folder + "/",
        "runtime": {"python": "3.12", "requirements": "pocket-requirements.txt"},
        "commands": {
            "install": ["python", "-m", "pip", "install", "-r", "pocket-requirements.txt"],
            "list_maps": ["python", "render_pocket_map.py", "--pack", folder, "--list"],
            "render_map": ["python", "render_pocket_map.py", "--pack", folder, "--map", "MAP_ID", "--output", "recreated.png"],
            "verify": ["python", "validate_pocket_reusable.py", "--pack", folder, "--self-test"],
            "render_remix_from_checkout": ["python", "tools/render_art_remix.py", "--input", "remix.json", "--output", "remix.png"]
        },
        "view_validation": {
            "completeness_option": "--require-six-views",
            "recorded_block_option": "--allow-recorded-generation-blocks",
            "blocked_views_remain_incomplete": True
        },
        "instructions": [
            "Extract each independent collection into its own directory; do not overwrite subset reusable/index.json files with other collections.",
            "Catalog paths resolve relative to catalog_root; PNG sidecars retain provenance.",
            "The Git checkout is the canonical full library. Rebuild it with its extension generators; selected-map archives include only referenced dependencies.",
            "Detached remix rendering requires --art-commit with the recorded trusted revision; mixed-library remixes need every named library.",
            "Reconstruction residuals are not procedural gameplay tiles. Inferred views are newly designed.",
            "Omitted raw generation atlases have repository locations and hashes in archive-manifest.json; they are not required for PNG reuse or reconstruction.",
            "No new licence is granted; consult retained source attribution and repository records."
        ]
    })
    contents["archive-manifest.json"] = encoded({"schema_version": 1, "tags": ["metadata-document", "archive-manifest"], "maps": [m["id"] for m in index["maps"]], "assets": len(index["assets"]), "external_provenance": list(external.values()), "files": [{"path": p, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()} for p,data in sorted(contents.items())], "note": "Lists every archive member except this self-describing manifest."})
    return contents


def write_zip(output, contents, max_bytes):
    if output.suffix.lower() != ".zip":
        raise ValueError("Archive destination must use .zip")
    if max_bytes <= 0:
        raise ValueError("Archive size limit must be positive")
    for name in contents:
        if Path(name).is_absolute() or ".." in Path(name).parts:
            raise ValueError(f"Unsafe archive member path: {name}")
    output.parent.mkdir(parents=True,exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=".pocket-export-",suffix=".zip",dir=output.parent)
    os.close(handle)
    try:
        with zipfile.ZipFile(temporary,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
            for name,data in sorted(contents.items()):
                info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0))
                info.compress_type=zipfile.ZIP_DEFLATED
                info.external_attr=0o100644 << 16
                archive.writestr(info,data)
        size=Path(temporary).stat().st_size
        if size > max_bytes:
            raise ValueError(f"Archive would be {size/1048576:.1f} MiB; limit is {max_bytes/1048576:.1f} MiB. Export smaller groups using repeated --map IDs.")
        os.replace(temporary,output)
        return size
    finally:
        if Path(temporary).exists():
            Path(temporary).unlink()


def main():
    parser=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pack",type=Path,default=DEFAULT_PACK)
    parser.add_argument("--map",dest="maps",action="append",help="Include only this map and transitive dependencies; repeatable")
    parser.add_argument("--asset",dest="assets",action="append",help="Include this asset and its dependencies; repeatable")
    parser.add_argument("--output",type=Path)
    parser.add_argument("--plan",action="store_true")
    parser.add_argument("--include-raw",action="store_true")
    parser.add_argument("--max-mib",type=float,default=95)
    args=parser.parse_args()
    try:
        contents=plan(args.pack.resolve(),args.maps,args.include_raw,args.assets)
        result={"entries":len(contents),"uncompressed_mib":round(sum(map(len,contents.values()))/1048576,2),"maps":args.maps if args.maps is not None else ([] if args.assets else "all"),"assets":args.assets or []}
        if not args.plan:
            if not args.output:
                parser.error("--output is required unless --plan is used")
            result["compressed_mib"]=round(write_zip(args.output,contents,int(args.max_mib*1048576))/1048576,2)
            result["output"]=str(args.output)
            result["sha256"]=hashlib.sha256(args.output.read_bytes()).hexdigest()
        print(json.dumps(result,indent=2))
        return 0
    except (OSError,ValueError,KeyError,TypeError) as exc:
        parser.exit(2,f"package_pocket_reusable: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
