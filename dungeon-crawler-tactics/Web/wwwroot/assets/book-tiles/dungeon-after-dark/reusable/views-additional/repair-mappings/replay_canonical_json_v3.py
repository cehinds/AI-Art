"""Restore frozen canonical JSON only after replayed PNGs pass hash checks."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path, PurePosixPath

HERE=Path(__file__).resolve().parent
OUT=HERE.parent
BOOK=OUT.parent.parent
SPEC=json.loads((HERE/'replay-canonical-json-v3.json').read_text())
# Restore explicitly retained, independently approved PNG artifact inputs after all
# raw-atlas and installed-correction replay, before validating final PNG parity.
import runpy
runpy.run_path(str(HERE/'replay_retained_approved_pngs_v1.py'))
INDEX=OUT/'set-index.json'
MAIN_INDEX=BOOK/'reusable/index.json'

def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()
def safe(root:Path,rel:str)->Path:
    p=PurePosixPath(rel)
    if p.is_absolute() or '..' in p.parts:raise ValueError(f'unsafe relative path: {rel!r}')
    q=(root/Path(*p.parts)).resolve();q.relative_to(root.resolve());return q

idx=json.loads(INDEX.read_text())
assets={a['id']:a for a in idx.get('assets',[])}
prepared=[]
if len(SPEC['metadata_entries'])!=4464 or len(assets)!=4464:
    raise ValueError('canonical replay requires exactly 4464 indexed assets and snapshots')
# Validate ALL image outputs before any metadata write, so this stage cannot hide
# a missing or mismatched PNG by restoring an old sidecar/index.
for e in SPEC['metadata_entries']:
    aid=e['asset_id'];asset=assets.get(aid)
    if asset is None:raise ValueError(f'{aid}: missing indexed asset')
    if asset['metadata_path']!=e['metadata_path'] or asset['image']['path']!=e['image_path']:
        raise ValueError(f'{aid}: rebuilt index identity/path differs from frozen canonical mapping')
    png=safe(BOOK,e['image_path'])
    if not png.is_file() or sha(png)!=e['image_sha256']:
        raise ValueError(f'{aid}: replayed PNG missing or differs from final frozen SHA')
    snap=safe(OUT,e['snapshot_path'])
    if sha(snap)!=e['sha256']:raise ValueError(f'{aid}: sidecar snapshot hash mismatch')
    doc=json.loads(snap.read_text())
    if doc.get('id')!=aid or doc.get('metadata_path')!=e['metadata_path'] or doc.get('image',{}).get('path')!=e['image_path']:
        raise ValueError(f'{aid}: sidecar snapshot identity/path mismatch')
    if doc['image'].get('sha256')!=e['image_sha256']:
        raise ValueError(f'{aid}: snapshot sidecar does not bind expected PNG hash')
    prepared.append((e,snap))
index_snapshot=safe(OUT,SPEC['set_index_snapshot'])
if sha(index_snapshot)!=SPEC['set_index_sha256']:
    raise ValueError('canonical set-index snapshot hash mismatch')
canonical_idx=json.loads(index_snapshot.read_text())
if len(canonical_idx.get('assets',[]))!=4464:
    raise ValueError('canonical set-index snapshot has unexpected asset count')
main_snapshot=safe(OUT,SPEC['main_index_snapshot'])
if sha(main_snapshot)!=SPEC['main_index_sha256']:
    raise ValueError('canonical main reusable-index snapshot hash mismatch')
canonical_main=json.loads(main_snapshot.read_text())
main_assets={a.get('id'):a for a in canonical_main.get('assets',[])}
for e,_snap in prepared:
    main_asset=main_assets.get(e['asset_id'])
    if not main_asset or main_asset.get('metadata_path')!=e['metadata_path'] or main_asset.get('image',{}).get('path')!=e['image_path'] or main_asset.get('image',{}).get('sha256')!=e['image_sha256']:
        raise ValueError(f"{e['asset_id']}: canonical main-index mirror mismatch")
# All failure-prone validation has completed. Atomically emit exact sidecar bytes.
for e,snap in prepared:
    dst=safe(BOOK,e['metadata_path']);dst.parent.mkdir(parents=True,exist_ok=True)
    tmp=dst.with_name(dst.name+'.tmp');tmp.write_bytes(snap.read_bytes());os.replace(tmp,dst)
# Catalog is emitted last so its identities and declarations align with sidecars.
tmp=INDEX.with_name(INDEX.name+'.tmp');tmp.write_bytes(index_snapshot.read_bytes());os.replace(tmp,INDEX)
tmp=MAIN_INDEX.with_name(MAIN_INDEX.name+'.tmp');tmp.write_bytes(main_snapshot.read_bytes());os.replace(tmp,MAIN_INDEX)
print(json.dumps({'recipe_id':SPEC['recipe_id'],'sidecars_replayed':len(prepared),
                  'pngs_read_and_verified':len(prepared),'set_index_sha256':sha(INDEX),
                  'main_index_sha256':sha(MAIN_INDEX),
                  'pngs_written':0},indent=2))
