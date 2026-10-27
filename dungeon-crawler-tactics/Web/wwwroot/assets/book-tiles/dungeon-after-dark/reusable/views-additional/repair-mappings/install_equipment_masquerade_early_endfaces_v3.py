"""Install Page-approved Masquerade/Early stair end faces with exact hash guards."""
from pathlib import Path
import copy, hashlib, json, os, struct
from PIL import Image

HERE = Path(__file__).resolve().parent
OUT = HERE.parent
BOOK = OUT.parent.parent
INDEX = OUT / 'set-index.json'
RECIPE = HERE / 'replay-installed-dark-repairs-v2.json'
CANDDIR = OUT / 'candidates/equipment-dark-stairs-successor-20261026'
GUARD = CANDDIR / 'masquerade-early-endfaces-v4-install-guard.json'
MANIFEST = CANDDIR / 'masquerade-early-endfaces-v3-candidate.json'
REVIEW = Path('/workspace/scratch/page-equipment-masquerade-early-endfaces-v3-review.json')
REVIEW_LOCAL = OUT / 'qa/page-equipment-masquerade-early-endfaces-v3-review.json'
PROMPTDIR = OUT / 'prompts/equipment-masquerade-early-endfaces-20261026'
BEFORE = OUT / 'prebuilt/equipment-masquerade-early-endfaces-v3-before'
BATCH = 'equipment-masquerade-early-endfaces-v3'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def rgba_sha(path):
    im = Image.open(path).convert('RGBA')
    return hashlib.sha256(struct.pack('>II', *im.size) + im.tobytes()).hexdigest()

def safe(root, rel):
    path = (root / rel).resolve()
    path.relative_to(root.resolve())
    return path

def atomic(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    tmp.write_bytes(data if isinstance(data, bytes) else data.encode())
    os.replace(tmp, path)

def main():
    guard = json.loads(GUARD.read_text())
    review = json.loads(REVIEW.read_text())
    assert sha(MANIFEST) == guard['previous_manifest']['sha256'] == review['manifest_sha256']
    assert review['source_all_six_base_candidate_hashes_verified']
    assert guard['batch'] == 'equipment-dark-stairs-endfaces-v4-install-guard'
    accepted = {(d['object_id'], d['view']): d['candidate_sha256']
                for d in review['decisions'] if d['status'] == 'candidate-direction-accepted'}
    rows = {(a['object_id'], a['view']): a for a in guard['assets']}
    assert len(accepted) == 8 and set(accepted) == set(rows)
    assert all(v in ('front', 'rear') for _, v in accepted)
    if REVIEW_LOCAL.exists():
        assert sha(REVIEW_LOCAL) == sha(REVIEW)
    else:
        atomic(REVIEW_LOCAL, REVIEW.read_bytes())

    idx = json.loads(INDEX.read_text())
    recipe = json.loads(RECIPE.read_text())
    assets = {a['id']: copy.deepcopy(a) for a in idx['assets']}
    sets = {s['object_id']: copy.deepcopy(s) for s in idx['view_sets']}
    entries = recipe['entries']
    entrymap = {e['asset_id']: e for e in entries}
    prepared = []

    for (oid, view), candidate_sha in sorted(accepted.items()):
        row = rows[(oid, view)]
        aid = f'{oid}.{view}'
        assert row['asset_id'] == aid and row['sha256'] == candidate_sha
        binding = guard['source_bindings'][oid]
        source = safe(BOOK, binding['source']['path'])
        assert sha(source) == binding['source']['sha256'] == row['provenance']['source_sha256']
        for direction, base in binding['base_views'].items():
            assert sha(safe(BOOK, base['path'])) == base['sha256'], f'{aid}: {direction} base changed'
        candidate = safe(CANDDIR, row['candidate_path'])
        assert sha(candidate) == candidate_sha

        asset = assets[aid]
        dst = safe(BOOK, asset['image']['path'])
        metadata = safe(BOOK, asset['metadata_path'])
        base_sha = binding['base_views'][view]['sha256']
        assert sha(dst) in (base_sha, candidate_sha), f'{aid}: live PNG changed since reviewed base'
        old = json.loads(metadata.read_text())
        assert old['image']['sha256'] == base_sha

        prov = row['provenance']
        raw_rel = prov['generated_atlas_path']
        request_rel = prov['generation_request_path']
        raw = safe(BOOK, raw_rel)
        request = safe(BOOK, request_rel)
        assert sha(raw) == prov['generated_atlas_sha256']
        assert sha(request) == prov['generation_request_sha256']
        req = json.loads(request.read_text())
        prompt = req['prompt_text']
        prompt_sha = hashlib.sha256(prompt.encode()).hexdigest()
        assert prompt_sha == prov['prompt_sha256'] == req['prompt_sha256']
        prompt_path = PROMPTDIR / f"{req['request_id']}.txt"
        if prompt_path.exists():
            assert prompt_path.read_text() == prompt
        else:
            atomic(prompt_path, prompt)

        new = copy.deepcopy(old)
        im = Image.open(candidate).convert('RGBA')
        new['image'].update(width=im.width, height=im.height,
                            sha256=candidate_sha, rgba_sha256=rgba_sha(candidate))
        new.setdefault('provenance_history', []).append({
            'candidate_id': f'{BATCH}:{aid}',
            'previous_provenance': copy.deepcopy(old.get('provenance', {})),
            'previous_image_sha256': base_sha,
        })
        source_rel = binding['source']['path']
        provenance = {
            'method': 'source-guided-imagegen-stair-endface-correction',
            'source_image': source_rel,
            'source_sha256': binding['source']['sha256'],
            'candidate_image': f"reusable/views-additional/candidates/equipment-dark-stairs-successor-20261026/{row['candidate_path']}",
            'candidate_image_sha256': candidate_sha,
            'candidate_manifest': 'reusable/views-additional/candidates/equipment-dark-stairs-successor-20261026/masquerade-early-endfaces-v3-candidate.json',
            'candidate_manifest_sha256': sha(MANIFEST),
            'install_guard': 'reusable/views-additional/candidates/equipment-dark-stairs-successor-20261026/masquerade-early-endfaces-v4-install-guard.json',
            'install_guard_sha256': sha(GUARD),
            'candidate_review_record': 'reusable/views-additional/qa/page-equipment-masquerade-early-endfaces-v3-review.json',
            'candidate_review_sha256': sha(REVIEW_LOCAL),
            'raw_atlas': raw_rel,
            'raw_atlas_sha256': prov['generated_atlas_sha256'],
            'request_path': request_rel,
            'request_sha256': prov['generation_request_sha256'],
            'request_id': req['request_id'],
            'prompt_path': f'reusable/views-additional/prompts/equipment-masquerade-early-endfaces-20261026/{prompt_path.name}',
            'prompt_sha256': prompt_sha,
            'normalization': copy.deepcopy(row['normalization']),
            'notes': prov.get('notes', '') + ' Hidden construction is inferred, not recovered source pixels.',
        }
        for key in ('source_image', 'candidate_image', 'candidate_manifest', 'install_guard',
                    'candidate_review_record', 'raw_atlas', 'request_path', 'prompt_path'):
            assert not provenance[key].startswith('/'), (aid, key, provenance[key])
            assert safe(BOOK, provenance[key]).is_file(), (aid, key, provenance[key])
        new['provenance'] = provenance
        metadata_bytes = (json.dumps(new, indent=2) + '\n').encode()
        metadata_sha = hashlib.sha256(metadata_bytes).hexdigest()
        snapshot = f'reusable/views-additional/prebuilt/replay-sidecars-final-v1/{aid}.json'
        entry = {
            'asset_id': aid,
            'image_path': new['image']['path'],
            'candidate_path': str(candidate.relative_to(OUT)),
            'candidate_sha256': candidate_sha,
            'base_sha256': base_sha,
            'final_sha256': candidate_sha,
            'metadata_path': new['metadata_path'],
            'metadata_snapshot_path': snapshot,
            'metadata_sha256': metadata_sha,
            'live_before_install_sha256': base_sha,
            'superseded_installed_sha256': base_sha,
            'review_record': provenance['candidate_review_record'],
            'candidate_manifest_sha256': sha(MANIFEST),
        }
        prior = entrymap.get(aid)
        if prior:
            # F/REAR have no prior approved replay entries; reject unexpected overlap.
            assert prior['final_sha256'] == base_sha, f'{aid}: unexpected prior replay target'
            entries[entries.index(prior)] = entry
        else:
            entries.append(entry)
        entrymap[aid] = entry
        prepared.append((aid, oid, dst, metadata, candidate, base_sha, candidate_sha,
                         new, metadata_bytes, metadata_sha, snapshot, entry))

    # Prepare immutable bases and sidecar snapshots before changing any live leaf.
    for aid, oid, dst, metadata, candidate, base_sha, candidate_sha, new, metadata_bytes, metadata_sha, snapshot, entry in prepared:
        before_png = BEFORE / f'{aid}.png'
        before_json = BEFORE / f'{aid}.json'
        if before_png.exists():
            assert sha(before_png) == base_sha
        else:
            atomic(before_png, dst.read_bytes())
        if before_json.exists():
            assert json.loads(before_json.read_text())['image']['sha256'] == base_sha
        else:
            atomic(before_json, metadata.read_bytes())
        snapshot_path = safe(BOOK, snapshot)
        if snapshot_path.exists():
            assert sha(snapshot_path) == metadata_sha, f'{aid}: stale snapshot conflict'
        else:
            atomic(snapshot_path, metadata_bytes)

    for aid, oid, dst, metadata, candidate, base_sha, candidate_sha, new, metadata_bytes, metadata_sha, snapshot, entry in prepared:
        if sha(dst) == base_sha:
            atomic(dst, candidate.read_bytes())
        assert sha(dst) == candidate_sha
        if sha(metadata) != metadata_sha:
            atomic(metadata, metadata_bytes)
        assert sha(metadata) == metadata_sha
        assets[aid] = copy.deepcopy(new)

    for oid in {row[1] for row in prepared}:
        sets[oid]['complete'] = False
        sets[oid]['notes'] = 'Page-approved end-face candidates installed; waiting for live current source-plus-six review.'
    new_index = copy.deepcopy(idx)
    new_index['assets'] = [copy.deepcopy(assets[a['id']]) for a in idx['assets']]
    new_index['view_sets'] = [copy.deepcopy(sets[s['object_id']]) for s in idx['view_sets']]
    assert len({a['id'] for a in new_index['assets']}) == len(new_index['assets'])
    assert len({s['object_id'] for s in new_index['view_sets']}) == len(new_index['view_sets'])
    atomic(RECIPE, json.dumps(recipe, indent=2) + '\n')
    atomic(INDEX, json.dumps(new_index, indent=2) + '\n')
    print(json.dumps({'installed': [row[0] for row in prepared],
                      'index_sha256': sha(INDEX), 'recipe_entries': len(entries)}, indent=2))

if __name__ == '__main__':
    main()
