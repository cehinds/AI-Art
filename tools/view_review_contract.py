"""Portable, current-file approval evidence for independently reviewed art."""
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path

VIEWS = ('front', 'top', 'right', 'left', 'bottom', 'rear')
POLICY = 'current-source-and-six-independent-review-v1'
REVIEW_PATH = 'reusable/view-review.json'


def encoded(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode()


def statistics(records):
    return {'expected_sets': len(records), 'approved_sets': sum(r['complete'] for r in records),
            'statuses': dict(sorted(Counter(r['status'] for r in records).items()))}


def reference(report):
    return {'path': REVIEW_PATH, 'sha256': hashlib.sha256(encoded(report)).hexdigest(),
            'statistics': report['statistics']}


def expected_objects(index):
    return {a.get('object_id', a['id']) for a in index['assets'] if a.get('views', {}).get('applicable')}


def project(report, object_ids):
    result = copy.deepcopy(report)
    result['sets'] = [r for r in result['sets'] if r['object_id'] in object_ids]
    result['statistics'] = statistics(result['sets'])
    return result


def load_review(pack, index, required=False):
    """Validate the report against the exported catalog and actual PNG bytes."""
    from validate_pocket_reusable import contained, unique_records, view_reference
    ref = index.get('view_review')
    if not ref:
        if required:
            raise ValueError('Missing independent view-review JSON')
        return None
    raw = contained(pack, ref['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest() != ref.get('sha256'):
        raise ValueError('View-review JSON hash mismatch')
    report = json.loads(raw)
    if report.get('schema_version') != 1 or report.get('path_base') != 'library-root':
        raise ValueError('Unsupported view-review JSON contract')
    records = unique_records(report['sets'], 'object_id', 'independent view reviews')
    if set(records) != expected_objects(index):
        raise ValueError('View-review inventory differs from physical catalog')
    counts = statistics(report['sets'])
    if report.get('statistics') != counts or ref.get('statistics') != counts:
        raise ValueError('Inaccurate independent view-review statistics')
    assets = unique_records(index['assets'], 'id', 'review catalog assets')
    groups = unique_records(index.get('view_sets', []), 'object_id', 'review catalog sets')
    physical = {}
    for asset in index['assets']:
        if asset.get('views', {}).get('applicable'):
            physical.setdefault(asset.get('object_id', asset['id']), []).append(asset)
    hashes = {}

    def check_file(info):
        path = contained(pack, info['path'])
        if path not in hashes:
            hashes[path] = hashlib.sha256(path.read_bytes()).hexdigest()
        if hashes[path] != info.get('sha256'):
            raise ValueError('Stale view-review file hash: ' + info['path'])

    for oid, record in records.items():
        complete = record.get('complete') is True
        if complete != (record.get('status') == 'passed'):
            raise ValueError('Inconsistent view-review approval: ' + oid)
        group = groups.get(oid, {})
        if bool(group.get('complete')) != complete:
            raise ValueError('Catalog set approval differs from independent review: ' + oid)
        for asset in physical.get(oid, []):
            if bool(asset['views'].get('complete')) != complete:
                raise ValueError('Catalog asset approval differs from independent review: ' + asset['id'])
        if record.get('source'):
            check_file(record['source'])
        if set(record.get('views', {})) - set(VIEWS):
            raise ValueError('Unknown reviewed direction: ' + oid)
        for view, info in record.get('views', {}).items():
            asset = assets.get(info.get('asset_id'), {})
            if (asset.get('object_id') != oid or asset.get('view') != view
                    or asset.get('image', {}).get('path') != info['path']
                    or view_reference(group.get('views', {}).get(view)) != info['asset_id']):
                raise ValueError('View-review leaf differs from catalog: ' + oid + '/' + view)
            if record.get('source') and asset.get('provenance', {}).get('source_image') != record['source']['path']:
                raise ValueError('View-review source differs from catalog: ' + oid)
            check_file(info)
        if complete:
            review = record.get('review') or {}
            from merge_view_reviews import REVIEWERS, timestamp
            if (set(record['views']) != set(VIEWS) or not record.get('source')
                    or review.get('status') != 'pass' or review.get('reviewer') not in REVIEWERS
                    or timestamp(review.get('reviewed_at')) is None):
                raise ValueError('Incomplete independent approval evidence: ' + oid)
        elif required:
            raise ValueError('Independent six-view review incomplete: ' + oid)
    return report


def attach_review(pack, index):
    """Add the optional report reference; enforce it when strict validation runs."""
    index['view_review_policy'] = POLICY
    path = pack / REVIEW_PATH
    if path.is_file():
        raw = path.read_bytes()
        report = json.loads(raw)
        index['view_review'] = {'path': REVIEW_PATH, 'sha256': hashlib.sha256(raw).hexdigest(),
                                'statistics': report['statistics']}
        load_review(pack, index)
    else:
        index.pop('view_review', None)
    return index
