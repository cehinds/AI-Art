#!/usr/bin/env python3
"""Normalize one generated orthographic view and replace only that view.

The generated source image is retained under raw/targeted-repairs. This helper
preserves all other five PNGs, sidecars and asset references for the object.
"""
import argparse
import hashlib
import json
import shutil
import struct
from pathlib import Path

from PIL import Image

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--object-id', required=True)
    ap.add_argument('--view', required=True, choices=('front', 'top', 'right', 'left', 'bottom', 'rear'))
    ap.add_argument('--input', required=True, type=Path)
    ap.add_argument('--atlas', type=Path, help='Optional full generated atlas retained for replay provenance.')
    ap.add_argument('--cell', help='Optional source cell coordinates, for example col=2,row=0.')
    ap.add_argument('--target-width', type=int, help='Optional target pixel width for calibrated compact plans.')
    ap.add_argument('--rotate', type=int, choices=(90,180,270), help='Optional clockwise rotation before normalization.')
    ap.add_argument('--flip-horizontal', action='store_true', help='Mirror the normalized view horizontally.')
    ap.add_argument('--prompt', required=True, help='Exact generation prompt, retained with raw input.')
    ap.add_argument('--notes', required=True)
    args = ap.parse_args()

    aid = f'{args.object_id}.{args.view}'
    output = OUT / 'images' / f'{aid}.png'
    sidecar = output.with_suffix('.json')
    meta = json.loads(sidecar.read_text())
    idx_path = OUT / 'set-index.json'
    idx = json.loads(idx_path.read_text())
    if meta.get('object_id') != args.object_id or meta.get('view') != args.view:
        raise ValueError(f'Existing sidecar does not identify {aid}')

    raw_dir = OUT / 'raw' / 'targeted-repairs'
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw = raw_dir / f'{aid}.png'
    recipe = raw_dir / f'{aid}.json'
    shutil.copy2(args.input, raw)
    atlas_copy=None
    if args.atlas:
        atlas_copy=raw_dir/f'{aid}.atlas.png'
        shutil.copy2(args.atlas,atlas_copy)
    recipe.write_text(json.dumps({'object_id': args.object_id, 'view': args.view,
                                  'input_image': raw.relative_to(ROOT).as_posix(),
                                  'input_sha256': hashlib.sha256(raw.read_bytes()).hexdigest(),
                                  'generated_atlas': atlas_copy.relative_to(ROOT).as_posix() if atlas_copy else None,
                                  'generated_atlas_sha256': hashlib.sha256(atlas_copy.read_bytes()).hexdigest() if atlas_copy else None,
                                  'source_cell': args.cell,
                                  'target_width_px': args.target_width,
                                  'rotation_degrees_ccw': (-args.rotate if args.rotate else 0) % 360,
                                  'flip_horizontal': args.flip_horizontal,
                                  'prompt': args.prompt, 'notes': args.notes}, indent=2) + '\n')

    source = Image.open(raw).convert('RGBA')
    bbox = source.getchannel('A').getbbox()
    if not bbox:
        raise ValueError('Generated image has no visible alpha')
    crop = source.crop(bbox)
    if args.rotate:
        crop=crop.rotate(-args.rotate,expand=True,resample=Image.Resampling.NEAREST)
    if args.flip_horizontal:
        crop=crop.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    # Keep the pack's standard 204px max object footprint and crisp clusters.
    scale = (args.target_width / crop.width) if args.target_width else (204 / max(crop.size))
    size = (max(1, round(crop.width * scale)), max(1, round(crop.height * scale)))
    crop = crop.resize(size, Image.Resampling.NEAREST)
    canvas = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
    offset = ((256 - size[0]) // 2, (256 - size[1]) // 2)
    canvas.alpha_composite(crop, offset)
    canvas.save(output, optimize=True)

    raw_bytes = output.read_bytes()
    rgba = canvas.tobytes()
    meta['image'].update({'path': output.relative_to(ROOT).as_posix(), 'width': 256, 'height': 256,
                          'sha256': hashlib.sha256(raw_bytes).hexdigest(),
                          'rgba_sha256': hashlib.sha256(struct.pack('>II', 256, 256) + rgba).hexdigest()})
    meta['provenance'].update({'method': 'generated',
                               'generated_atlas': atlas_copy.relative_to(ROOT).as_posix() if atlas_copy else raw.relative_to(ROOT).as_posix(),
                               'generated_atlas_sha256': hashlib.sha256(atlas_copy.read_bytes()).hexdigest() if atlas_copy else hashlib.sha256(raw.read_bytes()).hexdigest(),
                               'source_rect': {'alpha_bounds': list(bbox), 'source_size': list(source.size), 'source_cell':args.cell},
                               'normalization': {'scale': scale, 'offset_px': list(offset),
                                                 'resampling': 'nearest', 'frame_size': [256, 256],
                                                 'target_width_px':args.target_width},
                               'repair_recipe': recipe.relative_to(ROOT).as_posix(),
                               'notes': args.notes})
    meta['metadata_path'] = sidecar.relative_to(ROOT).as_posix()
    sidecar.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + '\n')

    for asset in idx['assets']:
        if asset.get('id') == aid:
            asset.clear()
            asset.update(meta)
            break
    else:
        raise ValueError(f'{aid} not found in set-index')
    for group in idx['view_sets']:
        if group.get('object_id') == args.object_id:
            group['complete'] = False
            group['geometry_qa'] = {'status': 'pending-review', 'reason': 'Targeted view was regenerated; awaiting independent current-hash QA.'}
            group.setdefault('notes', 'Targeted view repair; other accepted directions retained.')
            break
    idx_path.write_text(json.dumps(idx, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({'id': aid, 'image_sha256': meta['image']['sha256'], 'raw': raw.relative_to(ROOT).as_posix()}))


if __name__ == '__main__':
    main()
