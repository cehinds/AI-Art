"""Cardinal wall evidence requires bound primitives, masks and package bytes."""
import hashlib,json,tempfile,unittest
from pathlib import Path
from zipfile import ZipFile
import asset_attachment_tags as tags

def sha(raw):return hashlib.sha256(raw).hexdigest()

class WallComponentEvidenceTests(unittest.TestCase):
    def fixture(self,project):
        root=project/'Web/wwwroot/assets';base=root/'wall-components';base.mkdir(parents=True)
        (root/'reusable-library.json').write_text(tags.encoded({'libraries':[]}))
        source=project/'Web/source.png';source.write_bytes(b'source');(base/'module.png').write_bytes(b'module')
        assets=[{'id':'wall-'+str(mask),'mask':mask,'kind':'network-tile','file':'module.png','sha256':sha(b'module'),
                 'provenance':{'kind':'inferred-assembled-variant','primitives':['cap']}} for mask in range(16)]
        doc={'schemaVersion':1,'grid':{'tileSize':64,'canvas':[64,96]},'edgeContract':'cardinal match',
             'assets':assets,'construction':[{'id':'cap','file':'module.png','sha256':sha(b'module'),'provenance':{'file':'Web/source.png','sha256':sha(b'source')}}],
             'samples':{'room':'room.json'}}
        (base/'room.json').write_text(json.dumps({'schemaVersion':1,'grid':64,'instances':[{'assetId':'wall-0'}]}))
        (base/'manifest.json').write_text(json.dumps(doc,separators=(',',':')))
        members=[{'file':p.name,'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in sorted(base.iterdir())]
        (base/'package-manifest.json').write_text(json.dumps({'schemaVersion':1,'members':members},separators=(',',':')))
        with ZipFile(base/'wall-components.zip','w') as z:
            for p in sorted(base.iterdir()):
                if p.suffix!='.zip':z.writestr(p.name,p.read_bytes())
        return root,base

    def test_apply_check_preserves_every_pack_byte(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,base=self.fixture(Path(tmp));before={p:p.read_bytes() for p in base.iterdir()}
            tags.apply(root);tags.refresh_legacy_archives(root);tags.apply(root,check=True)
            self.assertTrue(all(p.read_bytes()==raw for p,raw in before.items()))

    def test_corrupt_source_member_or_unlisted_file_fails_before_writes(self):
        for name in ['Web/source.png','Web/wwwroot/assets/wall-components/module.png','Web/wwwroot/assets/wall-components/unlisted.json']:
            with tempfile.TemporaryDirectory() as tmp:
                project=Path(tmp);root,base=self.fixture(project);(project/name).write_bytes(b'bad')
                with self.assertRaisesRegex(ValueError,'wall component'):
                    tags.apply(root)
                self.assertFalse((root/tags.RULES_NAME).exists())

    def test_non_evidenced_metadata_remains_taggable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,base=self.fixture(Path(tmp));p=base/'manifest.json';d=json.loads(p.read_text());d.pop('edgeContract');p.write_text(json.dumps(d))
            self.assertEqual(tags.verified_wall_component_documents(root),set())
            tags.apply(root);self.assertIn('attachment',json.loads(p.read_text())['assets'][0])

if __name__=='__main__':unittest.main()
