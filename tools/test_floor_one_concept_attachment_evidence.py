"""Floor 1 concept bytes require full source, coverage and portable closure."""
import hashlib,json,tempfile,unittest
from pathlib import Path
from zipfile import ZipFile
import asset_attachment_tags as tags

def sha(raw):return hashlib.sha256(raw).hexdigest()

class FloorConceptEvidenceTests(unittest.TestCase):
    def fixture(self,project):
        root=project/'Web/wwwroot/assets';base=root/'floor-one-concepts';base.mkdir(parents=True)
        (root/'reusable-library.json').write_text(tags.encoded({'libraries':[]}))
        sources=[];panels=[];coverage=[]
        for batch in range(6):
            path=f'source-{batch}.png';(base/path).write_bytes(b'source')
            sources.append({'id':str(batch),'path':path,'sha256':sha(b'source'),'canvasSize':[6,1],'provenance':'inferred concept'})
            for column in range(6):
                number=batch*6+column;ident=f'panel-{number}';path=ident+'.png';raw=str(number).encode();(base/path).write_bytes(raw)
                entry={'id':ident,'order':number,'status':'generic','layout':'inferred'};coverage.append(entry)
                panels.append({**entry,'sourceId':str(batch),'sourceRect':[column,0,1,1],'rectFormat':'xywh','path':path,'nativeSize':[1,1],'sha256':sha(raw),'pixelSha256':f'{number:064x}','boundaryReview':'reviewed'})
        scope={'book':1,'floor':1};doc={'schemaVersion':1,'title':'Floor 1 concept-art studies','scope':scope,'sources':sources,'panels':panels}
        (base/'coverage.json').write_text(json.dumps({'schemaVersion':1,'scope':scope,'panels':coverage}))
        (base/'manifest.json').write_text(json.dumps(doc,separators=(',',':')))
        members=[{'file':p.name,'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in sorted(base.iterdir())]
        (base/'package-manifest.json').write_text(json.dumps({'schemaVersion':1,'members':members},separators=(',',':')))
        with ZipFile(base/'floor-one-concepts.zip','w') as z:
            for p in sorted(base.iterdir()):
                if p.suffix!='.zip':z.writestr(p.name,p.read_bytes())
        return root,base

    def test_apply_check_preserves_every_pack_byte(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,base=self.fixture(Path(tmp));before={p:p.read_bytes() for p in base.iterdir()}
            tags.apply(root);tags.refresh_legacy_archives(root);tags.apply(root,check=True)
            self.assertTrue(all(p.read_bytes()==raw for p,raw in before.items()))

    def test_corrupt_source_panel_or_unlisted_file_fails_before_writes(self):
        for name in ['source-0.png','panel-0.png','unlisted.json']:
            with tempfile.TemporaryDirectory() as tmp:
                root,base=self.fixture(Path(tmp));(base/name).write_bytes(b'bad')
                with self.assertRaisesRegex(ValueError,'Floor 1'):
                    tags.apply(root)
                self.assertFalse((root/tags.RULES_NAME).exists())

    def test_non_evidenced_metadata_remains_taggable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,base=self.fixture(Path(tmp));p=base/'manifest.json';d=json.loads(p.read_text());d.pop('title');p.write_text(json.dumps(d))
            self.assertEqual(tags.verified_floor_one_concept_documents(root),set())
            tags.apply(root);self.assertIn('tags',json.loads(p.read_text()))

if __name__=='__main__':unittest.main()
