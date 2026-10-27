"""Multipart downloads remain exact ZIPs and reject altered or unsafe inputs."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from assemble_archive_parts import assemble
from export_pocket_collections import stage_download


class ArchivePartsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.archive = self.root / 'collection.zip'
        with zipfile.ZipFile(self.archive, 'w', compression=zipfile.ZIP_STORED) as z:
            z.writestr('asset.png', bytes(range(256)) * 8)
            z.writestr('asset.json', json.dumps({'tags': ['tile'], 'rotation': 0}))
        self.original = self.archive.read_bytes()

    def split(self):
        descriptor, files = stage_download(self.archive, 512)
        self.manifest = self.root / descriptor['name']
        self.doc = json.loads(self.manifest.read_bytes())
        return descriptor, files

    def test_real_zip_round_trip_and_strict_part_budget(self):
        row, files = self.split()
        self.assertEqual(row['format'], 'multipart-zip')
        self.assertTrue(all(p['bytes'] < 512 for p in row['parts']))
        self.assertNotIn(self.archive.name, files)
        self.assertIn('assemble_archive_parts.py', files)
        self.assertEqual(self.archive.read_bytes(), self.original)
        target = self.root / 'joined.zip'
        result = assemble(self.manifest, target)
        self.assertEqual(result['sha256'], hashlib.sha256(self.original).hexdigest())
        self.assertEqual(target.read_bytes(), self.original)
        with zipfile.ZipFile(target) as z:
            self.assertIsNone(z.testzip())
            self.assertEqual(json.loads(z.read('asset.json'))['tags'], ['tile'])

    def test_small_zip_stays_direct_download(self):
        row, files = stage_download(self.archive, len(self.original) + 1)
        self.assertEqual(row['format'], 'zip')
        self.assertEqual(files, [self.archive.name])
        self.assertEqual(row['parts'], [])

    def test_exact_limit_is_split_below_limit(self):
        row, _ = stage_download(self.archive, len(self.original))
        self.assertEqual(len(row['parts']), 2)

    def test_corruption_preserves_existing_destination(self):
        self.split()
        part = self.root / self.doc['parts'][0]['file']
        data = bytearray(part.read_bytes()); data[0] ^= 1; part.write_bytes(data)
        target = self.root / 'existing.zip'; target.write_bytes(b'keep')
        with self.assertRaisesRegex(ValueError, 'hash/size mismatch'):
            assemble(self.manifest, target)
        self.assertEqual(target.read_bytes(), b'keep')

    def test_reordered_duplicate_or_escaping_parts_rejected(self):
        self.split()
        original = self.manifest.read_bytes()
        for mutation in ('order', 'duplicate', 'escape'):
            doc = json.loads(original)
            if mutation == 'order': doc['parts'].reverse()
            if mutation == 'duplicate': doc['parts'][1]['file'] = doc['parts'][0]['file']
            if mutation == 'escape': doc['parts'][0]['file'] = '../outside'
            self.manifest.write_text(json.dumps(doc))
            with self.assertRaises(ValueError):
                assemble(self.manifest, self.root / 'bad.zip')
            self.assertFalse((self.root / 'bad.zip').exists())

    def test_whole_archive_hash_and_input_overwrite_rejected(self):
        self.split()
        target = self.root / self.doc['parts'][0]['file']
        with self.assertRaisesRegex(ValueError, 'overwrite'):
            assemble(self.manifest, target)
        self.doc['archive']['sha256'] = '0' * 64
        self.manifest.write_text(json.dumps(self.doc))
        with self.assertRaisesRegex(ValueError, 'Assembled archive'):
            assemble(self.manifest, self.root / 'bad.zip')
        self.assertFalse((self.root / 'bad.zip').exists())


if __name__ == '__main__':
    unittest.main()
