"""Reference layers require original inventory, source and archive evidence."""
import hashlib,json,tempfile,unittest
from pathlib import Path
from zipfile import ZipFile
import asset_attachment_tags as tags

def sha(raw):return hashlib.sha256(raw).hexdigest()

class ReferenceLayerEvidenceTests(unittest.TestCase):
    def fixture(self,project):
        root=project/'Web/wwwroot/assets';base=root/'reference-layers';base.mkdir(parents=True)
        (root/'reusable-library.json').write_text(tags.encoded({'libraries':[]}))
        (project/'source.png').write_bytes(b'source');(base/'layer.png').write_bytes(b'layer')
        original={'schemaVersion':1,'source':'source.png','sourceSha256':sha(b'source'),'canvas':[1,1],'representation':'visible source fragments; occluded pixels are absent, not inferred','layers':[{'id':'original','file':'original.png','componentSha256':sha(b'layer'),'provenance':{'kind':'literal-source-pixels','sourceSha256':sha(b'source')}}]};original_path=root/'concept-reconstruction/manifest.json';original_path.parent.mkdir();original_path.write_text(json.dumps(original))
        doc={'schemaVersion':1,'coordinateSystem':'native reference pixels; top-left origin; no scale, rotation or snapping',
             'source':'source.png','sourceSha256':sha(b'source'),'sourceManifestSha256':sha(original_path.read_bytes()),
             'groups':[{'id':'ground'}],'layers':[{'id':'layer','file':'layer.png','sha256':sha(b'layer'),'kind':'original-visible','sourceRef':{'file':'source.png','sha256':sha(b'source')}}],
             'originalFragments':[{'id':'original','file':'original.png','offset':None,'size':None,'visiblePixels':0,'sha256':sha(b'layer')}],
             'validation':{'changedRgbaPixels':0,'maxChannelDifference':0,'sourceFragmentCount':1,'sourceAnnotationCount':1,'exportedLayerCount':1}}
        (base/'manifest.json').write_text(json.dumps(doc,separators=(',',':')))
        members=[{'file':p.name,'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in sorted(base.iterdir())]
        (base/'package-manifest.json').write_text(json.dumps({'schemaVersion':1,'members':members},separators=(',',':')))
        with ZipFile(base/'reference-layers.zip','w') as z:
            for p in sorted(base.iterdir()):
                if p.suffix!='.zip':z.writestr(p.name,p.read_bytes())
        return root,base

    def test_apply_check_preserves_every_pack_byte(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,base=self.fixture(Path(tmp));before={p:p.read_bytes() for p in base.iterdir()}
            tags.apply(root);tags.refresh_legacy_archives(root);tags.apply(root,check=True)
            self.assertTrue(all(p.read_bytes()==raw for p,raw in before.items()))

    def test_corrupt_source_member_or_unlisted_file_fails_before_writes(self):
        for name in ['source.png','Web/wwwroot/assets/reference-layers/layer.png','Web/wwwroot/assets/reference-layers/unlisted.json']:
            with tempfile.TemporaryDirectory() as tmp:
                project=Path(tmp);root,base=self.fixture(project);(project/name).write_bytes(b'bad')
                with self.assertRaisesRegex(ValueError,'reference layer'):
                    tags.apply(root)
                self.assertFalse((root/tags.RULES_NAME).exists())

    def test_non_evidenced_metadata_remains_taggable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,base=self.fixture(Path(tmp));p=base/'manifest.json';d=json.loads(p.read_text());d.pop('coordinateSystem');p.write_text(json.dumps(d))
            self.assertEqual(tags.verified_reference_layer_documents(root),set())
            tags.apply(root);self.assertIn('attachment',json.loads(p.read_text())['layers'][0])

if __name__=='__main__':unittest.main()
