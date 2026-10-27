#!/usr/bin/env python3
"""Rebuild pure race-circuit floor TOP views from canonical source pixels."""
from pathlib import Path
import sys
import hashlib, json, os, struct, tempfile
from PIL import Image

OUT = Path(__file__).resolve().parent
PACK = OUT.parents[1]
ROOT = PACK.parents[0]
IDS = (
    'race-circuits-race-asphalt-floor',
    'race-circuits-painted-grid-asphalt-floor',
    'race-circuits-garage-concrete-floor',
    'race-circuits-pit-service-grating-floor',
    'race-circuits-race-asphalt-edge-transition',
    'race-circuits-race-asphalt-corner-transition',
)

def atomic(path, data):
    fd, tmp = tempfile.mkstemp(prefix=path.name + '.', suffix='.tmp', dir=path.parent)
    os.close(fd)
    Path(tmp).write_text(json.dumps(data, indent=2) + '\n')
    os.replace(tmp, path)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    index_path = OUT / 'set-index.json'
    index = json.loads(index_path.read_text())
    aset = {a['id']: a for a in index['assets']}
    manifest = json.loads((PACK / 'manifest.json').read_text())['assets']
    source = {a['id'].removesuffix('--native'): a for a in manifest}
    changed = []
    selected_ids = tuple(sys.argv[1:]) or IDS
    for oid in selected_ids:
        record = source[oid]
        rel = f"{record['source']['sheet']}/components/{oid}.png"
        path = PACK / rel
        source_png = Image.open(path).convert('RGBA')
        alpha_bounds = source_png.getchannel('A').getbbox()
        if alpha_bounds is None:
            raise ValueError(f'{oid}: canonical source has no visible alpha')
        crop = source_png.crop(alpha_bounds)
        # Match the physical tile width in its four inferred horizontal edge views.
        edge_widths = []
        for direction in ('front', 'right', 'left', 'rear'):
            edge = Image.open(OUT / f'{oid}.{direction}.png').convert('RGBA')
            bounds = edge.getchannel('A').getbbox()
            if bounds is None:
                raise ValueError(f'{oid}.{direction}: no edge silhouette')
            edge_widths.append(bounds[2] - bounds[0])
        target = min(208, max(edge_widths))
        scale = target / max(crop.size)
        nw, nh = max(1, round(crop.width * scale)), max(1, round(crop.height * scale))
        crop = crop.resize((nw, nh), Image.Resampling.NEAREST)
        canvas = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
        offset = (128 - nw // 2, 128 - nh // 2)
        canvas.alpha_composite(crop, offset)
        aid = f'{oid}.top'
        dest = PACK / aset[aid]['image']['path']
        canvas.save(dest, optimize=True)
        meta_path = OUT / f'{aid}.json'
        meta = json.loads(meta_path.read_text())
        imghash = sha(dest)
        rgba_hash = hashlib.sha256(struct.pack('>II', 256, 256) + canvas.tobytes()).hexdigest()
        meta['image'].update({'width': 256, 'height': 256, 'sha256': imghash, 'rgba_sha256': rgba_hash})
        prov = meta.setdefault('provenance', {})
        prior = {k: prov[k] for k in ('method', 'source_atlas', 'source_atlas_sha256', 'generation_recipe', 'crop_bounds_px') if k in prov}
        prov.update({
            'method': 'reused-canonical-source-top',
            'source_image': rel,
            'source_sha256': sha(path),
            'notes': 'The existing canonical floor component is its true TOP plan. Its exact alpha crop is reused with isotropic nearest-neighbor frame normalization; other directions remain inferred.',
            'reuse': {
                'source_component': rel,
                'source_component_sha256': sha(path),
                'alpha_bounds_px': list(alpha_bounds),
                'resized_bounds_px': [nw, nh],
                'canvas_offset_px': list(offset),
                'isotropic_scale': scale,
                'edge_view_target_width_px': target,
                'superseded_generated_view': prior,
            },
        })
        atomic(meta_path, meta)
        aset[aid].update(meta)
        changed.append({'object_id': oid, 'asset_id': aid, 'source_image': rel, 'source_sha256': sha(path), 'image_sha256': imghash, 'rgba_sha256': rgba_hash, 'target_width_px': target})
    index['assets'] = list(aset.values())
    atomic(index_path, index)
    pending_path = OUT / 'pending-review-batches.json'
    if pending_path.exists():
        pending = json.loads(pending_path.read_text())
        by_id = {x['object_id']: x for x in pending.get('objects', [])}
        for item in changed:
            obj = by_id.get(item['object_id'])
            if obj and 'top' in obj.get('views', {}):
                obj['views']['top']['sha256'] = item['image_sha256']
        atomic(pending_path, pending)
    print(json.dumps({'updated': changed}, indent=2))

if __name__ == '__main__':
    main()
