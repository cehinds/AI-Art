"""Replay the west-wall plan axis correction without anisotropic resizing."""
from pathlib import Path
import hashlib, json, os, struct
from PIL import Image

HERE = Path(__file__).resolve().parent
OUT = HERE.parent
BOOK = OUT.parent.parent
SPEC = json.loads((HERE / '121-westwall-plan-rotation.json').read_text())
INDEX_PATH = OUT / 'set-index.json'
index = json.loads(INDEX_PATH.read_text())
changed = False
for view, hashes in SPEC['views'].items():
    aid = f"{SPEC['object_id']}.{view}"
    asset = next(a for a in index['assets'] if a['id'] == aid)
    png = BOOK / asset['image']['path']
    current = hashlib.sha256(png.read_bytes()).hexdigest()
    if current == hashes['after_sha256']:
        continue
    if current == hashes['before_sha256']:
        original = Image.open(png).convert('RGBA')
        corrected = original.transpose(Image.Transpose.ROTATE_90)
    elif current == hashes['rotated_intermediate_sha256']:
        corrected = Image.open(png).convert('RGBA')
    else:
        raise RuntimeError(f"{aid}: unexpected input hash {current}; refusing double or unknown transform")
    side = round(corrected.width * hashes['uniform_scale'])
    small = corrected.resize((side, side), Image.Resampling.NEAREST)
    canvas = Image.new('RGBA', corrected.size, (0, 0, 0, 0))
    offset = ((corrected.width - side) // 2, (corrected.height - side) // 2)
    canvas.alpha_composite(small, offset)
    canvas.save(png, optimize=True)
    rgba = canvas.tobytes()
    asset.setdefault('provenance_history', []).append({
        'image_sha256_before_transform': current,
        'provenance': asset.get('provenance', {}),
        'transform': 'rotate-90-counterclockwise then uniform plan scale 2/3',
    })
    asset['image']['sha256'] = hashlib.sha256(png.read_bytes()).hexdigest()
    asset['image']['rgba_sha256'] = hashlib.sha256(struct.pack('>II', canvas.width, canvas.height) + rgba).hexdigest()
    asset['provenance'].update({
        'method': 'orthographic-plan-rotation-and-uniform-scale',
        'view_transform': '90-degree-counterclockwise in image plane, then uniform scale 2/3',
        'geometry_basis': 'manifest squareLayout west-wall: footprint extends along map Y',
        'notes': 'Rotated and uniformly scaled the plan to align its documented long-Y axis and match the side span; no anisotropic deformation.',
    })
    (BOOK / asset['metadata_path']).write_text(json.dumps(asset, indent=2) + '\n')
    if asset['image']['sha256'] != hashes['after_sha256']:
        raise RuntimeError(f"{aid}: replay did not produce the recorded hash")
    changed = True
if changed:
    view_set = next(s for s in index['view_sets'] if s['object_id'] == SPEC['object_id'])
    view_set['complete'] = False
    view_set['notes'] = 'West-wall TOP/BOTTOM rotated and uniformly scaled to documented long-Y footprint; pending independent current-hash review.'
tmp = INDEX_PATH.with_suffix('.json.tmp')
tmp.write_text(json.dumps(index, indent=2) + '\n')
os.replace(tmp, INDEX_PATH)
