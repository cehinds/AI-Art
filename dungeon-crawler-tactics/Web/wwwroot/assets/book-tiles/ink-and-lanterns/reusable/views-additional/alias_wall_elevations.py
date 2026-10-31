#!/usr/bin/env python3
"""Install declared same-family accepted wall-face aliases on flagged corner elevations."""
import argparse
import hashlib
import json
import os
import pathlib
import struct
import tempfile
from PIL import Image

OUT = pathlib.Path(__file__).resolve().parent
PACK = OUT.parent.parent
INDEX_PATH = OUT / 'set-index.json'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def atomic_json(path, value):
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name+'.', suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(value, f, indent=2, ensure_ascii=False)
            f.write('\n'); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        try: os.unlink(tmp)
        except FileNotFoundError: pass
        raise

def atomic_copy(src, dst):
    fd, tmp = tempfile.mkstemp(dir=dst.parent, prefix=dst.name+'.', suffix='.tmp')
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(src.read_bytes()); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, dst)
    except BaseException:
        try: os.unlink(tmp)
        except FileNotFoundError: pass
        raise

def main(recipe_arg):
    recipe_path = pathlib.Path(recipe_arg)
    if not recipe_path.is_absolute(): recipe_path = OUT / recipe_path
    recipe = json.loads(recipe_path.read_text())
    index = json.loads(INDEX_PATH.read_text())
    assets = {a['id']: a for a in index['assets']}
    unique_sets = {s['object_id']: s for s in index['view_sets']}
    sets = {s.get('source_id', s['object_id']): s for s in unique_sets.values()}
    sets.update(unique_sets)
    # Fail closed on any changed target or guide so aliases never overwrite review updates.
    for item in recipe['aliases']:
        target_id = item['target_object_id']
        guide_id = item.get('guide_object_id')
        if target_id not in sets: raise KeyError(target_id)
        for direction, mapping in item['views'].items():
            aid = sets[target_id]['views'][direction]
            actual = OUT / pathlib.Path(assets[aid]['image']['path']).name
            if sha(actual) != mapping['expected_target_sha256']:
                raise RuntimeError(f'target changed since recipe: {target_id}.{direction}')
            view_guide_id = mapping['guide_object_id']
            if view_guide_id not in sets: raise KeyError(view_guide_id)
            gid = sets[view_guide_id]['views'][mapping['guide_view']]
            guide = OUT / pathlib.Path(assets[gid]['image']['path']).name
            if sha(guide) != mapping['expected_guide_sha256']:
                raise RuntimeError(f'guide changed since recipe: {guide_id}.{mapping["guide_view"]}')
            if assets[gid]['image']['sha256'] != mapping['expected_guide_sha256']:
                raise RuntimeError(f'guide index hash mismatch: {guide_id}.{mapping["guide_view"]}')
    # Copy only explicitly listed affected views; preserve every other PNG and source lineage.
    for item in recipe['aliases']:
        target_id = item['target_object_id']
        for direction, mapping in item['views'].items():
            target_set = sets[target_id]
            aid = target_set['views'][direction]
            asset = assets[aid]
            gid = sets[mapping['guide_object_id']]['views'][mapping['guide_view']]
            guide_asset = assets[gid]
            src = OUT / pathlib.Path(guide_asset['image']['path']).name
            dest = OUT / pathlib.Path(asset['image']['path']).name
            atomic_copy(src, dest)
            image = Image.open(dest).convert('RGBA')
            file_sha = sha(dest)
            rgba_sha = hashlib.sha256(struct.pack('>II', *image.size) + image.tobytes()).hexdigest()
            metadata_path = PACK / asset['metadata_path']
            metadata = json.loads(metadata_path.read_text())
            metadata['image'].update({'path': asset['image']['path'], 'width': image.width, 'height': image.height,
                                      'sha256': file_sha, 'rgba_sha256': rgba_sha})
            prov = metadata.setdefault('provenance', {})
            prov.setdefault('method', 'generated')
            prov['derivation'] = {
                'method': mapping.get('derivation_method', 'same-family-accepted-wall-face-alias'),
                'guide_object_id': mapping['guide_object_id'],
                'guide_asset_id': gid,
                'guide_view': mapping['guide_view'],
                'guide_image_sha256': mapping['expected_guide_sha256'],
                'transform': 'exact 256x256 RGBA PNG copy; no resampling',
                'recipe': recipe_path.relative_to(PACK).as_posix(),
                'note': mapping.get('derivation_note', 'Inferred wall-arm projection; the target remains linked to its own canonical source image.')
            }
            atomic_json(metadata_path, metadata)
            asset['image'] = metadata['image']
            asset['provenance'] = prov
        target_set['complete'] = False
    atomic_json(INDEX_PATH, {'assets': list(assets.values()), 'view_sets': list(unique_sets.values())})
    print(json.dumps({'updated_objects': [x['target_object_id'] for x in recipe['aliases']],
                      'directions': sorted({d for x in recipe['aliases'] for d in x['views']}),
                      'recipe': recipe_path.relative_to(PACK).as_posix()}))

if __name__ == '__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('recipe'); main(ap.parse_args().recipe)
