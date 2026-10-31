#!/usr/bin/env python3
"""Install only the repaired rear view from the retained six-view atlas."""
from pathlib import Path
import hashlib,json,struct
import numpy as np
from PIL import Image
from scipy import ndimage
PACK=Path(__file__).resolve().parents[4]; VD=PACK/'reusable/views-additional'; OBJ='safe-services-diner-checker-tile-corner-transition'; VIEW='rear'
ATLAS='reusable/views-additional/raw/atlases/safe-services-diner-corner-rear-v1.png'
EXPECTED={'front':'7b33fbd0d43e335c6400451d0dffe8ebfe586b961087b8e346dc3d21a8da3692','top':'6e2e96afb2079bcf91e7222123b09500af1a8caba52f89e9a881da4b052a8a8b','right':'a026ce912948417d714ffb6e7a19099a87bb7bc0d20ed0a4d6baa024922ea638','left':'6d86112c0c6ae3c84df9832a349af31b09322984492b142c62b791fb23d034d9','bottom':'8ce0f01a663c79e658635bf693e464d19f8796595c79374fd5391ae4068c6cae','rear':'df4d7f8e0d00a137adff38e9d678d5a6b2c4aab0776ffad3d304754f0d5c2c41'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rgba_sha(im):return hashlib.sha256(struct.pack('>II',*im.size)+im.convert('RGBA').tobytes()).hexdigest()
idxp=VD/'set-index.json';idx=json.loads(idxp.read_text());atlas=Image.open(PACK/ATLAS).convert('RGBA')
if atlas.size!=(2172,724):raise SystemExit(f'unexpected atlas dimensions {atlas.size}')
# Exact current-hash guard for source-reviewed set; previous generated output is also accepted for replay.
for v,h in EXPECTED.items():
 f=VD/f'{OBJ}.{v}.png'; expected=h
 if v=='rear':
  # Current installed target is idempotent.
  current=json.loads((VD/f'{OBJ}.{v}.json').read_text())['image']['sha256']
  if sha(f)==current and current!=h: continue
 if sha(f)!=expected:raise SystemExit(f'hash guard failed for {v}')
# Tool rendered an extra row: the actual row-1, col-5 rear component is fully within bounds.
cell=atlas.crop((5*362,1*362,6*362,2*362)); ar=np.asarray(cell);mask=ar[:,:,3]>=245;labels,n=ndimage.label(mask,structure=np.ones((3,3),dtype=np.uint8));slices=ndimage.find_objects(labels); comps=[]
for i,sl in enumerate(slices,1):
 if sl is None:continue
 area=int((labels[sl]==i).sum())
 if area>=4:comps.append((area,i,sl))
if not comps:raise SystemExit('empty target cell')
area,label,sl=max(comps,key=lambda x:x[0]);x0,x1=sl[1].start,sl[1].stop;y0,y1=sl[0].start,sl[0].stop
if x0<=0 or y0<=0 or x1>=362 or y1>=362:raise SystemExit('target component touches nominal cell edge')
body=cell.crop((x0,y0,x1,y1)); ba=np.asarray(body).copy();ba[:,:,3]=np.where(labels[y0:y1,x0:x1]==label,255,0);body=Image.fromarray(ba,'RGBA')
scale=220/body.width; size=(220,round(body.height*scale));body=body.resize(size,Image.Resampling.NEAREST);canvas=Image.new('RGBA',(256,256),(0,0,0,0));canvas.alpha_composite(body,(18,248-size[1]))
dst=VD/f'{OBJ}.{VIEW}.png';canvas.save(dst,optimize=True);mp=VD/f'{OBJ}.{VIEW}.json';md=json.loads(mp.read_text());md['image']={'path':f'reusable/views-additional/{OBJ}.{VIEW}.png','width':256,'height':256,'sha256':sha(dst),'rgba_sha256':rgba_sha(canvas)};md['geometry_qa']='pending-review';md['provenance']['generated_atlas']=ATLAS;md['provenance']['generated_atlas_sha256']=sha(PACK/ATLAS);md['provenance']['generation_request']='reusable/views-additional/raw/requests/safe-services-diner-corner-rear-v1.json';md['provenance']['normalization']={'alpha_threshold':245,'minimum_component_area':4,'component_policy':'largest opaque connected body in full nominal atlas cell; preserve full bounds','cell_xywh':[5*362,362,362,362],'body_bbox_xyxy':[x0,y0,x1,y1],'component_area':area,'shared_scale':scale,'render_size':list(size),'canvas':[256,256],'resampling':'NEAREST','anchor_px':[128,248]};md['provenance']['notes']='Rear edge is inferred as low tile/concrete boundary with only a small termination of right-side trim; not recovered pixels.';mp.write_text(json.dumps(md,indent=2)+'\n')
for a in idx['assets']:
 if a.get('id')==md['id']:a.clear();a.update(md);break
proofs=json.loads((VD/'raw/targeted-repairs/reviewed-pass-proofs-pocket-scenery.json').read_text());proof=proofs.get(OBJ,{});source=PACK/proof.get('source_path','');ok=proof.get('status')=='pass' and source.is_file() and sha(source)==proof.get('source_sha256')
if ok:
 for v,h in proof.get('image_hashes',{}).items():
  if sha(VD/f'{OBJ}.{v}.png')!=h:ok=False;break
status='pass' if ok else 'pending-review'
for v in ('front','top','right','left','bottom','rear'):
 mp=VD/f'{OBJ}.{v}.json';md=json.loads(mp.read_text());md['geometry_qa']=status;mp.write_text(json.dumps(md,indent=2)+'\n')
 for a in idx['assets']:
  if a.get('id')==md['id']:a.clear();a.update(md);break
g=next(x for x in idx['view_sets'] if x['object_id']==OBJ);g['complete']=ok;g['geometry_qa']=status;g['notes']='Whole source+six root PASS restored from pinned current-hash proof.' if ok else 'Awaiting independent current-hash review.'
idxp.write_text(json.dumps(idx,indent=2)+'\n');print(json.dumps({'rear_sha256':sha(dst),'atlas_sha256':sha(PACK/ATLAS),'source_sha256':sha(PACK/'safe-services/components'/f'{OBJ}.png'),'geometry_qa':status,'body_bbox':[x0,y0,x1,y1],'render_size':size},indent=2))
