#!/usr/bin/env python3
"""Refresh hash-pinned final metadata/index snapshots after global tagging.

This updates only the retained replay manifest and its archived metadata/index
snapshots. It never changes active PNGs, sidecars, or the active set-index.
Run immediately before the final post-tag baseline capture and only after the
global tag/QA metadata freeze.
"""
from pathlib import Path
import argparse, datetime, hashlib, json, shutil, struct
from PIL import Image

OUT=Path(__file__).resolve().parent
PACK=OUT.parents[1]
MANIFEST=OUT/'raw/replay-retained/replay-retained-manifest.json'
INDEX=OUT/'set-index.json'

def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()
def under(root:Path,relative:str)->Path:
    rel=Path(relative)
    if rel.is_absolute() or '..' in rel.parts:raise SystemExit(f'unsafe retained path: {relative}')
    path=(root/rel).resolve()
    try:path.relative_to(root.resolve())
    except ValueError:raise SystemExit(f'retained path escapes root: {relative}')
    return path
def rgba_sha(path:Path)->str:
    im=Image.open(path).convert('RGBA')
    return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
def dump_atomic(path:Path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
    tmp.replace(path)

ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--confirm-final-tags',action='store_true',help='confirm all global tag/QA metadata changes are frozen')
args=ap.parse_args()
if not args.confirm_final_tags:raise SystemExit('refusing to refresh release snapshots before global tag freeze')
if not MANIFEST.is_file():raise SystemExit(f'missing retained replay manifest: {MANIFEST}')
manifest=json.loads(MANIFEST.read_text());idx=json.loads(INDEX.read_text())
if manifest.get('schema_version')!=1 or manifest.get('counts',{}).get('views')!=4464:
    raise SystemExit('retained replay manifest is not the expected 4,464-view release snapshot')
old_index_sha=manifest.get('release_set_index_sha256')
if not old_index_sha:raise SystemExit('retained manifest has no prior release index hash')
prior_baseline_path=OUT/'replay-baseline.json'
if not prior_baseline_path.is_file():raise SystemExit('missing prior frozen replay baseline')
prior_baseline=json.loads(prior_baseline_path.read_text())
if prior_baseline.get('set_index_sha256')!=old_index_sha:raise SystemExit('retained manifest and prior baseline do not share the same index')
prior_leaves={(g['object_id'],v):row for g in prior_baseline['sets'] for v,row in g['views'].items()}
assetmap={a['id']:a for a in idx.get('assets',[])}
expected={(x['object_id'],x['view']):x for x in manifest.get('leaves',[])}
if len(expected)!=4464 or len(assetmap)!=4464:raise SystemExit('expected exactly 4,464 retained leaves and indexed assets')
sets={g['object_id']:g for g in idx.get('view_sets',[])}
if len(sets)!=744:raise SystemExit('expected exactly 744 indexed view sets')
seen=set();metadata_count=0
for group in idx['view_sets']:
    oid=group['object_id']
    for view,aid in group.get('views',{}).items():
        key=(oid,view);leaf=expected.get(key);asset=assetmap.get(aid)
        if not leaf or not asset or aid!=f'{oid}.{view}' or key in seen:
            raise SystemExit(f'index identity differs from retained leaf map: {key}')
        seen.add(key)
        prior=prior_leaves.get(key)
        if not prior:raise SystemExit(f'prior frozen baseline lacks leaf {key}')
        png=under(PACK,asset['image']['path'])
        meta=under(PACK,asset['metadata_path'])
        if asset.get('image',{}).get('path')!=prior.get('image_path') or asset.get('metadata_path')!=prior.get('metadata_path'):
            raise SystemExit(f'active output path changed for {key}')
        md=json.loads(meta.read_text())
        if md.get('id')!=aid or md.get('object_id')!=oid or md.get('view')!=view or md.get('image',{}).get('path')!=asset['image']['path']:
            raise SystemExit(f'sidecar identity/path mismatch for {key}')
        if asset!=md:raise SystemExit(f'index and sidecar metadata payload differ for {key}')
        image_sha=sha(png);rgba=rgba_sha(png)
        source=under(PACK,leaf['source_path'])
        if not source.is_file() or sha(source)!=leaf['source_sha256']:
            raise SystemExit(f'approved native source changed for {key}')
        if image_sha!=leaf['release_image_sha256'] or image_sha!=prior['image_sha256'] or rgba!=prior['rgba_sha256'] or ('release_rgba_sha256' in leaf and rgba!=leaf['release_rgba_sha256']):
            raise SystemExit(f'PNG bytes changed since approved review: {key}')
        if not leaf.get('replay_before_overlay_metadata_sha256'):
            raise SystemExit(f'missing proven pre-overlay metadata hash for {key}')
        if asset.get('image',{}).get('sha256')!=image_sha or md.get('image',{}).get('sha256')!=image_sha:
            raise SystemExit(f'PNG file hash descriptors are not current for {key}')
        if asset.get('image',{}).get('rgba_sha256')!=rgba or md.get('image',{}).get('rgba_sha256')!=rgba:
            raise SystemExit(f'PNG RGBA descriptors are not current for {key}')
        md_rel=asset['metadata_path'];snapsha=sha(meta)
        snapshot_rel=f"raw/replay-retained/metadata-posttag/{oid}.{view}.{snapsha}.json"
        snap=under(OUT,snapshot_rel);snap.parent.mkdir(parents=True,exist_ok=True)
        if snap.exists():
            if sha(snap)!=snapsha:raise SystemExit(f'versioned metadata snapshot collision: {snapshot_rel}')
        else:shutil.copyfile(meta,snap)
        if sha(snap)!=snapsha:raise SystemExit(f'metadata snapshot copy mismatch: {snapshot_rel}')
        leaf.update({'release_metadata_sha256':snapsha,'metadata_snapshot_path':snapshot_rel,
                     'metadata_snapshot_sha256':snapsha,'metadata_path':md_rel})
        # Keep replay_before_overlay_metadata_sha256 from the proven pre-tag
        # replay as a distinct historical precondition. New release metadata
        # is restored from the exact snapshot when that recipe output appears.
        metadata_count+=1
if len(seen)!=4464:raise SystemExit(f'only refreshed {len(seen)} of 4,464 leaves')
prior_index_snapshot=under(OUT,manifest['release_index_snapshot_path'])
if not prior_index_snapshot.is_file() or sha(prior_index_snapshot)!=manifest.get('release_index_snapshot_sha256'):
    raise SystemExit('pre-existing retained index snapshot is missing or changed; refusing to overwrite it')
index_sha=sha(INDEX);index_snapshot_rel=f"raw/replay-retained/set-index-posttag-{index_sha}.json"
index_snapshot=under(OUT,index_snapshot_rel);index_snapshot.parent.mkdir(parents=True,exist_ok=True)
if index_snapshot.exists():
    if sha(index_snapshot)!=index_sha:raise SystemExit('versioned retained index snapshot collision')
else:shutil.copyfile(INDEX,index_snapshot)
if sha(index_snapshot)!=index_sha:raise SystemExit('index snapshot copy mismatch')
manifest['release_index_snapshot_path']=index_snapshot_rel
manifest['release_set_index_sha256']=index_sha
manifest['release_index_snapshot_sha256']=index_sha
manifest['created_at_after_global_freeze']=datetime.datetime.now(datetime.timezone.utc).isoformat()
manifest.setdefault('post_tag_refresh',{}).update({'sidecar_snapshots':metadata_count,'set_index_snapshot':index_snapshot_rel,
    'set_index_sha256':index_sha,'policy':'PNG bytes are guarded unchanged; refreshed sidecar/index snapshots preserve final tags and QA metadata exactly.'})
dump_atomic(MANIFEST,manifest)
print(json.dumps({'manifest':str(MANIFEST),'manifest_sha256':sha(MANIFEST),'refreshed_sidecars':metadata_count,
                  'refreshed_index_sha256':index_sha,'pngs_verified_unchanged':4464,'active_files_changed':False},indent=2))
