#!/usr/bin/env python3
"""Uniformly normalize only the held left view of the Jungle NW cap."""
from pathlib import Path
import hashlib,json,struct,shutil
import numpy as np
from PIL import Image
PACK=Path(__file__).resolve().parents[4];VD=PACK/'reusable/views-additional';OBJ='hunting-jungle-vine-covered-ruin-stone-endcap-northwest';VIEW='left'
EXPECTED={'front':'','top':'','right':'','left':'','bottom':'','rear':''}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rgba_sha(im):return hashlib.sha256(struct.pack('>II',*im.size)+im.convert('RGBA').tobytes()).hexdigest()
rev_hashes={'front': 'af84424a6ae2e7e81fb3b1017104c08980a410f45b45cd693c9a0de1f49d3037', 'top': 'a83cb46000bc1cbf83dbbf837998147c85c1fbca1bad67c19d74ae0d76114774', 'right': '7ba242bbcb2e8a3479cfdd7f5cf57560469e9eecc29ad33bbf39c2591e55250c', 'left': '7519b88cf4fec30937b37dc4d001e8d6928b3ee303d6d7631e161453c0d20d31', 'bottom': 'c149104eb2d9f11bc3c56e8fd100d99a92b98bfdd6568d538200c0d6924fa9c2', 'rear': '3bf941fbbee9d8c4cb5f59cc17cf8f69eb094821f3567dc9a370cee735c29542'}
left_final='76f2bc8113491462b71dc3d7591e29ea73021e0a4a7c46b5e5568a3c6663fe9f'
for v,h in rev_hashes.items():
 p=VD/f'{OBJ}.{v}.png'
 if v=='left' and sha(p)==left_final: continue
 if sha(p)!=h:raise SystemExit(f'captured current-hash guard failed: {v}')
# Use exact horizontal extents of the accepted three principal side/elevation profiles as common Z.
boxes=[]
for v in ('front','right','rear'):
 im=Image.open(VD/f'{OBJ}.{v}.png').convert('RGBA');mask=im.getchannel('A').point(lambda x:255 if x>=245 else 0);boxes.append(mask.getbbox())
target_h=round(sorted(b[3]-b[1] for b in boxes)[1])
p=VD/f'{OBJ}.{VIEW}.png'
if sha(p)==left_final: print('already installed'); raise SystemExit(0)
im=Image.open(p).convert('RGBA');bb=im.getchannel('A').point(lambda x:255 if x>=245 else 0).getbbox();
if not bb:raise SystemExit('empty left profile')
crop=im.crop(bb);scale=target_h/crop.height;size=(round(crop.width*scale),target_h)
if size[0]>256 or target_h>256:raise SystemExit(f'normalization would clip {size}')
crop=crop.resize(size,Image.Resampling.NEAREST);out=Image.new('RGBA',(256,256),(0,0,0,0));out.alpha_composite(crop,(128-size[0]//2,248-size[1]));
raw=VD/'raw/targeted-repairs';raw.mkdir(parents=True,exist_ok=True);shutil.copy2(p,raw/f'{OBJ}.left.before-scale.png');out.save(p,optimize=True)
mp=VD/f'{OBJ}.left.json';md=json.loads(mp.read_text());md['image']={'path':f'reusable/views-additional/{OBJ}.left.png','width':256,'height':256,'sha256':sha(p),'rgba_sha256':rgba_sha(out)};md['geometry_qa']='pending-review';md['provenance'].setdefault('repair_steps',[]).append({'operation':'uniform nearest-neighbor scaling of LEFT profile to common Z height','reference_views':['front','right','rear'],'reference_bbox_xyxy':[list(b) for b in boxes],'pre_scale_bbox_xyxy':list(bb),'target_height_px':target_h,'scale':scale,'render_size':list(size),'anchor_px':[128,248]});mp.write_text(json.dumps(md,indent=2)+'\n')
idxp=VD/'set-index.json';idx=json.loads(idxp.read_text());
for a in idx['assets']:
 if a.get('id')==md['id']:a.clear();a.update(md);break
g=next(x for x in idx['view_sets'] if x['object_id']==OBJ);g['complete']=False;g['geometry_qa']='pending-review';g['notes']='LEFT profile uniformly scaled to common elevation Z; all other directions preserved pending independent review.';idxp.write_text(json.dumps(idx,indent=2)+'\n')
recipe={'object_id':OBJ,'precondition_hashes':rev_hashes,'operation':'uniform nearest-neighbor scale LEFT to median accepted FRONT/RIGHT/REAR height','status':'installed-pending-review','target_height_px':target_h,'pre_scale_bbox':list(bb),'render_size':list(size)};(raw/f'{OBJ}-left-scale.json').write_text(json.dumps(recipe,indent=2)+'\n');print(json.dumps({'left_sha256':sha(p),'target_height_px':target_h,'before_bbox':bb,'render_size':size},indent=2))
