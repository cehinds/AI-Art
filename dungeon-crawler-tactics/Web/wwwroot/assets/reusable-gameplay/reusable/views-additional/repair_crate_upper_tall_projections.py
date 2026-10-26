from pathlib import Path
import hashlib, json, struct
import numpy as np
from PIL import Image
from scipy import ndimage

OUT = Path(__file__).resolve().parent
PACK = OUT.parents[1]
INDEX = OUT / 'set-index.json'
OID = 'concepts-forms-and-stances-crate-upper'
RECIPE_REL = 'reusable/views-additional/raw/crate-upper-tall-elevations.recipe.json'
RECIPE = json.loads((PACK / RECIPE_REL).read_text())
ATLAS_REL = RECIPE['source_atlas']
ATLAS_PATH = PACK / ATLAS_REL
ATLAS_BYTES = ATLAS_PATH.read_bytes()
ATLAS_HASH = hashlib.sha256(ATLAS_BYTES).hexdigest()
ATLAS = Image.open(ATLAS_PATH).convert('RGBA')
ARRAY = np.asarray(ATLAS)
LABELS, COUNT = ndimage.label(ARRAY[:, :, 3] >= int(RECIPE['alpha_threshold']), np.ones((3, 3), dtype=np.uint8))
INDEX_DATA = json.loads(INDEX.read_text())
ASSETS = {a['id']: a for a in INDEX_DATA['assets']}
VIEW_ORDER = ['front', 'right', 'left', 'rear']
cell_w = ATLAS.width / 4
cell_h = ATLAS.height
resolution_log = []

def sha(data): return hashlib.sha256(data).hexdigest()
def save_png(image, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, optimize=True)
    return path.read_bytes()

def install_elevation(view, col):
    xlo, xhi = round(col * cell_w), round((col + 1) * cell_w)
    cx, cy = (xlo + xhi) / 2, cell_h / 2
    candidates = []
    for label in range(1, COUNT + 1):
        yy, xx = np.where(LABELS[:, xlo:xhi] == label)
        if len(xx) < 500:
            continue
        gx = xx + xlo
        bbox = (int(gx.min()), int(yy.min()), int(gx.max() + 1), int(yy.max() + 1))
        touches = bbox[0] <= xlo + 2 or bbox[2] >= xhi - 2 or bbox[1] <= 2 or bbox[3] >= cell_h - 2
        if touches:
            continue
        score = ((float(gx.mean()) - cx) / (xhi - xlo)) ** 2 + ((float(yy.mean()) - cy) / cell_h) ** 2
        candidates.append((score, label, bbox, len(xx)))
    if not candidates:
        raise RuntimeError(f'{view}: no complete isolated alpha component in cell')
    _, label, (x0, y0, x1, y1), area = min(candidates)
    # Crop only the chosen object component; neighboring speckles/cell leakage stay out.
    local_mask = LABELS[y0:y1, x0:x1] == label
    piece = ATLAS.crop((x0, y0, x1, y1))
    alpha = np.asarray(piece.getchannel('A'))
    piece.putalpha(Image.fromarray(np.where(local_mask, alpha, 0).astype('uint8')))
    scale = float(RECIPE['shared_scale'])
    nw, nh = max(1, round(piece.width * scale)), max(1, round(piece.height * scale))
    piece = piece.resize((nw, nh), Image.Resampling.NEAREST)
    frame = Image.new('RGBA', (256, 256))
    ox, oy = (128 - nw // 2, int(RECIPE['ground_anchor_y']) - nh)
    if ox < 0 or oy < 0 or ox + nw > 256 or oy + nh > 256:
        raise RuntimeError(f'{view}: inferred crate elevation would clip ({nw}x{nh} at {ox},{oy})')
    frame.alpha_composite(piece, (ox, oy))
    asset = ASSETS[f'{OID}.{view}']
    image_rel = asset['image']['path']
    image_path = PACK / image_rel
    encoded = save_png(frame, image_path)
    metadata = dict(asset)
    metadata['image'] = {'path': image_rel, 'width': 256, 'height': 256,
        'sha256': sha(encoded),
        'rgba_sha256': hashlib.sha256(struct.pack('>II', 256, 256) + frame.tobytes()).hexdigest()}
    metadata['anchor_px'] = [128, 128]
    provenance = dict(metadata.get('provenance', {}))
    provenance.update({
        'method': 'generated',
        'source_image': 'reusable/native/concepts-forms-and-stances-crate-upper.png',
        'native_front': 'reusable/native/concepts-forms-and-stances-crate-upper.png',
        'native_front_sha256': hashlib.sha256((PACK / 'reusable/native/concepts-forms-and-stances-crate-upper.png').read_bytes()).hexdigest(),
        'notes': 'Inferred orthographic elevation of the tall narrow source crate; X-bracing and warm timber/iron palette retained. Hidden surfaces are conservative illustration, not recovered pixels.',
        'source_atlas': ATLAS_REL,
        'source_atlas_sha256': ATLAS_HASH,
        'generation_recipe': RECIPE_REL,
        'prompt_path': RECIPE['prompt'],
        'prompt_sha256': hashlib.sha256((PACK / RECIPE['prompt']).read_bytes()).hexdigest(),
        'crop_bounds_px': {
            'nominal_cell': {'column': col, 'row': 0, 'bounds': [xlo, 0, xhi, cell_h]},
            'alpha_bounds_global': [x0, y0, x1, y1],
            'component_labels': [int(label)],
            'resized_bounds_px': [nw, nh],
            'canvas_offset_px': [ox, oy],
            'shared_scale': scale
        }
    })
    metadata['provenance'] = provenance
    meta_rel = asset['metadata_path']
    (PACK / meta_rel).write_text(json.dumps(metadata, indent=2) + '\n')
    ASSETS[f'{OID}.{view}'] = metadata
    resolution_log.append({'view': view, 'bounds_xyxy': [x0, y0, x1, y1], 'component_label': int(label), 'area': int(area), 'scale': scale, 'output_bbox': list(frame.getchannel('A').getbbox()), 'sha256': metadata['image']['sha256']})

def resize_plan(view, scale):
    asset = ASSETS[f'{OID}.{view}']
    # Re-render accepted plan from its declared atlas and XYXY crop metadata, then resize isotropically.
    prov = asset['provenance']; crop = prov['crop_bounds_px']; old_recipe = json.loads((PACK / prov['generation_recipe']).read_text())
    raw_path = PACK / prov['source_atlas']; raw = Image.open(raw_path).convert('RGBA'); arr = np.asarray(raw)
    labels, _ = ndimage.label(arr[:, :, 3] >= int(old_recipe.get('alpha_threshold', 245)), np.ones((3, 3), dtype=np.uint8))
    x0, y0, x1, y1 = crop['alpha_bounds_global']; keep = list(map(int, crop['component_labels']))
    mask = np.isin(labels[y0:y1, x0:x1], keep)
    piece = raw.crop((x0, y0, x1, y1))
    if old_recipe.get('preserve_alpha', False):
        alpha = np.asarray(piece.getchannel('A')); piece.putalpha(Image.fromarray(np.where(mask, alpha, 0).astype('uint8')))
    else:
        piece.putalpha(Image.fromarray((mask * 255).astype('uint8')))
    nw, nh = round(crop['resized_bounds_px'][0] * scale), round(crop['resized_bounds_px'][1] * scale)
    piece = piece.resize((nw, nh), Image.Resampling.NEAREST)
    frame = Image.new('RGBA', (256, 256)); ox, oy = (128 - nw // 2, 128 - nh // 2); frame.alpha_composite(piece, (ox, oy))
    image_rel = asset['image']['path']; encoded = save_png(frame, PACK / image_rel)
    metadata = dict(asset); metadata['image'] = {'path': image_rel, 'width': 256, 'height': 256, 'sha256': sha(encoded), 'rgba_sha256': hashlib.sha256(struct.pack('>II', 256, 256) + frame.tobytes()).hexdigest()}
    metadata['anchor_px'] = [128,128]
    provenance = dict(metadata['provenance']); crop = dict(provenance['crop_bounds_px']); crop['resized_bounds_px'] = [nw,nh]; crop['canvas_offset_px'] = [ox,oy]; crop['shared_scale'] = float(crop.get('shared_scale',1.0))*scale; crop['isotropic_calibration'] = float(crop.get('isotropic_calibration',1.0))*scale; provenance['crop_bounds_px'] = crop
    provenance['notes'] = 'Inferred square plan footprint isotropically calibrated to the revised tall elevation width; hidden underside details remain conservative.'
    metadata['provenance'] = provenance; (PACK / asset['metadata_path']).write_text(json.dumps(metadata,indent=2)+'\n'); ASSETS[f'{OID}.{view}'] = metadata
    resolution_log.append({'view':view,'plan_source_atlas':prov['source_atlas'],'scale_from_accepted_plan':scale,'output_bbox':list(frame.getchannel('A').getbbox()),'sha256':metadata['image']['sha256']})

for view, col in zip(VIEW_ORDER, range(4)):
    install_elevation(view, col)
for view in ['top','bottom']:
    resize_plan(view, .8)
INDEX_DATA['assets'] = [ASSETS.get(a['id'], a) for a in INDEX_DATA['assets']]
INDEX.write_text(json.dumps(INDEX_DATA,indent=2)+'\n')
(PACK / 'reusable/views-additional/raw/crate-upper-tall-elevations-installed.json').write_text(json.dumps({'object_id':OID,'atlas_sha256':ATLAS_HASH,'views':resolution_log},indent=2)+'\n')
print(json.dumps(resolution_log,indent=2))
