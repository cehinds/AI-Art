"""Reproducibly extract 6x3 generated orthographic view atlases.

Usage: python3 split_atlas.py ATLAS 'object-id,row' ...
The atlas is retained under raw/ with prompt and source references in provenance.
"""
import hashlib, json, struct, sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent
PACK = HERE.parents[1]
VIEWS = ['front', 'top', 'right', 'left', 'bottom', 'rear']
ATLAS = Path(sys.argv[1]).resolve()
OBJECTS = [(arg.rsplit(',', 1)[0], int(arg.rsplit(',', 1)[1])) for arg in sys.argv[2:]]

def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def rgba_hash(image):
    image = image.convert('RGBA')
    return hashlib.sha256(struct.pack('>II', image.width, image.height) + image.tobytes()).hexdigest()

roads = json.loads((PACK / 'collections/roads/manifest.json').read_text())['assets']
forest = json.loads((PACK / 'collections/forest/manifest.json').read_text())['assets']
source_assets = {a['id']: a for a in roads + forest}
image = Image.open(ATLAS).convert('RGBA')
# Generated atlases can have non-divisible pixel dimensions; partition by
# fractional boundaries and round each edge independently to avoid drift.
raw_dir = HERE / 'raw'
raw_dir.mkdir(parents=True, exist_ok=True)
raw_path = raw_dir / ATLAS.name
if raw_path.resolve() != ATLAS:
    raw_path.write_bytes(ATLAS.read_bytes())
raw_rel = raw_path.relative_to(PACK).as_posix()
raw_digest = file_hash(raw_path)
prov_path = raw_path.with_suffix('.provenance.json')
prov = json.loads(prov_path.read_text()) if prov_path.exists() else {}
prov.update({'file': raw_rel, 'sha256': raw_digest, 'width': image.width, 'height': image.height,
             'grid': {'columns': 6, 'rows': 3, 'order': VIEWS},
             'objects': [{'object_id': oid, 'row': row,
                          'source_image': source_assets[oid]['file'],
                          'cell_bounds_px': [[round(c*image.width/6), round(row*image.height/3),
                                              round((c+1)*image.width/6), round((row+1)*image.height/3)]
                                             for c in range(6)]} for oid, row in OBJECTS]})
prov_path.write_text(json.dumps(prov, indent=2) + '\n')

# Build silhouettes across the full atlas rather than clipping at nominal grid
# edges. Some generated views drift across a column boundary while remaining
# centered in their intended slot. Assign connected silhouettes to the nearest
# logical slot by their centroid and retain their complete bounds.
rgba = np.asarray(image).copy()
if np.all(rgba[:, :, 3] == 255):
    rgb = rgba[:, :, :3].astype(np.int16)
    neutral = (rgb.max(axis=2) - rgb.min(axis=2) <= 8) & (rgb.mean(axis=2) >= 205)
    seeds = np.zeros(neutral.shape, dtype=bool)
    seeds[0, :] = neutral[0, :]; seeds[-1, :] = neutral[-1, :]
    seeds[:, 0] = neutral[:, 0]; seeds[:, -1] = neutral[:, -1]
    bg = ndimage.binary_propagation(seeds, structure=np.array([[0,1,0],[1,1,1],[0,1,0]], dtype=bool), mask=neutral)
    rgba[bg, 3] = 0
atlas_alpha = rgba[:, :, 3] > 16
component_labels, component_count = ndimage.label(atlas_alpha, structure=np.ones((3,3), dtype=np.uint8))
component_sizes = np.bincount(component_labels.ravel())
components = {slot: [] for slot in [(r, c) for r in range(3) for c in range(6)]}
for label in range(1, component_count + 1):
    if component_sizes[label] < 8:
        continue
    ys, xs = np.where(component_labels == label)
    cy, cx = float(ys.mean()), float(xs.mean())
    row_slot = min(range(3), key=lambda r: abs(cy - (r + 0.5) * image.height / 3))
    col_slot = min(range(6), key=lambda c: abs(cx - (c + 0.5) * image.width / 6))
    components[(row_slot, col_slot)].append((label, int(component_sizes[label]), (int(xs.min()), int(ys.min()), int(xs.max())+1, int(ys.max())+1)))

index_path = HERE / 'set-index.json'
index = json.loads(index_path.read_text()) if index_path.exists() else {'assets': [], 'view_sets': []}
for object_id, row in OBJECTS:
    src = source_assets[object_id]
    crop_list = []
    for col in range(6):
        x0, x1 = round(col*image.width/6), round((col+1)*image.width/6)
        y0, y1 = round(row*image.height/3), round((row+1)*image.height/3)
        slot_components = components[(row, col)]
        largest = max((size for _, size, _ in slot_components), default=0)
        keep_labels = [label for label, size, _ in slot_components if size >= max(8, largest * 0.08)]
        keep = np.isin(component_labels, keep_labels)
        bounds = Image.fromarray((keep * 255).astype(np.uint8)).getbbox()
        if bounds:
            crop_rgba = rgba[bounds[1]:bounds[3], bounds[0]:bounds[2]].copy()
            crop_rgba[:, :, 3] = np.where(keep[bounds[1]:bounds[3], bounds[0]:bounds[2]], crop_rgba[:, :, 3], 0).astype(np.uint8)
            crop = Image.fromarray(crop_rgba, 'RGBA')
        else:
            crop = None
        crop_list.append((crop, [x0,y0,x1,y1], bounds, slot_components, keep_labels))
    if any(crop is None for crop, _, _, _, _ in crop_list):
        raise RuntimeError(f'{object_id}: missing view(s) {[VIEWS[i] for i,(c,_,_,_,_) in enumerate(crop_list) if c is None]}')
    scale = 220 / max(max(crop.size) for crop, _, _, _, _ in crop_list)
    view_map = {}
    for view, (crop, cell_bounds, alpha_bounds, slot_components, keep_labels) in zip(VIEWS, crop_list):
        size = (max(1, round(crop.width * scale)), max(1, round(crop.height * scale)))
        normalized = crop.resize(size, Image.Resampling.NEAREST)
        canvas = Image.new('RGBA', (256, 256), (0,0,0,0))
        canvas.alpha_composite(normalized, ((256-size[0])//2, 248-size[1]))
        asset_id = object_id + '.' + view
        rel_img = f'reusable/views-roads-forest/{asset_id}.png'
        image_path = PACK / rel_img
        canvas.save(image_path)
        rel_meta = f'reusable/views-roads-forest/{asset_id}.json'
        referenced = [src['file']]
        ref_hash = file_hash(PACK / src['file'])
        data = {'id': asset_id, 'name': src['label'] + ' ' + view,
                'kind': 'tile' if src['category'] == 'terrain' else 'sprite',
                'tags': [src['collection'], view, 'orthographic', 'inferred-view'],
                'image': {'path': rel_img, 'width': 256, 'height': 256,
                          'sha256': file_hash(image_path), 'rgba_sha256': rgba_hash(canvas)},
                'object_id': object_id, 'view': view,
                'provenance': {'method': 'generated', 'source_image': src['file'],
                    'source_image_sha256': ref_hash, 'referenced_source_images': [{'path': p, 'sha256': ref_hash} for p in referenced],
                    'generated_atlas': raw_rel, 'generated_atlas_sha256': raw_digest,
                    'crop_bounds_px': {'logical_cell': cell_bounds, 'complete_component_bounds_atlas': list(alpha_bounds),
                        'component_labels': [{'label': label, 'pixels': size, 'bounds_atlas': list(bounds)} for label,size,bounds in slot_components if label in keep_labels]},
                    'cell_extraction': '8-connected alpha components across the full atlas; component centroid assigned to nearest logical row and column center; all retained component bounds are composited, including bounds crossing nominal cell edges',
                    'normalization': {'method': 'nearest-neighbor', 'shared_scale_per_object': scale,
                        'max_long_side_px': 220, 'canvas_px': [256,256], 'anchor_px': [128,248],
                        'alpha_island_filter': '8-connected over atlas, assign by centroid; retain slot components >= max(8px, 8% of largest assigned component)',
                        'background_cleanup': 'if atlas is fully opaque, flood neutral near-gray pixels (channel range <=8, mean >=205) connected to atlas boundary using 4-connectivity'},
                    'notes': 'Generated inferred orthographic view; hidden surfaces extrapolated conservatively, not recovered source pixels.'},
                'anchor_px': [128,248], 'metadata_path': rel_meta}
        (PACK / rel_meta).write_text(json.dumps(data, indent=2) + '\n')
        index['assets'] = [a for a in index['assets'] if a['id'] != asset_id]
        index['assets'].append(data)
        view_map[view] = asset_id
    index['view_sets'] = [s for s in index['view_sets'] if s['object_id'] != object_id]
    index['view_sets'].append({'object_id': object_id, 'views': view_map, 'complete': len(view_map) == 6,
                               'notes': 'Six generated orthographic views; inferred unseen surfaces.'})
    print(object_id, len(view_map), 'views')
index_path.write_text(json.dumps(index, indent=2) + '\n')
