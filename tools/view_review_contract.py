"""Portable, current-file approval evidence for independently reviewed art."""
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path

VIEWS = ('front', 'top', 'right', 'left', 'bottom', 'rear')
POLICY = 'current-source-and-six-independent-review-v1'
REVIEW_PATH = 'reusable/view-review.json'
LEGACY_REVIEW_PATH = 'reusable/legacy-view-review.json'


def file_evidence(pack, relative):
    """Hash actual source bytes and decoded pixels; never trust catalog hashes."""
    from validate_pocket_reusable import contained
    from PIL import Image
    from io import BytesIO
    import struct
    path = contained(pack, relative)
    raw = path.read_bytes()
    with Image.open(BytesIO(raw)) as image:
        rgba = image.convert('RGBA')
        pixel_hash = hashlib.sha256(struct.pack('>II', *rgba.size) + rgba.tobytes()).hexdigest()
    return {'path': relative, 'sha256': hashlib.sha256(raw).hexdigest(), 'rgba_sha256': pixel_hash}


def canonical_primary(pack, object_id, assets, group):
    """Bind a generated set to id==object_id, never to a later scene alias."""
    from validate_pocket_reusable import view_reference
    parent = assets.get(object_id)
    if not parent or parent.get('object_id', object_id) != object_id or not parent.get('image', {}).get('path'):
        raise ValueError('Missing canonical physical source: ' + object_id)
    primary = {'asset_id': object_id, **file_evidence(pack, parent['image']['path'])}
    context = parent.get('provenance', {}).get('source_image')
    checked = {primary['path']: primary}
    for reference in group.get('views', {}).values():
        leaf = assets.get(view_reference(reference), {})
        provenance = leaf.get('provenance', {})
        native = provenance.get('native_front')
        if native:
            if native not in checked:checked[native] = file_evidence(pack, native)
            if checked[native]['rgba_sha256'] != primary['rgba_sha256']:
                raise ValueError('Noncanonical native_front source: ' + object_id)
            if provenance.get('native_front_sha256') not in (None, checked[native]['sha256']):
                raise ValueError('Stale canonical native_front hash: ' + object_id)
        source = provenance.get('source_image')
        if source and source not in (primary['path'], context):
            if source not in checked:checked[source] = file_evidence(pack, source)
            if checked[source]['rgba_sha256'] != primary['rgba_sha256']:
                raise ValueError('Generated source is not the canonical physical crop: ' + object_id)
    return primary


def encoded(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode()


def statistics(records):
    return {'expected_sets': len(records), 'approved_sets': sum(r['complete'] for r in records),
            'statuses': dict(sorted(Counter(r['status'] for r in records).items()))}


def reference(report, legacy=False):
    ref = {'path': LEGACY_REVIEW_PATH if legacy else REVIEW_PATH,
           'sha256': hashlib.sha256(encoded(report)).hexdigest(), 'statistics': report['statistics']}
    if legacy:
        ref['coverage'] = {'mode': 'targeted-existing-assets',
            'object_ids': sorted(r['object_id'] for r in report['sets']),
            'note': 'Targeted review of existing assets; other previously delivered assets retain their existing reviews.'}
    return ref


def expected_objects(index):
    return {a.get('object_id', a['id']) for a in index['assets'] if a.get('views', {}).get('applicable')}


def project(report, object_ids):
    result = copy.deepcopy(report)
    result['sets'] = [r for r in result['sets'] if r['object_id'] in object_ids]
    result['statistics'] = statistics(result['sets'])
    return result


def load_review(pack, index, required=False, legacy=False, allow_recorded_blocks=False):
    """Validate the report against the exported catalog and actual PNG bytes."""
    from validate_pocket_reusable import contained, unique_records, view_reference
    ref = index.get('legacy_view_review' if legacy else 'view_review')
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
    from generation_block_contract import load_blocks, records as block_records
    blocks_report = load_blocks(pack, index) if allow_recorded_blocks else None
    if blocks_report and blocks_report['scope'] != report.get('scope'):
        raise ValueError('Generation-block scope differs from independent review')
    blocks = block_records(blocks_report)
    records = unique_records(report['sets'], 'object_id', 'independent view reviews')
    expected = expected_objects(index)
    if legacy:
        coverage = ref.get('coverage', {})
        declared = coverage.get('object_ids', [])
        if (coverage.get('mode') != 'targeted-existing-assets'
                or report.get('scope_mode') != 'targeted-existing-assets'
                or len(declared) != len(set(declared)) or not set(declared) <= expected):
            raise ValueError('Invalid targeted legacy review coverage')
        expected = set(declared)
    if set(records) != expected:
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
        if record.get('primary_source'):
            primary = canonical_primary(pack, oid, assets, group)
            if record['primary_source'] != primary:
                raise ValueError('Stale or noncanonical primary source review: ' + oid)
        elif complete:
            raise ValueError('Missing canonical primary source review: ' + oid)
        if complete:
            review = record.get('review') or {}
            from merge_view_reviews import reviewer_allowed, timestamp
            if (set(record['views']) != set(VIEWS) or not record.get('source')
                    or review.get('status') != 'pass' or not reviewer_allowed(review.get('reviewer'), report.get('scope'))
                    or timestamp(review.get('reviewed_at')) is None):
                raise ValueError('Incomplete independent approval evidence: ' + oid)
            proof = review.get('source_evidence') or {}
            info = proof.get('reviewed_reference')
            if proof.get('method') not in ('verified-capture-manifest', 'direct-reviewed-source') or not info:
                raise ValueError('Missing reviewed canonical crop evidence: ' + oid)
            actual = file_evidence(pack, info['path'])
            if actual != info or actual['rgba_sha256'] != primary['rgba_sha256']:
                raise ValueError('Stale reviewed crop evidence: ' + oid)
            if proof['method'] == 'verified-capture-manifest':
                import re
                if not re.fullmatch('[0-9a-f]{64}', proof.get('capture_manifest_sha256', '')):
                    raise ValueError('Missing verified capture manifest digest: ' + oid)
        elif required:
            block = blocks.get(oid)
            review = record.get('review') or {}
            from merge_view_reviews import FAILURES, reviewer_allowed, timestamp
            affected = review.get('affected_views', [])
            if (not block or record.get('primary_source') != block['primary_source']
                    or record.get('views') != block['views']
                    or record.get('status') != 'needs-correction'
                    or review.get('status') not in FAILURES
                    or not reviewer_allowed(review.get('reviewer'), report.get('scope'))
                    or timestamp(review.get('reviewed_at')) is None
                    or not isinstance(affected, list) or not affected
                    or len(affected) != len(set(affected))
                    or not set(affected) <= set(block['affected_views'])):
                raise ValueError('Independent six-view review incomplete: ' + oid)
    return report


def attach_review(pack, index, legacy=False):
    """Add the optional report reference; enforce it when strict validation runs."""
    field = 'legacy_view_review' if legacy else 'view_review'
    index[field + '_policy'] = POLICY
    path = pack / (LEGACY_REVIEW_PATH if legacy else REVIEW_PATH)
    if path.is_file():
        raw = path.read_bytes()
        report = json.loads(raw)
        index[field] = reference(report, legacy)
        index[field]['sha256'] = hashlib.sha256(raw).hexdigest()
        load_review(pack, index, legacy=legacy)
    else:
        index.pop(field, None)
    from generation_block_contract import attach_blocks
    attach_blocks(pack, index)
    return index
