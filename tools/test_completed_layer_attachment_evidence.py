"""Complete-component packs require source provenance and full byte closure."""
import hashlib,json,tempfile,unittest
from pathlib import Path
from zipfile import ZipFile
import asset_attachment_tags as tags

def sha(raw):return hashlib.sha256(raw).hexdigest()

class CompletedLayerEvidenceTests(unittest.TestCase):
    def fixture(self,project):
        root=project/'Web/wwwroot/assets';base=root/'completed-layers';base.mkdir(parents=True)
        (root/'reusable-library.json').write_text(tags.encoded({'libraries':[]}))
        (project/'source.png').write_bytes(b'source');(base/'module.png').write_bytes(b'module')
        doc={'schemaVersion':1,'coordinateSystem':'native pixels, top-left origin','counts':{'totalAssets':1},
             'assets':[{'id':'module','file':'module.png','sha256':sha(b'module'),'complete':True,'fullComponent':True,
                 'provenance':{'kind':'inferred-module','sourceFile':'source.png','sha256':sha(b'source')}}],
             'instances':[{'assetId':'module','offset':[0,0]}],'layers':[{'id':'ground'}],
             'architectureSource':{'file':'source.png','sha256':sha(b'source')}}
        for name in ['manifest.json','recipe.json']:(base/name).write_text(json.dumps(doc,separators=(',',':')))
        members=[{'file':p.name,'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in sorted(base.iterdir())]
        (base/'package-manifest.json').write_text(json.dumps({'schemaVersion':1,'members':members},separators=(',',':')))
        with ZipFile(base/'completed-layers.zip','w') as z:
            for p in sorted(base.iterdir()):
                if p.suffix!='.zip':z.writestr(p.name,p.read_bytes())
        return root,base

    def test_apply_check_preserves_every_pack_byte(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,base=self.fixture(Path(tmp));before={p:p.read_bytes() for p in base.iterdir()}
            tags.apply(root);tags.refresh_legacy_archives(root);tags.apply(root,check=True)
            self.assertTrue(all(p.read_bytes()==raw for p,raw in before.items()))

    def test_corrupt_source_member_or_unlisted_file_fails_before_writes(self):
        for name in ['source.png','Web/wwwroot/assets/completed-layers/module.png','Web/wwwroot/assets/completed-layers/unlisted.json']:
            with tempfile.TemporaryDirectory() as tmp:
                project=Path(tmp);root,base=self.fixture(project);(project/name).write_bytes(b'bad')
                with self.assertRaisesRegex(ValueError,'completed layer'):
                    tags.apply(root)
                self.assertFalse((root/tags.RULES_NAME).exists())

    def test_non_evidenced_metadata_remains_taggable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,base=self.fixture(Path(tmp));p=base/'manifest.json';d=json.loads(p.read_text());d.pop('counts');p.write_text(json.dumps(d))
            self.assertEqual(tags.verified_completed_layer_documents(root),set())
            tags.apply(root);self.assertIn('attachment',json.loads(p.read_text())['assets'][0])

if __name__=='__main__':unittest.main()
