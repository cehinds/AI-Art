"""Map grid evidence is immutable only with full source and archive binding."""
import hashlib,json,tempfile,unittest
from pathlib import Path
from zipfile import ZipFile
import asset_attachment_tags as tags

def sha(raw):return hashlib.sha256(raw).hexdigest()

class MapGridEvidenceTests(unittest.TestCase):
    def fixture(self,project):
        root=project/'Web/wwwroot/assets';base=root/'map-grid-pass';base.mkdir(parents=True)
        (root/'reusable-library.json').write_text(tags.encoded({'libraries':[]}))
        (project/'source.png').write_bytes(b'source');(project/'original.json').write_bytes(b'{}')
        (base/'module.png').write_bytes(b'module')
        doc={'version':1,'grid':{'columns':6,'rows':4,'cellSize':256,'subgrid':2,'moduleSize':128},
             'sources':[{'id':'generated','path':'source.png','sha256':sha(b'source'),'provenance':'generated reconstruction'}],
             'components':[{'id':'module','path':'module.png','sha256':sha(b'module'),'sourceId':'generated','provenance':'generated-reconstruction'}],
             'environmentReconstruction':{'reusableComponent':False,'provenance':'Visible source plus inferred hidden surfaces',
                 'sourceManifest':'original.json','sourceManifestSha256':sha(b'{}'),
                 'originalLayers':[{'file':'source.png','sha256':sha(b'source'),'provenance':'original-visible'}]}}
        (base/'manifest.json').write_text(json.dumps(doc,separators=(',',':')))
        members=[{'file':p.name,'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in sorted(base.iterdir())]
        (base/'package-manifest.json').write_text(json.dumps({'schemaVersion':1,'members':members},separators=(',',':')))
        with ZipFile(base/'map-grid-pass.zip','w') as z:
            for p in sorted(base.iterdir()):
                if p.suffix!='.zip':z.writestr(p.name,p.read_bytes())
        return root,base

    def test_apply_check_preserves_every_pack_byte(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,base=self.fixture(Path(tmp));before={p:p.read_bytes() for p in base.iterdir()}
            tags.apply(root);tags.refresh_legacy_archives(root);tags.apply(root,check=True)
            self.assertTrue(all(p.read_bytes()==raw for p,raw in before.items()))

    def test_corrupt_source_member_or_incomplete_inventory_fails_before_writes(self):
        for name in ['source.png','Web/wwwroot/assets/map-grid-pass/module.png','Web/wwwroot/assets/map-grid-pass/unlisted.json']:
            with tempfile.TemporaryDirectory() as tmp:
                project=Path(tmp);root,base=self.fixture(project);(project/name).write_bytes(b'bad')
                with self.assertRaisesRegex(ValueError,'map grid'):
                    tags.apply(root)
                self.assertFalse((root/tags.RULES_NAME).exists())

    def test_incomplete_metadata_remains_taggable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,base=self.fixture(Path(tmp));p=base/'manifest.json';d=json.loads(p.read_text());d.pop('grid');p.write_text(json.dumps(d))
            self.assertEqual(tags.verified_map_grid_documents(root),set())
            tags.apply(root);self.assertIn('tags',json.loads(p.read_text()))

if __name__=='__main__':unittest.main()
