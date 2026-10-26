#!/usr/bin/env python3
"""Install only broad RIGHT/LEFT side elevations for Personal Space NE endcap."""
from pathlib import Path
import json,hashlib,struct
import numpy as np
from PIL import Image
from scipy import ndimage
PACK=Path(__file__).resolve().parents[4];VD=PACK/'reusable/views-additional';R=json.loads((VD/'raw/targeted-repairs/personal-space-endcap-ne-sides-v2.json').read_text());o=R['object_id'];ap=PACK/R['atlas'];atlas=Image.open(ap).convert('RGBA');ah=hashlib.sha256(ap.read_bytes()).hexdigest()
if ah!=R['atlas_sha256']:raise SystemExit('atlas hash mismatch')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rgba(im):return hashlib.sha256(struct.pack('>II',*im.size)+im.convert('RGBA').tobytes()).hexdigest()
src=PACK/R['source'];
if sha(src)!=R['source_sha256']:raise SystemExit('source changed')
for v,h in R['views'].items():
 p=VD/f'{o}.{v}.png';md=json.loads((VD/f'{o}.{v}.json').read_text());installed=md.get('provenance',{}).get('generated_atlas_sha256')==ah
 if installed:
  if sha(p)!=md['image']['sha256']:raise SystemExit(f'installed bytes changed {v}')
 elif sha(p)!=h:raise SystemExit(f'current hash guard failed {v}')
a=np.asarray(atlas);labels,n=ndimage.label(a[:,:,3]>=245,structure=np.ones((3,3),dtype=np.uint8));centers={2:858,3:1314}
idxp=VD/'set-index.json';idx=json.loads(idxp.read_text())
for c in R['cells']:
 v,col,scale=c['view'],c['col'],c['scale'];cx=centers[col];best=None
 for lab,sl in enumerate(ndimage.find_objects(labels),1):
  if sl is None:continue
  area=int((labels[sl]==lab).sum())
  if area<1000:continue
  yy,xx=ndimage.center_of_mass(labels==lab);d=abs(xx-cx)
  if best is None or d<best[0]:best=(d,lab,area,sl)
 if best is None or best[0]>100:raise SystemExit(f'missing {v} cell: {best}')
 _,lab,area,sl=best;x0,y0,x1,y1=sl[1].start,sl[0].start,sl[1].stop,sl[0].stop
 body=atlas.crop((x0,y0,x1,y1));px=np.asarray(body).copy();px[:,:,3]=np.where(labels[y0:y1,x0:x1]==lab,255,0).astype(np.uint8);body=Image.fromarray(px,'RGBA');size=(round(body.width*scale),round(body.height*scale));body=body.resize(size,Image.Resampling.NEAREST);canvas=Image.new('RGBA',(256,256),(0,0,0,0));canvas.alpha_composite(body,(128-size[0]//2,248-size[1]));dst=VD/f'{o}.{v}.png';canvas.save(dst,optimize=True);mp=VD/f'{o}.{v}.json';md=json.loads(mp.read_text());md['image']={'path':f'reusable/views-additional/{o}.{v}.png','width':256,'height':256,'sha256':sha(dst),'rgba_sha256':rgba(canvas)};md['geometry_qa']='pending-review';md['provenance']['generated_atlas']=R['atlas'];md['provenance']['generated_atlas_sha256']=ah;md['provenance']['generation_request']='reusable/views-additional/raw/requests/personal-space-endcap-ne-sides-v2.json';md['provenance']['source_sha256']=R['source_sha256'];md['provenance']['normalization']={'alpha_threshold':245,'component_policy':'whole-atlas connected component assigned to its view column by centroid; full selected component bounds retained','component_group':[{'label':lab,'area':area,'bbox':[x0,y0,x1,y1]}],'shared_scale':scale,'render_size':list(size),'canvas':[256,256],'resampling':'NEAREST','anchor_px':[128,248]};md['provenance']['notes']='Inferred orthographic long-Y wall elevation with source-faithful plaster and timber; matched to common wall Z. Not recovered pixels.';mp.write_text(json.dumps(md,indent=2)+'\n')
 for a in idx['assets']:
  if a.get('id')==md['id']:a.clear();a.update(md);break
g=next(x for x in idx['view_sets'] if x['object_id']==o);g['complete']=False;g['geometry_qa']='pending-review';g['notes']='RIGHT/LEFT regenerated as full-height long-Y plaster and timber wall faces; FRONT/TOP/BOTTOM/REAR preserved pending independent review.';idxp.write_text(json.dumps(idx,indent=2)+'\n');print(json.dumps({v:sha(VD/f'{o}.{v}.png') for v in ['front','top','right','left','bottom','rear']},indent=2))
