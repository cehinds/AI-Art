#!/usr/bin/env python3
"""Apply QA states only when an independent source+six byte proof matches replay outputs."""
from pathlib import Path
import argparse,hashlib,json,struct
from PIL import Image
OUT=Path(__file__).resolve().parent; PACK=OUT.parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--check-only',action='store_true');args=parser.parse_args()
idxp=OUT/'set-index.json';idx=json.loads(idxp.read_text())
over=json.loads((OUT/'geometry-qa-overrides.json').read_text())['objects']
proof_file=OUT/'reviewed-pass-proofs.json';proofs=json.loads(proof_file.read_text()).get('proofs',{}) if proof_file.exists() else {}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def refresh_image_descriptor(asset):
 """Keep the image descriptor bound to the PNG when writing the sidecar/index."""
 image=asset.get('image',{}); rel=image.get('path')
 if not rel: raise ValueError(f"{asset.get('id')} has no image.path")
 png=PACK/rel
 if not png.is_file(): raise FileNotFoundError(f"{asset.get('id')} image is missing: {png}")
 with Image.open(png) as opened:
  rgba=opened.convert('RGBA'); w,h=rgba.size
  image.update({'width':w,'height':h,'sha256':sha(png),'rgba_sha256':hashlib.sha256(struct.pack('>II',w,h)+rgba.tobytes()).hexdigest()})
 asset['image']=image
results=[]
for group in idx['view_sets']:
 oid=group['object_id'];state=over.get(oid,{});proof=proofs.get(oid);passed=False;reason='No current-hash independent PASS proof.'
 if proof and proof.get('status')=='pass':
  src=PACK/proof['source_path'];source_ok=src.is_file() and sha(src)==proof['source_sha256']
  refs={}
  for view,aid in group.get('views',{}).items():
   asset=next((a for a in idx['assets'] if a.get('id')==aid),None)
   refs[view]=(PACK/asset['image']['path']) if asset and asset.get('image',{}).get('path') else None
  required={'front','top','right','left','bottom','rear'}
  outputs_ok=set(refs)==required and all(p is not None and p.is_file() and sha(p)==proof['image_hashes'].get(v) for v,p in refs.items())
  if source_ok and outputs_ok:
   passed=True;reason='Current canonical source and all six replayed PNG hashes match the independent PASS proof.'
  elif not source_ok:reason='Independent PASS proof source hash does not match current canonical source.'
  else:reason='One or more replayed view PNGs differ from the independent PASS proof.'
 elif state.get('status')=='cleared':reason='Legacy cleared override lacks a current source-plus-six PASS proof; kept pending to prevent stale approval promotion.'
 status='cleared' if passed else (state.get('status') if state.get('status') not in ('cleared',None) else 'pending-review')
 group['complete']=passed and len(group.get('views',{}))==6
 group['geometry_qa']=status
 group['qa_replay_gate']={'status':'pass' if passed else 'pending-review','reason':reason,'proof_reviewed_at':proof.get('reviewed_at') if passed else None}
 if not passed:group['notes']=(group.get('notes','')+' '+reason).strip()
 for asset in idx['assets']:
  if asset.get('object_id')==oid:
   asset['geometry_qa']=status
   if not args.check_only:
    refresh_image_descriptor(asset)
    side=PACK/asset['metadata_path'];side.write_text(json.dumps(asset,indent=2)+'\n')
 results.append({'object_id':oid,'status':'pass' if passed else 'pending-review','reason':reason})
if not args.check_only:
 idxp.write_text(json.dumps(idx,indent=2)+'\n')
 (OUT/'qa-replay-results.json').write_text(json.dumps({'schema_version':1,'proof_file':proof_file.name,'results':results},indent=2)+'\n')
print(json.dumps({'sets':len(results),'proof_pass':sum(x['status']=='pass' for x in results),'pending':sum(x['status']!='pass' for x in results),'check_only':args.check_only},indent=2))
