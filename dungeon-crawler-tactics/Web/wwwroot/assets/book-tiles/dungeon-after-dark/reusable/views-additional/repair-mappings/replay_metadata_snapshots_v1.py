"""Restore canonical retained per-asset JSON after the offline image build."""
from pathlib import Path
import hashlib,json,os
HERE=Path(__file__).resolve().parent;OUT=HERE.parent;BOOK=OUT.parent.parent;INDEX=OUT/'set-index.json'
SPEC=json.loads((HERE/'replay_metadata_snapshots_v1.json').read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def safe(root,rel):
 p=(root/rel).resolve();p.relative_to(root.resolve());return p
idx=json.loads(INDEX.read_text());assets={a['id']:a for a in idx['assets']};prepared=[]
for e in SPEC['entries']:
 assert e['asset_id'] in assets
 snap=safe(BOOK,e['metadata_snapshot_path']);assert sha(snap)==e['final_sha256'],f"{e['asset_id']}: snapshot changed"
 asset=json.loads(snap.read_text());assert asset['id']==e['asset_id'] and asset['metadata_path']==e['metadata_path']
 dst=safe(BOOK,e['metadata_path']);cur=sha(dst) if dst.exists() else None
 assert cur in {None,e['base_sha256'],e['final_sha256']},f"{e['asset_id']}: unexpected sidecar {cur}"
 prepared.append((e,snap,dst,cur,asset))
for e,snap,dst,cur,asset in prepared:
 if cur!=e['final_sha256']:
  dst.parent.mkdir(parents=True,exist_ok=True);tmp=dst.with_name(dst.name+'.tmp');tmp.write_bytes(snap.read_bytes());os.replace(tmp,dst)
 assert sha(dst)==e['final_sha256']
 assets[e['asset_id']].clear();assets[e['asset_id']].update(asset)
tmp=INDEX.with_name(INDEX.name+'.tmp');tmp.write_text(json.dumps(idx,indent=2)+'\n');os.replace(tmp,INDEX)
print(json.dumps({'recipe_id':SPEC['recipe_id'],'sidecars_replayed':len(prepared)},indent=2))
