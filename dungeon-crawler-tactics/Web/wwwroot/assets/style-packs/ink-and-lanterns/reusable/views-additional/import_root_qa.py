"""Import exact-hash independent geometry QA decisions from the shared root ledger."""
from pathlib import Path
import hashlib, json

OUT = Path(__file__).resolve().parent
PACK = OUT.parents[1]
LEDGER = Path('/workspace/scratch/view-qa-root.json')
INDEX = OUT / 'set-index.json'

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> None:
    root = json.loads(LEDGER.read_text())
    index = json.loads(INDEX.read_text())
    sets = {s['object_id']: s for s in index['view_sets']}
    assets = {a['id']: a for a in index['assets']}
    report = {'source_ledger': str(LEDGER), 'applied': [], 'mismatches': [], 'not_found': []}
    for key, review in root['reviewed'].items():
        prefix = 'style-packs/ink-and-lanterns::'
        if not key.startswith(prefix):
            continue
        oid = key[len(prefix):]
        if oid not in sets:
            report['not_found'].append(oid)
            continue
        source = Path(review['source'])
        hashes_ok = source.is_file() and sha(source) == review.get('source_sha256')
        current = {}
        group = sets[oid]
        for view in ['front', 'top', 'right', 'left', 'bottom', 'rear']:
            aid = group.get('views', {}).get(view)
            asset = assets.get(aid)
            if not asset:
                hashes_ok = False
                current[view] = None
                continue
            image = PACK / asset['image']['path']
            value = sha(image) if image.is_file() else None
            current[view] = value
            if value != review.get('image_hashes', {}).get(view):
                hashes_ok = False
        if not hashes_ok:
            report['mismatches'].append({'object_id': oid, 'source_hash_current': sha(source) if source.is_file() else None, 'source_hash_expected': review.get('source_sha256'), 'view_hashes_current': current, 'view_hashes_expected': review.get('image_hashes')})
            continue
        status = review.get('status')
        notes = review.get('notes', [])
        shared = {'reviewer': review.get('reviewer', 'root'), 'reviewed_at': review.get('reviewed_at'), 'source_sha256': review.get('source_sha256'), 'image_hashes': review.get('image_hashes'), 'notes': notes}
        if status == 'pass':
            group['complete'] = True
            group['geometry_qa'] = {'status': 'independently-reviewed-pass', **shared}
        elif status == 'needs-correction':
            affected = review.get('affected_views') or []
            group['complete'] = False
            group['geometry_qa'] = {'status': 'pending-correction', 'views': affected, 'reason': '\n'.join(notes) if isinstance(notes, list) else str(notes), 'atlas_self_inspected': True, **shared}
        else:
            report['mismatches'].append({'object_id': oid, 'unexpected_status': status})
            continue
        report['applied'].append({'object_id': oid, 'status': status, 'affected_views': review.get('affected_views', [])})
    INDEX.write_text(json.dumps({'assets': list(assets.values()), 'view_sets': list(sets.values())}, indent=2) + '\n')
    (OUT / 'root-qa-import.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f"Applied {len(report['applied'])}; hash mismatches {len(report['mismatches'])}; missing sets {len(report['not_found'])}")
    if report['mismatches']:
        print('Mismatches:', ', '.join(x['object_id'] for x in report['mismatches']))

if __name__ == '__main__':
    main()
