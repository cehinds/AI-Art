"""Layer review kit evidence binds all scenes and single/multipart archive bytes."""
import hashlib,json,tempfile,unittest
from pathlib import Path
from zipfile import ZipFile
import asset_attachment_tags as tags

def sha(data):return hashlib.sha256(data).hexdigest()

class LayerReviewEvidenceTests(unittest.TestCase):
    def fixture(self,project,multipart=False):
        root=project/'Web/wwwroot/assets';base=root/'top-down-layer-kit';base.mkdir(parents=True)
        (root/'reusable-library.json').write_text(tags.encoded({'libraries':[]}))
        original=root/'floor-one-concepts-top-down';original.mkdir();catalog=[];scenes=[]
        def asset(name,data,size):
            p=base/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
            return {'path':name,'sha256':sha(data),'size':size}
        for n in range(36):
            ident='scene-'+str(n);data=ident.encode();source=original/(ident+'.png');source.write_bytes(data);catalog.append({'id':ident,'order':n,'path':source.name,'sha256':sha(data),'nativeSize':[2,2]})
            component={'id':'part','category':'object','x':0,'y':0,'bounds':[0,0,1,1],'visiblePixelCount':1,'provenance':{'kind':'visible-source'},'asset':asset(ident+'/part.png',b'part',[1,1]),'mask':asset(ident+'/mask.png',b'mask',[2,2])}
            exact={'base':asset(ident+'/base.png',b'base',[2,2]),'baseProvenance':{'kind':'inferred'},'claim':'Visible source replay only','components':[component],'metrics':{'differentPixels':0,'totalPixels':4}}
            scene={'schemaVersion':1,'id':ident,'order':n,'size':[2,2],'source':{**asset(ident+'/original.png',data,[2,2]),'originalSha256':sha(data)},'grid':{'major':14,'sub':3,'xBoundaries':[round(i*2/14) for i in range(15)],'yBoundaries':[round(i*2/14) for i in range(15)]},'exact':exact,'reusable':{**exact,'claim':'Inferred review interpretation'}}
            p=base/ident/'scene.json';p.write_text(json.dumps(scene));scene['scenePath']=ident+'/scene.json';scenes.append(scene)
        source_doc={'schemaVersion':1,'source':'scene-0.png','sourceSha256':catalog[0]['sha256'],'canvas':[2,2],'representation':'visible source fragments; occluded pixels are absent, not inferred','layers':[{'id':'literal','file':'scene-0.png','componentSha256':catalog[0]['sha256'],'provenance':{'kind':'literal-source-pixels','sourceSha256':catalog[0]['sha256']}}],'panels':catalog};(original/'manifest.json').write_text(json.dumps(source_doc))
        doc={'schemaVersion':1,'title':'Top-down layer kit','scenes':scenes,'coverage':[{'id':s['id'],'built':True} for s in scenes]};(base/'manifest.json').write_text(json.dumps(doc))
        files=[p for p in base.rglob('*') if p.is_file()];members=[{'file':p.relative_to(base).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in files];receipt=base/'package-manifest.json';receipt.write_text(json.dumps({'schemaVersion':1,'members':members}));archive=base/'top-down-layer-kit.zip'
        with ZipFile(archive,'w') as z:
            for p in [*files,receipt]:z.writestr(p.relative_to(base).as_posix(),p.read_bytes())
        if multipart:
            data=archive.read_bytes();archive.unlink();parts=[]
            for number,block in enumerate([data[:len(data)//2],data[len(data)//2:]],1):
                name=f'top-down-layer-kit.zip.part-{number:03d}';(base/name).write_bytes(block);parts.append({'number':number,'file':name,'bytes':len(block),'sha256':sha(block)})
            helper=base/'assemble_archive_parts.py';helper.write_bytes(b'fixture helper')
            proof={'schema_version':1,'kind':'multipart-zip','archive':{'file':'top-down-layer-kit.zip','bytes':len(data),'sha256':sha(data)},'payloadManifestSha256':sha(receipt.read_bytes()),'parts':parts,'assemblyTool':{'file':helper.name,'bytes':helper.stat().st_size,'sha256':sha(helper.read_bytes())}};(base/'top-down-layer-kit.zip.parts.json').write_text(json.dumps(proof))
        return root,base

    def test_single_and_multipart_evidence_preserves_every_payload_byte(self):
        for multipart in [False,True]:
            with tempfile.TemporaryDirectory() as tmp:
                root,base=self.fixture(Path(tmp),multipart);before={p:p.read_bytes() for p in root.rglob('*') if p.is_file() and p.name!='reusable-library.json'}
                tags.apply(root);tags.refresh_legacy_archives(root);tags.apply(root,check=True)
                self.assertTrue(all(p.read_bytes()==raw for p,raw in before.items()))

    def test_corrupt_source_payload_or_extra_file_fails_before_writes(self):
        for name in ['floor-one-concepts-top-down/scene-0.png','top-down-layer-kit/scene-0/part.png','top-down-layer-kit/unlisted.json']:
            with tempfile.TemporaryDirectory() as tmp:
                root,base=self.fixture(Path(tmp));(root/name).write_bytes(b'changed')
                with self.assertRaises(ValueError):tags.apply(root)
                self.assertFalse((root/tags.RULES_NAME).exists())

    def test_corrupt_archive_part_fails_before_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,base=self.fixture(Path(tmp),True);(base/'top-down-layer-kit.zip.part-001').write_bytes(b'changed')
            with self.assertRaises(ValueError):tags.apply(root)
            self.assertFalse((root/tags.RULES_NAME).exists())

    def test_non_evidenced_json_remains_taggable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,base=self.fixture(Path(tmp));p=base/'manifest.json';doc=json.loads(p.read_text());doc.pop('title');p.write_text(json.dumps(doc))
            self.assertEqual(tags.verified_top_down_layer_documents(root),set());tags.apply(root);self.assertIn('tags',json.loads(p.read_text()))

if __name__=='__main__':unittest.main()
