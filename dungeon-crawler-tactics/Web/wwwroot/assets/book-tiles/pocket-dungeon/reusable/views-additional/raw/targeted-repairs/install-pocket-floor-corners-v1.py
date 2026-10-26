#!/usr/bin/env python3
"""Install target corner-transition views only, using bounded atlas CCs."""
from pathlib import Path
import json,hashlib,struct,shutil
import numpy as np
from PIL import Image
from scipy import ndimage
PACK=Path(__file__).resolve().parents[4];VD=PACK/'reusable/views-additional';R=json.loads((VD/'raw/targeted-repairs/pocket-floor-corners-v1-install.json').read_text());ap=PACK/R['atlas'];atlas=Image.open(ap).convert('RGBA');ah=hashlib.sha256(ap.read_bytes()).hexdigest()
if ah!=R['atlas_sha256']:raise SystemExit('atlas SHA mismatch')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rgba(im):return hashlib.sha256(struct.pack('>II',*im.size)+im.convert('RGBA').tobytes()).hexdigest()
idxp=VD/'set-index.json';idx=json.loads(idxp.read_text());arr=np.asarray(atlas);labels,n=ndimage.label(arr[:,:,3]>=245,structure=np.ones((3,3),dtype=np.uint8))
for row in R['rows']:
 o=row['object_id'];src=PACK/row['source'];
 if sha(src)!=row['source_sha256']:raise SystemExit(f'source changed: {o}')
 for v,h in row['views'].items():
  p=VD/f'{o}.{v}.png';md=json.loads(p.with_suffix('.json').read_text());installed=md.get('provenance',{}).get('generated_atlas_sha256')==ah
  if installed:
   if sha(p)!=md['image']['sha256']:raise SystemExit(f'installed output changed {o}.{v}')
  elif sha(p)!=h:raise SystemExit(f'current source+six hash guard failed: {o}.{v}')
for c in R['cells']:
 o,row,col,v,scale=c['object_id'],c['row'],c['col'],c['view'],c['scale'];cx,cy=R['centroids_x'][col],R['centroids_y'][row];best=None
 for lab,sl in enumerate(ndimage.find_objects(labels),1):
  if sl is None:continue
  area=int((labels[sl]==lab).sum())
  if area<500:continue
  yy,xx=ndimage.center_of_mass(labels==lab);dist=((xx-cx)**2+(yy-cy)**2)**.5
  if best is None or dist<best[0]:best=(dist,lab,area,sl)
 if best is None or best[0]>80:raise SystemExit(f'main object missing {o}.{v}: {best}')
 _,lab,area,sl=best;x0,y0,x1,y1=sl[1].start,sl[0].start,sl[1].stop,sl[0].stop;body=atlas.crop((x0,y0,x1,y1));px=np.asarray(body).copy();px[:,:,3]=np.where(labels[y0:y1,x0:x1]==lab,255,0).astype(np.uint8);body=Image.fromarray(px,'RGBA');size=(round(body.width*scale),round(body.height*scale));body=body.resize(size,Image.Resampling.NEAREST);canvas=Image.new('RGBA',(256,256),(0,0,0,0));canvas.alpha_composite(body,(128-size[0]//2,248-size[1]));dst=VD/f'{o}.{v}.png';snap=VD/'raw/targeted-repairs'/f'{o}.{v}.before-floor-corners-v1.png';
 if not snap.exists():shutil.copy2(dst,snap)
 canvas.save(dst,optimize=True);mp=VD/f'{o}.{v}.json';md=json.loads(mp.read_text());md['image']={'path':f'reusable/views-additional/{o}.{v}.png','width':256,'height':256,'sha256':sha(dst),'rgba_sha256':rgba(canvas)};md['geometry_qa']='pending-review';md['provenance']['generated_atlas']=R['atlas'];md['provenance']['generated_atlas_sha256']=ah;md['provenance']['generation_request']='reusable/views-additional/raw/requests/pocket-floor-corners-v1.json';md['provenance']['source_sha256']=next(x['source_sha256'] for x in R['rows'] if x['object_id']==o);md['provenance']['normalization']={'alpha_threshold':245,'component_policy':'whole-atlas CC selected by row/view centroid; full component bounds retained; no fixed-cell clipping','component_group':[{'label':lab,'area':area,'bbox':[x0,y0,x1,y1]}],'shared_scale':scale,'render_size':list(size),'canvas':[256,256],'resampling':'NEAREST','anchor_px':[128,248]};md['provenance']['notes']='Source-specific inferred orthographic floor-corner projection; not recovered pixels.';mp.write_text(json.dumps(md,indent=2)+'\n')
 for a in idx['assets']:
  if a.get('id')==md['id']:a.clear();a.update(md);break
for row in R['rows']:
 g=next(x for x in idx['view_sets'] if x['object_id']==row['object_id']);g['complete']=False;g['geometry_qa']='pending-review';g['notes']='Targeted floor-corner projections installed with accepted TOP preserved where applicable; awaiting independent source+six review.'
idxp.write_text(json.dumps(idx,indent=2)+'\n');print(json.dumps([{'object_id':c['object_id'],'view':c['view'],'sha256':sha(VD/f"{c['object_id']}.{c['view']}.png")} for c in R['cells']],indent=2))
