"""Fourteen-by-fourteen overlays retain original bindings and archive bytes."""
import hashlib,json,tempfile,unittest
from pathlib import Path
from zipfile import ZipFile
import asset_attachment_tags as tags

def sha(raw):return hashlib.sha256(raw).hexdigest()

class ConceptGridEvidenceTests(unittest.TestCase):
    def fixture(self,project):
        root=project/'Web/wwwroot/assets';base=root/'floor-one-concept-grids';base.mkdir(parents=True)
        (root/'reusable-library.json').write_text(tags.encoded({'libraries':[]}));(base/'font.ttf').write_bytes(b'font')
        sets=[];panels=[]
        for ident,pack in [('original','floor-one-concepts'),('top-down','floor-one-concepts-top-down')]:
            source_dir=root/pack;source_dir.mkdir();(source_dir/'source.png').write_bytes(b'source');catalog=[]
            for n in range(36):
                raw=(ident+str(n)).encode();path=f'panel-{n}.png';(source_dir/path).write_bytes(raw)
                source={'id':str(n),'path':path,'sha256':sha(raw),'nativeSize':[14,14],'order':n,'batch':n//6+1};catalog.append(source)
                target=f'{ident}-{n}.png';(base/target).write_bytes(b'overlay'+raw)
                geometry={'columns':list('ABCDEFGHIJKLMN'),'rows':list(range(1,15)),'xBoundaries':list(range(15)),'yBoundaries':list(range(15)),'contentRect':[2,2,14,14]}
                panels.append({'id':str(n),'set':ident,'order':n,'batch':n//6+1,'sourcePath':f'Web/wwwroot/assets/{pack}/{path}','sourceSha256':sha(raw),'sourceSize':[14,14],'path':target,'sha256':sha(b'overlay'+raw),'size':[18,18],'grid':geometry})
            source={'schemaVersion':1,'source':'source.png','sourceSha256':sha(b'source'),'canvas':[14,14],'representation':'visible source fragments; occluded pixels are absent, not inferred','layers':[{'id':'literal','file':'panel-0.png','componentSha256':catalog[0]['sha256'],'provenance':{'kind':'literal-source-pixels','sourceSha256':sha(b'source')}}],'panels':catalog}
            raw=json.dumps(source).encode();(source_dir/'manifest.json').write_bytes(raw);copy=ident+'-manifest.json';(base/copy).write_bytes(raw)
            sets.append({'id':ident,'sourcePack':pack,'manifestPath':copy,'manifestSha256':sha(raw)})
        doc={'schemaVersion':1,'title':'Floor1 concept-art coordinate grids','style':{'divisions':14,'styleApprovedByRoot':True,'margin':2},'font':{'path':'font.ttf','sha256':sha(b'font')},'sourceSets':sets,'panels':panels}
        (base/'manifest.json').write_text(json.dumps(doc));members=[{'file':p.name,'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in sorted(base.iterdir())]
        (base/'package-manifest.json').write_text(json.dumps({'schemaVersion':1,'members':members}))
        with ZipFile(base/'floor-one-concept-grids.zip','w') as z:
            for p in sorted(base.iterdir()):
                if p.suffix!='.zip':z.writestr(p.name,p.read_bytes())
        return root,base

    def test_apply_check_preserves_overlays_and_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,base=self.fixture(Path(tmp));before={p:p.read_bytes() for p in root.rglob('*') if p.is_file() and p.name!='reusable-library.json'}
            tags.apply(root);tags.refresh_legacy_archives(root);tags.apply(root,check=True)
            self.assertTrue(all(p.read_bytes()==raw for p,raw in before.items()))

    def test_corrupt_source_output_or_unlisted_file_fails_before_writes(self):
        for relative in ['floor-one-concepts/panel-0.png','floor-one-concept-grids/original-0.png','floor-one-concept-grids/unlisted.json']:
            with tempfile.TemporaryDirectory() as tmp:
                root,base=self.fixture(Path(tmp));(root/relative).write_bytes(b'bad')
                with self.assertRaisesRegex(ValueError,'concept grid'):
                    tags.apply(root)
                self.assertFalse((root/tags.RULES_NAME).exists())

    def test_eight_division_geometry_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,base=self.fixture(Path(tmp));p=base/'manifest.json';doc=json.loads(p.read_text());doc['panels'][0]['grid']['columns']=list('ABCDEFGH');p.write_text(json.dumps(doc))
            with self.assertRaisesRegex(ValueError,'fourteen-by-fourteen'):
                tags.apply(root)
            self.assertFalse((root/tags.RULES_NAME).exists())

    def test_non_evidenced_json_remains_taggable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,base=self.fixture(Path(tmp));p=base/'manifest.json';doc=json.loads(p.read_text());doc.pop('title');p.write_text(json.dumps(doc))
            self.assertEqual(tags.verified_floor_one_grid_documents(root),set())
            tags.apply(root);self.assertIn('tags',json.loads(p.read_text()))

if __name__=='__main__':unittest.main()
