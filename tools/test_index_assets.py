"""Index only deliverable art while retaining explicitly tracked ignored inputs."""
import hashlib
from pathlib import Path
import subprocess
import tempfile
import unittest
from index_assets import build_index


class AssetIndexTests(unittest.TestCase):
    def test_tracked_ignored_inputs_and_normal_untracked_art_are_indexed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);subprocess.run(['git','init','-q',str(root)],check=True)
            (root/'.gitignore').write_text('*.tmp\n*.b64\n')
            assets=root/'dungeon-crawler-tactics/Web/wwwroot/assets';assets.mkdir(parents=True)
            retained=assets/'retained.png.b64';retained.write_bytes(b'historical-transport')
            subprocess.run(['git','-C',str(root),'add','-f',str(retained.relative_to(root))],check=True)
            (assets/'scratch.tmp').write_bytes(b'')
            (assets/'untracked.png.b64').write_bytes(b'ignored-transport')
            visible=assets/'new.png';visible.write_bytes(b'new-png')
            outside=root/'dungeon-crawler-tactics/private.txt';outside.write_text('not an asset folder')
            index=build_index(root,'dungeon-crawler-tactics');files={f['path']:f for f in index['files']}
            self.assertEqual(set(files),{'Web/wwwroot/assets/retained.png.b64','Web/wwwroot/assets/new.png'})
            self.assertEqual(files['Web/wwwroot/assets/retained.png.b64']['sha256'],hashlib.sha256(retained.read_bytes()).hexdigest())
            self.assertEqual(files['Web/wwwroot/assets/new.png']['bytes'],len(b'new-png'))
            self.assertEqual(build_index(root,'dungeon-crawler-tactics'),index)

    def test_deleted_tracked_files_are_not_indexed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);subprocess.run(['git','init','-q',str(root)],check=True)
            path=root/'dungeon-crawler-tactics/Docs/removed.txt';path.parent.mkdir(parents=True);path.write_text('old')
            subprocess.run(['git','-C',str(root),'add',str(path.relative_to(root))],check=True);path.unlink()
            self.assertEqual(build_index(root,'dungeon-crawler-tactics')['files'],[])


if __name__=='__main__':unittest.main()
