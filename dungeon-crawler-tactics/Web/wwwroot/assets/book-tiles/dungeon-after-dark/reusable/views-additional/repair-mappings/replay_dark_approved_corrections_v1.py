"""Replay Root-approved Dark scoped corrections from retained pack-local rasters."""
from pathlib import Path, PurePosixPath
import hashlib, json, os
HERE=Path(__file__).resolve().parent
OUT=HERE.parent
BOOK=OUT.parent.parent
SPEC_PATH=HERE/'dark-approved-corrections-replay-v1.json'
SPEC=json.loads(SPEC_PATH.read_text())
INDEX=OUT/'set-index.json'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def safe(root,rel):
 p=PurePosixPath(rel)
 if p.is_absolute() or '..' in p.parts: raise ValueError(f'unsafe path: {rel}')
 q=(root/Path(*p.parts)).resolve();q.relative_to(root.resolve());return q
idx=json.loads(INDEX.read_text());assets={a['id']:a for a in idx['assets']};sets={s['object_id']:s for s in idx.get('view_sets',[])}
prepared=[]
# Validate every dependency and active output before the first write.
for e in SPEC['entries']:
 aid=e['asset_id'];a=assets.get(aid)
 if not a: raise ValueError(f'{aid}: missing set-index asset')
 if a.get('metadata_path')!=e['metadata_path'] or a.get('image',{}).get('path')!=e['image_path']:
  raise ValueError(f'{aid}: rebuilt asset path differs from replay binding')
 candidate=safe(BOOK,e['candidate_path'])
 if sha(candidate)!=e['candidate_sha256']: raise ValueError(f'{aid}: retained candidate hash mismatch')
 manifest=safe(BOOK,e['candidate_manifest_path'])
 if sha(manifest)!=e['candidate_manifest_sha256']: raise ValueError(f'{aid}: candidate manifest hash mismatch')
 if e.get('request_path') and sha(safe(BOOK,e['request_path']))!=e['request_sha256']: raise ValueError(f'{aid}: request hash mismatch')
 if e.get('raw_input_path') and sha(safe(BOOK,e['raw_input_path']))!=e['raw_input_sha256']: raise ValueError(f'{aid}: raw copy hash mismatch')
 source=safe(BOOK,e['source_path'])
 if sha(source)!=e['source_sha256']: raise ValueError(f'{aid}: canonical target source hash mismatch')
 snapshot=safe(BOOK,e['metadata_snapshot_path'])
 if sha(snapshot)!=e['metadata_snapshot_sha256']: raise ValueError(f'{aid}: sidecar snapshot hash mismatch')
 doc=json.loads(snapshot.read_text())
 if doc.get('id')!=aid or doc.get('metadata_path')!=e['metadata_path'] or doc.get('image',{}).get('path')!=e['image_path'] or doc.get('image',{}).get('sha256')!=e['candidate_sha256']:
  raise ValueError(f'{aid}: sidecar snapshot identity/content mismatch')
 # This helper runs only after the build produced a base image. It never fills a missing output.
 output=safe(BOOK,e['image_path'])
 if not output.is_file(): raise FileNotFoundError(f'{aid}: base builder did not produce output')
 current=sha(output)
 if current not in {e['base_sha256'],e['candidate_sha256']}:
  raise ValueError(f'{aid}: unexpected active output hash {current}')
 metadata=safe(BOOK,e['metadata_path'])
 prepared.append((e,candidate,snapshot,output,metadata,current))
# All dependencies are hash-checked; now copy retained raster inputs and restore matching metadata.
for e,candidate,snapshot,output,metadata,current in prepared:
 if current!=e['candidate_sha256']:
  tmp=output.with_name(output.name+'.tmp');tmp.write_bytes(candidate.read_bytes());os.replace(tmp,output)
 assert sha(output)==e['candidate_sha256']
 tmp=metadata.with_name(metadata.name+'.tmp');tmp.write_bytes(snapshot.read_bytes());os.replace(tmp,metadata)
# Keep current, reviewed symmetry declarations additive and explicit.
for oid,groups in SPEC.get('symmetry_overrides',{}).items():
 s=sets.get(oid)
 if s is None: raise ValueError(f'{oid}: missing set declaration')
 s['symmetry']=groups
 s['complete']=False
# Write set-index only; final canonical main/index snapshot is an explicit later stage.
tmp=INDEX.with_name(INDEX.name+'.tmp');tmp.write_text(json.dumps(idx,indent=2,ensure_ascii=False)+'\n');os.replace(tmp,INDEX)
print(json.dumps({'recipe_id':SPEC['recipe_id'],'outputs_replayed':len(prepared),'outputs_written':sum(1 for e,*rest in prepared if rest[-1]!=e['candidate_sha256']),'missing_outputs_restored':0,'set_index_sha256':sha(INDEX)},indent=2))
