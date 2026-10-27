"""Exported crop-coordinate provenance keeps real image hashes and dimensions."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from PIL import Image
from package_pocket_reusable import encoded, plan
from validate_pocket_reusable import digest, validate, retained_snapshot_basis


class GeometryExportTests(unittest.TestCase):
    def fixture(self, root):
        (root / 'reusable').mkdir()
        for name, size in [('source.png', (10, 10)), ('crop.png', (4, 4)),
                           ('atlas.png', (20, 12)), ('extractor.png', (40, 24))]:
            Image.new('RGBA', size, (40, 80, 120, 255)).save(root / name)
        def sha(name):
            return hashlib.sha256((root / name).read_bytes()).hexdigest()
        with Image.open(root / 'crop.png') as image:
            rgba = digest(image)
        asset = {'id': 'crop', 'name': 'Crop', 'tags': ['ui'], 'kind': 'ui', 'view': 'source', 'anchor_px': [2, 2],
                 'image': {'path': 'crop.png', 'width': 4, 'height': 4,
                           'sha256': sha('crop.png'), 'rgba_sha256': rgba},
                 'metadata_path': 'crop.json',
                 'views': {'applicable': False, 'reason': 'Flat UI'},
                 'provenance': {'method': 'fixture-crop', 'source_image': 'source.png', 'source_sha256': sha('source.png'),
                                'source_atlas': 'atlas.png', 'source_atlas_sha256': sha('atlas.png'),
                                'crop_bounds_px': {'alpha_bounds_global': [31, 2, 39, 7]},
                                'source_rect_image': 'atlas.png', 'source_rect_image_sha256': sha('atlas.png'),
                                'source_rect_coordinate_format': 'xyxy', 'source_rect': [3, 4, 7, 8],
                                'normalization_adapter': {'extractor_atlas': 'extractor.png',
                                                          'extractor_sha256': sha('extractor.png')}}}
        self.write(root, asset)
        (root / 'manifest.json').write_bytes(encoded({'assets': []}))
        (root / 'README.md').write_text('Fixture\n')
        return asset

    def write(self, root, asset):
        (root / 'crop.json').write_bytes(encoded(asset))
        (root / 'reusable/index.json').write_bytes(encoded({'assets': [asset], 'maps': [], 'view_sets': []}))

    def test_external_geometry_images_are_measured_and_hash_bound(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.fixture(root)
            contents = plan(root, [], selected_assets=['crop'])
            entries = json.loads(contents['library/reusable/archive-provenance.json'])['external_provenance']
            by_path = {r['path']: r for r in entries}
            for name, size in [('atlas.png', [20, 12]), ('extractor.png', [40, 24])]:
                self.assertEqual(by_path[name]['size_px'], size)
                self.assertEqual(by_path[name]['sha256'], hashlib.sha256((root / name).read_bytes()).hexdigest())
                self.assertNotIn('library/' + name, contents)
            full = plan(root, [], include_raw=True, selected_assets=['crop'])
            for name in ('atlas.png', 'extractor.png'):
                self.assertEqual(full['library/' + name], (root / name).read_bytes())
            extracted = root / 'extracted'
            for relative, raw in contents.items():
                output = extracted / relative
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(raw)
            # The crop's x=39 fits the explicit extractor, not the x=20
            # generation atlas. Neither raw image is present in this archive.
            validate(extracted / 'library', require_views=True)

    def test_wrong_coordinate_image_hash_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); asset = self.fixture(root)
            for field in ('source_rect_image_sha256', 'extractor_sha256'):
                changed = json.loads(json.dumps(asset))
                target = changed['provenance'] if field.startswith('source_rect') else changed['provenance']['normalization_adapter']
                target[field] = '0' * 64
                self.write(root, changed)
                with self.assertRaisesRegex(ValueError, 'atlas hash mismatch'):
                    plan(root, [], selected_assets=['crop'])

    def test_normalization_evidence_recipe_is_included_and_hash_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); asset = self.fixture(root)
            recipe = root / 'scale-proof.json'
            producer = root / 'producer.json'
            producer.write_bytes(encoded({'method': 'isotropic-fit'}))
            recipe.write_bytes(encoded({'records': [{'original_recipe_path': producer.name,
                'original_recipe_sha256': hashlib.sha256(producer.read_bytes()).hexdigest()}]}))
            asset['provenance']['normalization'] = {'scale_evidence': {
                'recipe_path': recipe.name,
                'recipe_sha256': hashlib.sha256(recipe.read_bytes()).hexdigest()}}
            self.write(root, asset)
            contents = plan(root, [], selected_assets=['crop'])
            self.assertEqual(contents['library/scale-proof.json'], recipe.read_bytes())
            self.assertEqual(contents['library/producer.json'], producer.read_bytes())
            producer.write_bytes(encoded({'method': 'changed'}))
            with self.assertRaisesRegex(ValueError, 'Normalization evidence recipe hash mismatch'):
                plan(root, [], selected_assets=['crop'])
            recipe.write_bytes(encoded({'records': ['changed']}))
            with self.assertRaisesRegex(ValueError, 'Normalization evidence recipe hash mismatch'):
                plan(root, [], selected_assets=['crop'])

    def test_retained_snapshot_export_contains_distinct_verified_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); asset = self.fixture(root)
            asset['object_id'] = 'crop'
            (root / 'snapshot.png').write_bytes((root / 'crop.png').read_bytes())
            proof = {'records': [{'object_id': 'crop', 'view': 'source',
                'active_output_path': 'crop.png', 'active_output_sha256': asset['image']['sha256'],
                'active_output_rgba_sha256': asset['image']['rgba_sha256'],
                'snapshot_path': 'snapshot.png', 'snapshot_sha256': asset['image']['sha256'],
                'snapshot_rgba_sha256': asset['image']['rgba_sha256'], 'dimensions_px': [4, 4],
                'claim': 'Exact retained pixels', 'existing_explanation': 'Retained fixture input.'}]}
            (root / 'snapshot-proof.json').write_bytes(encoded(proof))
            normalization = {'retained_snapshot_evidence': {'schema_version': 1,
                'method': 'verified-retained-snapshot-v1', 'manifest_path': 'snapshot-proof.json',
                'manifest_sha256': hashlib.sha256(encoded(proof)).hexdigest(), 'object_id': 'crop', 'view': 'source'}}
            asset['provenance']['normalization'] = normalization
            self.write(root, asset)
            contents = plan(root, [], selected_assets=['crop'])
            extracted = root / 'extracted'
            for relative, raw in contents.items():
                output = extracted / relative
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(raw)
            self.assertIsNotNone(retained_snapshot_basis(extracted / 'library', asset, normalization, 'crop'))


if __name__ == '__main__':
    unittest.main()
