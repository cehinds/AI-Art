"""Guarded installer/replay for source-guided west-wall candidate batch 03."""
from pathlib import Path
import hashlib,json,os,struct
from PIL import Image
HERE=Path(__file__).resolve().parent;OUT=HERE.parent;BOOK=OUT.parent.parent;SPEC=json.loads((HERE/'install-westwalls-03.json').read_text());INDEX=OUT/'set-index.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
idx=json.loads(INDEX.read_text());assets={a['id']:a for a in idx['assets']}
for oid,spec in SPEC['sets'].items():
 assert sha(BOOK/spec['source_image'])==spec['source_sha256'],f'{oid}: source changed'
 assert len([s for s in idx['view_sets'] if s['object_id']==oid])==1,f'{oid}: duplicate view-set object_id'
 for view,item in spec['views'].items():
  asset=assets[item['asset_id']];out=BOOK/asset['image']['path'];cand=OUT/item['candidate_path'];cur=sha(out)
  assert cur in {item['before_sha256'],item['after_sha256']},f"{item['asset_id']}: unexpected live hash {cur}"
  assert sha(cand)==item['after_sha256'],f"{item['asset_id']}: candidate input changed"
for oid,spec in SPEC['sets'].items():
 for view,item in spec['views'].items():
  asset=assets[item['asset_id']];out=BOOK/asset['image']['path'];cand=OUT/item['candidate_path']
  if sha(out)!=item['after_sha256']:
   tmp=out.with_suffix('.png.tmp');tmp.write_bytes(cand.read_bytes());os.replace(tmp,out)
  im=Image.open(out).convert('RGBA');asset['image']['sha256']=sha(out);asset['image']['rgba_sha256']=hashlib.sha256(struct.pack('>II',im.width,im.height)+im.tobytes()).hexdigest()
  marker=f"{SPEC['candidate_batch']}:{oid}";hist=asset.setdefault('provenance_history',[])
  if not any(h.get('candidate_id')==marker for h in hist):hist.append({'candidate_id':marker,'previous_provenance':asset.get('provenance',{}),'previous_image_sha256':item['before_sha256']})
  b=im.getchannel('A').getbbox();layout=spec['component_layout'];comp=layout.get('detected_components',[]);vi=['front','top','right','left','bottom','rear'].index(view)
  asset['provenance']={'method':'generated-orthographic-six-view-atlas','source_image':spec['source_image'],'source_contact_sheet':spec['contact_sheet'],'source_contact_sheet_sha256':spec['contact_sheet_sha256'],'generated_atlas':spec['raw_atlas'],'generated_atlas_sha256':spec['raw_atlas_sha256'],'prompt_path':spec['prompt_path'],'prompt_sha256':spec['prompt_sha256'],'source_rect':comp[vi] if comp else None,'normalization':{'scale':spec['uniform_scale'],'offset_px':[b[0],b[1]],'resampling':'nearest','frame_size':[256,256],'anchor_px':[128,128],'distortion':'none; shared uniform factor across six views'},'view_transform':layout.get('plan_transform',{}).get(view,'none'),'geometry_basis':'manifest west-wall/NE orientation; long-Y plans, narrow ends, broad side elevations','notes':'Illustrative orthographic views; unseen back/underside surfaces are inferred, not recovered or metrically calibrated.'}
  meta=BOOK/asset['metadata_path'];tmp=meta.with_suffix('.json.tmp');tmp.write_text(json.dumps(asset,indent=2)+'\n');os.replace(tmp,meta)
 ss=next(s for s in idx['view_sets'] if s['object_id']==oid);ss['complete']=False;ss['notes']='Root-reviewed candidate installed; pending current-hash source+six approval.'
tmp=INDEX.with_suffix('.json.tmp');tmp.write_text(json.dumps(idx,indent=2)+'\n');os.replace(tmp,INDEX)
print(json.dumps({oid:{v:i['after_sha256'] for v,i in s['views'].items()} for oid,s in SPEC['sets'].items()},indent=2))
