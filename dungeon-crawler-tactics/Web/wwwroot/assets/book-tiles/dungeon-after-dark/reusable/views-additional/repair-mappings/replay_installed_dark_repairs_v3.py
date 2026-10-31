"""Replay latest installed corrections with hash guards and supersession handling."""
from pathlib import Path
import hashlib
import json
import os

HERE = Path(__file__).resolve().parent
OUT = HERE.parent
BOOK = OUT.parent.parent
SPEC = json.loads((HERE / 'replay-installed-dark-repairs-v3.json').read_text())
INDEX = OUT / 'set-index.json'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def safe(root, rel):
    path = (root / rel).resolve()
    path.relative_to(root.resolve())
    return path


idx = json.loads(INDEX.read_text())
assets = {asset['id']: asset for asset in idx['assets']}
prepared = []
history = {}
latest = {}
for entry in SPEC['entries']:
    history.setdefault(entry['asset_id'], []).append(entry)
    latest[entry['asset_id']] = entry

# A handful of historical base_sha256 values predate the exact current base
# recipe. Permit only bytes observed in a successful fresh base build, with
# its builder/spec/source inputs and each expected correction bound by hashes.
base_build = {}
base_proof_rel = SPEC.get('base_build_reconciliation_path')
if base_proof_rel:
    proof_path = safe(OUT, base_proof_rel)
    assert sha(proof_path) == SPEC.get('base_build_reconciliation_sha256'), 'base-build proof changed'
    proof = json.loads(proof_path.read_text())
    assert proof.get('schema_version') == 1 and proof.get('kind') == 'dark-fresh-base-output-reconciliation'
    builder = safe(BOOK, 'reusable/views-additional/build_all.py')
    assert sha(builder) == proof.get('base_builder_sha256'), 'base builder differs from reconciled run'
    for binding in proof.get('builder_input_files', []):
        path = safe(BOOK, binding['path'])
        assert sha(path) == binding['sha256'], f"base builder input changed: {binding['path']}"
    start_index = proof['starting_set_index_snapshot']
    assert sha(safe(BOOK, start_index['path'])) == start_index['sha256'], 'base build starting index changed'
    for row in proof.get('rows', []):
        aid = row['asset_id']
        assert aid not in base_build, f'{aid}: duplicate regenerated-base proof row'
        entry = latest.get(aid)
        assert entry and row['image_path'] == entry['image_path'], f'{aid}: regenerated-base proof has wrong target'
        assert row['historical_base_sha256'] == entry['base_sha256']
        assert row['expected_final_sha256'] == entry['final_sha256']
        assert row['candidate_path'] == entry['candidate_path'] and row['candidate_sha256'] == entry['candidate_sha256']
        candidate = safe(OUT, row['candidate_path'])
        assert sha(candidate) == row['candidate_sha256'], f'{aid}: correction candidate changed'
        snapshot = safe(OUT, row['metadata_snapshot_path'])
        assert row['metadata_snapshot_path'] == entry['metadata_snapshot_path']
        assert sha(snapshot) == row['metadata_sha256'] == entry['metadata_sha256'], f'{aid}: canonical snapshot changed'
        for dependency in row.get('verified_inputs', []):
            path = safe(BOOK, dependency['path'])
            assert sha(path) == dependency['sha256'], f"{aid}: base input changed: {dependency['path']}"
        base_build[aid] = row['fresh_base_sha256']

# The recipe is ordered history; only the final correction for an asset is
# authoritative. Earlier hashes are accepted only as recovery bases. This
# prevents a prior snapshot from silently replacing later review-backed art.
for entry in latest.values():
    asset_id = entry['asset_id']
    assert asset_id in assets
    candidate = safe(OUT, entry['candidate_path'])
    assert sha(candidate) == entry['candidate_sha256'], f'{asset_id}: candidate changed'
    # metadata_snapshot_path is emitted by the v3 refresher relative to OUT
    # (reusable/views-additional), like canonical-json-v3.snapshot_path.
    snapshot = safe(OUT, entry['metadata_snapshot_path'])
    assert sha(snapshot) == entry['metadata_sha256'], f'{asset_id}: sidecar snapshot changed'
    asset = json.loads(snapshot.read_text())
    assert asset['id'] == asset_id
    assert asset['image']['path'] == entry['image_path']
    assert asset['metadata_path'] == entry['metadata_path']

    destination = safe(BOOK, entry['image_path'])
    metadata_destination = safe(BOOK, entry['metadata_path'])
    current_png = sha(destination) if destination.exists() else None
    allowed_png = {None, entry['base_sha256'], entry['final_sha256']}
    allowed_png.update(old['final_sha256'] for old in history[asset_id])
    allowed_png.update(old['base_sha256'] for old in history[asset_id])
    if asset_id in base_build:
        allowed_png.add(base_build[asset_id])
    assert current_png in allowed_png, f'{asset_id}: unexpected/stale output {current_png}'

    current_metadata = sha(metadata_destination) if metadata_destination.exists() else None
    allowed_metadata = {None, entry['metadata_sha256']}
    allowed_metadata.update(old['metadata_sha256'] for old in history[asset_id])
    rebuilt_metadata = False
    if current_metadata not in allowed_metadata:
        # build_all may have regenerated this view through process_prebuilt_views,
        # which refreshes set-index.json but leaves the previous sidecar bytes.
        # Accept that transient sidecar only when identity/path still match and
        # the rebuilt index binds the exact permitted PNG hash; the frozen
        # snapshot below replaces it after replay.
        current_doc = json.loads(metadata_destination.read_text()) if metadata_destination.exists() else None
        rebuilt_metadata = bool(
            current_doc
            and current_doc.get('id') == asset_id
            and current_doc.get('metadata_path') == entry['metadata_path']
            and current_doc.get('image', {}).get('path') == entry['image_path']
            and current_png is not None
            and current_png in allowed_png
            and assets[asset_id].get('image', {}).get('sha256') == current_png
        )
        assert rebuilt_metadata, f'{asset_id}: unexpected/stale metadata {current_metadata}'
    prepared.append((entry, asset, candidate, destination, metadata_destination,
                     snapshot, current_png, current_metadata, rebuilt_metadata))

for (entry, asset, candidate, destination, metadata_destination, snapshot,
     current_png, current_metadata, rebuilt_metadata) in prepared:
    if current_png != entry['final_sha256']:
        destination.parent.mkdir(parents=True, exist_ok=True)
        temp = destination.with_name(destination.name + '.tmp')
        temp.write_bytes(candidate.read_bytes())
        os.replace(temp, destination)
    assert sha(destination) == entry['final_sha256']

    if current_metadata != entry['metadata_sha256']:
        metadata_destination.parent.mkdir(parents=True, exist_ok=True)
        temp = metadata_destination.with_name(metadata_destination.name + '.tmp')
        temp.write_bytes(snapshot.read_bytes())
        os.replace(temp, metadata_destination)
    assert sha(metadata_destination) == entry['metadata_sha256']
    assets[entry['asset_id']].clear()
    assets[entry['asset_id']].update(asset)

# Set-level contracts are separate from leaf provenance. Keep explicit group
# symmetry declarations in the catalog during replay instead of relying on
# narrative notes embedded in each sidecar.
view_sets = {item['object_id']: item for item in idx.get('view_sets', [])}
for override in SPEC.get('view_set_overrides', []):
    object_id = override['object_id']
    assert object_id in view_sets, f'{object_id}: missing view set for metadata override'
    target = view_sets[object_id]
    for key, value in override.items():
        if key == 'object_id':
            continue
        target[key] = value

temp = INDEX.with_name(INDEX.name + '.tmp')
temp.write_text(json.dumps(idx, indent=2) + '\n')
os.replace(temp, INDEX)
print(json.dumps({
    'recipe_id': SPEC['recipe_id'],
    'replayed_pngs': len(prepared),
    'replayed_sidecars': len(prepared),
    'replaced_rebuilt_base_sidecars': sum(1 for row in prepared if row[-1]),
    'history_entries': len(SPEC['entries']),
    'authoritative_assets': len(latest),
}, indent=2))
