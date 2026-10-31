from pathlib import Path
import hashlib, json
from PIL import Image

ASSETS = Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets')
PACK = ASSETS / 'book-tiles/dungeon-after-dark'
CAND = PACK / 'reusable/views-additional/candidates/equipment-dark-masonry-rail8-20261026'
RAW, OUT = CAND / 'raw', CAND / 'images'
HAND = json.loads(Path('/workspace/scratch/equipment-dark-masonry-rail8-handoff-20261026.json').read_text())
OBJ = {x['object_id']: x for x in HAND['objects']}
IDS = ['iron-stations-station-tiled-masonry-outer-corner', 'iron-stations-station-tiled-masonry-inner-corner',
       'iron-stations-station-tiled-masonry-wall-northwest', 'iron-stations-station-tiled-masonry-wall-northeast']
VIEWS = ['front', 'top', 'right', 'left', 'bottom', 'rear']
CELL = 256
TARGET = 186
ALPHA_THRESHOLD = 64
ATLAS = RAW / 'iron-stations-four-sources-output-v3.png'
BOTTOM = RAW / 'iron-stations-bottom-output-v1.png'
PROMPT = RAW / 'iron-stations-four-sources-request-v3.json'
BOTTOM_PROMPT = RAW / 'iron-stations-bottom-request-v1.json'

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def alpha_crop(image, threshold=ALPHA_THRESHOLD):
    image = image.convert('RGBA')
    alpha = image.getchannel('A').point(lambda v: 255 if v >= threshold else 0)
    box = alpha.getbbox()
    if box is None: raise ValueError('empty alpha cell')
    crop = image.crop(box)
    # Drop only the low-alpha background glow/noise, retaining edge pixels >=32.
    a = crop.getchannel('A').point(lambda v: 0 if v < 32 else v)
    crop.putalpha(a)
    return crop, list(box)

def fit(image, scale):
    w, h = image.size
    nw, nh = max(1, round(w * scale)), max(1, round(h * scale))
    im = image.resize((nw, nh), Image.Resampling.NEAREST)
    if nw > TARGET or nh > TARGET:
        raise ValueError(f'oversize {nw}x{nh}')
    canvas = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
    offset = ((256 - nw)//2, (256 - nh)//2)
    canvas.alpha_composite(im, offset)
    return canvas, [nw, nh], list(offset)

atlas = Image.open(ATLAS).convert('RGBA')
if atlas.size != (6*CELL, 4*CELL): raise ValueError(f'unexpected station atlas size {atlas.size}')
bottom = Image.open(BOTTOM).convert('RGBA')
bottom_cell_h = bottom.height / 4
bottom_prompt_json = json.loads(BOTTOM_PROMPT.read_text())
station_prompt_json = json.loads(PROMPT.read_text())
sets = []
for row, oid in enumerate(IDS):
    cells = {}
    for col, view in enumerate(VIEWS):
        if view == 'bottom':
            box = (0, round(row*bottom_cell_h), bottom.width, round((row+1)*bottom_cell_h))
            raw_cell = bottom.crop(box)
            crop, alpha_box = alpha_crop(raw_cell)
            raw_path, prompt_path = BOTTOM, BOTTOM_PROMPT
            raw_rect = [box[0], box[1], box[2]-box[0], box[3]-box[1]]
        else:
            box = (col*CELL, row*CELL, (col+1)*CELL, (row+1)*CELL)
            raw_cell = atlas.crop(box)
            crop, alpha_box = alpha_crop(raw_cell)
            raw_path, prompt_path = ATLAS, PROMPT
            raw_rect = [box[0], box[1], CELL, CELL]
        cells[view] = {'crop': crop, 'alpha_box_cell_xyxy': alpha_box, 'raw_path': raw_path,
                       'prompt_path': prompt_path, 'raw_rect_xywh': raw_rect}

    # Calibrate bottom footprint uniformly to the top plan's maximum extent.
    top_size = cells['top']['crop'].size
    bottom_size = cells['bottom']['crop'].size
    bottom_scale = min(TARGET/max(bottom_size), max(top_size)/max(bottom_size))
    # One isotropic scalar for all generated directions; preserve raw relative view extents.
    max_generated = max(max(cells[v]['crop'].size) for v in ('front','right','left','rear'))
    shared_scale = TARGET / max_generated
    scales = {'front': shared_scale, 'right': shared_scale, 'left': shared_scale, 'rear': shared_scale,
              'top': TARGET/max(top_size), 'bottom': bottom_scale}
    source_path = Path(OBJ[oid]['source']['path'])
    source_sha = sha(source_path)
    for view in VIEWS:
        data = cells[view]
        crop = data['crop']
        if view == 'rear': crop = crop.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        if view == 'left': crop = crop.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        canvas, dims, offset = fit(crop, scales[view])
        out = OUT / f'{oid}.{view}.stage1.png'
        out.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(out, optimize=False)
        base = OBJ[oid]['views'][view]
        if sha(base['path']) != base['sha256']: raise ValueError(f'base changed: {oid}.{view}')
        raw_path, prompt_path = data['raw_path'], data['prompt_path']
        sets.append({
            'object_id': oid, 'view': view,
            'candidate_path': f'candidates/equipment-dark-masonry-rail8-20261026/images/{out.name}',
            'candidate_sha256': sha(out),
            'raw_path': f'reusable/views-additional/candidates/equipment-dark-masonry-rail8-20261026/raw/{raw_path.name}',
            'raw_sha256': sha(raw_path),
            'raw_cell_rect_xywh': data['raw_rect_xywh'],
            'alpha_threshold': ALPHA_THRESHOLD,
            'alpha_bbox_cell_xyxy': data['alpha_box_cell_xyxy'],
            'prompt_path': f'reusable/views-additional/candidates/equipment-dark-masonry-rail8-20261026/raw/{prompt_path.name}',
            'prompt_sha256': sha(prompt_path),
            'source_path': f'iron-stations/components/{oid}.png', 'source_sha256': source_sha,
            'geometry_guide_path': 'reusable/views-additional/candidates/equipment-dark-masonry-rail8-20261026/raw/iron-stations-approved-same-id-geometry-guide-v2.png',
            'geometry_guide_sha256': sha(RAW/'iron-stations-approved-same-id-geometry-guide-v2.png'),
            'uniform_scale': scales[view], 'resized_dimensions': dims, 'offset_px': offset, 'anchor_px': [128,128],
            'base_path': base['path'], 'base_sha256': base['sha256'],
            'geometry_note': ('Only alpha>=64 foreground retained from square six-by-four generated atlas; low-alpha halo removed. '
                              'Bottom is a separately generated below-camera view, uniformly calibrated to top plan span. '
                              'Same-ID approved alternate-style geometry guided the view; target Dark art was repainted, hidden surfaces inferred.'),
            'provenance_method': 'generated'
        })

manifest = {'candidate_id':'equipment-dark-masonry-rail8-stations-v1','sets':sets,
            'reproducibility':{'script_path':'reusable/views-additional/candidates/equipment-dark-masonry-rail8-20261026/raw/build_iron_stations_candidates_v1.py',
             'script_sha256':sha(Path(__file__)), 'resampler':'PIL.Image.Resampling.NEAREST','canvas':[256,256],
             'anchor_px':[128,128], 'alpha_crop_threshold':ALPHA_THRESHOLD,'transparent_threshold':32,
             'note':'Candidate-only; source and live view metadata are not modified.'}}
out = CAND/'iron-stations-candidate-manifest-v1.json'
out.write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'candidate_id':manifest['candidate_id'],'sets':len(sets),'manifest_sha256':sha(out)},indent=2))
