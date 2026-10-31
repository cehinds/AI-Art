#!/usr/bin/env python3
"""Install only validated main connected components for selected cap repair views."""
from pathlib import Path
import json,hashlib,struct
import numpy as np
from PIL import Image
from scipy import ndimage
PACK=Path(__file__).resolve().parents[4]; VD=PACK/'reusable/views-additional'; REC=VD/'raw/targeted-repairs/pocket-cap-batch-v2-install.json'; R=json.loads(REC.read_text()); atlas_path=PACK/R['atlas']; atlas=Image.open(atlas_path).convert('RGBA'); ah=hashlib.sha256(atlas_path.read_bytes()).hexdigest()
if ah!=R['atlas_sha256']:raise SystemExit('atlas hash mismatch')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rh(im):return hashlib.sha256(struct.pack('>II',*im.size)+im.convert('RGBA').tobytes()).hexdigest()
idxp=VD/'set-index.json';idx=json.loads(idxp.read_text()); arr=np.asarray(atlas); labels,n=ndimage.label(arr[:,:,3]>=245,structure=np.ones((3,3),dtype=np.uint8));
for oid,proof in R['objects'].items():
 src=PACK/proof['source']
 if sha(src)!=proof['source_sha256']:raise SystemExit(f'source changed: {oid}')
 for v,h in proof['views'].items():
  p=VD/f'{oid}.{v}.png'; md=json.loads((VD/f'{oid}.{v}.json').read_text()); installed=md.get('provenance',{}).get('generated_atlas_sha256')==ah
  if installed:
   if sha(p)!=md['image']['sha256']:raise SystemExit(f'installed view changed: {oid}.{v}')
  elif sha(p)!=h:raise SystemExit(f'current-byte guard failed: {oid}.{v}')
for c in R['cells']:
 oid,v,row,col,scale=c['object_id'],c['view'],c['row'],c['col'],c['scale']; cx=[165,404,624,835,1060,1270][col];cy=[168,375,579,790,1011][row];best=None
 for lab,sl in enumerate(ndimage.find_objects(labels),1):
  if sl is None:continue
  area=int((labels[sl]==lab).sum())
  if area<500:continue
  yy,xx=ndimage.center_of_mass(labels==lab);dist=((xx-cx)**2+(yy-cy)**2)**.5
  if best is None or dist<best[0]:best=(dist,lab,area,sl)
 if best is None or best[0]>25:raise SystemExit(f'no clean object component at {oid}.{v}: {best}')
 _,lab,area,sl=best;x0,y0,x1,y1=sl[1].start,sl[0].start,sl[1].stop,sl[0].stop
 if x0<20 or y0<60 or x1>atlas.width-20 or y1>atlas.height-20:raise SystemExit(f'cell content touches atlas boundary {oid}.{v}')
 crop=atlas.crop((x0,y0,x1,y1)); px=np.asarray(crop).copy(); px[:,:,3]=np.where(labels[y0:y1,x0:x1]==lab,255,0).astype(np.uint8); crop=Image.fromarray(px,'RGBA'); size=(round(crop.width*scale),round(crop.height*scale)); crop=crop.resize(size,Image.Resampling.NEAREST); canvas=Image.new('RGBA',(256,256),(0,0,0,0)); canvas.alpha_composite(crop,(128-size[0]//2,248-size[1])); dst=VD/f'{oid}.{v}.png'; canvas.save(dst,optimize=True); mp=VD/f'{oid}.{v}.json'; md=json.loads(mp.read_text());md['image']={'path':f'reusable/views-additional/{oid}.{v}.png','width':256,'height':256,'sha256':sha(dst),'rgba_sha256':rh(canvas)};md['geometry_qa']='pending-review';md['provenance']['generated_atlas']=R['atlas'];md['provenance']['generated_atlas_sha256']=ah;md['provenance']['generation_request']='reusable/views-additional/raw/requests/pocket-cap-batch-v2.json';md['provenance']['source_sha256']=R['objects'][oid]['source_sha256'];md['provenance']['normalization']={'alpha_threshold':245,'component_policy':'whole-atlas connected components assigned to labeled row/view cell by centroid; entire selected component bounds retained; no fixed cell clipping','component_group':[{'label':lab,'area':area,'bbox':[x0,y0,x1,y1]}],'shared_scale':scale,'render_size':list(size),'canvas':[256,256],'resampling':'NEAREST','anchor_px':[128,248]};md['provenance']['notes']='Inferred orthographic source-specific physical cap projection. Not recovered pixels.';mp.write_text(json.dumps(md,indent=2)+'\n')
 for a in idx['assets']:
  if a.get('id')==md['id']:a.clear();a.update(md);break
for oid in R['objects']:
 g=next(x for x in idx['view_sets'] if x['object_id']==oid);g['complete']=False;g['geometry_qa']='pending-review';g['notes']='Targeted cap views regenerated; other directions preserved and this set awaits independent source+six review.'
idxp.write_text(json.dumps(idx,indent=2)+'\n')
print(json.dumps({'atlas_sha256':ah,'changed':[{'object_id':c['object_id'],'view':c['view'],'sha256':sha(VD/f"{c['object_id']}.{c['view']}.png")} for c in R['cells']]},indent=2))
