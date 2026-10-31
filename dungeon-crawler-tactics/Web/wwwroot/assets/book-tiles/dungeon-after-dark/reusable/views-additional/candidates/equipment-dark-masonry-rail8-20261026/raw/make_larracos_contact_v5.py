import hashlib, json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/dungeon-after-dark')
CAND = ROOT / 'reusable/views-additional/candidates/equipment-dark-masonry-rail8-20261026'
HAND = json.loads(Path('/workspace/scratch/equipment-dark-masonry-rail8-handoff-20261026.json').read_text())
manifest_path = CAND / 'larracos-candidate-manifest-v5.json'
manifest = json.loads(manifest_path.read_text())
sets = {(x['object_id'], x['view']): x for x in manifest['sets']}
ids = ['faction-larracos-ancient-city-masonry-outer-corner', 'faction-larracos-ancient-city-masonry-inner-corner']
views = ['front', 'top', 'right', 'left', 'bottom', 'rear']
tile_w, tile_h, pad = 180, 175, 26
cols = 13
canvas = Image.new('RGB', (cols * tile_w, len(ids) * (tile_h + 28) + pad), 'white')
draw = ImageDraw.Draw(canvas)
labels = ['SOURCE'] + [f'BASE {v.upper()}' for v in views] + [f'CAND {v.upper()}' for v in views]
for col, label in enumerate(labels):
    draw.text((col * tile_w + 4, 4), label, fill='black')

proof = {'candidate_id': manifest['candidate_id'], 'manifest_path': str(manifest_path),
         'manifest_sha256': hashlib.sha256(manifest_path.read_bytes()).hexdigest(), 'contact': None, 'objects': []}
for row, oid in enumerate(ids):
    obj = next(x for x in HAND['objects'] if x['object_id'] == oid)
    source_path = Path(obj['source']['path'])
    rowproof = {'object_id': oid, 'source': {'path': str(source_path), 'sha256': hashlib.sha256(source_path.read_bytes()).hexdigest()},
                'base': {}, 'candidates': {}}
    proof['objects'].append(rowproof)
    files = [source_path]
    for v in views:
        base_rel = sets[(oid, v)]['base_path']
        files.append(ROOT / base_rel)
    for v in views:
        files.append(CAND / 'images' / Path(sets[(oid, v)]['candidate_path']).name)
    for col, path in enumerate(files):
        img = Image.open(path).convert('RGBA')
        checker = Image.new('RGBA', (tile_w - 8, tile_h - 8), (235, 235, 235, 255))
        d = ImageDraw.Draw(checker)
        for y in range(0, tile_h - 8, 10):
            for x in range(0, tile_w - 8, 10):
                if (x // 10 + y // 10) % 2:
                    d.rectangle((x, y, x + 9, y + 9), fill=(210, 210, 210, 255))
        img.thumbnail((tile_w - 16, tile_h - 16), Image.Resampling.NEAREST)
        checker.alpha_composite(img, ((checker.width - img.width) // 2, (checker.height - img.height) // 2))
        x, y = col * tile_w + 4, row * (tile_h + 28) + pad
        canvas.paste(checker.convert('RGB'), (x, y))
        file_sha = hashlib.sha256(path.read_bytes()).hexdigest()
        if col == 0:
            continue
        key = views[(col - 1) % 6]
        (rowproof['base'] if col <= 6 else rowproof['candidates'])[key] = {'path': str(path), 'sha256': file_sha}
    draw.text((4, row * (tile_h + 28) + pad + tile_h), oid, fill='black')

contact = CAND / 'larracos-source-base-candidate-contact-v5.png'
canvas.save(contact)
proof['contact'] = {'path': str(contact), 'sha256': hashlib.sha256(contact.read_bytes()).hexdigest()}
proof_path = CAND / 'larracos-contact-proof-v5.json'
proof_path.write_text(json.dumps(proof, indent=2) + '\n')
print(json.dumps({'contact': str(contact), 'contact_sha256': hashlib.sha256(contact.read_bytes()).hexdigest(),
                  'proof': str(proof_path), 'proof_sha256': hashlib.sha256(proof_path.read_bytes()).hexdigest(),
                  'manifest_sha256': proof['manifest_sha256']}, indent=2))
