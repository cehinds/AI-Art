"""Hash-bound release exceptions for recorded actual image-tool blocks, never approval."""
import copy
import hashlib
import json

PATH = 'reusable/generation-blocks.json'
POLICY = 'recorded-image-tool-block-release-v1'
TARGETS = {
    ('style-packs/pocket-dungeon', 'arsenal-throwing-knives'): {'top', 'bottom'},
    ('style-packs/ink-and-lanterns', 'arsenal-throwing-knives'): {'top', 'bottom'},
    ('style-packs/ink-and-lanterns', 'iron-sword'): {'top'},
    ('style-packs/ink-and-lanterns', 'arsenal-hand-axe'): {'top', 'bottom'},
    **{('style-packs/ink-and-lanterns', f'attacks-carl-kick-{n:02}'): {'bottom'} for n in (1, 2, 3)},
    ('reusable-gameplay', 'directional--brittany'): {'bottom'},
    ('style-packs/ink-and-lanterns', 'arsenal-recurve-bow'): {'front', 'top', 'right', 'left', 'bottom', 'rear'},
    ('book-tiles/dungeon-after-dark', 'bubble-airship-bomb-rack'): {'top'},
}
REQUESTS = {
    ('style-packs/pocket-dungeon', 'arsenal-throwing-knives'): {'0c226e2d-cd63-496f-bb15-9fc716cc748e'},
    ('style-packs/ink-and-lanterns', 'arsenal-throwing-knives'): {
        '5ed245c2-e22c-4424-bc70-1c146108f233', 'f6dfbdee-2580-4cc9-ba75-3c77137ba1da'},
    ('style-packs/ink-and-lanterns', 'iron-sword'): {'2124307c-f6dc-4115-a081-ba6896c34e23'},
    ('style-packs/ink-and-lanterns', 'arsenal-hand-axe'): {'6f909dfb-288d-48b8-8b33-21709d8b2c45'},
    **{('style-packs/ink-and-lanterns', f'attacks-carl-kick-{n:02}'): {'82d28979-b9cf-4e35-9dfa-10a41dea122c'} for n in (1, 2, 3)},
    ('reusable-gameplay', 'directional--brittany'): {
        'c12e81c5-1da1-414a-ac63-33ebbd91930a', '9597774b-4897-42f0-96e9-c8ed4964018c',
        '07c74a96-f5d7-4b2b-ad21-d4e49996f319'},
    ('style-packs/ink-and-lanterns', 'arsenal-recurve-bow'): {'01e77624-66e2-4803-a093-773861a20e76'},
    ('book-tiles/dungeon-after-dark', 'bubble-airship-bomb-rack'): {'b859fd7b-afb2-4fc1-8f03-baba15f4951e'},
}
CARL_BATCH = {f'attacks-carl-kick-{n:02}' for n in (1, 2, 3)}


def receipt_facts(tool, scope, oid, binding):
    """Interpret known receipts without rewriting their returned fields."""
    if (scope, oid) == ('book-tiles/dungeon-after-dark', 'bubble-airship-bomb-rack'):
        valid = (tool.get('object_id') == oid and tool.get('status') == 'blocked'
                 and tool.get('direction') == 'top' and tool.get('code') == 'moderation_blocked'
                 and tool.get('moderation_stage') == 'input' and tool.get('category') == 'violence')
        return valid, {'top'}, {tool.get('request_id')}
    if (scope, oid) == ('style-packs/ink-and-lanterns', 'arsenal-recurve-bow'):
        views = tool.get('affected_views', [])
        valid = (tool.get('object_id') == oid and tool.get('status') == 'rejected'
                 and isinstance(views, list) and len(views) == 6
                 and set(views) == {'FRONT', 'TOP', 'RIGHT', 'LEFT', 'BOTTOM', 'REAR'}
                 and tool.get('error_code') == 'moderation_blocked'
                 and tool.get('moderation_stage') == 'input'
                 and tool.get('moderation_categories') == ['violence'])
        return valid, {v.lower() for v in views}, {tool.get('request_id')}
    if scope == 'style-packs/ink-and-lanterns' and oid in CARL_BATCH:
        members = tool.get('object_ids', [])
        valid = (isinstance(members, list) and len(members) == len(CARL_BATCH)
                 and set(members) == CARL_BATCH and tool.get('status') == 'rejected'
                 and tool.get('affected_views') == ['BOTTOM']
                 and tool.get('error_code') == 'moderation_blocked'
                 and tool.get('moderation_stage') == 'output'
                 and tool.get('moderation_categories') == ['other'])
        return valid, {'bottom'}, {tool.get('request_id')}
    if (scope, oid) == ('reusable-gameplay', 'directional--brittany'):
        failures = tool.get('failed_imagegen_requests', [])
        candidate = tool.get('allowed_but_rejected_candidate', {})
        source = binding['primary_source']
        valid = (tool.get('object_id') == oid and tool.get('status') == 'blocked'
                 and tool.get('blocked_view') == 'bottom' and tool.get('complete') is False
                 and len(failures) == 3
                 and all(r.get('result') == 'blocked' and r.get('stage') == 'output'
                         and r.get('categories') in (['sexual'], ['other']) for r in failures)
                 and tool.get('canonical_source') == {'path': source['path'], 'sha256': source['sha256']}
                 and tool.get('current_view_sha256') == {v: info['sha256'] for v, info in binding['views'].items()}
                 and candidate.get('installed_view') == binding['views']['bottom']['path']
                 and candidate.get('installed_view_sha256') == binding['views']['bottom']['sha256'])
        return valid, {'bottom'}, {r.get('request_id') for r in failures}
    views = tool.get('affected_views', tool.get('requested_views', tool.get('views', [])))
    requests = {r.get('request_id') for r in tool.get('rejection_requests', [])}
    if tool.get('request_id'):
        requests.add(tool['request_id'])
    valid = (tool.get('status') == 'blocked' and tool.get('object_id') == oid
             and isinstance(views, list) and len(views) == len(set(views)))
    return valid, set(views), requests


def encoded(value):
    return (json.dumps(prepare_document(value), indent=2, ensure_ascii=False) + '\n').encode()


def prepare_document(value):
    """Author policy/evidence BEFORE pinning; later all-JSON tagging is a no-op."""
    from asset_attachment_tags import enrich_document
    return enrich_document(copy.deepcopy(value), 'unspecified')


def statistics(records):
    return {'recorded_blocked_sets': len(records),
            'recorded_blocked_views': sum(len(r['affected_views']) for r in records)}


def reference(report):
    return {'path': PATH, 'sha256': hashlib.sha256(encoded(report)).hexdigest(),
            'statistics': statistics(report['records'])}


def project(report, object_ids):
    result = copy.deepcopy(report)
    result['records'] = [r for r in result['records'] if r['object_id'] in object_ids]
    result['statistics'] = statistics(result['records'])
    return result


def evidence_files(report):
    for row in (report or {}).get('records', []):
        yield row['evidence']
        yield from row.get('supporting_files', [])
        yield row['unaffected_review']['source_evidence']['reviewed_reference']


def load_blocks(pack, index):
    """Validate optional portable policy, current files and explicit partial review."""
    from validate_pocket_reusable import contained, unique_records, view_reference
    from view_review_contract import VIEWS, canonical_primary, file_evidence
    from merge_view_reviews import reviewer_allowed, timestamp
    ref = index.get('generation_blocks')
    if not ref:
        return None
    raw = contained(pack, ref['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest() != ref.get('sha256'):
        raise ValueError('Generation-block report hash mismatch')
    report = json.loads(raw)
    if raw != encoded(report):
        raise ValueError('Generation-block report must be tag-normalized before pinning')
    if (report.get('schema_version') != 1 or report.get('path_base') != 'library-root'
            or report.get('policy') != POLICY):
        raise ValueError('Unsupported generation-block contract')
    scope = report.get('scope')
    records = unique_records(report['records'], 'object_id', 'recorded generation blocks')
    if (report.get('statistics') != statistics(report['records'])
            or ref.get('statistics') != report['statistics']):
        raise ValueError('Inaccurate generation-block statistics')
    assets = unique_records(index['assets'], 'id', 'generation-block catalog assets')
    groups = unique_records(index.get('view_sets', []), 'object_id', 'generation-block sets')

    def check(info):
        path = contained(pack, info['path'])
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != info.get('sha256'):
            raise ValueError('Stale generation-block evidence: ' + info['path'])
        if path.suffix.lower() == '.json' and raw != encoded(json.loads(raw)):
            raise ValueError('Generation-block JSON must be tag-normalized before pinning: ' + info['path'])
        return path

    for oid, row in records.items():
        affected = row.get('affected_views', [])
        if (not isinstance(affected, list) or len(affected) != len(set(affected))
                or set(affected) != TARGETS.get((scope, oid))):
            raise ValueError('Unlisted generation-block object or directions: ' + oid)
        if (row.get('status') != 'external-generation-blocked' or row.get('complete') is not False
                or not row.get('reason') or timestamp(row.get('recorded_at')) is None):
            raise ValueError('Generation block must remain explicitly incomplete: ' + oid)
        group = groups.get(oid, {})
        if group.get('complete') is not False:
            raise ValueError('Generation block cannot approve catalog set: ' + oid)
        primary = canonical_primary(pack, oid, assets, group)
        if row.get('primary_source') != primary:
            raise ValueError('Stale generation-block primary source: ' + oid)
        views = row.get('views', {})
        if set(views) != set(VIEWS):
            raise ValueError('Generation block must bind all six existing leaves: ' + oid)
        for view, info in views.items():
            aid = view_reference(group.get('views', {}).get(view))
            leaf = assets.get(aid, {})
            if (info.get('asset_id') != aid or leaf.get('object_id') != oid
                    or leaf.get('view') != view or leaf.get('image', {}).get('path') != info.get('path')):
                raise ValueError('Generation-block leaf differs from catalog: ' + oid + '/' + view)
            check(info)
        evidence_raw = check(row['evidence']).read_bytes()
        tool = json.loads(evidence_raw)
        if evidence_raw != encoded(tool):
            raise ValueError('Generation-block evidence must be tag-normalized before pinning: ' + oid)
        valid_receipt, tool_views, request_ids = receipt_facts(tool, scope, oid, row)
        if (not valid_receipt or tool_views != set(affected)
                or request_ids != REQUESTS[(scope, oid)]):
            raise ValueError('Missing actual image-tool block evidence: ' + oid)
        dependencies = {f['path']: f for f in row.get('supporting_files', [])}
        for info in dependencies.values():
            check(info)
        if tool.get('prompt_path') and tool['prompt_path'] not in dependencies:
            raise ValueError('Missing portable generation-block prompt: ' + oid)
        for field in ('source_contact_sheet', 'input_contact_sheet'):
            if tool.get(field) and tool[field] not in dependencies:
                raise ValueError('Missing portable generation-block input contact: ' + oid)
        candidate = tool.get('allowed_but_rejected_candidate', {})
        if candidate:
            info = dependencies.get(candidate.get('raw_atlas'), {})
            if not info or info.get('sha256') != candidate.get('raw_atlas_sha256'):
                raise ValueError('Missing portable rejected-candidate raw evidence: ' + oid)
        # Historical absolute session review-contact citations are archival.
        # The portable canonical partial review below remains authoritative.
        review = row.get('unaffected_review', {})
        unaffected = set(VIEWS) - set(affected)
        if (review.get('status') != 'independent-partial-review'
                or not reviewer_allowed(review.get('reviewer'), scope)
                or timestamp(review.get('reviewed_at')) is None
                or set(review.get('approved_views', [])) != unaffected
                or len(review.get('approved_views', [])) != len(unaffected)
                or set(review.get('views', {})) != unaffected):
            raise ValueError('Missing unaffected-direction independent approval: ' + oid)
        if review.get('source') != {k: v for k, v in primary.items() if k != 'asset_id'}:
            raise ValueError('Partial review source differs from canonical crop: ' + oid)
        for view in unaffected:
            if review['views'][view] != views[view]:
                raise ValueError('Stale unaffected-direction approval: ' + oid + '/' + view)
        proof = review.get('source_evidence', {})
        info = proof.get('reviewed_reference', {})
        if (proof.get('method') not in {'direct-reviewed-source', 'verified-capture-manifest'}
                or file_evidence(pack, info.get('path')) != info
                or info.get('rgba_sha256') != primary['rgba_sha256']):
            raise ValueError('Missing reviewed canonical crop evidence for block: ' + oid)
        if proof['method'] == 'verified-capture-manifest':
            import re
            if not re.fullmatch('[0-9a-f]{64}', proof.get('capture_manifest_sha256', '')):
                raise ValueError('Missing partial-review capture digest: ' + oid)
        for alias in row.get('blocked_pixel_aliases', []):
            if (not isinstance(alias, list) or len(alias) < 2 or len(alias) != len(set(alias))
                    or not set(alias) <= set(affected)):
                raise ValueError('Unapproved-view alias exception escapes block: ' + oid)
    return report


def records(report):
    return {r['object_id']: r for r in (report or {}).get('records', [])}


def attach_blocks(pack, index):
    """Preserve an authored frozen policy through builds; never create one."""
    path = pack / PATH
    if not path.is_file():
        index.pop('generation_blocks', None)
        return index
    raw = path.read_bytes()
    report = json.loads(raw)
    index['generation_blocks'] = reference(report)
    # load_blocks checks canonical encoding/tag stability, evidence, current
    # source/leaves and independent partial review before the builder writes.
    load_blocks(pack, index)
    return index
