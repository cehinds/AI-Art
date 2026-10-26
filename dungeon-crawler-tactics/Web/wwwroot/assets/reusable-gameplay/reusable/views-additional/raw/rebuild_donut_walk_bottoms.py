"""Replay the two generated phase-specific Donut underside projections."""
from pathlib import Path
import hashlib, json, struct
import numpy as np
from PIL import Image
from scipy import ndimage
PACK=Path(__file__).resolve().parents[3]
OUT=PACK/'reusable/views-additional'
ATLAS_REL='reusable/views-additional/raw/donut-walk2-walk3-bottom-atlas.png'
ATLAS_PATH=PACK/ATLAS_REL
atlas=Image.open(ATLAS_PATH).convert('RGBA'); rgba=np.asarray(atlas)
labels,n=ndimage.label(rgba[:,:,3]>=245,np.ones((3,3),dtype=np.uint8))
rows=[('revamp--characters--donut--walk2',0,887),('revamp--characters--donut--walk3',887,1774)]
chosen=[]
for oid,y0,y1 in rows:
    stats=[]
    for lab in range(1,n+1):
        yy,xx=np.where(labels[y0:y1]==lab)
        if len(xx): stats.append((len(xx),lab,int(xx.min()),int(yy.min()+y0),int(xx.max()+1),int(yy.max()+y0+1)))
    chosen.append((oid,*max(stats)))
target_height=188
scale=target_height/(sum(c[-1]-c[-3] for c in chosen)/len(chosen))
idxp=OUT/'set-index.json'; idx=json.loads(idxp.read_text()); amap={a['id']:a for a in idx['assets']}
raw_hash=hashlib.sha256(ATLAS_PATH.read_bytes()).hexdigest()
recipe_rel='reusable/views-additional/raw/donut-walk2-walk3-bottom.recipe.json'
recipe={'request_id':'exec-d9c03f65-bc7d-4e18-be9d-18f29370cf0b','raw_atlas':ATLAS_REL,'raw_atlas_sha256':raw_hash,'layout':'one column, two rows; row 1 walk2, row 2 walk3','alpha_threshold':245,'selection':'largest connected alpha component per row; isolated alpha specks excluded','uniform_scale':scale,'target_height_px':target_height,'anchor_px':[128,128]}
(PACK/recipe_rel).write_text(json.dumps(recipe,indent=2)+'\n')
for oid,area,lab,x0,y0,x1,y1 in chosen:
    aid=f'{oid}.bottom'; meta=amap[aid]; crop=atlas.crop((x0,y0,x1,y1))
    mask=labels[y0:y1,x0:x1]==lab
    crop.putalpha(Image.fromarray((mask*255).astype('uint8')))
    w=max(1,round(crop.width*scale)); h=max(1,round(crop.height*scale))
    crop=crop.resize((w,h),Image.Resampling.NEAREST)
    offset=(128-w//2,128-h//2); frame=Image.new('RGBA',(256,256)); frame.alpha_composite(crop,offset)
    dest=PACK/meta['image']['path']; frame.save(dest,optimize=True); encoded=dest.read_bytes()
    meta['image']['sha256']=hashlib.sha256(encoded).hexdigest()
    meta['image']['rgba_sha256']=hashlib.sha256(struct.pack('>II',256,256)+frame.tobytes()).hexdigest()
    meta['provenance'].update({'method':'generated','source_image':f'reusable/native/{oid}.png','native_front':f'reusable/native/{oid}.png','native_front_sha256':hashlib.sha256((PACK/f'reusable/native/{oid}.png').read_bytes()).hexdigest(),'source_atlas':ATLAS_REL,'source_atlas_sha256':raw_hash,'generation_recipe':recipe_rel,'crop_bounds_px':{'alpha_bounds_global':[x0,y0,x1,y1],'component_labels':[lab],'resized_bounds_px':[w,h],'canvas_offset_px':list(offset),'shared_scale':scale,'selection_mode':'largest-connected-component-per-row','alpha_threshold':245,'target_extent_from_view':'revamp--characters--donut--walk1.bottom','row':1 if 'walk2' in oid else 2},'notes':'Inferred strict below-camera view of this exact walking phase; pale belly, undersides of paws and legs face camera; dorsal fur, crown and eyes are occluded. Distinct gait footprint preserved. Hidden surfaces are illustrative inference, not recovered pixels.'})
    (PACK/meta['metadata_path']).write_text(json.dumps(meta,indent=2)+'\n'); amap[aid]=meta
    print(aid, [x0,y0,x1,y1], [w,h], offset, scale, meta['image']['sha256'])
for i,a in enumerate(idx['assets']): idx['assets'][i]=amap[a['id']]
for g in idx['view_sets']:
    if g['object_id'] in {x[0] for x in rows}:
        g['complete']=False; g['geometry_qa']={'status':'pending-review','views':['bottom'],'atlas_self_inspected':True,'notes':'Phase-specific orthographic undersides; awaiting independent Page source-plus-six review.'}
idxp.write_text(json.dumps(idx,indent=2)+'\n')
