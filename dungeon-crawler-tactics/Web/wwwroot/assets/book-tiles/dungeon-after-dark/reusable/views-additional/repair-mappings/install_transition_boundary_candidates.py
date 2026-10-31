"""Install the reviewed boundary-view remaps with exact current-byte guards."""
from pathlib import Path
import hashlib, json, os, struct
from PIL import Image

HERE = Path(__file__).resolve().parent
OUT = HERE.parent
BOOK = OUT.parent.parent
INDEX = OUT / 'set-index.json'
SPEC_PATH = OUT / 'candidates/transitions-boundary-remaps-v1/candidate.json'
SPEC = json.loads(SPEC_PATH.read_text())
VIEWS = ('front', 'top', 'right', 'left', 'bottom', 'rear')

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def safe(rel):
    p = (BOOK / rel).resolve()
    p.relative_to(BOOK.resolve())
    return p

def rgba_sha(path):
    im = Image.open(path).convert('RGBA')
    return hashlib.sha256(struct.pack('>II', *im.size) + im.tobytes()).hexdigest()

idx = json.loads(INDEX.read_text())
assets = {a['id']: a for a in idx['assets']}
sets = {s['object_id']: s for s in idx['view_sets']}
assert len(sets) == len(idx['view_sets']), 'duplicate object_id in view_sets'
prepared = []
for group in SPEC['sets']:
    oid = group['object_id']
    assert oid in sets, f'missing view_set {oid}'
    assert len(group['views']) == len({v['view'] for v in group['views']})
    for entry in group['views']:
        aid = entry['asset_id']
        assert aid in assets and aid == f"{oid}.{entry['view']}"
        a = assets[aid]
        dst = safe(a['image']['path'])
        mdst = safe(a['metadata_path'])
        candidate = (OUT / entry['candidate_path']).resolve()
        candidate.relative_to(OUT.resolve())
        assert sha(candidate) == entry['candidate_sha256'], f'{aid}: candidate hash changed'
        source = safe(entry['source_image'])
        assert sha(source) == entry['source_sha256'], f'{aid}: source hash changed'
        if 'raw_atlas' in entry:
            assert sha(safe(entry['raw_atlas'])) == entry['raw_atlas_sha256']
            assert sha(safe(entry['prompt_path'])) == entry['prompt_sha256']
        if 'source_contact_sheet' in entry:
            assert sha(safe(entry['source_contact_sheet'])) == entry['source_contact_sheet_sha256']
        expected_sidecar = hashlib.sha256((json.dumps(a, indent=2) + '\n').encode()).hexdigest()
        prepared.append((group, entry, a, dst, mdst, candidate, sha(dst), sha(mdst) if mdst.exists() else None, expected_sidecar))

# Capture exact prior outputs before any write, then fail closed if the live files
# move between preparation and installation.
snaproot = OUT / 'prebuilt/transition-boundary-snapshots-v1'
for group, entry, a, dst, mdst, candidate, before, before_meta, expected_sidecar in prepared:
    snap = snaproot / f"{entry['asset_id']}.png"
    snap.parent.mkdir(parents=True, exist_ok=True)
    if not snap.exists():
        snap.write_bytes(dst.read_bytes())
    assert sha(snap) == before, f"{entry['asset_id']}: snapshot/current bytes differ"

install_log = []
for group, entry, a, dst, mdst, candidate, before, before_meta, expected_sidecar in prepared:
    assert sha(dst) == before, f"{entry['asset_id']}: output changed during install"
    if before_meta is not None:
        assert sha(mdst) == before_meta, f"{entry['asset_id']}: sidecar changed during install"
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_name(dst.name + '.tmp')
    tmp.write_bytes(candidate.read_bytes())
    os.replace(tmp, dst)

    old_prov = a.get('provenance', {})
    hist = a.setdefault('provenance_history', [])
    marker = 'transitions-boundary-remaps-v1:' + entry['asset_id']
    if not any(h.get('candidate_id') == marker for h in hist):
        hist.append({'candidate_id': marker, 'previous_provenance': old_prov, 'previous_image_sha256': before})
    im = Image.open(dst).convert('RGBA')
    a['image']['sha256'] = sha(dst)
    a['image']['rgba_sha256'] = hashlib.sha256(struct.pack('>II', *im.size) + im.tobytes()).hexdigest()
    a['anchor_px'] = [128, 128]
    if entry['method'] == 'exact-view-alias':
        a['provenance'] = {
            'method': 'exact-symmetric-view-alias',
            'source_image': entry['source_image'],
            'source_sha256': entry['source_sha256'],
            'alias_from_asset_id': entry['alias_from_asset_id'],
            'alias_reason': entry['alias_reason'],
            'retained_alias_png': entry['retained_alias_png'],
            'retained_before_png': 'reusable/views-additional/prebuilt/transition-boundary-snapshots-v1/' + entry['asset_id'] + '.png',
            'normalization': {'frame_size': list(im.size), 'anchor_px': [128, 128], 'distortion': 'none; exact pixel alias'}
        }
    else:
        provenance = {
            'method': 'source-guided-orthographic-boundary-repair',
            'source_image': entry['source_image'],
            'source_sha256': entry['source_sha256'],
            'retained_before_png': 'reusable/views-additional/prebuilt/transition-boundary-snapshots-v1/' + entry['asset_id'] + '.png',
            'normalization': {
                'scale': entry['uniform_scale'], 'offset_px': [0, 0],
                'resampling': 'nearest', 'frame_size': list(im.size), 'anchor_px': [128, 128],
                'distortion': 'none; uniform aspect-preserving normalization'
            },
            'notes': 'Illustrative orthographic art; hidden surfaces are inferred, not recovered from source pixels.'
        }
        for key in ('raw_atlas', 'raw_atlas_sha256', 'prompt_path', 'prompt_sha256', 'source_contact_sheet', 'source_contact_sheet_sha256', 'source_rect', 'transform', 'alias_from_asset_id', 'alias_reason'):
            if key in entry:
                provenance[key] = entry[key]
        a['provenance'] = provenance
    mdst.parent.mkdir(parents=True, exist_ok=True)
    tmp = mdst.with_name(mdst.name + '.tmp')
    tmp.write_text(json.dumps(a, indent=2) + '\n')
    os.replace(tmp, mdst)
    install_log.append({'asset_id': entry['asset_id'], 'before_sha256': before, 'after_sha256': sha(dst), 'metadata_path': str(mdst.relative_to(BOOK))})

for group in SPEC['sets']:
    sets[group['object_id']]['complete'] = False
    sets[group['object_id']]['notes'] = 'Boundary placement repair installed; awaiting current-hash source-plus-six review.'

tmp = INDEX.with_name(INDEX.name + '.tmp')
tmp.write_text(json.dumps(idx, indent=2) + '\n')
os.replace(tmp, INDEX)
log = {'candidate_id': SPEC['candidate_id'], 'installed': install_log, 'sets_pending_review': [g['object_id'] for g in SPEC['sets']]}
(OUT / 'repair-mappings/install-transition-boundary-remaps-v1.json').write_text(json.dumps(log, indent=2) + '\n')
print(json.dumps({'installed': len(install_log), 'sets_pending_review': log['sets_pending_review']}, indent=2))
