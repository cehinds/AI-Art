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
    ('style-packs/ink-and-lanterns', 'arsenal-spear'): {'top', 'bottom'},
    ('book-tiles/dungeon-after-dark', 'faction-battlefield-siege-engine-emplacement'): {'rear'},
    ('book-tiles/dungeon-after-dark', 'industry-menagerie-goblin-workbench'): {'top'},
    ('book-tiles/dungeon-after-dark', 'industry-menagerie-improvised-cannon-emplacement'): {'top', 'rear'},
    ('book-tiles/dungeon-after-dark', 'industry-menagerie-kennel-cage-section'): {'top'},
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
    ('style-packs/ink-and-lanterns', 'arsenal-spear'): {'665246dd-074d-429b-b12d-516f5b70df9f'},
    ('book-tiles/dungeon-after-dark', 'faction-battlefield-siege-engine-emplacement'): {'bd9ae23c-f368-4a9f-902d-d042760e6646'},
    **{('book-tiles/dungeon-after-dark', oid): {'19523388-b475-449a-a092-52307d277980'} for oid in (
        'industry-menagerie-goblin-workbench', 'industry-menagerie-improvised-cannon-emplacement',
        'industry-menagerie-kennel-cage-section')},
}
CARL_BATCH = {f'attacks-carl-kick-{n:02}' for n in (1, 2, 3)}
SIEGE = ('book-tiles/dungeon-after-dark', 'faction-battlefield-siege-engine-emplacement')
SIEGE_ERROR = ('Image-generation safety system returned HTTP 400 moderation_blocked; '
               'do not retry this same request or an equivalent substitute.')
SIEGE_PROMPT_SHA256 = '966f78c8bd683b5d0e86d9f9678ae882f5945833d3f8eb3e7dc9a9653496fc8f'
WORKTOP_BATCH_ID = '19523388-b475-449a-a092-52307d277980'
BATCH_REASON = 'batch rejection; individual request attribution unavailable'
# These are the four actual concurrent requests, not four attributed rejections.
WORKTOP_PROMPTS = {
    ('industry-menagerie-goblin-workbench', 'top'): '3abae1ec30015f060ad0f90dae59f5f3e9dd16461a8effa289e406d38869c3c1',
    ('industry-menagerie-improvised-cannon-emplacement', 'top'): '30ec8b3b1a11c761ab4e48bda065bd449e9616944d967d0bc288e600fe7a389e',
    ('industry-menagerie-improvised-cannon-emplacement', 'rear'): '0c531a5d34b6e0929b0e4952b23bb4ddb03bd9988ad8e3aaf49b83971e6f2993',
    ('industry-menagerie-kennel-cage-section', 'top'): 'c53ef5604dc5c3213ee6775a870d25f98beee2fb435da19664635e8a28c47668',
}
INTERRUPTED_BATCH_PROMPTS = {
    'reusable/views-additional/prompts/root-dark-worktops6-20261026/goblin-workbench-top.txt':
        '78f91e7dd398af2b22adc22e4c9878c14af8d7f02ff7778886099bd08a8dcf9f',
    'reusable/views-additional/prompts/root-dark-worktops6-20261026/cage-top.txt':
        '549bf933deddc3b8e4772c67960f39b646b8a2962dd6bbeb26cd82817a7b7a2b',
}
INTERRUPTED_BATCH_STATUS = ('imagegen call issued, execution aborted by Root after ~17 seconds before any response '
    'mapping/raw PNG was saved; do not retry; included direction was already safety-blocked in batch01')


def worktop_target(scope, oid):
    return scope == 'book-tiles/dungeon-after-dark' and any(o == oid for o, _ in WORKTOP_PROMPTS)


def siege_reference_paths(oid):
    prefix = 'reusable/views-additional/candidates/core-dark-next-six-props-20261026/raw/current-snapshots/'
    return {role: prefix + oid + '.' + role + '.png' for role in ('source', 'left')}


def worktop_reference_paths(oid):
    return ['industry-menagerie/components/' + oid + '.png',
            'reusable/views-additional/images/' + oid + '.front.png',
            'reusable/views-additional/images/' + oid + '.top.png']


def historical_reference_matches(value, relative):
    """Match an archival receipt citation; never open its absolute session path."""
    return isinstance(value, str) and (value == relative or value.endswith('/' + relative))


def additional_receipt_support(tool, scope, oid, binding):
    """Known portable input files required by the two retained Dark receipts.

    Values are receipt/canonical hashes where available. None means the raw
    receipt did not report a digest; the frozen supporting_files binding must
    still pin and validate the file. No absolute historical path is opened.
    """
    if (scope, oid) == SIEGE:
        request = tool['requests'][0]
        return {path: request['reference_hashes'][role]
                for role, path in siege_reference_paths(oid).items()}
    if worktop_target(scope, oid):
        required = {}
        for target_oid, _ in WORKTOP_PROMPTS:
            paths = worktop_reference_paths(target_oid)
            required.update({path: None for path in paths})
            if target_oid == oid:
                required.update({path: info['sha256'] for path, info in zip(paths,
                    (binding['primary_source'], binding['views']['front'], binding['views']['top']))})
        required.update(INTERRUPTED_BATCH_PROMPTS)
        return required
    return {}


def receipt_facts(tool, scope, oid, binding):
    """Interpret known receipts without rewriting their returned fields."""
    if not isinstance(tool, dict):
        return False, set(), set()
    if (scope, oid) == SIEGE:
        requests = tool.get('requests', [])
        request = requests[0] if isinstance(requests, list) and len(requests) == 1 else {}
        request = request if isinstance(request, dict) else {}
        refs = request.get('referenced_image_paths', [])
        paths = siege_reference_paths(oid)
        hashes = request.get('reference_hashes', {})
        valid = (request.get('object_id') == oid and request.get('direction') == 'rear'
                 and request.get('status') == 'blocked' and request.get('stage') == 'input'
                 and request.get('category') == 'violence' and request.get('error') == SIEGE_ERROR
                 and request.get('candidate_only') is True and request.get('affected_view_unresolved') is True
                 and isinstance(request.get('prompt'), str)
                 and hashlib.sha256(request['prompt'].encode()).hexdigest() == SIEGE_PROMPT_SHA256
                 and isinstance(hashes, dict) and set(hashes) == {'source', 'left'}
                 and hashes.get('source') == binding['primary_source']['sha256']
                 and isinstance(hashes.get('left'), str) and len(hashes['left']) == 64
                 and isinstance(refs, list) and len(refs) == 2
                 and all(historical_reference_matches(value, paths[role])
                         for value, role in zip(refs, ('source', 'left'))))
        return valid, {'rear'}, {request.get('request_id')}
    if worktop_target(scope, oid):
        targets = tool.get('blocked_batch_targets', [])
        scope_rows = tool.get('requested_batch_scope', [])
        error = tool.get('exact_error_response', {})
        actual = [(r.get('object_id'), r.get('direction')) for r in targets if isinstance(r, dict)
                  and isinstance(r.get('object_id'), str) and isinstance(r.get('direction'), str)] if isinstance(targets, list) else []
        declared = [(r.get('object_id'), r.get('direction')) for r in scope_rows if isinstance(r, dict)
                    and isinstance(r.get('object_id'), str) and isinstance(r.get('direction'), str)] if isinstance(scope_rows, list) else []
        valid = (isinstance(targets, list) and len(targets) == 4 and len(actual) == 4
                 and set(actual) == set(WORKTOP_PROMPTS) and len(set(actual)) == 4
                 and isinstance(scope_rows, list) and len(scope_rows) == 4
                 and len(declared) == 4 and set(declared) == set(WORKTOP_PROMPTS)
                 and tool.get('blocking_tool_request_id') == WORKTOP_BATCH_ID
                 and tool.get('record_type') == 'safety-blocked image-generation batch; do not retry any listed directions'
                 and tool.get('request_id_association') == 'One of the four concurrent calls returned this error; the executor did not identify which call. Treat all four requested directions as blocked and unavailable.'
                 and error == {'status_code': 400, 'type': 'image_generation_user_error',
                     'code': 'moderation_blocked', 'moderation_stage': 'input',
                     'safety_violations': ['violence'], 'request_id': WORKTOP_BATCH_ID,
                     'exact_message': 'Your request was rejected by the safety system. If you believe this is an error, contact us at help.openai.com and include the request ID ' + WORKTOP_BATCH_ID + '. safety_violations=[violence].'}
                 and binding.get('reason') == BATCH_REASON)
        for row in targets if isinstance(targets, list) else []:
            if not isinstance(row, dict):
                valid = False
                continue
            key = (row.get('object_id'), row.get('direction'))
            prompt = row.get('prompt')
            refs = row.get('reference_image_paths', [])
            expected = worktop_reference_paths(row.get('object_id') if isinstance(row.get('object_id'), str) else '')
            valid = valid and (all(isinstance(v, str) for v in key) and key in WORKTOP_PROMPTS
                and isinstance(prompt, str) and hashlib.sha256(prompt.encode()).hexdigest() == WORKTOP_PROMPTS.get(key)
                and row.get('prompt_sha256') == WORKTOP_PROMPTS.get(key)
                and row.get('tool_request_id') is None and row.get('candidate_status') == 'blocked-batch'
                and row.get('candidate_file_saved') is False
                and row.get('tool_request_id_status') == 'No per-call ID returned; one concurrent call in this batch returned the safety error below, exact blocked target is unknown.'
                and isinstance(refs, list) and len(refs) == 3
                and all(historical_reference_matches(value, relative) for value, relative in zip(refs, expected)))
        attempts = tool.get('second_attempts_before_root_stop', [])
        valid = valid and isinstance(attempts, list) and len(attempts) == 2
        seen_prompts = set()
        for attempt in attempts if isinstance(attempts, list) else []:
            if not isinstance(attempt, dict):
                valid = False
                continue
            path = attempt.get('prompt_path')
            valid = valid and (isinstance(path, str) and path in INTERRUPTED_BATCH_PROMPTS
                and attempt.get('prompt_sha256') == INTERRUPTED_BATCH_PROMPTS.get(path)
                and attempt.get('status') == INTERRUPTED_BATCH_STATUS
                and attempt.get('direction') == 'top'
                and attempt.get('object_id') in {'industry-menagerie-goblin-workbench', 'industry-menagerie-kennel-cage-section'})
            if isinstance(path, str):
                seen_prompts.add(path)
        valid = valid and seen_prompts == set(INTERRUPTED_BATCH_PROMPTS)
        return valid, TARGETS[(scope, oid)], {tool.get('blocking_tool_request_id')}
    if (scope, oid) == ('style-packs/ink-and-lanterns', 'arsenal-spear'):
        valid = (tool.get('object_id') == oid and tool.get('target_views') == ['top', 'bottom']
                 and tool.get('affected_views') == ['top', 'bottom']
                 and tool.get('status') == 'blocked-by-imagegen-input-moderation'
                 and tool.get('moderation_stage') == 'input' and tool.get('categories') == ['violence']
                 and tool.get('tool_error', {}).get('code') == 'moderation_blocked'
                 and tool.get('source_image') == binding['primary_source']['path']
                 and tool.get('installed') is False and tool.get('raw_atlas') is None
                 and all(isinstance(tool.get(k), str) and tool[k] for k in
                         ('prompt_path', 'source_contact_sheet', 'prompt_copy_path', 'evidence_path'))
                 and isinstance(tool.get('geometry_guide'), list) and len(tool['geometry_guide']) == 2
                 and all(isinstance(p, str) and p for p in tool['geometry_guide']))
        return valid, {'top', 'bottom'}, {tool.get('request_id')}
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
        for path, expected in additional_receipt_support(tool, scope, oid, row).items():
            if path not in dependencies or (expected and dependencies[path].get('sha256') != expected):
                raise ValueError('Missing or changed portable recorded-batch input: ' + path)
        if tool.get('prompt_path') and tool['prompt_path'] not in dependencies:
            raise ValueError('Missing portable generation-block prompt: ' + oid)
        for field in ('source_contact_sheet', 'input_contact_sheet'):
            if tool.get(field) and tool[field] not in dependencies:
                raise ValueError('Missing portable generation-block input contact: ' + oid)
        for guide in tool.get('geometry_guide', []):
            if guide not in dependencies:
                raise ValueError('Missing portable generation-block geometry guide: ' + oid)
        if tool.get('prompt_sha256'):
            if dependencies.get(tool.get('prompt_path'), {}).get('sha256') != tool['prompt_sha256']:
                raise ValueError('Generation-block prompt hash disagrees with receipt: ' + oid)
        if tool.get('prompt_copy_path'):
            info = dependencies.get(tool['prompt_copy_path'])
            if not info:
                raise ValueError('Missing portable generation-block prompt copy: ' + oid)
            prompt_copy = json.loads(contained(pack, info['path']).read_bytes())
            if (prompt_copy.get('prompt_path') != tool.get('prompt_path')
                    or prompt_copy.get('prompt_sha256') != tool.get('prompt_sha256')
                    or hashlib.sha256(prompt_copy.get('prompt', '').encode()).hexdigest() != tool.get('prompt_sha256')):
                raise ValueError('Generation-block prompt copy content differs: ' + oid)
        if tool.get('evidence_path'):
            info = dependencies.get(tool['evidence_path'])
            if not info:
                raise ValueError('Missing portable generation-block request copy: ' + oid)
            request = json.loads(contained(pack, info['path']).read_bytes())
            for field in ('object_id', 'target_views', 'request_id', 'status', 'tool_error', 'source_image', 'geometry_guide'):
                if request.get(field) != tool.get(field):
                    raise ValueError('Generation-block request copy content differs: ' + oid)
        # Embedded hashes of original JSON copies remain archival receipt
        # values. Current supporting_files hashes bind tag-normalized copies;
        # their request/prompt contents are additionally checked above.
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
