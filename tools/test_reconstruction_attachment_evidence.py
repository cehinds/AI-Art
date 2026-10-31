"""Byte-bound products remain immutable; ordinary JSON still gets tags."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile
import asset_attachment_tags as tags

class ReconstructionEvidenceTests(unittest.TestCase):
    def fixture(self, root):
        (root / 'reusable-library.json').write_text(tags.encoded({'libraries': []}))
        base = root / 'concept-reconstruction'
        base.mkdir()
        docs = {'manifest.json': {}, 'derived/catalog.json': {'schemaVersion': 1, 'assets': [{'id': 'tile'}], 'roles': {}},
                'derived/validation.json': {}, 'procedural/recipe.json': {'schemaVersion': 2, '$schema': 'recipe.schema.json', 'entities': []},
                'procedural/room-9.json': {'seed': 9}}
        outputs = {}
        for name in ['combat-concept-components.zip', 'concept-generator.zip', 'combat-concept.ora', 'reconstructed.png', 'diff.png', 'coverage-map.png', *docs]:
            p = base / name
            p.parent.mkdir(exist_ok=True, parents=True)
            p.write_bytes(json.dumps(docs[name], separators=(',', ':')).encode() if name in docs else b'fixture')
            outputs[name] = hashlib.sha256(p.read_bytes()).hexdigest()
        receipt = {'schemaVersion': 1, 'status': 'verified', 'sourceReplay': {'unassignedPixels': 0, 'changedPixels': 0}, 'outputs': outputs}
        (base / 'build-report.json').write_text(tags.encoded(receipt))
        return base

    def test_receipt_and_bound_json_survive_apply_and_check(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); base = self.fixture(root)
            ordinary = base / 'ordinary.json'
            ordinary.write_text('{"id":"barrel","file":"barrel.png"}')
            before = {p: p.read_bytes() for p in tags.verified_reconstruction_documents(root)}
            tags.apply(root)
            self.assertTrue(all(p.read_bytes() == raw for p, raw in before.items()))
            self.assertIn('attachment', json.loads(ordinary.read_text()))
            self.assertEqual(tags.apply(root, check=True)['changed'], 0)

    def test_corrupt_bound_document_fails_before_writes(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); base = self.fixture(root)
            (base / 'derived/catalog.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'Invalid reconstruction build evidence'):
                tags.apply(root)
            self.assertFalse((root / tags.RULES_NAME).exists())

    def test_incomplete_receipt_is_not_an_exemption(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); base = self.fixture(root)
            (base / 'build-report.json').write_text('{"schemaVersion":1,"outputs":{}}')
            self.assertEqual(tags.verified_reconstruction_documents(root), set())
            tags.apply(root)
            self.assertIn('tags', json.loads((base / 'derived/catalog.json').read_text()))

    def test_portable_package_preserved_and_corrupt_member_rejected(self):
        for corrupt in [False, True]:
            with tempfile.TemporaryDirectory() as d:
                root = Path(d); package = root / 'portable.zip'
                # External matching name intentionally differs; it must never
                # replace the package's declared immutable member.
                (root / 'recipe.json').write_bytes(b'external')
                manifest = {'schemaVersion': 1, 'requiredEntries': ['recipe.json'],
                            'sha256': {'recipe.json': hashlib.sha256(b'{}').hexdigest()}}
                with ZipFile(package, 'w') as z:
                    z.writestr('recipe.json', b'corrupt' if corrupt else b'{}')
                    z.writestr('package-manifest.json', json.dumps(manifest))
                before = package.read_bytes()
                if corrupt:
                    with self.assertRaisesRegex(ValueError, 'Invalid portable package member'):
                        tags.refresh_legacy_archives(root)
                else:
                    tags.refresh_legacy_archives(root)
                    self.assertEqual(package.read_bytes(), before)

if __name__ == '__main__':
    unittest.main()
