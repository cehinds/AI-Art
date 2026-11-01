"""Whole-object evidence remains distinct from old comparison cutouts."""
import hashlib,json,tempfile,unittest
from pathlib import Path
from zipfile import ZipFile
import asset_attachment_tags as tags

def sha(data):return hashlib.sha256(data).hexdigest()

class WholeObjectEvidenceTests(unittest.TestCase):
    def fixture(self,project):
        root=project/'Web/wwwroot/assets';base=root/'top-down-object-kit';base.mkdir(parents=True)
        (root/'reusable-library.json').write_text(tags.encoded({'libraries':[]}));old=root/'top-down-layer-kit';old.mkdir()
        scenes=[]
        for n in range(36):
            component={'id':'legacy','asset':{'path':'legacy.png','sha256':sha(b'cutout')},'x':0,'y':0}
            scenes.append({'id':str(n),'exact':{'components':[component]},'reusable':{'components':[component]}})
        (old/'manifest.json').write_text(json.dumps({'scenes':scenes}))
        def asset(name,data,size):
            p=base/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);return {'path':name,'sha256':sha(data),'size':size}
        source={'id':'generated','transparentBackground':True,**asset('sources/generated.png',b'source',[8,8])}
        obj={'id':'whole','sourceId':'generated','sourceRect':[1,1,4,4],'padding':2,'asset':asset('objects/whole.png',b'whole',[8,8]),'provenance':{'kind':'ai-generated-whole-object','inferred':True,'originalReferencePixelRecovery':False},'manualQa':{'status':'root-approved-whole-shape-review'},'alphaQa':{'sourceEdgeAlphaMax':0,'thresholdForBoundsOnly':16,'alphaAtMost16Fraction':.5}}
        reference={'id':'legacy','asset':asset('references/scene-0/legacy.png',b'cutout',[1,1]),'position':[0,0]}
        mapping={'id':'placement','sceneId':'0','objectId':'whole','replacementScope':'atomic','replaceComponentIds':['legacy'],'previousComponents':[reference]}
        coverage=[{'id':str(n),'mappings':int(n==0),'wholeObjectIds':['whole'] if n==0 else [],'mappedAtomicOrAssemblyTargets':int(n==0),'partialDemoTargets':0,'previousReusableComponents':1,'unmappedComponents':int(n!=0)} for n in range(36)]
        doc={'schemaVersion':1,'title':'Whole reconstructed top-down objects','sources':[source],'objects':[obj],'mappings':[mapping],'sceneCoverage':coverage,'counts':{'objects':1,'mappingInstances':1,'scenesWithPlacements':1,'unmappedScenes':35}};(base/'manifest.json').write_text(json.dumps(doc))
        files=[p for p in base.rglob('*') if p.is_file()];members=[{'file':p.relative_to(base).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in files];receipt=base/'package-manifest.json';receipt.write_text(json.dumps({'schemaVersion':1,'members':members}))
        with ZipFile(base/'top-down-object-kit.zip','w') as z:
            for p in [*files,receipt]:z.writestr(p.relative_to(base).as_posix(),p.read_bytes())
        return root,base

    def test_apply_check_preserves_whole_object_pack(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,base=self.fixture(Path(tmp));before={p:p.read_bytes() for p in base.rglob('*') if p.is_file()}
            tags.apply(root);tags.refresh_legacy_archives(root);tags.apply(root,check=True)
            self.assertTrue(all(p.read_bytes()==raw for p,raw in before.items()))

    def test_corrupt_source_object_or_unlisted_file_fails_before_writes(self):
        for name in ['sources/generated.png','objects/whole.png','unlisted.json']:
            with tempfile.TemporaryDirectory() as tmp:
                root,base=self.fixture(Path(tmp));(base/name).write_bytes(b'changed')
                with self.assertRaises(ValueError):tags.apply(root)
                self.assertFalse((root/tags.RULES_NAME).exists())

    def test_visible_cutout_cannot_claim_whole_object_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,base=self.fixture(Path(tmp));p=base/'manifest.json';doc=json.loads(p.read_text());doc['objects'][0]['provenance']['kind']='exact-visible-source-extraction';p.write_text(json.dumps(doc))
            with self.assertRaisesRegex(ValueError,'whole-object provenance'):
                tags.apply(root)
            self.assertFalse((root/tags.RULES_NAME).exists())

    def test_non_evidenced_json_remains_taggable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,base=self.fixture(Path(tmp));p=base/'manifest.json';doc=json.loads(p.read_text());doc.pop('title');p.write_text(json.dumps(doc))
            self.assertEqual(tags.verified_top_down_object_documents(root),set());tags.apply(root);self.assertIn('tags',json.loads(p.read_text()))

if __name__=='__main__':unittest.main()
