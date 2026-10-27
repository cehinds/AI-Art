"""Losslessly replay retained correct stage-floor front/rear PNGs after atlas normalization."""
from pathlib import Path
import hashlib,json,os
HERE=Path(__file__).resolve().parent;OUT=HERE.parent;BOOK=OUT.parent.parent
SPEC=json.loads((HERE/'replay-snapshot-directions-2026-10-26.json').read_text());INDEX=OUT/'set-index.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def safe(root,rel):
 p=(root/rel).resolve();p.relative_to(root.resolve());return p
idx=json.loads(INDEX.read_text());assets={a['id']:a for a in idx['assets']};prepared=[]
for row in SPEC['directions']:
 a=assets[row['asset_id']];dst=safe(BOOK,a['image']['path']);mdst=safe(BOOK,a['metadata_path']);png=safe(BOOK,row['snapshot_png']);meta=safe(BOOK,row['snapshot_json']);src=safe(BOOK,row['source_image'])
 assert sha(src)==row['source_sha256'],f"{row['asset_id']}: source changed"
 assert sha(png)==row['png_sha256'] and sha(meta)==row['metadata_sha256'],f"{row['asset_id']}: retained input changed"
 current=sha(dst) if dst.exists() else None;assert current in {None,row['before_sha256'],row.get('stale_replay_sha256')},f"{row['asset_id']}: unexpected destination {current}"
 current_meta=sha(mdst) if mdst.exists() else None;assert current_meta in {None,row['metadata_sha256'],row['before_metadata_sha256'],row.get('stale_replay_metadata_sha256')},f"{row['asset_id']}: unexpected sidecar {current_meta}"
 snap=json.loads(meta.read_text());assert snap['id']==row['asset_id'] and snap['source']['source_sha256']==row['source_sha256']
 prepared.append((row,dst,mdst,png,meta))
# All guards are checked before any image or metadata is replaced.
for row,dst,mdst,png,meta in prepared:
 if not dst.exists() or sha(dst)!=row['png_sha256']:
  tmp=dst.with_suffix('.png.tmp');tmp.write_bytes(png.read_bytes());os.replace(tmp,dst)
 if not mdst.exists() or sha(mdst)!=row['metadata_sha256']:
  tmp=mdst.with_suffix('.json.tmp');tmp.write_bytes(meta.read_bytes());os.replace(tmp,mdst)
 snap=json.loads(meta.read_text());a=assets[row['asset_id']];a.clear();a.update(snap);a['image']['sha256']=row['png_sha256'];a['metadata_path']=str(mdst.relative_to(BOOK));a['image']['rgba_sha256']=snap['image']['rgba_sha256']
for oid in SPEC['sets_pending_independent_review']:
 ss=[s for s in idx['view_sets'] if s['object_id']==oid];assert len(ss)==1,f'{oid}: duplicate view-set object id';ss[0]['notes']='Correct thin floor profiles replayed as exact retained PNG+sidecar bytes; current review status is preserved.'
tmp=INDEX.with_suffix('.json.tmp');tmp.write_text(json.dumps(idx,indent=2)+'\n');os.replace(tmp,INDEX)
print(json.dumps({'restored_exact_directions':len(prepared),'sets_pending':len(SPEC['sets_pending_independent_review'])},indent=2))
