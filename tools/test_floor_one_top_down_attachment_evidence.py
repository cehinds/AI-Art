"""Overhead revision remains separately bound to human review attestations."""
import hashlib,json,tempfile,unittest
from pathlib import Path
from zipfile import ZipFile
import asset_attachment_tags as tags
import test_floor_one_concept_attachment_evidence as fixtures

class OverheadConceptEvidenceTests(unittest.TestCase):
    def seal(self,base):
        receipt=base/'package-manifest.json';package=base/'floor-one-concepts-top-down.zip'
        files=[p for p in sorted(base.iterdir()) if p not in [receipt,package]]
        members=[{'file':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]
        receipt.write_text(json.dumps({'schemaVersion':1,'members':members}))
        with ZipFile(package,'w') as z:
            for p in [*files,receipt]:z.writestr(p.name,p.read_bytes())

    def fixture(self,project):
        root,old=fixtures.FloorConceptEvidenceTests().fixture(project)
        base=old.with_name('floor-one-concepts-top-down');old.rename(base);(base/'floor-one-concepts.zip').unlink()
        p=base/'manifest.json';doc=json.loads(p.read_text());doc['title']='Floor 1 overhead concept-art revision';sheets=[]
        for source in doc['sources']:
            review={'projection':'direct-overhead','reviewer':'root','assessment':'Reviewed visible overhead composition'}
            source['cameraReview']=review;sheets.append({'id':source['id'],'reviewed':True,'rootApproved':True,'cameraReview':review})
        p.write_text(json.dumps(doc));(base/'spec.json').write_text(json.dumps({'sheets':sheets}));self.seal(base)
        return root,base

    def test_apply_check_preserves_overhead_pack(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,base=self.fixture(Path(tmp));before={p:p.read_bytes() for p in base.iterdir()}
            tags.apply(root);tags.refresh_legacy_archives(root);tags.apply(root,check=True)
            self.assertTrue(all(p.read_bytes()==raw for p,raw in before.items()))

    def test_missing_human_approval_fails_before_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,base=self.fixture(Path(tmp));p=base/'spec.json';doc=json.loads(p.read_text());doc['sheets'][0]['rootApproved']=False;p.write_text(json.dumps(doc));self.seal(base)
            with self.assertRaisesRegex(ValueError,'recorded human overhead approval'):
                tags.apply(root)
            self.assertFalse((root/tags.RULES_NAME).exists())

    def test_non_evidenced_json_remains_taggable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,base=self.fixture(Path(tmp));p=base/'manifest.json';doc=json.loads(p.read_text());doc.pop('title');p.write_text(json.dumps(doc))
            self.assertEqual(tags.verified_floor_one_top_down_documents(root),set())
            tags.apply(root);self.assertIn('tags',json.loads(p.read_text()))

if __name__=='__main__':unittest.main()
