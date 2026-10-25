#!/usr/bin/env python3
"""Validate and export six independent Pocket Dungeon download collections.

Each archive carries its own dependency-closed subset index. Extract collections
separately; never merge subset index.json files. The Git checkout is canonical.
All six archives are staged and independently validated before index.downloads is
updated. Run only after view generation and the catalog rebuild have completed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import zipfile

sys.dont_write_bytecode = True

from package_pocket_reusable import encoded, plan, write_zip
from validate_pocket_reusable import DEFAULT_PACK, read_json, unique_records, validate

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


def check_coverage(index):
    expected = set(unique_records(index["maps"], "id", "catalog maps"))
    assigned = [map_id for _, _, maps in COLLECTIONS for map_id in maps]
    if len(assigned) != len(set(assigned)):
        raise ValueError("A reconstruction map is assigned to multiple collections")
    if expected != set(assigned):
        raise ValueError(f"Collection coverage mismatch: missing={sorted(expected-set(assigned))}, unknown={sorted(set(assigned)-expected)}")


def verify_archive(path, work):
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
    return validate(work / "pocket-dungeon", require_views=True)


def export(pack, max_mib=95, dry_run=False):
    index_path = pack / "reusable/index.json"
    original = read_json(index_path)
    check_coverage(original)
    baseline = catalog_hash(original)
    validation = validate(pack, require_views=True)
    if dry_run:
        return {"status": "validated-plan", "catalog_content_sha256": baseline,
                "maps": validation["maps_pixel_exact"],
                "collections": [{"id": key, "label": label, "maps": list(maps)} for key, label, maps in COLLECTIONS]}
    downloads = []
    destination = pack / "reusable/downloads"
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".pocket-export-", dir=destination) as temporary:
        staging = Path(temporary)
        for key, label, maps in COLLECTIONS:
            print(f"Building and validating {key} ({len(maps)} maps)", flush=True)
            contents = plan(pack, list(maps))
            archive_name = f"pocket-{key}.zip"
            archive = staging / archive_name
            byte_count = write_zip(archive, contents, int(max_mib * 1048576))
            with tempfile.TemporaryDirectory(prefix="pocket-unpack-") as extracted:
                result = verify_archive(archive, Path(extracted))
            relative = f"reusable/downloads/{archive_name}"
            downloads.append({"id": key, "label": label, "path": relative, "file": relative,
                "bytes": byte_count, "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
                "maps": list(maps), "asset_count": result["assets_checked"],
                "pixel_exact_maps": result["maps_pixel_exact"],
                "description": "Independent collection; extract separately. Do not merge subset indexes."})
        current = read_json(index_path)
        if catalog_hash(current) != baseline:
            raise ValueError("Catalog changed during export; staged downloads were not published")
        # Detect edits to source PNGs that occurred without rebuilding the catalog.
        validate(pack, require_views=True)
        for item in downloads:
            name = Path(item["path"]).name
            os.replace(staging / name, destination / name)
        current["downloads"] = downloads
        temporary_index = staging / "index.json"
        temporary_index.write_bytes(encoded(current))
        os.replace(temporary_index, index_path)
    return {"status": "exported-and-validated", "catalog_content_sha256": baseline,
            "maps": validation["maps_pixel_exact"], "downloads": downloads}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pack", type=Path, default=DEFAULT_PACK)
    parser.add_argument("--max-mib", type=float, default=95)
    parser.add_argument("--plan", action="store_true", help="Validate the full library and show collection coverage without writing")
    args = parser.parse_args()
    try:
        print(json.dumps(export(args.pack.resolve(), args.max_mib, args.plan), indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as exc:
        parser.exit(2, f"export_pocket_collections: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
