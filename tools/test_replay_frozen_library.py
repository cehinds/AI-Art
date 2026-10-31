"""Portable replay restores exact metadata without disguising it as raw-derived."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from PIL import Image
import replay_frozen_library as replay


class FrozenReplayTests(unittest.TestCase):
    def fixture(self, root):
        pack=root/'assets/style-packs/dungeon-after-dark';(pack/'raw').mkdir(parents=True);(pack/'views').mkdir();(pack/'reusable').mkdir()
        Image.new('RGBA',(3,4),(70,80,90,255)).save(pack/'raw/input.png');shutil.copyfile(pack/'raw/input.png',pack/'views/object.png')
        asset={'id':'object','image':{'path':'views/object.png','sha256':replay.file_sha(pack/'views/object.png'),'rgba_sha256':replay.rgba_sha(pack/'views/object.png')},'metadata_path':'views/object.json','provenance':{'source_atlas':'raw/input.png'}}
        (pack/'views/object.json').write_text(json.dumps(asset)+'\n');(pack/'reusable/index.json').write_text(json.dumps({'assets':[asset]})+'\n')
        (pack/'rebuild.py').write_text("from pathlib import Path\nimport shutil\np=Path(__file__).resolve().parent\nshutil.copyfile(p/'raw/input.png',p/'views/object.png')\n(p/'views/object.json').write_text('{}')\n")
        cfg={'canonical_root':pack,'pack_relative':'style-packs/dungeon-after-dark','index_paths':['reusable/index.json'],'builder':'rebuild.py','builder_argv':[],'expected_counts':{'unique_indexed_pngs':1},'builder_report_paths':[]}
        return pack,cfg

    def test_frozen_metadata_zip_relocates_and_replays_exact_png_and_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);pack,cfg=self.fixture(root);receipts=root/'receipts'
            expected=(pack/'views/object.json').read_bytes()
            with patch.object(replay,'ROOT',receipts):
                replay.freeze('style-dark',cfg)
                receipt=json.loads(replay.receipt_path('style-dark').read_text());self.assertNotIn('canonical_root',receipt);self.assertEqual(receipt['pack_root'],cfg['pack_relative']);self.assertTrue((receipts/'style-dark/frozen-inputs/metadata.zip').is_file())
                relocated=root/'relocated/assets/style-packs/dungeon-after-dark';shutil.copytree(pack,relocated);cfg={**cfg,'canonical_root':relocated}
                replay.replay('style-dark',cfg,root/'isolated')
                result=json.loads((root/'isolated/reports/result.json').read_text());self.assertTrue(result['active_pngs_exact']);self.assertTrue(result['metadata_exact']);self.assertIn('views/object.json',result['builder_metadata_byte_changes']);self.assertEqual((root/'isolated/dungeon-after-dark/views/object.json').read_bytes(),expected)

    def test_active_png_cannot_be_declared_as_source(self):
        metadata={'views/object.json':json.dumps({'provenance':{'source_atlas':'views/object.png'}}).encode()}
        with self.assertRaisesRegex(ValueError,'depends on active outputs'):replay.discover_png_dependencies(Path('/unused'),metadata,{'views/object.png'},[],'style-ink')

    def test_tampered_metadata_archive_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);pack,cfg=self.fixture(root)
            with patch.object(replay,'ROOT',root/'receipts'):
                replay.freeze('style-dark',cfg);path=root/'receipts/style-dark/frozen-inputs/metadata.zip';path.write_bytes(path.read_bytes()+b'tampered')
                with self.assertRaisesRegex(ValueError,'archive hash mismatch'):replay.verify_snapshot('style-dark',cfg)

    def test_unsafe_relative_pack_input_rejected(self):
        for value in ['../escape','/absolute','.','']:
            with self.subTest(value=value),self.assertRaises(ValueError):replay.safe_rel(value)


if __name__=='__main__':unittest.main()
