#!/usr/bin/env python3
"""Guarded installation of the two source-faithful, tucked-wing Mongo views."""
from pathlib import Path
import hashlib,json,os,struct
from PIL import Image
HERE=Path(__file__).resolve().parent;RAW=HERE/'raw';STAGE=RAW/'mongo-se-walk12-v2-candidates'
ATLAS=RAW/'mongo-se-walk12-tucked-wing-v2-20261026.png'
REQUEST='exec-15003868-31c8-4a3d-8110-36ae4fbf32fe'
SOURCE_SHA={
 'directional--mongo--se--walk1':'beb25c447e059625fade08dfa47e4029fcce9d0926b088d0e0487f3e1095a139',
 'directional--mongo--se--walk2':'88b38a1b860f16d1d4c76bc97450a01976b120531815ef2d0446154b38ad3dcd',
}
# Hashes of live views captured before staging; stop if another writer changed any target.
OLD={
 'directional--mongo--se--walk1':{'front':'24477597a9945cdfece929623ec2209f5592f55f7986ab23172ae48ba88fac49','top':'445a02061cd209d3aafaeb6baf9d94a338e2c48cec1f654e212af22e604a80da','bottom':'c30d1b88138a0112fd06c25226b6ba295402234e422677e5a9b5e7eb144e1a1a','rear':'884b558e3416a0767ae3ed64ad9d86885277cfee27b88518f606ac5c2c605a0c'},
 'directional--mongo--se--walk2':{'front':'fb843f2b9ddb6d794d1bfbd4251bfbe321fb7aa3a59fd8898688782baa3b7e61','top':'e56077039e60f79edb4f88ada132fdc7dbd16ceff4e539801f5dbf393a22606e','bottom':'991d68987b978aa95b3bf0cfb60a52fbcf10e06be25e859347d6c8c384378431','rear':'0539bf2055b791d448cc217c704d21b58ae4aa0673bfcf133c28ba523386f792'}
}
def sha(b):return hashlib.sha256(b).hexdigest()
def rh(im):return sha(struct.pack('>II',*im.size)+im.convert('RGBA').tobytes())
report=json.loads((STAGE/'mongo-se-walk12-v2-stage-report.json').read_text()); atlas_sha=sha(ATLAS.read_bytes())
if report['source_atlas_sha256']!=atlas_sha or report['generation_request_id']!=REQUEST:raise SystemExit('retained generation source mismatch')
index_path=HERE/'set-index.json';index=json.loads(index_path.read_text()); assets={a['id']:a for a in index['assets']}
for oid,views in OLD.items():
 source=HERE.parents[0]/'native'/f'{oid}.png'; actual_source_sha=sha(source.read_bytes())
 expected=SOURCE_SHA[oid]
 if expected=='TO_BE_FILLED':expected=assets[f'{oid}.front']['provenance']['native_front_sha256']
 if actual_source_sha!=expected:raise SystemExit(f'canonical source changed for {oid}')
 for view,old_sha in views.items():
  aid=f'{oid}.{view}';live=HERE/f'{aid}.png';old=live.read_bytes()
  row=next(x for x in report['candidates'] if x['object_id']==oid and x['view']==view)
  cand=HERE/row['candidate_path']; new=cand.read_bytes()
  if sha(new)!=row['png_sha256']:raise SystemExit(f'staged candidate changed: {aid}')
  if sha(old) not in (old_sha,row['png_sha256']):raise SystemExit(f'live target changed: {aid}')
# Copy exact pre-install PNG bytes into retained evidence before atomic replacement.
staged=[]
for oid,views in OLD.items():
 source=HERE.parents[0]/'native'/f'{oid}.png'; source_sha=sha(source.read_bytes())
 for view,old_sha in views.items():
  aid=f'{oid}.{view}'; live=HERE/f'{aid}.png'; side=HERE/f'{aid}.json'; old=live.read_bytes()
  row=next(x for x in report['candidates'] if x['object_id']==oid and x['view']==view)
  cand=HERE/row['candidate_path']; new=cand.read_bytes(); meta=json.loads(side.read_text())
  if meta['provenance'].get('source_image')!=f'reusable/native/{oid}.png':raise SystemExit(f'noncanonical source ref for {aid}')
  staged.append((oid,view,aid,live,side,old,new,cand,meta,source_sha,row))
for oid,view,aid,live,side,old,new,cand,meta,source_sha,row in staged:
 backup=STAGE/'previous-live'/f'{aid}.png';backup.parent.mkdir(exist_ok=True)
 if not backup.exists():backup.write_bytes(old)
 original=backup.read_bytes()
 temp=live.with_suffix('.png.tmp');temp.write_bytes(new);os.replace(temp,live)
 im=Image.open(cand).convert('RGBA');meta['image']['sha256']=sha(new);meta['image']['rgba_sha256']=rh(im)
 meta['provenance'].update({'source_image':f'reusable/native/{oid}.png','source_image_sha256':source_sha,'native_front':f'reusable/native/{oid}.png','native_front_sha256':source_sha,'source_atlas':f'reusable/views-additional/raw/{ATLAS.name}','source_atlas_sha256':atlas_sha,'generation_request_id':REQUEST,'generation_prompt':'reusable/views-additional/raw/mongo-se-walk12-tucked-wing-v2-20261026.prompt.txt','generation_recipe':'reusable/views-additional/stage_mongo_se_walk12_wings_v2_20261026.py','generation_reference_images':[{'path':f'reusable/views-additional/raw/mongo-se-{oid.rsplit("--",1)[-1]}-wing-reference.png'}],'notes':'Inferred orthographic view retaining the exact tucked-wing walking phase and source leg phase; unseen surfaces are inferred, not recovered pixels. Independently pending review.','crop_bounds_px':{'coordinate_format':'xywh','nominal_cell':{'bounds':row['cell_bounds_xywh'],'source_coordinate_format':'rounded xywh from fractional atlas grid'},'alpha_threshold':16,'alpha_bounds_global_xywh':[row['cell_bounds_xywh'][0]+row['alpha_bbox_local_xyxy'][0],row['cell_bounds_xywh'][1]+row['alpha_bbox_local_xyxy'][1],row['alpha_bbox_local_xyxy'][2]-row['alpha_bbox_local_xyxy'][0],row['alpha_bbox_local_xyxy'][3]-row['alpha_bbox_local_xyxy'][1]],'resized_wh':row['resized_wh'],'canvas_offset_px':row['canvas_offset_xy'],'shared_anchor_px':[128,128],'uniform_scale':row['uniform_scale'],'normalization':'one shared isotropic scale calibrated from accepted front Z and top Y extents across both poses'}})
 side.write_text(json.dumps(meta,indent=2)+'\n');assets[aid].clear();assets[aid].update(meta)
 (STAGE/f'{aid}.install-record.json').write_text(json.dumps({'object_id':oid,'view':view,'source_image':meta['provenance']['source_image'],'source_image_sha256':source_sha,'previous_live_sha256':sha(original),'installed_candidate_sha256':sha(new),'generation_request_id':REQUEST,'source_atlas_sha256':atlas_sha,'candidate_path':str(cand.relative_to(HERE)),'review_status':'pending-independent-source-plus-six-review'},indent=2)+'\n')
# Preserve every sibling and keep group-level QA explicitly pending.
index['assets']=[assets[a['id']] for a in index['assets']]
for group in index['view_sets']:
 if group['object_id'] in OLD:
  group['complete']=False
  group['geometry_qa']={'status':'pending-review','views':['front','top','bottom','rear'],'notes':'Targeted tucked-wing projections installed; independent source-plus-six review required.'}
tmp=index_path.with_suffix('.json.tmp');tmp.write_text(json.dumps(index,indent=2)+'\n');os.replace(tmp,index_path)
print(json.dumps({'installed':[{f'{x[0]}.{x[1]}':sha(x[6])} for x in staged],'sets_pending_review':list(OLD)},indent=2))
