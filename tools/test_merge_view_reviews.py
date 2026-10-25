"""Approval regressions: stale files, source evidence, revocations and partial QA."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from PIL import Image

import merge_view_reviews as merge


class ApprovalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.pack = Path(self.temp.name)
        Image.new('RGBA', (3,4), (10,20,30,255)).save(self.pack / 'source.png')
        self.assets = {'crate': {'id':'crate','image':{'path':'source.png'},'views':{'applicable':True}}}
        self.group = {'object_id': 'crate', 'complete': True, 'views': {}}
        self.review = {'status': 'pass', 'reviewer': 'root', 'reviewed_at': '2026-10-25T10:00:00+00:00',
                       'source': str(self.pack / 'source.png'), 'source_sha256': merge.sha(self.pack / 'source.png'),
                       'image_hashes': {}, 'view_paths': {}}
        for v in merge.VIEWS:
            path = self.pack / (v + '.png'); path.write_bytes(v.encode())
            ident = 'crate.' + v
            self.assets[ident] = {'id': ident, 'object_id': 'crate', 'view': v,
                                  'image': {'path': path.name}, 'provenance': {'source_image': 'source.png'}}
            self.group['views'][v] = ident
            self.review['image_hashes'][v] = merge.sha(path)
            self.review['view_paths'][v] = str(path)

    def result(self, *records):
        return merge.review_set(self.pack, 'crate', self.group, self.assets,
                                [('root', r) for r in (records or [self.review])])

    def test_pass_requires_current_source_and_every_view(self):
        self.assertTrue(self.result()['complete'])
        (self.pack / 'bottom.png').write_bytes(b'new-correction')
        self.assertFalse(self.result()['complete'])
        self.review['image_hashes']['bottom'] = merge.sha(self.pack / 'bottom.png')
        self.assertTrue(self.result()['complete'])
        (self.pack / 'source.png').write_bytes(b'different-source')
        self.assertFalse(self.result()['complete'])

    def test_missing_source_evidence_never_passes(self):
        del self.review['source_sha256']
        result = self.result()
        self.assertFalse(result['complete'])
        self.assertEqual(result['excluded_review_counts']['missing-or-stale-source-evidence'], 1)

    def test_partial_views_and_pending_snapshot_never_promote(self):
        self.review['status'] = 'pending'
        self.review['view_reviews'] = {v: {'status': 'pass'} for v in merge.VIEWS}
        self.assertFalse(self.result()['complete'])

    def test_latest_decisive_review_wins_pending_does_not_override(self):
        pending = {**self.review, 'status': 'pending', 'reviewed_at': '2026-10-25T13:00:00+00:00'}
        rejected = {**self.review, 'status': 'issues', 'reviewed_at': '2026-10-25T11:00:00+00:00'}
        self.assertTrue(self.result(self.review, pending)['complete'])
        self.assertEqual(self.result(self.review, rejected, pending)['status'], 'needs-correction')
        resolved = {**self.review, 'reviewed_at': '2026-10-25T12:00:00+00:00'}
        self.assertTrue(self.result(self.review, rejected, resolved, pending)['complete'])

    def test_rejection_tie_wins_and_hash_current_defect_needs_no_source_evidence(self):
        rejected = {**self.review, 'status': 'needs-correction'}
        del rejected['source_sha256']
        self.assertFalse(self.result(self.review, rejected)['complete'])

    def test_mismatched_leaf_or_review_path_cannot_pass(self):
        self.assets['crate.top']['object_id'] = 'other'
        self.assertFalse(self.result()['complete'])
        self.assets['crate.top']['object_id'] = 'crate'
        self.review['view_paths']['top'] = str(self.pack / 'elsewhere.png')
        self.assertFalse(self.result()['complete'])

    def test_export_is_relative_covers_missing_objects_and_apply_is_idempotent(self):
        catalog = {'assets': [self.assets['crate'], {'id':'missing','views':{'applicable':True}}]}
        worker = {'assets': list(self.assets.values()), 'view_sets': [self.group]}
        report = merge.merge_library(self.pack, 'fixture', catalog, worker,
                    [('root', {'reviewed': {'fixture::crate': self.review}})])
        self.assertEqual(report['statistics']['expected_sets'], 2)
        self.assertEqual(report['statistics']['approved_sets'], 1)
        self.assertNotIn(str(self.pack), json.dumps(report))
        applied = merge.apply_approvals(copy.deepcopy(worker), report)
        self.assertEqual(merge.apply_approvals(copy.deepcopy(applied), report), applied)
        self.assertEqual(applied['view_sets'][0]['geometry_qa']['status'], 'passed')
        self.assertEqual(report['sets'][1]['status'], 'missing-views')

    def test_containment_and_independent_identity(self):
        self.assets['crate.top']['image']['path'] = '../outside.png'
        with self.assertRaises(ValueError): self.result()
        self.assets['crate.top']['image']['path'] = 'top.png'
        self.review['reviewer'] = 'worker'
        self.assertFalse(self.result()['complete'])

    def scene_fixture(self):
        Image.new('RGBA',(12,12),(90,80,70,255)).save(self.pack/'scene.png')
        self.assets['crate']['provenance']={'source_image':'scene.png'}
        for view in merge.VIEWS:
            self.assets['crate.'+view]['provenance']={'source_image':'scene.png',
                'native_front':'source.png','native_front_sha256':merge.sha(self.pack/'source.png')}
        capture={'objects':[{'object_id':'crate','source':{'path':str(self.pack/'source.png'),
            'sha256':merge.sha(self.pack/'source.png')},'views':{v:{'path':self.review['view_paths'][v],
            'sha256':self.review['image_hashes'][v]} for v in merge.VIEWS}}]}
        path=self.pack/'capture.json';path.write_text(json.dumps(capture))
        self.review.update(source=str(self.pack/'scene.png'),source_sha256=merge.sha(self.pack/'scene.png'),
            source_evidence={'capture_manifest':str(path),'capture_manifest_sha256':merge.sha(path)})

    def test_canonical_capture_preserves_valid_scene_review_without_backfilling(self):
        self.scene_fixture()
        result=self.result()
        self.assertTrue(result['complete'])
        self.assertEqual(result['primary_source']['path'],'source.png')
        self.assertEqual(result['review']['source_evidence']['method'],'verified-capture-manifest')
        self.assertNotIn(str(self.pack),json.dumps(result))
        # Recording only a whole scene never proves which crop was reviewed.
        del self.review['source_evidence']
        self.assertFalse(self.result()['complete'])

    def test_alias_swap_and_changed_crop_fail_with_unchanged_scene_and_views(self):
        self.scene_fixture()
        Image.new('RGBA',(3,4),(200,20,30,255)).save(self.pack/'alias.png')
        leaf=self.assets['crate.front']['provenance'];leaf['native_front']='alias.png'
        leaf['native_front_sha256']=merge.sha(self.pack/'alias.png')
        self.assertEqual(self.result()['status'],'invalid-canonical-source')
        leaf['native_front']='source.png';leaf['native_front_sha256']=merge.sha(self.pack/'source.png')
        Image.new('RGBA',(3,4),(80,90,100,255)).save(self.pack/'source.png')
        for v in merge.VIEWS:self.assets['crate.'+v]['provenance']['native_front_sha256']=merge.sha(self.pack/'source.png')
        self.assertFalse(self.result()['complete'])

    def test_tampered_capture_or_mismatched_capture_views_never_pass(self):
        self.scene_fixture();path=self.pack/'capture.json'
        document=json.loads(path.read_text());document['objects'][0]['views']['top']['sha256']='0'*64
        path.write_text(json.dumps(document))
        self.assertFalse(self.result()['complete'])
        self.review['source_evidence']['capture_manifest_sha256']=merge.sha(path)
        self.assertFalse(self.result()['complete'])

    def test_exact_rgba_reference_copy_is_valid_but_different_pixels_are_not(self):
        Image.open(self.pack/'source.png').save(self.pack/'copy.png',compress_level=0)
        self.assertNotEqual(merge.sha(self.pack/'copy.png'),merge.sha(self.pack/'source.png'))
        self.review.update(source=str(self.pack/'copy.png'),source_sha256=merge.sha(self.pack/'copy.png'))
        result=self.result();self.assertTrue(result['complete'])
        self.assertEqual(result['review']['source_evidence']['reviewed_reference']['path'],'copy.png')
        Image.new('RGBA',(3,4),(1,2,3,255)).save(self.pack/'copy.png')
        self.review['source_sha256']=merge.sha(self.pack/'copy.png')
        self.assertFalse(self.result()['complete'])

    def test_worker_cannot_replace_authoritative_canonical_parent(self):
        catalog={'assets':[self.assets['crate']]}
        worker={'assets':list(copy.deepcopy(self.assets).values()),'view_sets':[self.group]}
        worker['assets'][0]['image']['path']='alias.png'
        with self.assertRaisesRegex(ValueError,'override canonical physical parent'):
            merge.merge_library(self.pack,'fixture',catalog,worker,[])


if __name__ == '__main__':
    unittest.main()
