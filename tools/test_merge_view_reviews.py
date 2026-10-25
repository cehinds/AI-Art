"""Approval regressions: stale files, source evidence, revocations and partial QA."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

import merge_view_reviews as merge


class ApprovalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.pack = Path(self.temp.name)
        (self.pack / 'source.png').write_bytes(b'original-source')
        self.assets = {}
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
        catalog = {'assets': [{'id': x, 'views': {'applicable': True}} for x in ('crate', 'missing')]}
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


if __name__ == '__main__':
    unittest.main()
