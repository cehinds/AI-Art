from pathlib import Path
import hashlib, json
from PIL import Image

ROOT = Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/dungeon-after-dark')
RV = ROOT / 'reusable/views-additional'
CAND = RV / 'candidates/equipment-dark-masonry-rail8-20261026'
RAW, OUT = CAND / 'raw', CAND / 'images'
HAND = json.loads(Path('/workspace/scratch/equipment-dark-masonry-rail8-handoff-20261026.json').read_text())
OBJECTS = {x['object_id']: x for x in HAND['objects']}
IDS = ['faction-larracos-ancient-city-masonry-outer-corner', 'faction-larracos-ancient-city-masonry-inner-corner']
THRESHOLD = 64
TARGET = 186

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def crop_alpha(image, box, threshold):
    region = image.convert('RGBA').crop(box)
    mask = region.getchannel('A').point(lambda a: 255 if a >= threshold else 0)
    bounds = mask.getbbox()
    if bounds is None:
        raise ValueError(f'no alpha >= {threshold} in {box}')
    # Use the threshold only to identify the opaque foreground extent; retain
    # original antialiasing inside that exact rectangle.
    return region.crop(bounds), [box[0] + bounds[0], box[1] + bounds[1], box[0] + bounds[2], box[1] + bounds[3]]

def fit(image, mirror=False):
    if mirror:
        image = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    w, h = image.size
    scale = TARGET / max(w, h)
    nw, nh = max(1, round(w * scale)), max(1, round(h * scale))
    resized = image.resize((nw, nh), Image.Resampling.NEAREST)
    canvas = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
    offset = ((256 - nw) // 2, (256 - nh) // 2)
    canvas.alpha_composite(resized, offset)
    return canvas, scale, [nw, nh], list(offset)

bottom_atlas_path = RAW / 'larracos-bottoms-atlas-v3.png'
bottom_atlas = Image.open(bottom_atlas_path).convert('RGBA')
bottom_prompt = RAW / 'larracos-bottoms-request-v3.json'
sets = []
for row, oid in enumerate(IDS):
    source_rel = f'faction-larracos/components/{oid}.png'
    source_path = ROOT / source_rel
    source = Image.open(source_path).convert('RGBA')
    source_crop, source_box = crop_alpha(source, (0, 0, source.width, source.height), 1)

    elevation_path = RAW / f'{oid}-front-v5.png'
    request_path = RAW / f'{oid}-front-request-v5.json'
    if not elevation_path.is_file() or not request_path.is_file():
        raise FileNotFoundError(f'missing bound raw/request: {elevation_path}, {request_path}')
    elevation = Image.open(elevation_path).convert('RGBA')
    # Alpha 64 isolates the continuous painted masonry face and its attached
    # ornaments while rejecting low-alpha atlas debris. The face is shallow by
    # design; preserve its aspect ratio rather than stretching to an older Z.
    elevation_crop, elevation_box = crop_alpha(elevation, (0, 0, elevation.width, elevation.height), THRESHOLD)

    row_height = bottom_atlas.height // 2
    bottom_box = (0, row * row_height, bottom_atlas.width, (row + 1) * row_height)
    bottom_crop, bottom_source_box = crop_alpha(bottom_atlas, bottom_box, THRESHOLD)

    view_data = {
        'front': (elevation_crop, elevation_path, request_path, elevation_box, False,
                  'Generated broad masonry face, isotropically fitted from alpha>=64 foreground. The deliberately shallow shared elevation is inferred; it is not metrically recovered.'),
        'rear': (elevation_crop, elevation_path, request_path, elevation_box, True,
                 'Rigid horizontal reflection of the generated broad masonry face; unmarked reverse inferred by same-kit symmetry.'),
        'right': (elevation_crop, elevation_path, request_path, elevation_box, False,
                 'Generated broad masonry face applied to the perpendicular L-arm elevation by inferred same-kit symmetry.'),
        'left': (elevation_crop, elevation_path, request_path, elevation_box, True,
                 'Rigid horizontal reflection of the generated broad masonry face applied to the perpendicular L-arm elevation by inferred same-kit symmetry.'),
        'top': (source_crop, source_path, None, source_box, False,
                'Native source plan uniformly normalized; source pixels retained.'),
        'bottom': (bottom_crop, bottom_atlas_path, bottom_prompt, bottom_source_box, False,
                  'Generated underside atlas row, extracted with its own alpha>=64 bounds; hidden underside inferred.'),
    }

    obj = OBJECTS[oid]
    for view, (crop, raw_path, prompt_path, crop_box, mirror, note) in view_data.items():
        output, scale, dims, offset = fit(crop, mirror=mirror)
        out_path = OUT / f'{oid}.{view}.v5.png'
        out_path.parent.mkdir(parents=True, exist_ok=True)
        output.save(out_path, optimize=False)

        base_rel = f'reusable/views-additional/images/{oid}.{view}.png'
        expected_base_sha = obj['views'][view]['sha256']
        if sha(ROOT / base_rel) != expected_base_sha:
            raise RuntimeError(f'base changed since handoff: {oid}.{view}')

        raw_rel = source_rel if view == 'top' else f'reusable/views-additional/candidates/equipment-dark-masonry-rail8-20261026/raw/{raw_path.name}'
        prompt_rel = (f'reusable/views-additional/candidates/equipment-dark-masonry-rail8-20261026/raw/{prompt_path.name}'
                      if prompt_path else None)
        sets.append({
            'object_id': oid,
            'view': view,
            'candidate_path': f'candidates/equipment-dark-masonry-rail8-20261026/images/{out_path.name}',
            'candidate_sha256': sha(out_path),
            'raw_path': raw_rel,
            'raw_sha256': sha(raw_path),
            'prompt_path': prompt_rel,
            'prompt_sha256': sha(prompt_path) if prompt_path else None,
            'crop_alpha_threshold': 1 if view == 'top' else THRESHOLD,
            'crop_bbox_xyxy': crop_box,
            'uniform_scale': scale,
            'resized_dimensions': dims,
            'offset_px': offset,
            'anchor_px': [128, 128],
            'base_path': base_rel,
            'base_sha256': expected_base_sha,
            'source_path': source_rel,
            'source_sha256': sha(source_path),
            'geometry_note': note,
            'provenance_method': 'source-derived' if view == 'top' else 'generated',
        })

manifest = {
    'candidate_id': 'equipment-dark-masonry-rail8-larracos-v5',
    'sets': sets,
    'reproducibility': {
        'script_path': 'reusable/views-additional/candidates/equipment-dark-masonry-rail8-20261026/raw/build_larracos_candidates_v5.py',
        'script_sha256': sha(Path(__file__)),
        'resampler': 'PIL.Image.Resampling.NEAREST',
        'canvas': [256, 256],
        'anchor_px': [128, 128],
        'generated_elevation_alpha_threshold': THRESHOLD,
        'bottom_atlas_row_crop_alpha_threshold': THRESHOLD,
        'bottom_bbox_is_view_specific': True,
        'note': 'All candidates are staging only; no production files were written.'
    }
}
manifest_path = CAND / 'larracos-candidate-manifest-v5.json'
manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps({'candidate_id': manifest['candidate_id'], 'sets': len(sets), 'manifest_sha256': sha(manifest_path),
                  'elevations': {x['object_id']: {y: {'crop': x['crop_bbox_xyxy'], 'size': x['resized_dimensions'], 'scale': x['uniform_scale']}
                                                  for y in ('front', 'rear', 'right', 'left')
                                                  for x in sets if x['object_id'] == x['object_id'] and x['view'] == y}
                                 for x in sets if x['view'] == 'front'}}, indent=2))
