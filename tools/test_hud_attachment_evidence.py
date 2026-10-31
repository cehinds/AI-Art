"""HUD evidence stays immutable; incomplete metadata is still enriched."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile
import asset_attachment_tags as tags

class HudEvidenceTests(unittest.TestCase):
    def fixture(self, project):
        root=project/'Web/wwwroot/assets';base=root/'hud-components';base.mkdir(parents=True)
        (root/'reusable-library.json').write_text(tags.encoded({'libraries': []}))
        (project/'source.png').write_bytes(b'source')
        digest=hashlib.sha256(b'fragment').hexdigest()
        provenance={'kind':'literal-source-pixels','sourceSha256':hashlib.sha256(b'source').hexdigest()}
        layer={'id':'frame','file':'frame.png','sha256':digest,'componentSha256':digest,'provenance':provenance}
        original=json.dumps({'layers':[layer]}).encode();(project/'original.json').write_bytes(original)
        doc={'schemaVersion':1,'representation':'Visible source fragments; hidden pixels are absent.',
             'source':'source.png','sourceSha256':hashlib.sha256(b'source').hexdigest(),
             'fragmentManifest':'original.json','fragmentManifestSha256':hashlib.sha256(original).hexdigest(),
             'layers':[layer],'groups':[{'id':'widget','file':'widget.png'}],
             'verification':{'changedPixels':0,'maxChannelError':0,'transparentRgbNormalized':True}}
        (base/'frame.png').write_bytes(b'fragment');(base/'widget.png').write_bytes(b'widget')
        (base/'manifest.json').write_text(json.dumps(doc,separators=(',',':')))
        with ZipFile(base/'hud-components.zip','w') as z:
            for p in sorted(base.iterdir()):
                if p.suffix!='.zip':z.writestr(p.name,p.read_bytes())
        return root,base

    def test_apply_check_preserve_every_hud_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,base=self.fixture(Path(tmp));before={p:p.read_bytes() for p in base.iterdir()}
            tags.apply(root);tags.refresh_legacy_archives(root)
            self.assertEqual(tags.apply(root,check=True)['changed'],0)
            self.assertTrue(all(p.read_bytes()==raw for p,raw in before.items()))

    def test_corrupt_fragment_or_archive_fails_before_writes(self):
        for name in ['frame.png','widget.png']:
            with tempfile.TemporaryDirectory() as tmp:
                root,base=self.fixture(Path(tmp));(base/name).write_bytes(b'corrupt')
                with self.assertRaisesRegex(ValueError,'Invalid HUD'):
                    tags.apply(root)
                self.assertFalse((root/tags.RULES_NAME).exists())

    def test_incomplete_manifest_still_enriched(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,base=self.fixture(Path(tmp));p=base/'manifest.json';d=json.loads(p.read_text());d.pop('fragmentManifestSha256');p.write_text(json.dumps(d))
            self.assertEqual(tags.verified_hud_documents(root),set())
            tags.apply(root)
            self.assertIn('attachment',json.loads(p.read_text())['layers'][0])

if __name__=='__main__':unittest.main()
