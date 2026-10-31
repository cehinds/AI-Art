"""Rebuild a project asset index from Git-tracked and visible untracked art.

Run from any cwd. Git-ignored untracked scratch files are excluded; explicitly
tracked historical inputs remain included even when their suffix is ignored.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
FOLDERS = {'Web', 'Docs', 'UnityPackage', 'UnityProject', 'Wireframes'}


def build_index(root, project_name):
    root = Path(root).resolve()
    project = root / project_name
    output = subprocess.check_output(
        ['git', '-C', str(root), 'ls-files', '-z', '--cached', '--others',
         '--exclude-standard', '--', *[f'{project_name}/{folder}/' for folder in sorted(FOLDERS)]])
    files = []
    for value in sorted(set(output.split(b'\0')) - {b''}):
        path = root / value.decode('utf-8')
        if '__pycache__' in path.parts or path.suffix in {'.pyc', '.pyo'}:
            continue
        if path.is_symlink():
            raise ValueError(f'Symlinks are not assets: {path}')
        if path.is_file():
            files.append({'path': path.relative_to(project).as_posix(),
                          'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                          'bytes': path.stat().st_size})
    files.sort(key=lambda item: item['path'])
    return {'schemaVersion': 1, 'project': project_name, 'files': files}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project', choices=['dungeon-crawler-tactics'])
    args = parser.parse_args()
    index = build_index(ROOT, args.project)
    (ROOT / args.project / 'asset-index.json').write_text(json.dumps(index, indent=2) + '\n')
    print(f'Indexed {len(index["files"])} files ({sum(f["bytes"] for f in index["files"]) / 2**20:.1f} MiB)')


if __name__ == '__main__':
    main()
