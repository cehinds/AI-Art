"""Reconstructed HUD packs preserve hash-bound bytes, with no folder bypass."""
import hashlib,json,tempfile,unittest
from pathlib import Path
from zipfile import ZipFile
import asset_attachment_tags as tags

def sha(raw):return hashlib.sha256(raw).hexdigest()

class ReusableHudEvidenceTests(unittest.TestCase):
    def fixture(self,project):
        root=project/'Web/wwwroot/assets';base=root/'hud-reusable';base.mkdir(parents=True)
        (root/'reusable-library.json').write_text(tags.encoded({'libraries':[]}))
        (project/'original.json').write_bytes(b'{}');(project/'material.png').write_bytes(b'material')
        (base/'material.png').write_bytes(b'material');(base/'background.png').write_bytes(b'clean')
        doc={'schemaVersion':1,'sourceManifest':'original.json','sourceManifestSha256':sha(b'{}'),
             'materials':{'navy':{'file':'material.png','sha256':sha(b'material'),'originalFile':'material.png','originalSha256':sha(b'material')}},
             'assets':[{'id':'background','file':'background.png','sha256':sha(b'clean'),'provenance':{'kind':'reconstructed-imagegen-material'}}]}
        (base/'manifest.json').write_text(json.dumps(doc,separators=(',',':')))
        members=[{'file':p.name,'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in sorted(base.iterdir())]
        (base/'package-manifest.json').write_text(json.dumps({'schemaVersion':1,'members':members},separators=(',',':')))
        with ZipFile(base/'hud-reusable.zip','w') as z:
            for p in sorted(base.iterdir()):
                if p.suffix!='.zip':z.writestr(p.name,p.read_bytes())
        return root,base

    def test_apply_check_preserves_every_pack_byte(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,base=self.fixture(Path(tmp));before={p:p.read_bytes() for p in base.iterdir()}
            tags.apply(root);tags.refresh_legacy_archives(root);tags.apply(root,check=True)
            self.assertTrue(all(p.read_bytes()==raw for p,raw in before.items()))

    def test_bad_digest_and_unlisted_member_fail_before_writes(self):
        for corrupt in [True,False]:
            with tempfile.TemporaryDirectory() as tmp:
                root,base=self.fixture(Path(tmp));(base/('background.png' if corrupt else 'ordinary.json')).write_bytes(b'bad')
                with self.assertRaisesRegex(ValueError,'reusable HUD'):
                    tags.apply(root)
                self.assertFalse((root/tags.RULES_NAME).exists())

    def test_non_evidenced_metadata_is_enriched(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,base=self.fixture(Path(tmp));p=base/'manifest.json';d=json.loads(p.read_text());d.pop('sourceManifest');p.write_text(json.dumps(d))
            self.assertEqual(tags.verified_reusable_hud_documents(root),set())
            tags.apply(root);self.assertIn('attachment',json.loads(p.read_text())['assets'][0])

if __name__=='__main__':unittest.main()
