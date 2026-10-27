#!/usr/bin/env python3
"""Join a JSON-described multipart ZIP, checking every part before publishing it."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile


def file_hash(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def assemble(manifest_path, output):
    manifest_path, output = Path(manifest_path), Path(output)
    doc = json.loads(manifest_path.read_bytes())
    if doc.get('schema_version') != 1 or doc.get('kind') != 'multipart-zip':
        raise ValueError('Unsupported multipart archive manifest')
    parts = doc.get('parts', [])
    if not parts or not isinstance(parts, list):
        raise ValueError('Archive needs an ordered parts list')
    seen, inputs = set(), []
    for number, row in enumerate(parts, 1):
        name = row['file']
        if not isinstance(name, str) or Path(name).name != name or name in ('.', '..') or '\\' in name or name in seen:
            raise ValueError('Unsafe or duplicate part filename')
        if row.get('number') != number:
            raise ValueError('Archive parts are out of order')
        seen.add(name)
        source = manifest_path.parent / name
        if source.is_symlink() or source.stat().st_size != row['bytes'] or file_hash(source) != row['sha256']:
            raise ValueError('Archive part hash/size mismatch: ' + name)
        inputs.append(source)
    if output.resolve() in {manifest_path.resolve(), *(p.resolve() for p in inputs)}:
        raise ValueError('Output would overwrite an input')
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.assembling-', dir=output.parent)
    try:
        total, whole = 0, hashlib.sha256()
        with os.fdopen(fd, 'wb') as target:
            for source, row in zip(inputs, parts):
                part, count = hashlib.sha256(), 0
                with source.open('rb') as stream:
                    for block in iter(lambda: stream.read(1024 * 1024), b''):
                        target.write(block); part.update(block); whole.update(block)
                        count += len(block); total += len(block)
                if count != row['bytes'] or part.hexdigest() != row['sha256']:
                    raise ValueError('Archive part changed while assembling')
        if total != doc['archive']['bytes'] or whole.hexdigest() != doc['archive']['sha256']:
            raise ValueError('Assembled archive hash/size mismatch')
        os.replace(temporary, output)
        return {'bytes': total, 'sha256': whole.hexdigest(), 'parts': len(parts)}
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(assemble(args.manifest, args.output), indent=2))


if __name__ == '__main__':
    main()
