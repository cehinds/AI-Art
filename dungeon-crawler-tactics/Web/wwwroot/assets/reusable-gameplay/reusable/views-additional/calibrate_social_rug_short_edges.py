"""Uniformly calibrate the rectangular lounge rug short-edge projections."""
from pathlib import Path
from io import BytesIO
import hashlib,json,struct
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent;PACK=HERE.parents[1];INDEX=HERE/'set-index.json';OID='menu-concepts-safe-room-services--social-rug'
def sha(b):return hashlib.sha256(b).hexdigest()
def rgba(im):return sha(struct.pack('>II',*im.size)+im.convert('RGBA').tobytes())
idx=json.loads(INDEX.read_text());assets={a['id']:a for a in idx['assets']};outs={}
for view in ('right','left'):
 aid=f'{OID}.{view}';meta=json.loads((PACK/assets[aid]['metadata_path']).read_text());p=PACK/meta['image']['path'];old=p.read_bytes();input_sha=sha(old);frame=Image.open(p).convert('RGBA')
 # The accepted TOP footprint is 202 x 152px: short side is the projected world-Y depth.
 target=152; box=frame.getchannel('A').getbbox(); width=box[2]-box[0];scale=target/width
 nw=max(1,round(frame.width*scale));nh=max(1,round(frame.height*scale));small=frame.resize((nw,nh),Image.Resampling.NEAREST);offset=(128-nw//2,128-nh//2);out=Image.new('RGBA',(256,256));out.alpha_composite(small,offset);out.save(p,optimize=True)
 meta['image']['sha256']=sha(p.read_bytes());meta['image']['rgba_sha256']=rgba(out)
 meta['provenance']['postprocess']={'operation':'uniform-nearest-scale-about-anchor','input_sha256':input_sha,'scale':scale,'anchor_px':[128,128],'result_size_px':[nw,nh],'canvas_offset_px':list(offset),'reason':'short-side edge projection matches accepted rectangular TOP footprint Y-depth of 152px; uniform scaling only'}
 recipe_rel=f'reusable/views-additional/raw/social-rug-{view}-short-edge-calibration.recipe.json'
 recipe={'operation':'uniform-nearest-scale-about-anchor','input_image_id':aid,'input_sha256':input_sha,'scale':scale,'target_world_depth_px':target,'anchor_px':[128,128],'result_size_px':[nw,nh],'canvas_offset_px':list(offset),'output_id':aid,'notes':'Uniform scale only; aligns short-side edge extent with accepted rectangular plan depth.'}
 (PACK/recipe_rel).write_text(json.dumps(recipe,indent=2)+'\n');meta['provenance']['generation_recipe']=recipe_rel
 (PACK/assets[aid]['metadata_path']).write_text(json.dumps(meta,indent=2)+'\n');assets[aid]=meta;outs[aid]={'input_sha256':input_sha,'target_size':[nw,nh],'output_sha256':meta['image']['sha256'],'bbox':out.getchannel('A').getbbox()}
for g in idx['view_sets']:
 if g['object_id']==OID:g['complete']=False;g['geometry_qa']={'status':'pending-review','views':['top','right','left','bottom'],'atlas_self_inspected':True,'notes':'Rectangular rug pattern/underside and short-edge projections await independent review.'}
idx['assets']=[assets[a['id']] for a in idx['assets']];INDEX.write_text(json.dumps(idx,indent=2)+'\n');print(json.dumps(outs,indent=2))
