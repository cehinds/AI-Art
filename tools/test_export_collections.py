"""Portable collection validation and publication safeguards."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import zipfile

import export_pocket_collections as exporter
from package_pocket_reusable import encoded


class CollectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.pack = Path(self.temp.name) / 'test-library'
        (self.pack / 'reusable').mkdir(parents=True)
        self.index = {'maps': [{'id': 'room'}], 'assets': [{'id': 'floor'}, {'id': 'crate'}]}
        self.path = self.pack / 'reusable/index.json'
        self.path.write_bytes(encoded(self.index))
        self.document = {'schema_version': 1, 'collections': [
            {'id': 'rooms', 'label': 'Rooms', 'maps': ['room']},
            {'id': 'props', 'label': 'Props', 'assets': ['crate']}]}

    def test_map_and_explicit_asset_coverage(self):
        records = exporter.collection_records(self.document)
        exporter.check_coverage(self.index, records)
        records[1]['maps'] = ['room']
        with self.assertRaisesRegex(ValueError, 'multiple collections'):
            exporter.check_coverage(self.index, records)
        records[1]['maps'] = []
        records[1]['assets'] = ['missing']
        with self.assertRaisesRegex(ValueError, 'Unknown collection assets'):
            exporter.check_coverage(self.index, records)

    def test_unsafe_duplicate_empty_and_malformed_plans(self):
        for record in ({'id': '../outside', 'label': 'X', 'maps': ['room']},
                       {'id': 'empty', 'label': 'X'},
                       {'id': 'bad', 'label': 'X', 'maps': 'room'},
                       {'id': 'bad', 'label': 'X', 'maps': ['room', 'room']}):
            with self.subTest(record=record), self.assertRaises(ValueError):
                exporter.collection_records({'schema_version': 1, 'collections': [record]})
        self.document['collections'].append(self.document['collections'][0])
        with self.assertRaisesRegex(ValueError, 'duplicate collection id'):
            exporter.collection_records(self.document)

    def test_missing_maps_rejected(self):
        with self.assertRaisesRegex(ValueError, 'coverage mismatch'):
            exporter.check_coverage(self.index, [{'id': 'props', 'maps': [], 'assets': ['crate']}])

    def test_draft_plan_includes_unmapped_assets_and_closes_dependencies(self):
        self.index['maps'][0]['file'] = 'room.json'
        (self.pack / 'room.json').write_bytes(encoded({'layers': [{'asset_id': 'floor'}]}))
        self.index['assets'].extend([
            {'id': 'crate.front', 'object_id': 'crate'},
            {'id': 'clean-crate', 'canonical_asset_id': 'crate'}])
        self.index['view_sets'] = [{'object_id': 'crate', 'views': {'front': 'crate.front'}}]
        self.path.write_bytes(encoded(self.index))
        document = exporter.create_collection_plan(self.pack, 1)
        self.assertEqual(document['status'], 'unvalidated-plan')
        self.assertEqual(len(document['collections']), 2)
        props = document['collections'][1]
        self.assertEqual(len(props['assets']), 1)
        self.assertEqual(exporter.asset_dependencies(self.index, props['assets']),
                         {'crate', 'crate.front', 'clean-crate'})
        with self.assertRaisesRegex(ValueError, 'positive'):
            exporter.create_collection_plan(self.pack, 0)

    def test_archive_requires_one_known_root(self):
        for paths in ([], ['library/reusable/index.json', 'pocket-dungeon/reusable/index.json']):
            with self.assertRaises(ValueError):
                exporter.archive_catalog(paths)

    def make_archive(self, folder='library', tamper=False):
        relative = folder + '/reusable/index.json'
        data = encoded({'assets': []})
        manifest = {'files': [{'path': relative, 'size': len(data),
                               'sha256': hashlib.sha256(data).hexdigest()}]}
        output = Path(self.temp.name) / 'fixture.zip'
        with zipfile.ZipFile(output, 'w') as archive:
            archive.writestr(relative, data + (b' ' if tamper else b''))
            archive.writestr('archive-manifest.json', encoded(manifest))
        return output

    def test_generic_archive_integrity_and_root_validation(self):
        output = self.make_archive()
        work = Path(self.temp.name) / 'unpacked'
        with patch.object(exporter, 'validate', return_value={'ok': True}) as validate:
            self.assertEqual(exporter.verify_archive(output, work), {'ok': True})
            validate.assert_called_once_with(work / 'library', require_views=True)

    def test_tampered_archive_rejected_before_validation(self):
        output = self.make_archive(tamper=True)
        with patch.object(exporter, 'validate') as validate:
            with self.assertRaisesRegex(ValueError, 'integrity mismatch'):
                exporter.verify_archive(output, Path(self.temp.name) / 'bad')
            validate.assert_not_called()

    def run_export(self, omit_crate=False, mutate=False):
        result = {'maps_pixel_exact': 1, 'assets_checked': 1}
        def subset(pack, maps, selected_assets):
            assets = [{'id': 'floor'}] if maps else ([] if omit_crate else [{'id': 'crate'}])
            if mutate:
                changed = dict(self.index, title='concurrent edit')
                self.path.write_bytes(encoded(changed))
            return {'library/reusable/index.json': encoded({'assets': assets})}
        with patch.object(exporter, 'validate', return_value=result), \
             patch.object(exporter, 'plan', side_effect=subset), \
             patch.object(exporter, 'verify_archive', return_value=result):
            return exporter.export(self.pack, collections_plan=self.document)

    def test_publishes_all_collections_only_after_coverage(self):
        result = self.run_export()
        self.assertEqual(result['status'], 'exported-and-validated')
        downloads = json.loads(self.path.read_bytes())['downloads']
        self.assertEqual(len(downloads), 2)
        self.assertTrue(all((self.pack / d['path']).is_file() for d in downloads))

    def test_unmapped_assets_do_not_silently_disappear(self):
        before = self.path.read_bytes()
        with self.assertRaisesRegex(ValueError, 'asset coverage mismatch'):
            self.run_export(omit_crate=True)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertFalse(list((self.pack / 'reusable/downloads').glob('*.zip')))

    def test_concurrent_catalog_edit_preserved_without_publishing(self):
        with self.assertRaisesRegex(ValueError, 'Catalog changed'):
            self.run_export(mutate=True)
        self.assertEqual(json.loads(self.path.read_bytes())['title'], 'concurrent edit')
        self.assertFalse(list((self.pack / 'reusable/downloads').glob('*.zip')))


if __name__ == '__main__':
    unittest.main()
