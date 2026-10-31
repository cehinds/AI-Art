"""Replay the exact canonical asset sidecars and catalog after image output."""
from pathlib import Path
import hashlib,json

HERE=Path(__file__).resolve().parent;OUT=HERE.parent;BOOK=OUT.parent.parent
SPEC=json.loads((HERE/'replay-canonical-json-v2.json').read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def safe(root,rel):
 p=(root/rel).resolve();p.relative_to(root.resolve());return p
prepared=[]
for e in SPEC['metadata_entries']:
 snap=safe(OUT,e['snapshot_path']);assert sha(snap)==e['sha256'],f"{e['asset_id']}: retained sidecar changed"
 asset=json.loads(snap.read_text());assert asset['id']==e['asset_id'] and asset['metadata_path']==e['metadata_path']
 dst=safe(BOOK,e['metadata_path']);current=sha(dst) if dst.exists() else None
 if current != e['sha256']:
  raise RuntimeError(
   f"{e['asset_id']}: canonical sidecar snapshot is stale for the current build; "
   f"refusing to replace {current} with {e['sha256']}. Refresh only at final freeze."
  )
 prepared.append(e['asset_id'])
index_snapshot=safe(OUT,SPEC['set_index_snapshot']);assert sha(index_snapshot)==SPEC['set_index_sha256']
index=OUT/'set-index.json'
current_index_sha256=sha(index) if index.exists() else None
if current_index_sha256 != SPEC['set_index_sha256']:
 raise RuntimeError(
  'canonical catalog snapshot is stale for the current build; refusing to replace '
  f'{current_index_sha256} with {SPEC["set_index_sha256"]}. Refresh this snapshot only '
  'at final freeze, after all generation and repair recipes have been integrated.'
 )
assert sha(index)==SPEC['set_index_sha256']
print(json.dumps({'recipe_id':SPEC['recipe_id'],'sidecars_verified':len(prepared),'set_index_sha256':sha(index)},indent=2))
