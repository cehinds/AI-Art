#!/usr/bin/env python3
"""Restore exact reviewed Pocket outputs where historical replay recipes are superseded."""
from pathlib import Path
import hashlib, json, shutil

OUT = Path(__file__).resolve().parent
PACK = OUT.parents[1]
MANIFEST = OUT / 'raw/replay-retained/replay-retained-manifest.json'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

manifest = json.loads(MANIFEST.read_text())
baseline_path = OUT / 'replay-baseline.json'
if not baseline_path.is_file():
    raise SystemExit('missing frozen replay-baseline.json')
baseline = json.loads(baseline_path.read_text())
if baseline.get('set_index_sha256') != manifest['release_set_index_sha256']:
    raise SystemExit('retained-output manifest is bound to a different release set-index')

index_target = PACK / baseline['set_index_path']
index_snapshot = OUT / manifest['release_index_snapshot_path']
if sha(index_snapshot) != manifest['release_index_snapshot_sha256']:
    raise SystemExit('retained set-index snapshot hash mismatch')
pre_overlay_index_sha256 = sha(index_target)
if pre_overlay_index_sha256 not in (manifest['replay_before_overlay_set_index_sha256'], manifest['release_set_index_sha256']):
    # Superseded-op skips can change transient QA flags in this index. Require
    # exact identities and all leaf hashes below; the frozen index is restored last.
    transient = json.loads(index_target.read_text())
    expected_assets = {f"{g['object_id']}.{v}": (row['image_path'], row['metadata_path'])
                       for g in baseline['sets'] for v, row in g['views'].items()}
    actual_assets = {a.get('id'): (a.get('image', {}).get('path'), a.get('metadata_path'))
                     for a in transient.get('assets', [])}
    expected_sets = {g['object_id'] for g in baseline['sets']}
    actual_sets = {g.get('object_id') for g in transient.get('view_sets', [])}
    if actual_assets != expected_assets or actual_sets != expected_sets:
        raise SystemExit('transient replay index structure differs from frozen asset/set identities')

baseline_leaves = {
    (group['object_id'], view): row
    for group in baseline['sets']
    for view, row in group['views'].items()
}
restored_png = restored_metadata = 0
for leaf in manifest['leaves']:
    key = (leaf['object_id'], leaf['view'])
    row = baseline_leaves.get(key)
    if row is None or leaf['asset_id'] != f"{leaf['object_id']}.{leaf['view']}":
        raise SystemExit(f"unknown or mismatched leaf identity: {key}")
    if row['image_sha256'] != leaf['release_image_sha256'] or row['metadata_sha256'] != leaf['release_metadata_sha256']:
        raise SystemExit(f"leaf release hash differs from frozen baseline: {key}")
    source_rel = leaf['source_path']
    if baseline['sources'].get(source_rel) != leaf['source_sha256'] or sha(PACK / source_rel) != leaf['source_sha256']:
        raise SystemExit(f"canonical source identity/hash mismatch: {key}")

    png_target = PACK / row['image_path']
    if 'image_snapshot_path' in leaf:
        snapshot = OUT / leaf['image_snapshot_path']
        if sha(snapshot) != leaf['image_snapshot_sha256'] or leaf['image_snapshot_sha256'] != row['image_sha256']:
            raise SystemExit(f"retained PNG snapshot hash mismatch: {key}")
        current = sha(png_target)
        if current == leaf['replay_before_overlay_image_sha256']:
            png_target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(snapshot, png_target)
            restored_png += 1
        elif current != row['image_sha256']:
            raise SystemExit(f"unexpected replay PNG precondition: {key}")
    elif sha(png_target) != row['image_sha256']:
        raise SystemExit(f"recipe-derived PNG differs without a retained snapshot: {key}")

    meta_target = PACK / row['metadata_path']
    if 'metadata_snapshot_path' in leaf:
        snapshot = OUT / leaf['metadata_snapshot_path']
        if sha(snapshot) != leaf['metadata_snapshot_sha256'] or leaf['metadata_snapshot_sha256'] != row['metadata_sha256']:
            raise SystemExit(f"retained sidecar snapshot hash mismatch: {key}")
        current = sha(meta_target)
        if current == leaf['replay_before_overlay_metadata_sha256']:
            shutil.copyfile(snapshot, meta_target)
            restored_metadata += 1
        elif current != row['metadata_sha256']:
            raise SystemExit(f"unexpected replay sidecar precondition: {key}")
    elif sha(meta_target) != row['metadata_sha256']:
        raise SystemExit(f"recipe-derived sidecar differs without a retained snapshot: {key}")

shutil.copyfile(index_snapshot, index_target)
if sha(index_target) != manifest['release_set_index_sha256']:
    raise SystemExit('restored set-index does not match frozen release hash')
receipt = {
    'schema_version': 1,
    'scope': manifest['scope'],
    'manifest_sha256': sha(MANIFEST),
    'baseline_sha256': sha(baseline_path),
    'restored_pngs': restored_png,
    'restored_sidecars': restored_metadata,
    'restored_set_index': True,
    'pre_overlay_set_index_sha256': pre_overlay_index_sha256,
    'index_guard': 'exact asset ids, image paths, metadata paths, and view-set ids; per-leaf PNG/sidecar hashes are independently guarded',
    'policy': manifest['policy'],
}
correction_result = OUT / 'replay-run-result.json'
if correction_result.is_file():
    operations = json.loads(correction_result.read_text())
    superseded = [row for row in operations if 'superseded' in row.get('status', '')]
    receipt['superseded_operation_count'] = len(superseded)
    receipt['superseded_operations_sha256'] = hashlib.sha256(json.dumps(superseded, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    receipt['superseded_operations'] = superseded
Path('/workspace/scratch/pocket-retained-overlay-run-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt, indent=2))
