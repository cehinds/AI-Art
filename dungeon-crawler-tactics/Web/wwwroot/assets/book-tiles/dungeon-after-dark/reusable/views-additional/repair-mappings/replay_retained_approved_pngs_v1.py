"""Restore explicitly retained, independently approved PNG inputs before canonical metadata replay.

These bytes are retained final artifacts, not claims of regeneration from an atlas.
"""
from __future__ import annotations
import hashlib
import json
import os
import struct
from pathlib import Path, PurePosixPath
from PIL import Image

HERE = Path(__file__).resolve().parent
OUT = HERE.parent
BOOK = OUT.parent.parent
MANIFEST_PATH = HERE / 'retained-approved-pngs-v1.json'
MANIFEST_SHA256 = '08a0f7cefb092b6b98feff9c218a872b4c3e026d7821c6fa67f8a188dad3d5a8'

def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())
def safe(root: Path, rel: str) -> Path:
    part = PurePosixPath(rel)
    if part.is_absolute() or '..' in part.parts:
        raise ValueError(f'unsafe relative path: {rel!r}')
    out = (root / Path(*part.parts)).resolve()
    out.relative_to(root.resolve())
    return out

if sha_file(MANIFEST_PATH) != MANIFEST_SHA256:
    raise ValueError('retained-approved PNG manifest SHA-256 mismatch')
manifest = json.loads(MANIFEST_PATH.read_text())
if manifest.get('status') != 'explicit-retained-approved-png-inputs' or manifest.get('count') != 97 or len(manifest.get('entries', [])) != 97:
    raise ValueError('unexpected retained-approved PNG manifest scope')
review = safe(BOOK, manifest['review_path'])
if sha_file(review) != manifest['review_sha256']:
    raise ValueError('current whole-set review changed since retained-input approval')
review_doc = json.loads(review.read_text())
review_sets = {r['object_id']: r for r in review_doc.get('sets', [])}
# Verify the exact canonical index snapshots used to bind the retained rows. The
# live set-index is a rebuilt intermediate here, so row identity/source fields
# are checked against this immutable snapshot rather than a stale whole-file hash.
canonical_index_path = safe(OUT, 'prebuilt/replay-canonical-json-v3/set-index.json')
canonical_main_path = safe(OUT, 'prebuilt/replay-canonical-json-v3/main-reusable-index.json')
if sha_file(canonical_index_path) != manifest['canonical_set_index_sha256']:
    raise ValueError('canonical set-index binding changed')
if sha_file(canonical_main_path) != manifest['canonical_main_index_sha256']:
    raise ValueError('canonical main-index binding changed')
canonical_index = json.loads(canonical_index_path.read_text())
canonical_assets = {a['id']: a for a in canonical_index.get('assets', [])}
canonical_main = json.loads(canonical_main_path.read_text())
canonical_main_assets = {a['id']: a for a in canonical_main.get('assets', [])}
index_path = OUT / 'set-index.json'
index = json.loads(index_path.read_text())
assets = {a['id']: a for a in index.get('assets', [])}
if len(assets) != 4464 or len(canonical_assets) != 4464 or len(canonical_main_assets) != 16698:
    raise ValueError('retained-input replay requires 4464 view assets and 16698 main-index assets')
prepared = []
seen = set()
for row in manifest['entries']:
    aid = row['asset_id']
    if aid in seen:
        raise ValueError(f'duplicate retained-input target: {aid}')
    seen.add(aid)
    asset = assets.get(aid)
    canonical_asset = canonical_assets.get(aid)
    canonical_main_asset = canonical_main_assets.get(aid)
    if asset is None or canonical_asset is None or canonical_main_asset is None:
        raise ValueError(f'{aid}: target absent from rebuilt or canonical index')
    for label, bound in (('rebuilt', asset), ('canonical', canonical_asset), ('main-canonical', canonical_main_asset)):
        if (bound.get('object_id'), bound.get('view'), bound.get('image', {}).get('path')) != (row['object_id'], row['view'], row['image_path']):
            raise ValueError(f'{aid}: {label} index identity/path differs from frozen binding')
    if canonical_asset.get('image', {}).get('sha256') != row['image_sha256'] or canonical_asset.get('image', {}).get('rgba_sha256') != row['image_rgba_sha256']:
        raise ValueError(f'{aid}: canonical index no longer binds retained PNG bytes')
    source = asset.get('source', {})
    canonical_source = canonical_asset.get('source', {})
    main_source = canonical_main_asset.get('source', {})
    if any((s.get('object_id'), s.get('source_image'), s.get('source_sha256')) != (row['object_id'], row['source_path'], row['source_sha256']) for s in (canonical_source, main_source)):
        raise ValueError(f'{aid}: canonical index source binding differs from retained record')
    if (source.get('object_id'), source.get('source_image'), source.get('source_sha256')) != (row['object_id'], row['source_path'], row['source_sha256']):
        raise ValueError(f'{aid}: rebuilt set-index source binding differs from frozen source')
    source_path = safe(BOOK, row['source_path'])
    if sha_file(source_path) != row['source_sha256']:
        raise ValueError(f'{aid}: canonical source input changed')
    approved = review_sets.get(row['object_id'])
    if not approved or approved.get('status') != 'passed' or approved.get('complete') is not True:
        raise ValueError(f'{aid}: whole-set approval no longer passes')
    view_record = approved.get('views', {}).get(row['view'], {})
    if view_record.get('path') != row['review_view_path'] or view_record.get('sha256') != row['review_view_sha256'] or view_record.get('sha256') != row['image_sha256']:
        raise ValueError(f'{aid}: review does not bind retained output')
    retained = safe(OUT, row['retained_input_path'])
    data = retained.read_bytes()
    if sha_bytes(data) != row['retained_input_sha256'] or row['retained_input_sha256'] != row['image_sha256']:
        raise ValueError(f'{aid}: retained PNG input hash mismatch')
    from io import BytesIO
    with Image.open(BytesIO(data)) as image:
        image.load()
        rgba = image.convert('RGBA')
        rgba_sha = sha_bytes(struct.pack('>II', rgba.width, rgba.height) + rgba.tobytes())
        size = list(rgba.size)
    if rgba_sha != row['image_rgba_sha256'] or size != row['dimensions_px']:
        raise ValueError(f'{aid}: retained PNG dimensions/RGBA hash mismatch')
    destination = safe(BOOK, row['image_path'])
    prepared.append((row, asset, data, destination))
# Do not write any output until every input, source, review and index binding passed.
dry_run = os.environ.get('DARK_RETAINED_REPLAY_DRY_RUN') == '1'
if not dry_run:
  for row, asset, data, destination in prepared:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = destination.with_name(destination.name + '.retained.tmp')
    temp.write_bytes(data)
    os.replace(temp, destination)
    asset['image']['sha256'] = row['image_sha256']
    asset['image']['rgba_sha256'] = row['image_rgba_sha256']
  # Keep rebuilt index hashes aligned with the restored PNGs; canonical JSON replay follows.
  temp_index = index_path.with_name(index_path.name + '.retained.tmp')
  temp_index.write_text(json.dumps(index, indent=2, ensure_ascii=False) + '\n')
  os.replace(temp_index, index_path)
print(json.dumps({'recipe_id': manifest['recipe_id'], 'retained_png_inputs': len(prepared), 'pngs_written': 0 if dry_run else len(prepared), 'dry_run': dry_run, 'index_sha256': sha_file(index_path), 'retention_semantics': 'exact approved PNG artifact copy; not regenerated from atlas'}, indent=2))
