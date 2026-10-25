#!/usr/bin/env python3
"""Export current-file independent six-view approval evidence as portable JSON.

Run read-only while artists work. Use --apply only after writers are frozen;
it updates set approvals and reusable/view-review.json without changing PNGs.
Ledgers are supplied as REVIEWER=PATH, never inferred from a worker's flags.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path

VIEWS = ('front', 'top', 'right', 'left', 'bottom', 'rear')
REVIEWERS = {'root', 'page_inventory', 'reconstruction_design'}
FAILURES = {'issues', 'needs-correction', 'needs-review', 'rejected', 'fail'}
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ASSETS = ROOT / 'dungeon-crawler-tactics/Web/wwwroot/assets'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def encode(value):
    return json.dumps(value, indent=2, ensure_ascii=False) + '\n'


def contained(root, relative):
    if not isinstance(relative, str) or Path(relative).is_absolute() or '..' in Path(relative).parts:
        raise ValueError(f'Unsafe relative path: {relative!r}')
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f'Path escapes library: {relative}')
    return path


def unique(records, field):
    result = {}
    for record in records:
        key = record[field]
        if key in result:
            raise ValueError(f'Duplicate {field}: {key}')
        result[key] = record
    return result


def timestamp(value):
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if result.tzinfo is None:
            raise ValueError('Timezone missing')
        return result.timestamp()
    except (AttributeError, TypeError, ValueError):
        return None


def review_set(pack, object_id, group, assets, reviews):
    result = {'object_id': object_id, 'complete': False, 'status': 'missing-views',
              'source': None, 'views': {}, 'review': None, 'reasons': []}
    if group is None:
        result['reasons'] = ['No generated six-view set.']
        return result
    paths, sources = {}, set()
    for direction in VIEWS:
        ref = group.get('views', {}).get(direction)
        ident = ref.get('asset_id') if isinstance(ref, dict) else ref
        leaf = assets.get(ident)
        if not leaf or leaf.get('object_id') != object_id or leaf.get('view') != direction:
            result['reasons'].append(f'{direction}: missing or mismatched canonical leaf.')
            continue
        path = contained(pack, leaf['image']['path'])
        if not path.is_file():
            result['reasons'].append(f'{direction}: PNG is missing.')
            continue
        paths[direction] = path
        result['views'][direction] = {'asset_id': ident, 'path': path.relative_to(pack).as_posix(), 'sha256': sha(path)}
        source = leaf.get('provenance', {}).get('source_image')
        if not source:
            result['reasons'].append(f'{direction}: source image is undeclared.')
        else:
            sources.add(contained(pack, source))
    if len(paths) != 6 or result['reasons']:
        return result
    if len(sources) != 1 or not next(iter(sources)).is_file():
        result['status'] = 'invalid-source'
        result['reasons'] = ['Six directions must reference one existing source image.']
        return result
    source = next(iter(sources))
    result['source'] = {'path': source.relative_to(pack).as_posix(), 'sha256': sha(source)}
    current = {v: result['views'][v]['sha256'] for v in VIEWS}
    decisions, excluded = [], Counter()
    for reviewer, record in reviews:
        status = record.get('status')
        if status != 'pass' and status not in FAILURES:
            continue  # Automatic snapshots and partial view_reviews are not approval.
        if record.get('image_hashes') != current:
            excluded['stale-or-incomplete-view-hashes'] += 1
            continue
        reviewed_paths = record.get('view_paths', {})
        if set(reviewed_paths) != set(VIEWS) or any(Path(reviewed_paths[v]).resolve() != paths[v] for v in VIEWS):
            excluded['mismatched-view-paths'] += 1
            continue
        when = timestamp(record.get('reviewed_at'))
        if when is None:
            excluded['missing-review-time'] += 1
            continue
        # A current-image defect blocks approval even if its reviewer did not
        # capture source evidence. Passing requires BOTH source identity/hash.
        if status == 'pass' and (record.get('source_sha256') != result['source']['sha256']
                or Path(record.get('source') or record.get('source_path') or '/').resolve() != source):
            excluded['missing-or-stale-source-evidence'] += 1
            continue
        if record.get('reviewer', reviewer) != reviewer or reviewer not in REVIEWERS:
            excluded['untrusted-reviewer'] += 1
            continue
        decisions.append((when, status != 'pass', reviewer, record))
    if excluded:
        result['excluded_review_counts'] = dict(sorted(excluded.items()))
    if not decisions:
        result['status'] = 'pending-independent-review'
        result['reasons'] = ['No whole-set independent PASS with current source and all six PNG hashes.']
        return result
    # Latest decisive review wins. At the same timestamp a rejection wins.
    _, rejected, reviewer, record = max(decisions, key=lambda r: r[:3])
    result['status'] = 'needs-correction' if rejected else 'passed'
    result['complete'] = not rejected
    result['review'] = {'reviewer': reviewer, 'reviewed_at': record['reviewed_at'],
                        'status': record['status'], 'notes': record.get('notes', []),
                        'affected_views': record.get('affected_views', [])}
    return result


def merge_library(pack, scope, catalog, worker, ledgers):
    expected = {a.get('object_id', a['id']) for a in catalog['assets'] if a.get('views', {}).get('applicable')}
    groups = unique(worker.get('view_sets', []), 'object_id')
    assets = unique(worker.get('assets', []), 'id')
    unexpected = sorted(set(groups) - expected)
    if unexpected:
        raise ValueError(f'Generated sets absent from canonical physical inventory: {unexpected}')
    records = [review_set(pack, oid, groups.get(oid), assets,
                         [(reviewer, ledger['reviewed'][scope + '::' + oid])
                          for reviewer, ledger in ledgers if scope + '::' + oid in ledger.get('reviewed', {})])
               for oid in sorted(expected)]
    return {'schema_version': 1, 'tags': ['attachment-tagged', 'coverage', 'independent-review', 'metadata-document', 'six-view-review'],
            'path_base': 'library-root', 'scope': scope,
            'policy': 'Complete only with a whole-set independent PASS matching the current source and every principal PNG. Partial reviews and worker completion flags do not approve a set. Hidden surfaces remain inferred illustrative art.',
            'statistics': {'expected_sets': len(records), 'approved_sets': sum(r['complete'] for r in records),
                           'statuses': dict(sorted(Counter(r['status'] for r in records).items()))},
            'sets': records}


def apply_approvals(worker, report):
    records = {r['object_id']: r for r in report['sets']}
    for group in worker['view_sets']:
        record = records[group['object_id']]
        group['complete'] = record['complete']
        group['geometry_qa'] = {'status': 'passed' if record['complete'] else record['status'],
                               'evidence': 'reusable/view-review.json',
                               'object_id': group['object_id'],
                               'source_sha256': (record['source'] or {}).get('sha256'),
                               'image_hashes': {v: a['sha256'] for v, a in record['views'].items()}}
        if record['review']:
            group['geometry_qa'].update(record['review'])
            group['geometry_qa']['status'] = 'passed' if record['complete'] else record['status']
    return worker


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets', type=Path, default=DEFAULT_ASSETS)
    parser.add_argument('--ledger', action='append', required=True, help='REVIEWER=PATH; repeat for independent ledgers')
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--apply', action='store_true', help='Write approvals only after all workers are frozen')
    parser.add_argument('--require-complete', action='store_true')
    args = parser.parse_args()
    ledgers = []
    for spec in args.ledger:
        reviewer, path = spec.split('=', 1)
        if reviewer not in REVIEWERS:
            parser.error(f'Unknown independent reviewer: {reviewer}')
        ledgers.append((reviewer, read(Path(path))))
    root = args.assets.resolve()
    reports = []
    for entry in read(root / 'reusable-library.json')['libraries']:
        if entry['base'] == 'style-packs/pocket-dungeon':
            continue  # Original 326 sets were delivered previously; do not re-author.
        pack = contained(root, entry['base'])
        worker_path = pack / 'reusable/views-additional/set-index.json'
        worker = read(worker_path) if worker_path.is_file() else {'assets': [], 'view_sets': []}
        report = merge_library(pack, entry['base'], read(contained(root, entry['index'])), worker, ledgers)
        reports.append(report)
        if args.apply:
            (pack / 'reusable/view-review.json').write_text(encode(report))
            worker_path.write_text(encode(apply_approvals(worker, report)))
    summary = {'schema_version': 1, 'libraries': reports,
               'expected_sets': sum(r['statistics']['expected_sets'] for r in reports),
               'approved_sets': sum(r['statistics']['approved_sets'] for r in reports)}
    args.report.write_text(encode(summary))
    print(encode({k: v for k, v in summary.items() if k != 'libraries'}).strip())
    if args.require_complete and summary['approved_sets'] != summary['expected_sets']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
