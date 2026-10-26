#!/usr/bin/env python3
"""Install only current-hash-guarded Iron Tracks endcap side and underside views."""
from pathlib import Path
import json,hashlib,struct,shutil
import numpy as np
from PIL import Image
from scipy import ndimage
PACK=Path(__file__).resolve().parents[4];VD=PACK/'reusable/views-additional';RAW=VD/'raw'
ids=['iron-tracks-tunnel-stone-endcap-northwest','iron-tracks-tunnel-stone-endcap-northeast']
ledger=json.loads(Path('/workspace/scratch/view-qa-root.json').read_text())['reviewed'];idxp=VD/'set-index.json';idx=json.loads(idxp.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rsha(im):return hashlib.sha256(struct.pack('>II',*im.size)+im.convert('RGBA').tobytes()).hexdigest()
def extract(atlas,labels,row,col,rows,cols):
 cy=(row+.5)*atlas.height/rows;cx=(col+.5)*atlas.width/cols;candidates=[]
 for lab,sl in enumerate(ndimage.find_objects(labels),1):
  if sl is None:continue
  area=int((labels[sl]==lab).sum())
  if area<500:continue
  yy,xx=ndimage.center_of_mass(labels==lab);dist=((xx-cx)**2+(yy-cy)**2)**.5
  candidates.append((dist,lab,area,sl))
 if not candidates:raise SystemExit(f'missing row={row} col={col}')
 dist,lab,area,sl=min(candidates)
 if dist>min(atlas.width/cols,atlas.height/rows)*.45:raise SystemExit(f'component outside assigned atlas cell: row={row} col={col} dist={dist}')
 x0,y0,x1,y1=sl[1].start,sl[0].start,sl[1].stop,sl[0].stop
 px=np.asarray(atlas.crop((x0,y0,x1,y1))).copy();px[:,:,3]=np.where(labels[y0:y1,x0:x1]==lab,255,0).astype(np.uint8)
 return Image.fromarray(px,'RGBA'),[x0,y0,x1,y1],lab,area
# Verify all latest independent source+six captures before changing only flagged views.
for row,oid in enumerate(ids):
 r=ledger.get('book-tiles/pocket-dungeon::'+oid)
 if not r or r.get('status')!='needs-correction' or set(r.get('affected_views',[]))!={'right','left','bottom'}:raise SystemExit(f'latest independent scope no longer authorizes this repair: {oid}')
 for v,path in r['view_paths'].items():
  if sha(path)!=r['image_hashes'][v]:raise SystemExit(f'current image hash differs from latest QA capture: {oid}.{v}')
 if sha(r['source'])!=r['source_sha256']:raise SystemExit(f'canonical source changed: {oid}')
# V3 portrait sides; V1 full-plan bottoms. Both exact retained generator outputs are bound in request JSON.
side_req=json.loads((RAW/'requests/iron-tracks-endcaps-sides-v2.json').read_text())
side_path=PACK/side_req['v3_output_path'];side_atlas=Image.open(side_path).convert('RGBA');side_sha=sha(side_path)
if side_sha!=side_req['v3_sha256']:raise SystemExit('v3 side atlas hash mismatch')
side_labels,_=ndimage.label(np.asarray(side_atlas.getchannel('A'))>=245,structure=np.ones((3,3),dtype=np.uint8))
plan_atlas_path=RAW/'atlases/iron-tracks-endcaps-sides-v1.png';plan_atlas=Image.open(plan_atlas_path).convert('RGBA');plan_sha=sha(plan_atlas_path)
plan_labels,_=ndimage.label(np.asarray(plan_atlas.getchannel('A'))>=245,structure=np.ones((3,3),dtype=np.uint8))
for row,oid in enumerate(ids):
 g=next(x for x in idx['view_sets'] if x['object_id']==oid)
 for view,col in [('right',0),('left',1)]:
  body,bbox,lab,area=extract(side_atlas,side_labels,row,col,2,2)
  # Common physical Z from the accepted front; isotropic scale, no stretch.
  front=Image.open(VD/f'{oid}.front.png').convert('RGBA');fy,fx=np.where(np.asarray(front.getchannel('A'))>=128);target_h=int(fy.max()+1-fy.min())
  scale=target_h/body.height;size=(round(body.width*scale),target_h);body=body.resize(size,Image.Resampling.NEAREST)
  frame=Image.new('RGBA',(256,256),(0,0,0,0));frame.alpha_composite(body,(128-size[0]//2,248-size[1]))
  dst=VD/f'{oid}.{view}.png';mp=VD/f'{oid}.{view}.json';md=json.loads(mp.read_text());snap=RAW/'targeted-repairs'/f'{oid}.{view}.before-endcaps-v3.png'
  if not snap.exists():shutil.copy2(dst,snap)
  frame.save(dst,optimize=True);md.setdefault('provenance_history',[]).append(md.get('provenance',{}))
  md['image']={'path':f'reusable/views-additional/{oid}.{view}.png','width':256,'height':256,'sha256':sha(dst),'rgba_sha256':rsha(frame)};md['geometry_qa']='pending-review';md['provenance']={'method':'generated','source_image':ledger['book-tiles/pocket-dungeon::'+oid]['source'].replace(str(PACK)+'/',''),'source_sha256':ledger['book-tiles/pocket-dungeon::'+oid]['source_sha256'],'generated_atlas':str(side_path.relative_to(PACK)),'generated_atlas_sha256':side_sha,'generation_request':'reusable/views-additional/raw/requests/iron-tracks-endcaps-sides-v2.json','normalization':{'alpha_threshold':245,'component_policy':'whole-atlas CC selected by assigned row/column centroid; full bounds retained','component':[lab,area,bbox],'uniform_scale':scale,'render_size':list(size),'canvas':[256,256],'resampling':'NEAREST','anchor_px':[128,248]},'notes':'Inferred compact endcap side elevation at accepted common Z; one-tile-depth profile, source-specific stone and moss preserved.'};mp.write_text(json.dumps(md,indent=2)+'\n')
  for a in idx['assets']:
   if a['id']==md['id']:a.clear();a.update(md);break
 # Bottom plan from v1 atlas; isotropic scale to accepted TOP footprint.
 body,bbox,lab,area=extract(plan_atlas,plan_labels,row,4,2,6);top=Image.open(VD/f'{oid}.top.png').convert('RGBA');ty,tx=np.where(np.asarray(top.getchannel('A'))>=128);tw=int(tx.max()+1-tx.min());th=int(ty.max()+1-ty.min());scale=min(tw/body.width,th/body.height);size=(round(body.width*scale),round(body.height*scale));body=body.resize(size,Image.Resampling.NEAREST);frame=Image.new('RGBA',(256,256),(0,0,0,0));frame.alpha_composite(body,(128-size[0]//2,248-size[1]))
 dst=VD/f'{oid}.bottom.png';mp=VD/f'{oid}.bottom.json';md=json.loads(mp.read_text());snap=RAW/'targeted-repairs'/f'{oid}.bottom.before-endcaps-v3.png'
 if not snap.exists():shutil.copy2(dst,snap)
 frame.save(dst,optimize=True);md.setdefault('provenance_history',[]).append(md.get('provenance',{}));md['image']={'path':f'reusable/views-additional/{oid}.bottom.png','width':256,'height':256,'sha256':sha(dst),'rgba_sha256':rsha(frame)};md['geometry_qa']='pending-review';md['provenance']={'method':'generated','source_image':ledger['book-tiles/pocket-dungeon::'+oid]['source'].replace(str(PACK)+'/',''),'source_sha256':ledger['book-tiles/pocket-dungeon::'+oid]['source_sha256'],'generated_atlas':str(plan_atlas_path.relative_to(PACK)),'generated_atlas_sha256':plan_sha,'generation_request':'reusable/views-additional/raw/requests/iron-tracks-endcaps-sides-v1.json','normalization':{'alpha_threshold':245,'component_policy':'whole-atlas CC selected by assigned row/column centroid; full bounds retained','component':[lab,area,bbox],'matched_reference':'accepted TOP footprint','uniform_scale':scale,'render_size':list(size),'canvas':[256,256],'resampling':'NEAREST','anchor_px':[128,248]},'notes':'Inferred underside plane matched isotropically to the source-derived top footprint; no top-face image stretch.'};mp.write_text(json.dumps(md,indent=2)+'\n')
 for a in idx['assets']:
  if a['id']==md['id']:a.clear();a.update(md);break
 g['complete']=False;g['geometry_qa']='pending-review';g['notes']='RIGHT/LEFT common-Z profiles and BOTTOM plan installed from retained atlases; awaiting independent current source+six review.'
idxp.write_text(json.dumps(idx,indent=2)+'\n');print(json.dumps({oid:{v:sha(VD/f'{oid}.{v}.png') for v in ['right','left','bottom']} for oid in ids},indent=2))
