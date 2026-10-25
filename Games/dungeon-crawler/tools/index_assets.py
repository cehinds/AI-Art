"""Rebuild a project asset index after exporting curated art. Run from any cwd."""
import argparse
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('project', choices=['dungeon-crawler-tactics'])
args = parser.parse_args()
project = root / args.project
files = []
for folder in ['Web', 'Docs', 'UnityPackage', 'UnityProject', 'Wireframes']:
    for path in sorted((project / folder).rglob('*')):
        if path.is_symlink():
            raise SystemExit(f'Symlinks are not assets: {path}')
        if path.is_file():
            files.append({'path': path.relative_to(project).as_posix(),
                          'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                          'bytes': path.stat().st_size})
files.sort(key=lambda item: item['path'])
index = {'schemaVersion': 1, 'project': args.project, 'files': files}
(project / 'asset-index.json').write_text(json.dumps(index, indent=2) + '\n')
print(f'Indexed {len(files)} files ({sum(f["bytes"] for f in files) / 2**20:.1f} MiB)')
