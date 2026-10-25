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


def primary_review_evidence(pack, object_id, record, primary, paths, current):
    """Recover only reviewed, hash-verified evidence, including captured crops."""
    from view_review_contract import file_evidence
    def verified_reference(info):
        path = Path(info.get('path') or '/').resolve()
        if not path.is_relative_to(pack.resolve()) or not path.is_file():return None
        actual = file_evidence(pack, path.relative_to(pack).as_posix())
        if actual['sha256'] != info.get('sha256') or actual['rgba_sha256'] != primary['rgba_sha256']:return None
        return actual
    captured = record.get('source_evidence', {})
    manifest_path = captured.get('capture_manifest')
    if manifest_path:
        path = Path(manifest_path)
        if not path.is_file():return None
        raw = path.read_bytes(); manifest_hash = hashlib.sha256(raw).hexdigest()
        if manifest_hash != captured.get('capture_manifest_sha256'):return None
        document = json.loads(raw)
        matches = [item for item in document.get('objects', []) if item.get('object_id') == object_id]
        if len(matches) != 1:return None
        item = matches[0]
        if set(item.get('views', {})) != set(VIEWS):return None
        if any(item['views'][v].get('sha256') != current[v]
               or Path(item['views'][v].get('path') or '/').resolve() != paths[v] for v in VIEWS):return None
        reference = verified_reference(item.get('source', {}))
        if reference:
            return {'method':'verified-capture-manifest', 'capture_manifest_sha256':manifest_hash,
                    'reviewed_reference':reference,
                    'equivalence':'Exact decoded width, height and RGBA equality with canonical primary crop.'}
        return None
    reference = verified_reference({'path':record.get('source') or record.get('source_path'),
                                    'sha256':record.get('source_sha256')})
    if reference:
        return {'method':'direct-reviewed-source', 'reviewed_reference':reference,
                'equivalence':'Exact decoded width, height and RGBA equality with canonical primary crop.'}
    return None


def review_set(pack, object_id, group, assets, reviews):
    result = {'object_id': object_id, 'complete': False, 'status': 'missing-views',
              'source': None, 'primary_source':None, 'views': {}, 'review': None, 'reasons': []}
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
    from view_review_contract import canonical_primary
    try:
        result['primary_source'] = canonical_primary(pack, object_id, assets, group)
    except (ValueError, OSError) as exc:
        result.update(status='invalid-canonical-source', reasons=[str(exc)])
        return result
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
        proof = primary_review_evidence(pack, object_id, record, result['primary_source'], paths, current) if status == 'pass' else None
        if status == 'pass' and proof is None:
            excluded['missing-or-stale-source-evidence'] += 1
            continue
        if record.get('reviewer', reviewer) != reviewer or reviewer not in REVIEWERS:
            excluded['untrusted-reviewer'] += 1
            continue
        decisions.append((when, status != 'pass', reviewer, record, proof))
    if excluded:
        result['excluded_review_counts'] = dict(sorted(excluded.items()))
    if not decisions:
        result['status'] = 'pending-independent-review'
        result['reasons'] = ['No whole-set independent PASS with current source and all six PNG hashes.']
        return result
    # Latest decisive review wins. At the same timestamp a rejection wins.
    _, rejected, reviewer, record, proof = max(decisions, key=lambda r: r[:3])
    result['status'] = 'needs-correction' if rejected else 'passed'
    result['complete'] = not rejected
    result['review'] = {'reviewer': reviewer, 'reviewed_at': record['reviewed_at'],
                        'status': record['status'], 'notes': record.get('notes', []),
                        'affected_views': record.get('affected_views', [])}
    if proof:result['review']['source_evidence'] = proof
    return result


def merge_library(pack, scope, catalog, worker, ledgers):
    expected = {a.get('object_id', a['id']) for a in catalog['assets'] if a.get('views', {}).get('applicable')}
    groups = unique(worker.get('view_sets', []), 'object_id')
    assets = unique(catalog.get('assets', []), 'id')
    for ident, asset in unique(worker.get('assets', []), 'id').items():
        if ident in expected:
            if ident not in assets or asset != assets[ident]:
                raise ValueError('Worker cannot override canonical physical parent: ' + ident)
        else:
            assets[ident] = asset
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
        if group['object_id'] not in records and report.get('scope_mode') == 'targeted-existing-assets':
            continue
        record = records[group['object_id']]
        group['complete'] = record['complete']
        group['geometry_qa'] = {'status': 'passed' if record['complete'] else record['status'],
                               'evidence': 'reusable/legacy-view-review.json' if report.get('scope_mode') == 'targeted-existing-assets' else 'reusable/view-review.json',
                               'object_id': group['object_id'],
                               'source_sha256': (record['source'] or {}).get('sha256'),
                               'primary_source': record.get('primary_source'),
                               'image_hashes': {v: a['sha256'] for v, a in record['views'].items()}}
        if record['review']:
            group['geometry_qa'].update(record['review'])
            group['geometry_qa']['status'] = 'passed' if record['complete'] else record['status']
    return worker


def legacy_inputs(pack, catalog, target_ids):
    """Read only the declared existing assets, across their original extensions."""
    expected = {a.get('object_id', a['id']) for a in catalog['assets'] if a.get('views', {}).get('applicable')}
    if len(target_ids) != len(set(target_ids)) or not set(target_ids) <= expected:
        raise ValueError('Invalid legacy review target inventory')
    workers = [(path, read(path)) for path in sorted((pack / 'reusable').glob('views-*/set-index.json'))]
    groups = [g for _, w in workers for g in w.get('view_sets', []) if g['object_id'] in target_ids]
    leaf_ids = {r.get('asset_id') if isinstance(r, dict) else r for g in groups for r in g['views'].values()}
    assets = [a for _, w in workers for a in w.get('assets', []) if a['id'] in leaf_ids]
    scoped = {**catalog, 'assets': [a for a in catalog['assets'] if a.get('object_id', a['id']) in target_ids]}
    return workers, scoped, {'assets': assets, 'view_sets': groups}


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
    legacy_targets = read(ROOT / 'tools/legacy_view_review_targets.json')['libraries']
    reports = []
    for entry in read(root / 'reusable-library.json')['libraries']:
        pack = contained(root, entry['base'])
        catalog = read(contained(root, entry['index']))
        legacy = entry['base'] in legacy_targets
        if legacy:
            workers, scoped, worker = legacy_inputs(pack, catalog, legacy_targets[entry['base']]['object_ids'])
            report = merge_library(pack, entry['base'], scoped, worker, ledgers)
            report['scope_mode'] = 'targeted-existing-assets'
            report['scope_note'] = legacy_targets[entry['base']]['note']
        else:
            worker_path = pack / 'reusable/views-additional/set-index.json'
            worker = read(worker_path) if worker_path.is_file() else {'assets': [], 'view_sets': []}
            workers = [(worker_path, worker)]
            report = merge_library(pack, entry['base'], catalog, worker, ledgers)
        reports.append(report)
        if args.apply:
            name = 'legacy-view-review.json' if legacy else 'view-review.json'
            (pack / 'reusable' / name).write_text(encode(report))
            for worker_path, worker in workers:
                value = encode(apply_approvals(worker, report))
                if not worker_path.exists() or worker_path.read_text() != value:
                    worker_path.parent.mkdir(parents=True, exist_ok=True)
                    worker_path.write_text(value)
    summary = {'schema_version': 1, 'libraries': reports,
               'expected_sets': sum(r['statistics']['expected_sets'] for r in reports),
               'targeted_existing_sets': sum(r['statistics']['expected_sets'] for r in reports if r.get('scope_mode') == 'targeted-existing-assets'),
               'approved_sets': sum(r['statistics']['approved_sets'] for r in reports)}
    args.report.write_text(encode(summary))
    print(encode({k: v for k, v in summary.items() if k != 'libraries'}).strip())
    if args.require_complete and summary['approved_sets'] != summary['expected_sets']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
