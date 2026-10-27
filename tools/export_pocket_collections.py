#!/usr/bin/env python3
"""Validate and export independent asset-library download collections.

Each archive carries its own dependency-closed subset index. Extract collections
separately; never merge subset index.json files. The Git checkout is canonical.
Large collections are published as size-limited parts with an ordered JSON
manifest and a hash-verifying assembly helper. Join all parts before extracting.
All archives are staged and independently validated before index.downloads is
updated. Run only after view generation and the catalog rebuild have completed.
The default plan is Pocket Dungeon's six collections. Other libraries require a
JSON --collections-plan with schema_version: 1 and collections containing id,
label, maps, and optional assets (for components not referenced by source maps).
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import sys
import tempfile
import zipfile

sys.dont_write_bytecode = True

from package_pocket_reusable import asset_dependencies, encoded, plan, write_zip
from validate_pocket_reusable import DEFAULT_PACK, contained, read_json, unique_records, validate
from assemble_archive_parts import assemble, file_hash

COLLECTIONS = (
    ("scenes", "Concept scenes and layered preview", ("concept-original", "concept-new", "concept-combat", "preview")),
    ("core", "Core dungeon, UI and supplies", ("atlas-world", "atlas-ui", "atlas-expansion", "atlas-supplies", "atlas-biomes", "atlas-services")),
    ("equipment", "Weapons, armor and gear", ("atlas-arsenal", "atlas-armor", "atlas-gear")),
    ("outdoor", "Settlements, roads and forests", ("atlas-settlements", "atlas-roads", "atlas-forest")),
    ("underground", "Highlands and caverns", ("atlas-highlands", "atlas-caverns")),
    ("motion", "Attacks and spell effects", ("atlas-attacks", "atlas-spells")),
)


def catalog_hash(index):
    return hashlib.sha256(encoded({key: value for key, value in index.items() if key != "downloads"})).hexdigest()


def collection_records(document=None):
    if document is None:
        return [{"id": key, "label": label, "maps": list(maps), "assets": []}
                for key, label, maps in COLLECTIONS]
    if not isinstance(document, dict) or document.get("schema_version") != 1:
        raise ValueError("Collection plan must have schema_version 1")
    records = document.get("collections")
    if not isinstance(records, list) or not records:
        raise ValueError("Collection plan must contain a nonempty collections list")
    seen = set()
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Each collection must be an object")
        key = record.get("id")
        if not isinstance(key, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", key) or key in seen:
            raise ValueError(f"Invalid or duplicate collection id: {key}")
        seen.add(key)
        if not isinstance(record.get("label"), str) or not record["label"].strip():
            raise ValueError(f"Collection needs a label: {key}")
        for field in ("maps", "assets"):
            values = record.get(field, [])
            if not isinstance(values, list) or any(not isinstance(v, str) or not v for v in values):
                raise ValueError(f"Collection {key}: {field} must be a list of ids")
            if len(set(values)) != len(values):
                raise ValueError(f"Collection {key}: duplicate {field}")
        if not record.get("maps") and not record.get("assets"):
            raise ValueError(f"Empty collection: {key}")
    return [{"id": r["id"], "label": r["label"], "maps": r.get("maps", []),
             "assets": r.get("assets", [])} for r in records]


def check_coverage(index, collections=None):
    collections = collection_records() if collections is None else collections
    expected = set(unique_records(index["maps"], "id", "catalog maps"))
    assigned = [map_id for record in collections for map_id in record["maps"]]
    if len(assigned) != len(set(assigned)):
        raise ValueError("A reconstruction map is assigned to multiple collections")
    if expected != set(assigned):
        raise ValueError(f"Collection coverage mismatch: missing={sorted(expected-set(assigned))}, unknown={sorted(set(assigned)-expected)}")
    assets = set(unique_records(index["assets"], "id", "catalog assets"))
    unknown = {a for r in collections for a in r.get("assets", [])} - assets
    if unknown:
        raise ValueError(f"Unknown collection assets: {sorted(unknown)}")


def archive_catalog(contents):
    candidates = [name for name in ("pocket-dungeon/reusable/index.json", "library/reusable/index.json") if name in contents]
    if len(candidates) != 1:
        raise ValueError("Archive must contain exactly one supported library catalog")
    return candidates[0]


def create_collection_plan(pack, maps_per_collection=4):
    """Draft map batches plus dependency-closed batches of unmapped assets.

    This inventories metadata only. Export still enforces current independent
    reviews, pixel-exact maps, ZIP size, hashes, and complete asset coverage.
    """
    if maps_per_collection < 1:
        raise ValueError("maps-per-collection must be positive")
    index = read_json(pack / 'reusable/index.json')
    maps = list(unique_records(index['maps'], 'id', 'catalog maps').values())
    all_assets = set(unique_records(index['assets'], 'id', 'catalog assets'))
    covered = set()
    collections = []
    for start in range(0, len(maps), maps_per_collection):
        batch = maps[start:start+maps_per_collection]
        selected = {layer['asset_id'] for entry in batch
                    for layer in read_json(contained(pack, entry['file']))['layers']}
        covered.update(asset_dependencies(index, selected))
        number = len(collections) + 1
        collections.append({'id': f'maps-{number:03}', 'label': f'Reconstructions {number}',
                            'maps': [m['id'] for m in batch], 'assets': []})
    remaining = all_assets - covered
    number = 0
    while remaining:
        seeds = []
        # Each seed can pull in a whole six-view object; avoid repeating seeds
        # already brought in by a sibling/canonical dependency.
        for _ in range(24):
            if not remaining:
                break
            seed = min(remaining)
            seeds.append(seed)
            remaining.difference_update(asset_dependencies(index, [seed]))
        number += 1
        collections.append({'id': f'assets-{number:03}', 'label': f'Additional assets {number}',
                            'maps': [], 'assets': seeds})
    document = {'schema_version': 1, 'tags': ['metadata-document', 'download-collection-plan'],
                'source_catalog_content_sha256': catalog_hash(index),
                'status': 'unvalidated-plan',
                'note': 'Regenerate after catalog changes. Export verifies content and size; split oversized collections.',
                'collections': collections}
    check_coverage(index, collection_records(document))
    return document


def verify_archive(path, work, allow_recorded_blocks=False):
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise ValueError(f"ZIP CRC check failed: {path.name}")
        for name in archive.namelist():
            if Path(name).is_absolute() or ".." in Path(name).parts:
                raise ValueError(f"Unsafe archive member: {name}")
        archive.extractall(work)
    manifest = read_json(work / "archive-manifest.json")
    expected = {item["path"] for item in manifest["files"]}
    actual = {item.relative_to(work).as_posix() for item in work.rglob("*") if item.is_file()}
    if actual != expected | {"archive-manifest.json"}:
        raise ValueError(f"Archive manifest is incomplete: {path.name}")
    for item in manifest["files"]:
        file = work / item["path"]
        if file.stat().st_size != item["size"] or hashlib.sha256(file.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError(f"Archive integrity mismatch: {path.name}/{item['path']}")
    catalog = archive_catalog(actual)
    options = {'allow_recorded_blocks': True} if allow_recorded_blocks else {}
    return validate(work / Path(catalog).parts[0], require_views=True, **options)


def stage_download(archive, max_bytes):
    """Keep small ZIPs intact; larger collections use ordered, verified parts."""
    if max_bytes <= 0:
        raise ValueError('Download size limit must be positive')
    size, digest = archive.stat().st_size, file_hash(archive)
    common = {'archive_bytes': size, 'archive_sha256': digest}
    if size < max_bytes:
        return {**common, 'format': 'zip', 'name': archive.name, 'bytes': size,
                'sha256': digest, 'parts': []}, [archive.name]
    # Strictly below the stated cap, including exact-multiple boundaries.
    part_size = max_bytes - 1
    if part_size <= 0:
        raise ValueError('Multipart size limit is too small')
    rows = []
    with archive.open('rb') as source:
        while block := source.read(part_size):
            number = len(rows) + 1
            path = archive.with_name(f'{archive.name}.part-{number:03d}')
            path.write_bytes(block)
            rows.append({'number': number, 'file': path.name, 'bytes': len(block),
                         'sha256': hashlib.sha256(block).hexdigest()})
    manifest = archive.with_name(archive.name + '.parts.json')
    doc = {'schema_version': 1, 'kind': 'multipart-zip',
           'tags': ['attachment-tagged', 'metadata-document', 'multipart-archive'],
           'archive': {'file': archive.name, 'bytes': size, 'sha256': digest},
           'parts': rows, 'assembly': {'operation': 'concatenate-in-listed-order',
             'tool': 'assemble_archive_parts.py',
             'command': f'python assemble_archive_parts.py {manifest.name} --output {archive.name}',
             'note': 'Download every part beside this JSON. Assemble and verify the ZIP before extracting it into its own directory.'}}
    helper = manifest.parent / 'assemble_archive_parts.py'
    helper.write_bytes(Path(__file__).with_name('assemble_archive_parts.py').read_bytes())
    doc['assembly']['tool_sha256'] = file_hash(helper)
    doc['assembly']['tool_bytes'] = helper.stat().st_size
    manifest.write_bytes(encoded(doc))
    # Reassemble the actual staged bytes, then validate that assembled ZIP below.
    archive.unlink()
    assemble(manifest, archive)
    return {**common, 'format': 'multipart-zip', 'name': manifest.name,
            'bytes': manifest.stat().st_size, 'sha256': file_hash(manifest), 'parts': rows,
            'assembly_tool': {'file': helper.name, 'bytes': helper.stat().st_size,
                              'sha256': file_hash(helper)}}, [manifest.name, helper.name, *[r['file'] for r in rows]]


def export(pack, max_mib=95, dry_run=False, collections_plan=None, allow_recorded_blocks=False):
    index_path = pack / "reusable/index.json"
    original = read_json(index_path)
    if collections_plan is None and pack.resolve() != DEFAULT_PACK.resolve():
        raise ValueError("Other libraries require an explicit --collections-plan JSON")
    collections = collection_records(collections_plan)
    check_coverage(original, collections)
    baseline = catalog_hash(original)
    validation = validate(pack, require_views=True, allow_recorded_blocks=allow_recorded_blocks)
    if dry_run:
        return {"status": "validated-plan-with-recorded-generation-blocks" if validation.get('recorded_blocked_set_count', 0) else "validated-plan", "catalog_content_sha256": baseline,
                "recorded_generation_blocks": validation.get('recorded_generation_blocks', []),
                "maps": validation["maps_pixel_exact"],
                "collections": collections}
    downloads = []
    staged_files = set()
    destination = pack / "reusable/downloads"
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".pocket-export-", dir=destination) as temporary:
        staging = Path(temporary)
        covered_assets = set()
        prefix = "pocket" if pack.resolve() == DEFAULT_PACK.resolve() else pack.name
        for record in collections:
            key, label, maps = record["id"], record["label"], record["maps"]
            print(f"Building and validating {key} ({len(maps)} maps)", flush=True)
            contents = plan(pack, list(maps), selected_assets=record["assets"])
            subset = json.loads(contents[archive_catalog(contents)])
            covered_assets.update(a["id"] for a in subset["assets"])
            archive_name = f"{prefix}-{key}.zip"
            archive = staging / archive_name
            # Temporary assembled ZIPs may exceed the per-file publication cap.
            # An uncompressed upper bound avoids discarding valid large closures.
            budget = max(int(max_mib * 1048576), sum(len(data) for data in contents.values()) + len(contents) * 1024 + 1048576)
            write_zip(archive, contents, budget)
            download, files = stage_download(archive, int(max_mib * 1048576))
            staged_files.update(files)
            with tempfile.TemporaryDirectory(prefix="pocket-unpack-") as extracted:
                result = verify_archive(archive, Path(extracted), allow_recorded_blocks)
            relative = f"reusable/downloads/{download['name']}"
            downloads.append({"id": key, "label": label, "path": relative, "file": relative,
                **{k: v for k, v in download.items() if k != 'name'},
                'parts': [{**row, 'path': 'reusable/downloads/' + row['file']} for row in download['parts']],
                "maps": list(maps), "assets": record["assets"], "asset_count": result["assets_checked"],
                "pixel_exact_maps": result["maps_pixel_exact"],
                "recorded_generation_blocks": result.get('recorded_generation_blocks', []),
                "description": "Assemble all parts using the JSON manifest, then extract this independent collection separately." if download['parts'] else "Independent collection; extract separately. Do not merge subset indexes."})
            if download['parts']:
                downloads[-1]['assembly_tool']['path'] = 'reusable/downloads/' + download['assembly_tool']['file']
                archive.unlink()
        expected_assets = {a["id"] for a in original["assets"]}
        if covered_assets != expected_assets:
            raise ValueError(f"Collection asset coverage mismatch: missing={sorted(expected_assets-covered_assets)}, unknown={sorted(covered_assets-expected_assets)}")
        current = read_json(index_path)
        if catalog_hash(current) != baseline:
            raise ValueError("Catalog changed during export; staged downloads were not published")
        # Detect edits to source PNGs that occurred without rebuilding the catalog.
        validate(pack, require_views=True, allow_recorded_blocks=allow_recorded_blocks)
        for name in sorted(staged_files):
            os.replace(staging / name, destination / name)
        current["downloads"] = downloads
        temporary_index = staging / "index.json"
        temporary_index.write_bytes(encoded(current))
        os.replace(temporary_index, index_path)
    return {"status": "exported-and-validated-with-recorded-generation-blocks" if validation.get('recorded_blocked_set_count', 0) else "exported-and-validated", "catalog_content_sha256": baseline,
            "recorded_generation_blocks": validation.get('recorded_generation_blocks', []),
            "maps": validation["maps_pixel_exact"], "downloads": downloads}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pack", type=Path, default=DEFAULT_PACK)
    parser.add_argument("--max-mib", type=float, default=95)
    parser.add_argument("--plan", action="store_true", help="Validate the full library and show collection coverage without writing")
    parser.add_argument("--allow-recorded-generation-blocks", action="store_true",
                        help="Allow only packaged hash-bound tool blocks; affected views remain unapproved")
    parser.add_argument("--collections-plan", type=Path, help="JSON collection definitions for this library")
    parser.add_argument("--write-collections-plan", type=Path, help="Write a draft JSON plan without exporting or approving artwork")
    parser.add_argument("--maps-per-collection", type=int, default=4, help="Maximum maps per generated draft collection")
    args = parser.parse_args()
    try:
        if args.write_collections_plan:
            if args.collections_plan or args.plan:
                raise ValueError("--write-collections-plan cannot be combined with --collections-plan or --plan")
            document = create_collection_plan(args.pack.resolve(), args.maps_per_collection)
            args.write_collections_plan.write_bytes(encoded(document))
            print(json.dumps({'status': 'unvalidated-plan', 'path': str(args.write_collections_plan),
                              'collections': len(document['collections'])}, indent=2))
            return 0
        document = read_json(args.collections_plan) if args.collections_plan else None
        print(json.dumps(export(args.pack.resolve(), args.max_mib, args.plan, document,
                                args.allow_recorded_generation_blocks), indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as exc:
        parser.exit(2, f"export_pocket_collections: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
