#!/usr/bin/env python3
"""Refresh progress and pending-QA JSON after indexing a view batch."""
import argparse, hashlib, json, os, tempfile
from pathlib import Path

OUT = Path(__file__).resolve().parent
PACK = OUT.parents[1]

def atomic(path, value):
    fd, tmp = tempfile.mkstemp(prefix=path.name + '.', suffix='.tmp', dir=path.parent)
    os.close(fd)
    Path(tmp).write_text(json.dumps(value, indent=2) + '\n')
    os.replace(tmp, path)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--contact', required=True, help='pack-relative source+six contact path')
    ap.add_argument('object_ids', nargs='+')
    args = ap.parse_args()
    canonical = json.loads((PACK / 'reusable/index.json').read_text())
    manifest = json.loads((PACK / 'manifest.json').read_text())['assets']
    index_path = OUT / 'set-index.json'
    index = json.loads(index_path.read_text())
    expected = {a.get('object_id', a.get('id')) for a in canonical.get('assets', [])
                if a.get('views', {}).get('applicable', True)}
    sets = {s['object_id']: s for s in index['view_sets']}
    assets = {a['id']: a for a in index['assets']}
    indexed = set(sets) & expected
    complete = sum(bool(sets[oid].get('complete')) for oid in indexed)
    progress = {'schema_version': 1, 'total_objects': len(expected),
                'indexed_objects': len(indexed), 'indexed_view_assets': len(index['assets']),
                'complete_sets': complete, 'incomplete_sets': len(indexed) - complete,
                'missing_source_ids': sorted(expected - indexed)}
    atomic(OUT / 'progress.json', progress)

    pending_path = OUT / 'pending-review-batches.json'
    pending = json.loads(pending_path.read_text())
    pending['indexed_count'] = len(indexed)
    by_manifest = {x['id'].removesuffix('--native'): x for x in manifest}
    for oid in args.object_ids:
        if oid not in indexed:
            raise ValueError(f'{oid}: not indexed')
        source = by_manifest[oid]['source']['sheet'] + '/components/' + oid + '.png'
        source_path = PACK / source
        if not source_path.exists():
            raise FileNotFoundError(source_path)
        view_map = sets[oid]['views']
        views = {v: {'asset_id': view_map[v], 'sha256': assets[view_map[v]]['image']['sha256']}
                 for v in ('front', 'top', 'right', 'left', 'bottom', 'rear')}
        recipe = None
        for v in view_map.values():
            meta = json.loads((PACK / assets[v]['metadata_path']).read_text())
            recipe = meta.get('provenance', {}).get('generation_recipe')
            if recipe:
                break
        entry = {'object_id': oid, 'review_status': 'pending-independent-qa',
                 'complete': False, 'source_image': source, 'source_sha256': sha(source_path),
                 'contact_sheet': args.contact, 'views': views}
        if recipe:
            entry['generation_recipe'] = recipe
        old = next((i for i, item in enumerate(pending['objects'])
                    if item.get('object_id') == oid), None)
        if old is None:
            pending['objects'].append(entry)
        else:
            pending['objects'][old] = entry
    pending['pending_batch_object_count'] = len(pending['objects'])
    atomic(pending_path, pending)
    print(json.dumps({'indexed': len(indexed), 'missing': len(expected-indexed),
                      'pending': len(pending['objects'])}))

if __name__ == '__main__':
    main()
