#!/usr/bin/env python3
"""Uniformly reduce the accepted River Reeds underside footprint to common scale."""
from pathlib import Path
import hashlib,json,struct
import numpy as np
from PIL import Image
PACK=Path(__file__).resolve().parents[4]; VD=PACK/'reusable/views-additional'; O='hunting-river-river-reeds'
IMG=VD/f'{O}.bottom.png'; META=VD/f'{O}.bottom.json'; IDX=VD/'set-index.json'
EXPECTED_INPUT='93efdf4e6c8e1056b55f65db5db97117c87e1c419314da4add7cdb1d40dcd8bd'; FACTOR=0.65
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rsha(im):return hashlib.sha256(struct.pack('>II',*im.size)+im.convert('RGBA').tobytes()).hexdigest()
md=json.loads(META.read_text()); current=sha(IMG)
if current!=EXPECTED_INPUT:
 if md.get('provenance',{}).get('normalization',{}).get('post_scale_recipe')=='river-reeds-bottom-scale-v1':
  raise SystemExit('already scaled; verify stored output hash instead of reapplying')
 raise SystemExit(f'input hash changed: {current}')
source=PACK/md['provenance']['source_image']
if sha(source)!=md['provenance']['source_sha256']: raise SystemExit('source changed')
im=Image.open(IMG).convert('RGBA'); alpha=np.asarray(im.getchannel('A')); y,x=np.where(alpha>0)
box=(int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)); body=im.crop(box)
size=(round(body.width*FACTOR),round(body.height*FACTOR)); body=body.resize(size,Image.Resampling.NEAREST)
out=Image.new('RGBA',(256,256),(0,0,0,0)); out.alpha_composite(body,(128-size[0]//2,248-size[1])); out.save(IMG,optimize=True)
md['image']={'path':f'reusable/views-additional/{O}.bottom.png','width':256,'height':256,'sha256':sha(IMG),'rgba_sha256':rsha(out)}
md['geometry_qa']='pending-review'; md['provenance']['normalization']['prior_input_sha256']=EXPECTED_INPUT;md['provenance']['normalization']['post_scale_recipe']='river-reeds-bottom-scale-v1';md['provenance']['normalization']['post_scale_factor']=FACTOR;md['provenance']['normalization']['prior_bbox_px']=list(box);md['provenance']['normalization']['post_scale_render_size']=list(size);md['provenance']['normalization']['resampling']='NEAREST';md['provenance']['notes']='Accepted submerged underside content uniformly reduced to the requested common plan X scale; material and aspect preserved.'
META.write_text(json.dumps(md,indent=2)+'\n');idx=json.loads(IDX.read_text())
for a in idx['assets']:
 if a.get('id')==md['id']:a.clear();a.update(md);break
g=next(g for g in idx['view_sets'] if g['object_id']==O);g['complete']=False;g['geometry_qa']='pending-review';g['notes']='Only BOTTOM uniformly scaled to match common plan width; independent review pending.';IDX.write_text(json.dumps(idx,indent=2)+'\n')
recipe={'object_id':O,'operation':'uniform nearest-neighbor scale of current BOTTOM alpha crop','input_sha256':EXPECTED_INPUT,'scale':FACTOR,'input_bbox_px':list(box),'output_sha256':sha(IMG),'output_size':list(size),'anchor_px':[128,248],'resampling':'NEAREST','source_sha256':md['provenance']['source_sha256'],'notes':'Preserves accepted submerged underside content and aspect; no other directions touched.'}
(VD/'raw/targeted-repairs/river-reeds-bottom-scale-v1.json').write_text(json.dumps(recipe,indent=2)+'\n');print(json.dumps(recipe,indent=2))
