"""Prepare immutable v3 Dark Book metadata snapshots after final metadata freeze.

This script is intentionally not called by build_all.py. Run it only after the
final tag/affected_views metadata pass. It never reads or writes PNG bytes.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path, PurePosixPath

HERE = Path(__file__).resolve().parent
OUT = HERE.parent
BOOK = OUT.parent.parent
INDEX = OUT / 'set-index.json'
MAIN_INDEX = BOOK / 'reusable/index.json'
INSTALLED_V2 = HERE / 'replay-installed-dark-repairs-v2.json'
SNAP_ROOT = OUT / 'prebuilt/replay-canonical-json-v3'
SIDECAR_ROOT = SNAP_ROOT / 'sidecars'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe(root: Path, rel: str) -> Path:
    p = PurePosixPath(rel)
    if p.is_absolute() or '..' in p.parts:
        raise ValueError(f'unsafe relative path: {rel!r}')
    path = (root / Path(*p.parts)).resolve()
    path.relative_to(root.resolve())
    return path


def atomic_immutable(path: Path, data: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(data).hexdigest()
    if path.exists():
        if sha(path) != digest:
            raise RuntimeError(f'refusing to overwrite immutable snapshot: {path}')
        return digest
    temp = path.with_name(path.name + '.tmp')
    temp.write_bytes(data)
    os.replace(temp, path)
    return digest


def validate_provenance(asset: dict) -> None:
    provenance = asset.get('provenance', {})
    for path_key in ('source_image', 'native_plan_image', 'native_front_image'):
        rel = provenance.get(path_key)
        if rel is None:
            continue
        if not isinstance(rel, str) or PurePosixPath(rel).is_absolute() or '..' in PurePosixPath(rel).parts:
            raise ValueError(f"{asset['id']}: unsafe provenance.{path_key}: {rel!r}")
        source = safe(BOOK, rel)
        if not source.is_file():
            raise FileNotFoundError(f"{asset['id']}: missing provenance.{path_key}: {rel}")
        hash_key = {'source_image':'source_sha256', 'native_plan_image':'native_plan_sha256',
                    'native_front_image':'native_front_sha256'}[path_key]
        expected = provenance.get(hash_key)
        if expected and sha(source) != expected:
            raise ValueError(f"{asset['id']}: provenance {hash_key} mismatch")


def main() -> None:
    index_bytes = INDEX.read_bytes()
    index = json.loads(index_bytes)
    main_index_bytes = MAIN_INDEX.read_bytes()
    main_index = json.loads(main_index_bytes)
    main_assets = {a.get('id'): a for a in main_index.get('assets', [])}
    assets = index.get('assets', [])
    ids = [a.get('id') for a in assets]
    if len(ids) != len(set(ids)) or len(ids) != 4464:
        raise ValueError(f'expected 4464 unique assets, got {len(ids)}')
    entries = []
    installed = json.loads(INSTALLED_V2.read_text())
    latest = {}
    for e in installed['entries']:
        latest[e['asset_id']] = e
    by_id = {a['id']: a for a in assets}
    # Validate every current canonical sidecar and PNG before writing snapshots.
    sidecar_payloads = []
    for asset in assets:
        aid = asset['id']
        md_rel = asset['metadata_path']
        png_rel = asset['image']['path']
        md_path = safe(BOOK, md_rel)
        png_path = safe(BOOK, png_rel)
        md_bytes = md_path.read_bytes()
        doc = json.loads(md_bytes)
        if doc.get('id') != aid or doc.get('metadata_path') != md_rel:
            raise ValueError(f'{aid}: sidecar identity/path mismatch')
        if doc.get('image', {}).get('path') != png_rel:
            raise ValueError(f'{aid}: sidecar PNG path mismatch')
        png_sha = sha(png_path)
        if doc['image'].get('sha256') != png_sha or asset['image'].get('sha256') != png_sha:
            raise ValueError(f'{aid}: sidecar/index PNG SHA does not match current PNG')
        validate_provenance(doc)
        validate_provenance(asset)
        main_asset = main_assets.get(aid)
        if not main_asset or main_asset.get('metadata_path') != md_rel or main_asset.get('image', {}).get('path') != png_rel:
            raise ValueError(f'{aid}: main reusable index identity/path mismatch')
        if main_asset.get('image', {}).get('sha256') != png_sha or main_asset.get('provenance') != doc.get('provenance'):
            raise ValueError(f'{aid}: main reusable index mirror differs from canonical sidecar')
        sidecar_payloads.append((aid, md_rel, md_bytes, png_sha))
    # Emit immutable sidecar snapshots and build the exact v3 canonical recipe.
    for aid, md_rel, md_bytes, png_sha in sidecar_payloads:
        snap_rel = f'prebuilt/replay-canonical-json-v3/sidecars/{aid}.json'
        snap_path = safe(OUT, snap_rel)
        digest = atomic_immutable(snap_path, md_bytes)
        entries.append({'asset_id':aid, 'metadata_path':md_rel,
                        'snapshot_path':snap_rel, 'sha256':digest,
                        'image_path':by_id[aid]['image']['path'], 'image_sha256':png_sha})
    index_snapshot_rel = 'prebuilt/replay-canonical-json-v3/set-index.json'
    index_snapshot_path = safe(OUT, index_snapshot_rel)
    index_digest = atomic_immutable(index_snapshot_path, index_bytes)
    main_snapshot_rel = 'prebuilt/replay-canonical-json-v3/main-reusable-index.json'
    main_snapshot_path = safe(OUT, main_snapshot_rel)
    main_digest = atomic_immutable(main_snapshot_path, main_index_bytes)
    canonical = {'recipe_id':'dark-book-canonical-json-v3-post-final-metadata',
                 'metadata_entries':entries, 'set_index_snapshot':index_snapshot_rel,
                 'set_index_sha256':index_digest, 'main_index_snapshot':main_snapshot_rel,
                 'main_index_sha256':main_digest}
    canonical_bytes = (json.dumps(canonical, indent=2) + '\n').encode()
    canonical_path = HERE / 'replay-canonical-json-v3.json'
    atomic_immutable(canonical_path, canonical_bytes)
    # Create a v3 installed-repair recipe whose snapshots have the same final
    # metadata state. Historical v2 bytes and their audit references are kept.
    repaired = json.loads(INSTALLED_V2.read_text())
    entry_map = {e['asset_id']:e for e in entries}
    for e in repaired['entries']:
        snap = entry_map.get(e['asset_id'])
        if snap is not None:
            e['metadata_snapshot_path'] = snap['snapshot_path']
            e['metadata_sha256'] = snap['sha256']
    installed_v3 = (json.dumps(repaired, indent=2) + '\n').encode()
    atomic_immutable(HERE / 'replay-installed-dark-repairs-v3.json', installed_v3)
    print(json.dumps({'recipe_id':canonical['recipe_id'], 'assets':len(entries),
                      'set_index_sha256':index_digest, 'main_index_sha256':main_digest,
                      'installed_repair_entries':len(repaired.get('entries',[])),
                      'pngs_written':0}, indent=2))


if __name__ == '__main__':
    main()
