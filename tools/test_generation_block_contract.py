"""Recorded blocks are narrow release exceptions, not six-view approvals."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image
import generation_block_contract as blocks
import view_review_contract as reviews
from validate_pocket_reusable import validate
from package_pocket_reusable import plan, write_zip
from export_pocket_collections import verify_archive, export


class RecordedBlockTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.pack = Path(self.temp.name) / 'pack'
        (self.pack / 'reusable').mkdir(parents=True)
        self.scope = 'style-packs/ink-and-lanterns'
        self.index = {'assets': [], 'view_sets': [], 'maps': [], 'view_review_policy': reviews.POLICY}
        self.rows = []
        for n, oid in enumerate(('iron-sword', 'crate')):
            source = oid + '.png'
            Image.new('RGBA', (8, 8), (10 + n, 30, 50, 255)).save(self.pack / source)
            group = {'object_id': oid, 'complete': oid != 'iron-sword', 'views': {}}
            parent = {'id': oid, 'name': oid, 'anchor_px': [4, 4], 'kind': 'sprite', 'tags': ['fixture'],
                      'image': {'path': source, 'width': 8, 'height': 8},
                      'provenance': {'method': 'source'},
                      'views': {'applicable': True, 'complete': group['complete']}}
            self.index['assets'].append(parent)
            infos = {}
            for i, view in enumerate(reviews.VIEWS):
                path = oid + '.' + view + '.png'
                im = Image.new('RGBA', (8, 8))
                for x in range(2, 6):
                    for y in range(2, 6):
                        im.putpixel((x, y), (40 + n * 10 + i, 60, 80, 255))
                im.save(self.pack / path)
                aid = oid + '.' + view
                group['views'][view] = aid
                parent['views'][view] = {'asset_id': aid, 'status': 'present'}
                self.index['assets'].append({'id': aid, 'name': aid, 'tags': ['fixture'], 'kind': 'sprite',
                    'object_id': oid, 'view': view, 'anchor_px': [4, 4], 'image': {'path': path, 'width': 8, 'height': 8},
                    'provenance': {'method': 'inferred', 'source_image': source},
                    'views': {'applicable': False, 'reason': 'Individual grouped view'}})
                infos[view] = {'asset_id': aid, 'path': path,
                               'sha256': hashlib.sha256((self.pack / path).read_bytes()).hexdigest()}
            self.index['view_sets'].append(group)
            primary = {'asset_id': oid, **reviews.file_evidence(self.pack, source)}
            proof = {'method': 'direct-reviewed-source', 'reviewed_reference': reviews.file_evidence(self.pack, source)}
            row = {'object_id': oid, 'complete': group['complete'],
                   'status': 'passed' if group['complete'] else 'needs-correction',
                   'source': {'path': source, 'sha256': primary['sha256']},
                   'primary_source': primary, 'views': infos,
                   'review': {'status': 'pass' if group['complete'] else 'issues', 'reviewer': 'root',
                              'affected_views': [] if group['complete'] else ['top'],
                              'reviewed_at': '2026-10-26T07:56:23+00:00', 'source_evidence': proof}}
            self.rows.append(row)
        row = self.rows[0]
        (self.pack / 'blocked.json').write_bytes(blocks.encoded({'object_id': 'iron-sword',
            'affected_views': ['top'], 'status': 'blocked', 'request_id': '2124307c-f6dc-4115-a081-ba6896c34e23'}))
        self.block = {'object_id': 'iron-sword', 'status': 'external-generation-blocked', 'complete': False,
            'affected_views': ['top'], 'reason': 'Actual fixture image-tool rejection',
            'recorded_at': '2026-10-26T08:00:00+00:00', 'primary_source': row['primary_source'],
            'views': copy.deepcopy(row['views']), 'evidence': {'path': 'blocked.json',
                'sha256': hashlib.sha256((self.pack / 'blocked.json').read_bytes()).hexdigest()},
            'unaffected_review': {'status': 'independent-partial-review', 'reviewer': 'root',
                'reviewed_at': '2026-10-26T07:56:23+00:00',
                'approved_views': [v for v in reviews.VIEWS if v != 'top'],
                'source': {k: v for k, v in row['primary_source'].items() if k != 'asset_id'},
                'views': {v: copy.deepcopy(info) for v, info in row['views'].items() if v != 'top'},
                'source_evidence': copy.deepcopy(row['review']['source_evidence'])}}
        self.block_report = {'schema_version': 1, 'path_base': 'library-root', 'scope': self.scope,
                             'policy': blocks.POLICY, 'records': [self.block]}
        (self.pack / 'README.md').write_text('Fixture only')
        (self.pack / 'manifest.json').write_text('{}')
        self.publish()

    def publish(self):
        self.report = {'schema_version': 1, 'path_base': 'library-root', 'scope': self.scope,
                       'sets': self.rows, 'statistics': reviews.statistics(self.rows)}
        (self.pack / reviews.REVIEW_PATH).write_bytes(reviews.encoded(self.report))
        self.index['view_review'] = reviews.reference(self.report)
        self.block_report['statistics'] = blocks.statistics(self.block_report['records'])
        (self.pack / blocks.PATH).write_bytes(blocks.encoded(self.block_report))
        self.index['generation_blocks'] = blocks.reference(self.block_report)
        for asset in self.index['assets']:
            (self.pack / Path(asset['image']['path']).with_suffix('.json')).write_bytes(reviews.encoded(asset))
        (self.pack / 'reusable/index.json').write_bytes(reviews.encoded(self.index))

    def test_default_strict_rejects_opt_in_preserves_incomplete(self):
        with self.assertRaisesRegex(ValueError, 'incomplete'):
            validate(self.pack, require_views=True)
        result = validate(self.pack, require_views=True, allow_recorded_blocks=True)
        self.assertEqual(result['recorded_blocked_set_count'], 1)
        self.assertEqual(result['recorded_blocked_view_count'], 1)
        self.assertGreater(result['missing_six_view_count'], 0)
        self.assertEqual(result['unexpected_incomplete_count'], 0)
        self.assertEqual(result['independent_view_review']['approved_sets'], 1)
        self.assertFalse(self.index['view_sets'][0]['complete'])
        self.assertEqual(self.rows[0]['status'], 'needs-correction')

    def test_unknown_object_direction_and_duplicate_records_rejected(self):
        for mutate in (lambda: self.block.update(object_id='other'),
                       lambda: self.block.update(affected_views=['top', 'bottom']),
                       lambda: self.block.update(affected_views=['*']),
                       lambda: self.block_report['records'].append(copy.deepcopy(self.block))):
            before = copy.deepcopy(self.block_report)
            mutate(); self.publish()
            with self.assertRaises(ValueError): blocks.load_blocks(self.pack, self.index)
            self.block_report = before; self.block = self.block_report['records'][0]

    def test_current_bytes_and_actual_tool_id_are_required(self):
        for name in ('iron-sword.png', 'iron-sword.front.png', 'blocked.json'):
            path = self.pack / name; before = path.read_bytes(); path.write_bytes(before + b'changed')
            with self.assertRaises(ValueError): blocks.load_blocks(self.pack, self.index)
            path.write_bytes(before)
        tool = {'object_id': 'arsenal-iron-sword', 'affected_views': ['top'],
                'status': 'blocked', 'request_id': 'actual-fixture-request'}
        (self.pack / 'blocked.json').write_bytes(blocks.encoded(tool))
        self.block['evidence']['sha256'] = hashlib.sha256((self.pack / 'blocked.json').read_bytes()).hexdigest()
        self.publish()
        with self.assertRaisesRegex(ValueError, 'actual image-tool'):
            blocks.load_blocks(self.pack, self.index)

    def test_unaffected_approval_cannot_be_invented_or_stale(self):
        for change in (lambda r: r.update(reviewer='artist'),
                       lambda r: r.update(approved_views=['front']),
                       lambda r: r['views']['front'].update(sha256='0'*64),
                       lambda r: r['source_evidence'].clear()):
            before = copy.deepcopy(self.block['unaffected_review'])
            change(self.block['unaffected_review']); self.publish()
            with self.assertRaises(ValueError): blocks.load_blocks(self.pack, self.index)
            self.block['unaffected_review'] = before

    def test_unrelated_incomplete_or_broken_direction_still_fails(self):
        self.index['view_sets'][1]['complete'] = False
        self.index['assets'][7]['views']['complete'] = False
        self.rows[1]['complete'] = False; self.rows[1]['status'] = 'needs-correction'; self.publish()
        with self.assertRaisesRegex(ValueError, 'incomplete'):
            validate(self.pack, True, True)
        self.index['view_sets'][0]['views']['front'] = 'crate.front'; self.publish()
        with self.assertRaisesRegex(ValueError, 'leaf differs|canonical physical crop'):
            validate(self.pack, True, True)

    def test_no_wildcard_alias_or_path_escape(self):
        self.block['blocked_pixel_aliases'] = [['top', 'front']]; self.publish()
        with self.assertRaisesRegex(ValueError, 'alias exception escapes'):
            blocks.load_blocks(self.pack, self.index)
        self.block.pop('blocked_pixel_aliases')
        self.block['evidence']['path'] = '../blocked.json'; self.publish()
        with self.assertRaisesRegex(ValueError, 'Unsafe'):
            blocks.load_blocks(self.pack, self.index)

    def test_current_unaffected_hold_or_pending_review_cannot_use_exception(self):
        for change in (lambda r: r.update(affected_views=['front']),
                       lambda r: r.update(affected_views=['top', 'front']),
                       lambda r: r.update(affected_views=[]),
                       lambda r: r.update(status='pending-review')):
            before = copy.deepcopy(self.rows[0]['review'])
            change(self.rows[0]['review']); self.publish()
            with self.assertRaisesRegex(ValueError, 'incomplete'):
                validate(self.pack, True, True)
            self.rows[0]['review'] = before

    def test_invented_tool_request_id_is_rejected_even_when_hash_matches(self):
        path = self.pack / 'blocked.json'
        tool = json.loads(path.read_bytes()); tool['request_id'] = 'invented'
        path.write_bytes(blocks.encoded(tool))
        self.block['evidence']['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.publish()
        with self.assertRaisesRegex(ValueError, 'actual image-tool'):
            blocks.load_blocks(self.pack, self.index)

    def test_policy_and_independent_report_cannot_disagree(self):
        self.rows[0]['views']['top']['sha256'] = '0'*64; self.publish()
        with self.assertRaisesRegex(ValueError, 'Stale view-review'):
            validate(self.pack, True, True)
        self.rows[0]['views']['top'] = copy.deepcopy(self.block['views']['top'])
        self.rows[0]['complete'] = True; self.rows[0]['status'] = 'passed'; self.publish()
        with self.assertRaisesRegex(ValueError, 'approval differs'):
            validate(self.pack, True, True)

    def test_full_and_subset_archive_revalidate_policy_and_evidence(self):
        for selected, expected in (('iron-sword.front', 1), ('crate.front', 0)):
            contents = plan(self.pack, [], selected_assets=[selected])
            catalog = json.loads(contents['library/reusable/index.json'])
            projected = json.loads(contents['library/' + blocks.PATH])
            self.assertEqual(projected['statistics']['recorded_blocked_sets'], expected)
            self.assertEqual('library/blocked.json' in contents, bool(expected))
            self.assertIn('generation_block_contract.py', contents)
            archive = Path(self.temp.name) / (selected + '.zip')
            write_zip(archive, contents, 1000000)
            destination = Path(self.temp.name) / (selected + '-extracted')
            result = verify_archive(archive, destination, allow_recorded_blocks=True)
            self.assertEqual(result['recorded_blocked_set_count'], expected)
            if expected:
                with self.assertRaisesRegex(ValueError, 'incomplete'):
                    verify_archive(archive, Path(self.temp.name) / 'strict-extracted')

    def test_export_threads_explicit_mode_through_real_fixture_archives(self):
        document = {'schema_version': 1, 'collections': [
            {'id': 'blocked-reference', 'label': 'Incomplete reference', 'assets': ['iron-sword'], 'maps': []},
            {'id': 'approved', 'label': 'Approved', 'assets': ['crate'], 'maps': []}]}
        with self.assertRaisesRegex(ValueError, 'incomplete'):
            export(self.pack, collections_plan=document)
        result = export(self.pack, collections_plan=document, allow_recorded_blocks=True)
        self.assertEqual(result['status'], 'exported-and-validated-with-recorded-generation-blocks')
        self.assertEqual(len(result['recorded_generation_blocks']), 1)
        current = json.loads((self.pack / 'reusable/index.json').read_bytes())
        self.assertFalse(current['view_sets'][0]['complete'])
        self.assertEqual(len(current['downloads']), 2)

    def test_tagging_policy_and_actual_evidence_is_byte_idempotent(self):
        from asset_attachment_tags import enrich_document
        for relative in (blocks.PATH, 'blocked.json'):
            raw = (self.pack / relative).read_bytes()
            for style in ('ink-and-lanterns', 'pocket-dungeon'):
                enriched = enrich_document(json.loads(raw), style)
                self.assertEqual(reviews.encoded(enriched), raw)
        path = self.pack / 'blocked.json'
        value = json.loads(path.read_bytes()); value.pop('tags')
        path.write_bytes(reviews.encoded(value))
        self.block['evidence']['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.publish()
        with self.assertRaisesRegex(ValueError, 'tag-normalized'):
            blocks.load_blocks(self.pack, self.index)

    def test_prompt_dependency_must_be_portable_and_hash_bound(self):
        prompt = self.pack / 'prompt.txt'; prompt.write_text('Retained exact request')
        path = self.pack / 'blocked.json'; value = json.loads(path.read_bytes())
        value['prompt_path'] = 'prompt.txt'; path.write_bytes(blocks.encoded(value))
        self.block['evidence']['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.publish()
        with self.assertRaisesRegex(ValueError, 'portable generation-block prompt'):
            blocks.load_blocks(self.pack, self.index)
        self.block['supporting_files'] = [{'path': 'prompt.txt', 'sha256': hashlib.sha256(prompt.read_bytes()).hexdigest()}]
        self.publish(); blocks.load_blocks(self.pack, self.index)
        contents = plan(self.pack, [], selected_assets=['iron-sword.front'])
        self.assertEqual(contents['library/prompt.txt'], prompt.read_bytes())
        prompt.write_text('changed')
        with self.assertRaisesRegex(ValueError, 'Stale generation-block evidence'):
            blocks.load_blocks(self.pack, self.index)

    def normalization_fixture(self):
        for name, size in [('shared.png', 64), ('separate.png', 128)]:
            Image.new('RGBA', (size, size), (70, 80, 90, 255)).save(self.pack / name)
        leaves = [a for a in self.index['assets'] if a.get('object_id') == 'crate']
        for leaf in leaves:
            leaf['provenance'].update(generated_atlas='shared.png',
                generated_atlas_sha256=hashlib.sha256((self.pack / 'shared.png').read_bytes()).hexdigest(),
                normalization={'scale': 0.125})
        return leaves

    def test_distinct_verified_raw_resolutions_allow_distinct_isotropic_factors(self):
        leaves = self.normalization_fixture()
        leaves[0]['provenance'].update(generated_atlas='separate.png',
            generated_atlas_sha256=hashlib.sha256((self.pack / 'separate.png').read_bytes()).hexdigest(),
            normalization={'scale': 0.0625})
        self.publish()
        self.assertEqual(validate(self.pack, True, True)['unexpected_incomplete_count'], 0)

    def test_same_verified_shared_input_still_requires_common_factor(self):
        leaves = self.normalization_fixture()
        leaves[0]['provenance']['normalization']['scale'] = 0.0625
        self.publish()
        with self.assertRaisesRegex(ValueError, 'inconsistent normalization scales: crate'):
            validate(self.pack, True, True)

    def test_legacy_unqualified_shared_basis_remains_strict(self):
        for i, leaf in enumerate(a for a in self.index['assets'] if a.get('object_id') == 'crate'):
            leaf['provenance']['normalization'] = {'scale': 0.0625 if i == 0 else 0.125}
        self.publish()
        with self.assertRaisesRegex(ValueError, 'inconsistent normalization scales: crate'):
            validate(self.pack, True, True)

    def clamped_fixture(self):
        leaves = self.normalization_fixture()
        for leaf in leaves:
            leaf['provenance']['normalization'].clear()
            leaf['provenance']['crop_bounds_px'] = {'alpha_bounds_global': [0, 0, 32, 32],
                'requested_shared_scale': 0.125, 'shared_scale': 0.125, 'resized_bounds_px': [4, 4]}
        leaves[0]['provenance']['crop_bounds_px'].update(
            alpha_bounds_global=[0, 0, 40, 40], shared_scale=0.1)
        return leaves

    def test_explicit_per_cell_fit_clamping_retains_shared_input_semantics(self):
        self.clamped_fixture(); self.publish()
        self.assertEqual(validate(self.pack, True, True)['unexpected_incomplete_count'], 0)

    def test_effective_crop_resize_and_finite_factors_are_verified(self):
        leaves = self.clamped_fixture(); crop = leaves[0]['provenance']['crop_bounds_px']
        for change in ({'shared_scale': 0.3}, {'resized_bounds_px': [9, 9]},
                       {'shared_scale': float('nan')}, {'requested_shared_scale': -1}):
            original = copy.deepcopy(crop); crop.update(change); self.publish()
            with self.assertRaisesRegex(ValueError, 'normalization factor|resized crop'):
                validate(self.pack, True, True)
            crop.clear(); crop.update(original)

    def test_recorded_uniform_projection_calibration_composes_with_raw_fit(self):
        leaves = self.clamped_fixture(); crop = leaves[0]['provenance']['crop_bounds_px']
        crop.update(projection_scale=0.5, resized_bounds_px=[2, 2]); self.publish()
        validate(self.pack, True, True)
        crop['projection_scale'] = 0; self.publish()
        with self.assertRaisesRegex(ValueError, 'projection normalization factor'):
            validate(self.pack, True, True)

    def test_builder_attach_preserves_frozen_reference_byte_idempotently(self):
        baseline = copy.deepcopy(self.index)
        self.index.pop('generation_blocks')  # Freshly regenerated builder index.
        reviews.attach_review(self.pack, self.index)
        self.assertEqual(reviews.encoded(self.index), reviews.encoded(baseline))
        reviews.attach_review(self.pack, self.index)
        self.assertEqual(reviews.encoded(self.index), reviews.encoded(baseline))
        legacy = copy.deepcopy(self.report); legacy['scope_mode'] = 'targeted-existing-assets'
        legacy['sets'] = [legacy['sets'][0]]; legacy['statistics'] = reviews.statistics(legacy['sets'])
        (self.pack / reviews.LEGACY_REVIEW_PATH).write_bytes(reviews.encoded(legacy))
        reviews.attach_review(self.pack, self.index, legacy=True)
        first = reviews.encoded(self.index)
        reviews.attach_review(self.pack, self.index, legacy=True)
        self.assertEqual(reviews.encoded(self.index), first)
        self.assertFalse(self.index['view_sets'][0]['complete'])

    def test_builder_absent_policy_stays_absent_and_stale_policy_fails(self):
        path = self.pack / blocks.PATH; before = path.read_bytes(); path.unlink()
        reviews.attach_review(self.pack, self.index)
        self.assertNotIn('generation_blocks', self.index)
        policy = json.loads(before); policy['records'][0]['views']['top']['sha256'] = '0'*64
        path.write_bytes(blocks.encoded(policy))
        with self.assertRaisesRegex(ValueError, 'Stale generation-block evidence'):
            reviews.attach_review(self.pack, self.index)

    def retarget(self, oid, scope):
        self.scope = scope; self.block_report['scope'] = scope
        for asset in self.index['assets']:
            if asset['id'] == 'iron-sword':
                asset['id'] = oid
            elif asset.get('object_id') == 'iron-sword':
                asset['object_id'] = oid; asset['id'] = oid + '.' + asset['view']
        group = self.index['view_sets'][0]; group['object_id'] = oid
        group['views'] = {v: oid + '.' + v for v in reviews.VIEWS}
        parent = self.index['assets'][0]
        for v in reviews.VIEWS: parent['views'][v]['asset_id'] = oid + '.' + v
        row = self.rows[0]; row['object_id'] = oid; row['primary_source']['asset_id'] = oid
        for v in reviews.VIEWS: row['views'][v]['asset_id'] = oid + '.' + v
        row['review']['affected_views'] = ['bottom']
        self.block.update(object_id=oid, affected_views=['bottom'], primary_source=row['primary_source'],
                          views=copy.deepcopy(row['views']))
        partial = self.block['unaffected_review']
        partial['approved_views'] = [v for v in reviews.VIEWS if v != 'bottom']
        partial['views'] = {v: copy.deepcopy(row['views'][v]) for v in partial['approved_views']}

    def write_receipt(self, value):
        path = self.pack / 'blocked.json'; path.write_bytes(blocks.encoded(value))
        self.block['evidence']['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.publish()

    def test_exact_carl_batch_receipt_and_unaffected_holds(self):
        self.retarget('attacks-carl-kick-03', 'style-packs/ink-and-lanterns')
        receipt = {'object_ids': sorted(blocks.CARL_BATCH), 'status': 'rejected', 'affected_views': ['BOTTOM'],
                   'request_id': '82d28979-b9cf-4e35-9dfa-10a41dea122c', 'error_code': 'moderation_blocked',
                   'moderation_stage': 'output', 'moderation_categories': ['other']}
        self.write_receipt(receipt)
        validate(self.pack, True, True)
        self.rows[0]['review']['affected_views'] = ['right', 'left', 'bottom']; self.publish()
        with self.assertRaisesRegex(ValueError, 'incomplete'):
            validate(self.pack, True, True)
        receipt['object_ids'].pop(); self.write_receipt(receipt)
        with self.assertRaisesRegex(ValueError, 'actual image-tool'):
            blocks.load_blocks(self.pack, self.index)

    def test_carl_input_contact_and_prompt_must_travel(self):
        self.retarget('attacks-carl-kick-01', 'style-packs/ink-and-lanterns')
        receipt = {'object_ids': sorted(blocks.CARL_BATCH), 'status': 'rejected', 'affected_views': ['BOTTOM'],
                   'request_id': '82d28979-b9cf-4e35-9dfa-10a41dea122c', 'error_code': 'moderation_blocked',
                   'moderation_stage': 'output', 'moderation_categories': ['other'],
                   'prompt_path': 'prompt.txt', 'source_contact_sheet': 'input.png'}
        (self.pack / 'prompt.txt').write_text('Exact retained prompt')
        Image.new('RGBA', (2, 2), (1, 2, 3, 255)).save(self.pack / 'input.png')
        self.block['supporting_files'] = [{'path': 'prompt.txt', 'sha256': hashlib.sha256((self.pack/'prompt.txt').read_bytes()).hexdigest()}]
        self.write_receipt(receipt)
        with self.assertRaisesRegex(ValueError, 'input contact'):
            blocks.load_blocks(self.pack, self.index)
        self.block['supporting_files'].append({'path': 'input.png', 'sha256': hashlib.sha256((self.pack/'input.png').read_bytes()).hexdigest()})
        self.publish(); contents = plan(self.pack, [], selected_assets=['attacks-carl-kick-01.front'])
        self.assertIn('library/input.png', contents); self.assertIn('library/prompt.txt', contents)
        self.assertEqual(json.loads(contents['library/blocked.json'])['affected_views'], ['BOTTOM'])

    def test_brittany_failure_list_excludes_allowed_but_invalid_candidate(self):
        self.retarget('directional--brittany', 'reusable-gameplay')
        Image.new('RGBA', (2, 2), (5, 6, 7, 255)).save(self.pack / 'candidate.png')
        raw_sha = hashlib.sha256((self.pack / 'candidate.png').read_bytes()).hexdigest()
        receipt = {'object_id': 'directional--brittany', 'status': 'blocked', 'blocked_view': 'bottom', 'complete': False,
            'canonical_source': {'path': 'iron-sword.png', 'sha256': self.block['primary_source']['sha256']},
            'current_view_sha256': {v: i['sha256'] for v, i in self.block['views'].items()},
            'failed_imagegen_requests': [{'request_id': ident, 'stage': 'output', 'categories': ['sexual'], 'result': 'blocked'}
                for ident in sorted(blocks.REQUESTS[('reusable-gameplay', 'directional--brittany')])],
            'allowed_but_rejected_candidate': {'request_id': 'allowed-not-a-block', 'raw_atlas': 'candidate.png',
                'raw_atlas_sha256': raw_sha, 'installed_view': self.block['views']['bottom']['path'],
                'installed_view_sha256': self.block['views']['bottom']['sha256'], 'review_contact': '/historical/session.json'}}
        self.write_receipt(receipt)
        with self.assertRaisesRegex(ValueError, 'rejected-candidate raw'):
            blocks.load_blocks(self.pack, self.index)
        self.block['supporting_files'] = [{'path': 'candidate.png', 'sha256': raw_sha}]
        self.publish(); validate(self.pack, True, True)
        contents = plan(self.pack, [], selected_assets=['directional--brittany.front'])
        self.assertIn('library/candidate.png', contents)
        receipt['failed_imagegen_requests'] = [{'request_id': 'allowed-not-a-block', 'result': 'blocked'}]
        self.write_receipt(receipt)
        with self.assertRaisesRegex(ValueError, 'actual image-tool'):
            blocks.load_blocks(self.pack, self.index)

    def test_all_six_known_block_remains_six_unapproved_references(self):
        self.retarget('arsenal-recurve-bow', 'style-packs/ink-and-lanterns')
        self.block['affected_views'] = list(reviews.VIEWS)
        self.rows[0]['review']['affected_views'] = list(reviews.VIEWS)
        self.block['unaffected_review'].update(approved_views=[], views={})
        receipt = {'object_id': 'arsenal-recurve-bow', 'status': 'rejected',
            'affected_views': [v.upper() for v in reviews.VIEWS],
            'request_id': '01e77624-66e2-4803-a093-773861a20e76',
            'error_code': 'moderation_blocked', 'moderation_stage': 'input',
            'moderation_categories': ['violence']}
        self.write_receipt(receipt)
        with self.assertRaisesRegex(ValueError, 'incomplete'):
            validate(self.pack, True)
        result = validate(self.pack, True, True)
        self.assertEqual(result['recorded_blocked_view_count'], 6)
        self.assertEqual(result['independent_view_review']['approved_sets'], 1)
        self.assertFalse(self.rows[0]['complete'])
        self.assertEqual(self.block['unaffected_review']['approved_views'], [])
        receipt['moderation_stage'] = 'output'; self.write_receipt(receipt)
        with self.assertRaisesRegex(ValueError, 'actual image-tool'):
            blocks.load_blocks(self.pack, self.index)

    def test_exact_bomb_direction_receipt_preserves_five_approved_views(self):
        self.retarget('bubble-airship-bomb-rack', 'book-tiles/dungeon-after-dark')
        self.block['affected_views'] = ['top']; self.rows[0]['review']['affected_views'] = ['top']
        partial = self.block['unaffected_review']
        partial['approved_views'] = [v for v in reviews.VIEWS if v != 'top']
        partial['views'] = {v: copy.deepcopy(self.block['views'][v]) for v in partial['approved_views']}
        receipt = {'object_id': 'bubble-airship-bomb-rack', 'direction': 'top', 'status': 'blocked',
                   'source_tool': 'image_gen.imagegen', 'code': 'moderation_blocked',
                   'moderation_stage': 'input', 'category': 'violence',
                   'request_id': 'b859fd7b-afb2-4fc1-8f03-baba15f4951e'}
        self.write_receipt(receipt)
        with self.assertRaisesRegex(ValueError, 'incomplete'):
            validate(self.pack, True)
        self.assertEqual(validate(self.pack, True, True)['recorded_blocked_view_count'], 1)
        contents = plan(self.pack, [], selected_assets=['bubble-airship-bomb-rack.front'])
        self.assertEqual(json.loads(contents['library/blocked.json'])['direction'], 'top')
        receipt['direction'] = 'bottom'; self.write_receipt(receipt)
        with self.assertRaisesRegex(ValueError, 'actual image-tool'):
            blocks.load_blocks(self.pack, self.index)

    def test_spear_target_views_and_portable_request_prompt_and_guides(self):
        self.retarget('arsenal-spear', 'style-packs/ink-and-lanterns')
        self.block['affected_views'] = ['top', 'bottom']; self.rows[0]['review']['affected_views'] = ['top', 'bottom']
        partial = self.block['unaffected_review']
        partial['approved_views'] = [v for v in reviews.VIEWS if v not in {'top', 'bottom'}]
        partial['views'] = {v: copy.deepcopy(self.block['views'][v]) for v in partial['approved_views']}
        prompt = 'Exact retained source-bound request'
        (self.pack/'prompt.txt').write_text(prompt); prompt_sha = hashlib.sha256(prompt.encode()).hexdigest()
        for name in ('input.png', 'guide-top.png', 'guide-bottom.png'):
            Image.new('RGBA', (2, 2), (7, 8, 9, 255)).save(self.pack/name)
        request = {'object_id': 'arsenal-spear', 'target_views': ['top', 'bottom'],
            'affected_views': ['top', 'bottom'], 'status': 'blocked-by-imagegen-input-moderation',
            'request_id': '665246dd-074d-429b-b12d-516f5b70df9f', 'moderation_stage': 'input',
            'categories': ['violence'], 'tool_error': {'code': 'moderation_blocked'},
            'source_image': 'iron-sword.png', 'raw_atlas': None, 'installed': False,
            'prompt_path': 'prompt.txt', 'source_contact_sheet': 'input.png',
            'geometry_guide': ['guide-top.png', 'guide-bottom.png']}
        (self.pack/'request.json').write_bytes(blocks.encoded(request))
        (self.pack/'prompt.json').write_bytes(blocks.encoded({'prompt_path': 'prompt.txt',
            'prompt_sha256': prompt_sha, 'prompt': prompt}))
        receipt = {**request, 'prompt_sha256': prompt_sha, 'evidence_path': 'request.json',
                   'prompt_copy_path': 'prompt.json', 'prompt_copy_sha256': 'a'*64}
        self.write_receipt(receipt)
        with self.assertRaisesRegex(ValueError, 'portable generation-block'):
            blocks.load_blocks(self.pack, self.index)
        self.block['supporting_files'] = [{'path': name, 'sha256': hashlib.sha256((self.pack/name).read_bytes()).hexdigest()}
            for name in ('prompt.txt', 'input.png', 'guide-top.png', 'guide-bottom.png', 'request.json', 'prompt.json')]
        self.publish(); validate(self.pack, True, True)
        contents = plan(self.pack, [], selected_assets=['arsenal-spear.front'])
        self.assertIn('library/request.json', contents); self.assertIn('library/guide-bottom.png', contents)
        # The old embedded JSON-copy hash is archival; current policy pins the
        # normalized JSON bytes and verifies exact prompt/request contents.
        bad = json.loads((self.pack/'prompt.json').read_bytes()); bad['prompt'] = 'changed'
        (self.pack/'prompt.json').write_bytes(blocks.encoded(bad))
        self.block['supporting_files'][-1]['sha256'] = hashlib.sha256((self.pack/'prompt.json').read_bytes()).hexdigest()
        self.publish()
        with self.assertRaisesRegex(ValueError, 'prompt copy content differs'):
            blocks.load_blocks(self.pack, self.index)


if __name__ == '__main__':
    unittest.main()
