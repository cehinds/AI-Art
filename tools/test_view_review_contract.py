"""Publication guards for approval hashes, canonical identity and subsets."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from PIL import Image

import merge_view_reviews as merge
import view_review_contract as contract
from asset_attachment_tags import enrich_document


class PublishedReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.pack = Path(self.temp.name)
        (self.pack/'reusable').mkdir()
        Image.new('RGBA',(4,4),(1,2,3,255)).save(self.pack/'source.png')
        self.group = {'object_id':'crate','complete':True,'views':{}}
        self.index = {'assets':[{'id':'crate','kind':'sprite','image':{'path':'source.png','width':4,'height':4},
                       'views':{'applicable':True,'complete':True}}],
                      'view_sets':[self.group]}
        record = {'status':'pass','reviewer':'root','reviewed_at':'2026-10-25T10:00:00+00:00',
                  'source':str(self.pack/'source.png'),'source_sha256':merge.sha(self.pack/'source.png'),
                  'image_hashes':{},'view_paths':{}}
        for view in merge.VIEWS:
            path=self.pack/(view+'.png');Image.new('RGBA',(4,4),(len(view),2,3,255)).save(path)
            ident='crate.'+view;self.group['views'][view]=ident
            self.index['assets'].append({'id':ident,'object_id':'crate','view':view,'kind':'sprite',
                'image':{'path':path.name,'width':4,'height':4},'provenance':{'source_image':'source.png'}})
            record['image_hashes'][view]=merge.sha(path);record['view_paths'][view]=str(path)
        self.report=merge.merge_library(self.pack,'fixture',self.index,
            {'assets':self.index['assets'],'view_sets':[self.group]},[('root',{'reviewed':{'fixture::crate':record}})])
        self.publish()

    def publish(self):
        (self.pack/contract.REVIEW_PATH).write_bytes(contract.encoded(self.report))
        self.index['view_review']=contract.reference(self.report)

    def test_current_review_and_tagging_are_stable(self):
        contract.attach_review(self.pack,self.index)
        self.assertEqual(contract.load_review(self.pack,self.index,True),self.report)
        tagged=enrich_document(copy.deepcopy(self.report),'gameplay')
        self.assertEqual(contract.encoded(tagged),contract.encoded(self.report))

    def test_changed_png_or_source_invalidates_approval(self):
        for filename in ('front.png','source.png'):
            path=self.pack/filename;original=path.read_bytes();path.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'Stale view-review file hash'):
                contract.load_review(self.pack,self.index,True)
            path.write_bytes(original)

    def test_changed_report_or_source_identity_is_rejected(self):
        path=self.pack/contract.REVIEW_PATH;path.write_text('{}')
        with self.assertRaisesRegex(ValueError,'JSON hash mismatch'):
            contract.load_review(self.pack,self.index)
        self.publish()
        self.index['assets'][1]['provenance']['source_image']='other.png'
        with self.assertRaisesRegex(ValueError,'source differs'):
            contract.load_review(self.pack,self.index)

    def test_worker_flag_and_missing_evidence_cannot_pass(self):
        self.report['sets'][0]['review']['reviewer']='artist'
        self.publish()
        with self.assertRaisesRegex(ValueError,'Incomplete independent approval'):
            contract.load_review(self.pack,self.index,True)
        self.index.pop('view_review')
        with self.assertRaisesRegex(ValueError,'Missing independent'):
            contract.load_review(self.pack,self.index,True)

    def test_missing_inventory_and_false_statistics_fail(self):
        self.report['sets'].clear();self.report['statistics']=contract.statistics([]);self.publish()
        with self.assertRaisesRegex(ValueError,'inventory differs'):
            contract.load_review(self.pack,self.index)
        self.index['assets']=[];self.index['view_sets']=[]
        contract.load_review(self.pack,self.index,True)
        self.index['view_review']['statistics']['expected_sets']=99
        with self.assertRaisesRegex(ValueError,'statistics'):
            contract.load_review(self.pack,self.index)

    def test_selected_collection_projects_evidence_and_hash(self):
        projected=contract.project(self.report,set())
        self.assertEqual(projected['sets'],[])
        self.assertEqual(projected['statistics']['approved_sets'],0)
        self.assertEqual(len(self.report['sets']),1)
        self.assertNotEqual(contract.reference(projected)['sha256'],contract.reference(self.report)['sha256'])

    def test_scene_unchanged_does_not_hide_primary_crop_change_or_alias_swap(self):
        Image.new('RGBA',(10,10),(90,80,70,255)).save(self.pack/'scene.png')
        self.index['assets'][0]['provenance']={'source_image':'scene.png'}
        for leaf in self.index['assets'][1:]:
            leaf['provenance']={'source_image':'scene.png','native_front':'source.png'}
        self.report['sets'][0]['source']={'path':'scene.png','sha256':merge.sha(self.pack/'scene.png')}
        self.publish();contract.load_review(self.pack,self.index,True)
        Image.new('RGBA',(4,4),(99,98,97,255)).save(self.pack/'alias.png')
        self.index['assets'][1]['provenance']['native_front']='alias.png'
        with self.assertRaisesRegex(ValueError,'Noncanonical native_front'):
            contract.load_review(self.pack,self.index,True)
        self.index['assets'][1]['provenance']['native_front']='source.png'
        Image.new('RGBA',(4,4),(100,101,102,255)).save(self.pack/'source.png')
        with self.assertRaisesRegex(ValueError,'primary source review'):
            contract.load_review(self.pack,self.index,True)

    def test_published_review_requires_canonical_and_reviewed_crop_bindings(self):
        record=self.report['sets'][0]
        primary=record.pop('primary_source');self.publish()
        with self.assertRaisesRegex(ValueError,'Missing canonical primary'):
            contract.load_review(self.pack,self.index,True)
        record['primary_source']=primary
        record['review'].pop('source_evidence');self.publish()
        with self.assertRaisesRegex(ValueError,'reviewed canonical crop'):
            contract.load_review(self.pack,self.index,True)

    def test_targeted_existing_review_is_explicit_and_cannot_replace_full_review(self):
        self.index['assets'].append({'id':'old-object','views':{'applicable':True,'complete':True}})
        legacy=copy.deepcopy(self.report);legacy['scope_mode']='targeted-existing-assets'
        (self.pack/contract.LEGACY_REVIEW_PATH).write_bytes(contract.encoded(legacy))
        contract.attach_review(self.pack,self.index,legacy=True)
        self.assertEqual(contract.load_review(self.pack,self.index,True,legacy=True),legacy)
        self.assertEqual(self.index['legacy_view_review']['coverage']['object_ids'],['crate'])
        with self.assertRaisesRegex(ValueError,'inventory differs'):
            contract.load_review(self.pack,self.index,True)
        self.index['legacy_view_review']['coverage']['object_ids'].append('missing-object')
        with self.assertRaisesRegex(ValueError,'legacy review coverage'):
            contract.load_review(self.pack,self.index,True,legacy=True)

    def test_targeted_application_preserves_unreviewed_existing_group(self):
        untouched={'object_id':'old-object','complete':True,'notes':'Earlier delivery review'}
        worker={'view_sets':[copy.deepcopy(self.group),copy.deepcopy(untouched)]}
        legacy=copy.deepcopy(self.report);legacy['scope_mode']='targeted-existing-assets'
        merge.apply_approvals(worker,legacy)
        self.assertEqual(worker['view_sets'][1],untouched)
        self.assertEqual(worker['view_sets'][0]['geometry_qa']['status'],'passed')
        self.assertEqual(worker['view_sets'][0]['geometry_qa']['evidence'],contract.LEGACY_REVIEW_PATH)

    def test_archive_retains_local_review_and_tools_for_selected_maps(self):
        from package_pocket_reusable import plan
        # A separately encoded but pixel-identical reviewed crop must travel with
        # the archive even when no asset's normal provenance references it.
        (self.pack/'evidence').mkdir()
        Image.open(self.pack/'source.png').save(self.pack/'evidence/reviewed-copy.png',compress_level=0)
        proof=self.report['sets'][0]['review']['source_evidence']
        proof['reviewed_reference']=contract.file_evidence(self.pack,'evidence/reviewed-copy.png')
        self.publish()
        self.index['assets'].append({'id':'icon','kind':'ui','image':{'path':'icon.png','width':4,'height':4}})
        Image.new('RGBA',(4,4),(90,80,70,255)).save(self.pack/'icon.png')
        self.index['maps']=[{'id':'icon-map','file':'map.json','source':'icon.png'}]
        (self.pack/'map.json').write_text(json.dumps({'layers':[{'asset_id':'icon'}]}))
        for asset in self.index['assets']:
            (self.pack/Path(asset['image']['path']).with_suffix('.json')).write_bytes(contract.encoded(asset))
        (self.pack/'manifest.json').write_text('{}')
        (self.pack/'README.md').write_text('Fixture')
        (self.pack/'reusable/index.json').write_bytes(contract.encoded(self.index))
        legacy=copy.deepcopy(self.report);legacy['scope_mode']='targeted-existing-assets'
        (self.pack/contract.LEGACY_REVIEW_PATH).write_bytes(contract.encoded(legacy))
        self.index['legacy_view_review']=contract.reference(legacy,legacy=True)
        (self.pack/'reusable/index.json').write_bytes(contract.encoded(self.index))
        for selected in (None,['icon-map']):
            contents=plan(self.pack,selected)
            if selected is None:self.assertIn('library/evidence/reviewed-copy.png',contents)
            self.assertIn('view_review_contract.py',contents)
            self.assertIn('merge_view_reviews.py',contents)
            with tempfile.TemporaryDirectory() as exported:
                root=Path(exported)
                for name,data in contents.items():
                    path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
                catalog=json.loads(contents['library/reusable/index.json'])
                report=contract.load_review(root/'library',catalog,True)
                self.assertEqual(report['statistics']['approved_sets'],0 if selected else 1)
                legacy_report=contract.load_review(root/'library',catalog,True,legacy=True)
                self.assertEqual(legacy_report['statistics']['approved_sets'],0 if selected else 1)


if __name__=='__main__':
    unittest.main()
