"""Exploration evidence binds distinct provenance and complete package bytes."""
import hashlib,json,tempfile,unittest
from pathlib import Path
from zipfile import ZipFile
import asset_attachment_tags as tags

def sha(raw):return hashlib.sha256(raw).hexdigest()

class ExplorationComponentEvidenceTests(unittest.TestCase):
    def fixture(self,project,reuse=False):
        root=project/'Web/wwwroot/assets';base=root/'exploration-components';base.mkdir(parents=True)
        (root/'reusable-library.json').write_text(tags.encoded({'libraries':[]}))
        (base/'source.png').write_bytes(b'source');(base/'module.png').write_bytes(b'module')
        component={'id':'patch','path':'module.png','pixelHash':'a'*64,'deduplication':'exact-existing' if reuse else 'new',
                   'provenance':{'kind':'visible-clean-surface-patch','sourceInPackage':'source.png','sourceSha256':sha(b'source')}}
        reused=[]
        if reuse:
            existing=project/'Web/existing.png';existing.write_bytes(b'module');component['existingPath']='Web/existing.png'
            reused=[{'id':'patch','existingPath':'Web/existing.png','pixelHash':'a'*64}]
        doc={'schemaVersion':1,'title':'Exploration components','components':[component],
             'deduplication':{'algorithm':'SHA256 of dimensions plus decoded RGBA bytes; equality requires identical dimensions and pixels','reused':reused,'newCount':0 if reuse else 1},
             'counts':{'inferred-restored-whole-object':0,'context-containing-reference-crop':0,'visible-clean-surface-patch':1}}
        (base/'room-recipe.json').write_text(json.dumps({'schemaVersion':1,'surface':{'componentId':'patch'},'placements':[{'componentId':'patch'}]}))
        (base/'manifest.json').write_text(json.dumps(doc,separators=(',',':')))
        members=[{'file':p.name,'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in sorted(base.iterdir())]
        (base/'package-hashes.json').write_text(json.dumps({'schemaVersion':1,'members':members},separators=(',',':')))
        with ZipFile(base/'exploration-components.zip','w') as z:
            for p in sorted(base.iterdir()):
                if p.suffix!='.zip':z.writestr(p.name,p.read_bytes())
        return root,base

    def test_apply_check_preserves_new_and_reused_pack_bytes(self):
        for reuse in [False,True]:
            with tempfile.TemporaryDirectory() as tmp:
                root,base=self.fixture(Path(tmp),reuse);before={p:p.read_bytes() for p in base.iterdir()}
                tags.apply(root);tags.refresh_legacy_archives(root);tags.apply(root,check=True)
                self.assertTrue(all(p.read_bytes()==raw for p,raw in before.items()))

    def test_corrupt_bound_member_or_unlisted_file_fails_before_writes(self):
        for name in ['source.png','module.png','unlisted.json']:
            with tempfile.TemporaryDirectory() as tmp:
                root,base=self.fixture(Path(tmp));(base/name).write_bytes(b'bad')
                with self.assertRaisesRegex(ValueError,'exploration component'):
                    tags.apply(root)
                self.assertFalse((root/tags.RULES_NAME).exists())

    def test_changed_reused_original_fails_before_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            project=Path(tmp);root,base=self.fixture(project,True);(project/'Web/existing.png').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'exploration component'):
                tags.apply(root)
            self.assertFalse((root/tags.RULES_NAME).exists())

    def test_non_evidenced_metadata_remains_taggable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,base=self.fixture(Path(tmp));p=base/'manifest.json';d=json.loads(p.read_text());d.pop('counts');p.write_text(json.dumps(d))
            self.assertEqual(tags.verified_exploration_component_documents(root),set())
            tags.apply(root);self.assertIn('tags',json.loads(p.read_text()))

if __name__=='__main__':unittest.main()
