#!/usr/bin/env python3
"""Install only source-faithful corrected projections for two legacy items."""
from pathlib import Path
import json,hashlib,struct
import numpy as np
from PIL import Image
from scipy import ndimage
PACK=Path(__file__).resolve().parents[4];VD=PACK/'reusable/views-equipment';R=json.loads((VD/'raw/targeted-repairs/legacy-dynamite-crossbow-v1-install.json').read_text());ap=PACK/R['atlas'];atlas=Image.open(ap).convert('RGBA');ah=hashlib.sha256(ap.read_bytes()).hexdigest()
if ah!=R['atlas_sha256']:raise SystemExit('atlas SHA mismatch')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rgba(im):return hashlib.sha256(struct.pack('>II',*im.size)+im.convert('RGBA').tobytes()).hexdigest()
idxp=VD/'set-index.json';idx=json.loads(idxp.read_text());arr=np.asarray(atlas);labels,n=ndimage.label(arr[:,:,3]>=245,structure=np.ones((3,3),dtype=np.uint8))
for oid,proof in R['objects'].items():
 if sha(PACK/proof['source'])!=proof['source_sha256']:raise SystemExit(f'source changed {oid}')
 for v,h in proof['views'].items():
  p=VD/'images'/f'{oid}.{v}.png';md=json.loads((p.with_suffix('.json')).read_text());installed=md.get('provenance',{}).get('generated_atlas_sha256')==ah
  if installed:
   if sha(p)!=md['image']['sha256']:raise SystemExit(f'installed bytes changed {oid}.{v}')
  elif sha(p)!=h:raise SystemExit(f'current root hash guard failed {oid}.{v}')
for c in R['cells']:
 oid,row,col,v,scale=c['object_id'],c['row'],c['col'],c['view'],c['scale'];targetx=[192,528,900,1273,1633,1980][col];targety=[219,522][row];best=None
 for lab,sl in enumerate(ndimage.find_objects(labels),1):
  if sl is None:continue
  area=int((labels[sl]==lab).sum())
  if area<1000:continue
  yy,xx=ndimage.center_of_mass(labels==lab);dist=((xx-targetx)**2+(yy-targety)**2)**.5
  if best is None or dist<best[0]:best=(dist,lab,area,sl)
 if best is None or best[0]>90:raise SystemExit(f'no main atlas component {oid}.{v} {best}')
 _,lab,area,sl=best;x0,y0,x1,y1=sl[1].start,sl[0].start,sl[1].stop,sl[0].stop;body=atlas.crop((x0,y0,x1,y1));px=np.asarray(body).copy();px[:,:,3]=np.where(labels[y0:y1,x0:x1]==lab,255,0).astype(np.uint8);body=Image.fromarray(px,'RGBA');size=(round(body.width*scale),round(body.height*scale));body=body.resize(size,Image.Resampling.NEAREST);canvas=Image.new('RGBA',(256,256),(0,0,0,0));canvas.alpha_composite(body,(128-size[0]//2,248-size[1]));dst=VD/'images'/f'{oid}.{v}.png';canvas.save(dst,optimize=True);mp=dst.with_suffix('.json');md=json.loads(mp.read_text());md['image']={'path':f'reusable/views-equipment/images/{oid}.{v}.png','width':256,'height':256,'sha256':sha(dst),'rgba_sha256':rgba(canvas)};md['geometry_qa']={'status':'pending-review','reason':'Targeted source-faithful orthographic correction installed; root current-hash review pending.'};md.setdefault('provenance',{}).update({'generated_atlas':R['atlas'],'generated_atlas_sha256':ah,'generation_request':'reusable/views-equipment/raw/targeted-repairs/legacy-dynamite-crossbow-v1.json','source_sha256':R['objects'][oid]['source_sha256']});md['provenance']['normalization']={'alpha_threshold':245,'component_policy':'whole-atlas CC selected by row/column cell centroid; full component bounds retained','component_group':[{'label':lab,'area':area,'bbox':[x0,y0,x1,y1]}],'shared_scale':scale,'render_size':list(size),'canvas':[256,256],'resampling':'NEAREST','anchor_px':[128,248]};md['provenance']['notes']='Source-faithful inferred orthographic view for fantasy inventory sprite, not recovered pixels.';mp.write_text(json.dumps(md,indent=2)+'\n')
 for a in idx['assets']:
  if a.get('id')==md['id']:a.clear();a.update(md);break
for oid in R['objects']:
 g=next(x for x in idx['view_sets'] if x['object_id']==oid);g['complete']=False;g['geometry_qa']={'status':'pending-review','reason':'Targeted legacy projection art installed; independent current-hash review pending.'}
idxp.write_text(json.dumps(idx,indent=2)+'\n');print(json.dumps({'atlas_sha256':ah,'installed':[{'object_id':c['object_id'],'view':c['view'],'sha256':sha(VD/'images'/f"{c['object_id']}.{c['view']}.png")} for c in R['cells']]},indent=2))
