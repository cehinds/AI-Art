#!/usr/bin/env python3
"""Install the source-matched wide submerged underside projection only."""
from pathlib import Path
import json,hashlib,struct,shutil
import numpy as np
from PIL import Image
from scipy import ndimage
PACK=Path(__file__).resolve().parents[4];VD=PACK/'reusable/views-additional';R=json.loads((VD/'raw/targeted-repairs/river-reeds-bottom-v5.json').read_text());o=R['object_id'];ap=PACK/R['atlas'];atlas=Image.open(ap).convert('RGBA');ah=hashlib.sha256(ap.read_bytes()).hexdigest()
if ah!=R['atlas_sha256']:raise SystemExit('atlas hash mismatch')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rgba(im):return hashlib.sha256(struct.pack('>II',*im.size)+im.convert('RGBA').tobytes()).hexdigest()
if sha(PACK/R['source'])!=R['source_sha256']:raise SystemExit('source changed')
for v,h in R['views'].items():
 p=VD/f'{o}.{v}.png';md=json.loads((VD/f'{o}.{v}.json').read_text());installed=md.get('provenance',{}).get('generated_atlas_sha256')==ah
 if installed:
  if sha(p)!=md['image']['sha256']:raise SystemExit(f'installed bytes changed {v}')
 elif sha(p)!=h:raise SystemExit(f'current hash guard failed {v}')
a=np.asarray(atlas);labels,n=ndimage.label(a[:,:,3]>=245,structure=np.ones((3,3),dtype=np.uint8));comps=[]
for lab,sl in enumerate(ndimage.find_objects(labels),1):
 if sl is None:continue
 area=int((labels[sl]==lab).sum())
 if area>=100:comps.append((area,lab,sl))
if len(comps)!=1:raise SystemExit(f'expected one isolated tile object, found {len(comps)}')
area,lab,sl=comps[0];x0,y0,x1,y1=sl[1].start,sl[0].start,sl[1].stop,sl[0].stop;body=atlas.crop((x0,y0,x1,y1));px=np.asarray(body).copy();px[:,:,3]=np.where(labels[y0:y1,x0:x1]==lab,255,0).astype(np.uint8);body=Image.fromarray(px,'RGBA');scale=R['cell']['scale'];size=(round(body.width*scale),round(body.height*scale));body=body.resize(size,Image.Resampling.NEAREST);canvas=Image.new('RGBA',(256,256),(0,0,0,0));canvas.alpha_composite(body,(128-size[0]//2,248-size[1]));dst=VD/f'{o}.bottom.png';snap=VD/'raw/targeted-repairs'/f'{o}.bottom.before-v5.png';
if not snap.exists():shutil.copy2(dst,snap)
canvas.save(dst,optimize=True);mp=VD/f'{o}.bottom.json';md=json.loads(mp.read_text());md['image']={'path':f'reusable/views-additional/{o}.bottom.png','width':256,'height':256,'sha256':sha(dst),'rgba_sha256':rgba(canvas)};md['geometry_qa']='pending-review';md['provenance']['generated_atlas']=R['atlas'];md['provenance']['generated_atlas_sha256']=ah;md['provenance']['generation_request']='reusable/views-additional/raw/requests/river-reeds-bottom-v5-edit.json';md['provenance']['source_sha256']=R['source_sha256'];md['provenance']['normalization']={'alpha_threshold':245,'component_policy':'entire single connected tile component retained, no fixed-cell clipping','component_group':[{'label':lab,'area':area,'bbox':[x0,y0,x1,y1]}],'shared_scale':scale,'render_size':list(size),'canvas':[256,256],'resampling':'NEAREST','anchor_px':[128,248]};md['provenance']['notes']='Inferred submerged underside of the source water tile with underwater reeds and root bases, no surface pad tops or cattail tips. Not recovered pixels.';mp.write_text(json.dumps(md,indent=2)+'\n');idxp=VD/'set-index.json';idx=json.loads(idxp.read_text())
for a in idx['assets']:
 if a.get('id')==md['id']:a.clear();a.update(md);break
g=next(x for x in idx['view_sets'] if x['object_id']==o);g['complete']=False;g['geometry_qa']='pending-review';g['notes']='Bottom updated to submerged full-footprint underside; other five views pending review, no accepted directions changed.';idxp.write_text(json.dumps(idx,indent=2)+'\n');print(json.dumps({'sha256':sha(dst),'atlas_bbox':[x0,y0,x1,y1],'render_size':list(size)},indent=2))
