"""Guarded install/replay of the root-approved studio-partition NE west-wall candidate."""
from pathlib import Path
import hashlib, json, os, struct
from PIL import Image
HERE=Path(__file__).resolve().parent
OUT=HERE.parent
BOOK=OUT.parent.parent
SPEC_PATH=HERE/'studio-partition-wall-northeast-v5-install.json'
SPEC=json.loads(SPEC_PATH.read_text())
INDEX=OUT/'set-index.json'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
idx=json.loads(INDEX.read_text())
assert sha(BOOK/SPEC['source_image'])==SPEC['source_sha256'],'source changed'
by_id={a['id']:a for a in idx['assets']}
for view,item in SPEC['views'].items():
 aid=item['asset_id']; asset=by_id[aid]; out=BOOK/asset['image']['path']; cand=OUT/item['candidate_path']
 cur=sha(out); assert cur in {item['before_sha256'],item['after_sha256']},f'{aid}: unexpected live hash {cur}'
 assert sha(cand)==item['after_sha256'],f'{aid}: candidate changed'
# Only after all guards pass, publish PNGs and updated sidecars.
for view,item in SPEC['views'].items():
 aid=item['asset_id']; asset=by_id[aid]; out=BOOK/asset['image']['path']; cand=OUT/item['candidate_path']
 cur=sha(out)
 if cur!=item['after_sha256']:
  tmp=out.with_suffix('.png.tmp');tmp.write_bytes(cand.read_bytes());os.replace(tmp,out)
 im=Image.open(out).convert('RGBA');rgba=im.tobytes();asset['image']['sha256']=sha(out);asset['image']['rgba_sha256']=hashlib.sha256(struct.pack('>II',im.width,im.height)+rgba).hexdigest()
 old=asset.get('provenance',{});hist=asset.setdefault('provenance_history',[])
 if not hist or hist[-1].get('candidate_id')!='studio-partition-wall-ne-v5':
  hist.append({'candidate_id':'studio-partition-wall-ne-v5','previous_provenance':old,'previous_image_sha256':item['before_sha256']})
 asset['provenance']={'method':'generated-orthographic-six-view-atlas','source_image':SPEC['source_image'],'source_contact_sheet':SPEC['contact_sheet'],'source_contact_sheet_sha256':SPEC['contact_sheet_sha256'],'generated_atlas':SPEC['raw_atlas'],'generated_atlas_sha256':SPEC['raw_atlas_sha256'],'prompt_path':SPEC['prompt_path'],'prompt_sha256':SPEC['prompt_sha256'],'source_rect':item['source_rect'],'normalization':{'scale':SPEC['extraction']['shared_uniform_scale'],'offset_px':[im.getchannel('A').getbbox()[0],im.getchannel('A').getbbox()[1]],'resampling':'nearest','frame_size':[256,256],'anchor_px':[128,128],'distortion':'none; uniform scale shared across all six views'},'view_transform':SPEC['extraction']['plan_transforms'].get(view,'none'),'geometry_basis':'manifest squareLayout west-wall: map footprint extends along Y; front/rear thin ends, right/left broad faces, top/bottom long-Y plans','notes':'Illustrative orthographic view; hidden surfaces are inferred, not recovered pixels or metrically calibrated.'}
 meta=BOOK/asset['metadata_path'];tmp=meta.with_suffix('.json.tmp');tmp.write_text(json.dumps(asset,indent=2)+'\n');os.replace(tmp,meta)
ss=[s for s in idx['view_sets'] if s['object_id']==SPEC['object_id']]
assert len(ss)==1,'view-set object_id must be unique'
ss[0]['complete']=False;ss[0]['notes']='Root-approved six-view candidate indexed; current source+six hash review pending.'
tmp=INDEX.with_suffix('.json.tmp');tmp.write_text(json.dumps(idx,indent=2)+'\n');os.replace(tmp,INDEX)
print(json.dumps({v:{'asset_id':item['asset_id'],'sha256':item['after_sha256']} for v,item in SPEC['views'].items()},indent=2))
