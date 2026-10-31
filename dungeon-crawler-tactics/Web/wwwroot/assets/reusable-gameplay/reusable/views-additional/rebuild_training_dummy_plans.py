"""Deterministically extract and normalize the generated training-dummy top/bottom atlas."""
from pathlib import Path
import hashlib,json,struct,shutil
import numpy as np
from PIL import Image
OUT=Path(__file__).resolve().parent; PACK=OUT.parents[1]
OID='menu-concepts-safe-room-services--training-dummy'
raw_rel='reusable/views-additional/raw/training-dummy-plan-correction-atlas.png'; raw=PACK/raw_rel
atlas=Image.open(raw).convert('RGBA'); w,h=atlas.size
if w < 2*h*.85: raise RuntimeError(f'expected two-column atlas, got {atlas.size}')
index_path=OUT/'set-index.json'; index=json.loads(index_path.read_text()); assets={a['id']:a for a in index['assets']}
backup=OUT/'raw'/'callback-inputs';backup.mkdir(parents=True,exist_ok=True)
changes=[]
for col,view in enumerate(('top','bottom')):
    x0=round(col*w/2); x1=round((col+1)*w/2)
    cell=atlas.crop((x0,0,x1,h)); arr=np.asarray(cell); mask=arr[:,:,3]>=245
    ys,xs=np.where(mask)
    if len(xs)==0: raise RuntimeError(f'empty generated {view} cell')
    bounds=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)]
    local=np.asarray(cell.crop(bounds)).copy(); local[:,:,3]=(local[:,:,3]>=245).astype('uint8')*255
    crop=Image.fromarray(local,'RGBA')
    scale=.24; nw,nh=round(crop.width*scale),round(crop.height*scale)
    crop=crop.resize((nw,nh),Image.Resampling.NEAREST)
    frame=Image.new('RGBA',(256,256)); offset=(128-nw//2,128-nh//2); frame.alpha_composite(crop,offset)
    aid=f'{OID}.{view}'; meta=assets[aid]; dest=PACK/meta['image']['path']; old=dest.read_bytes(); old_hash=hashlib.sha256(old).hexdigest(); shutil.copy2(dest,backup/f'{aid}.before-square-platform-correction.png');frame.save(dest,optimize=True)
    meta['image']['sha256']=hashlib.sha256(dest.read_bytes()).hexdigest();meta['image']['rgba_sha256']=hashlib.sha256(struct.pack('>II',256,256)+frame.tobytes()).hexdigest()
    meta['provenance'].update({'method':'generated','source_atlas':raw_rel,'source_atlas_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'generation_recipe':'reusable/views-additional/raw/training-dummy-plan-correction.recipe.json','notes':'Inferred orthographic plan projection; square wood-platform construction follows visible source evidence, unseen surfaces remain inferred.','crop_bounds_px':{'nominal_cell':{'column':col,'row':0,'bounds':[x0,0,x1,h]},'alpha_bounds_global':[x0+bounds[0],bounds[1],x0+bounds[2],bounds[3]],'cell_alpha_bounds':bounds,'component_labels':'all alpha>=245 pixels in isolated cell','resized_bounds_px':[nw,nh],'canvas_offset_px':list(offset),'shared_scale':scale}})
    (OUT/f'{aid}.json').write_text(json.dumps(meta,indent=2)+'\n');changes.append({'id':aid,'input_sha256':old_hash,'output_sha256':meta['image']['sha256'],'crop_bounds':[x0+bounds[0],bounds[1],x0+bounds[2],bounds[3]],'size':[nw,nh],'offset':offset})
for i,a in enumerate(index['assets']):
    if a['id'] in assets:index['assets'][i]=assets[a['id']]
for g in index['view_sets']:
    if g['object_id']==OID:
        g['complete']=False;g['notes']='Targeted square-platform TOP/BOTTOM correction awaits independent review.';g['geometry_qa']={'status':'pending-review','views':['top','bottom'],'notes':'Source depicts square wood platform; corrected generated top/bottom projections; awaiting fresh independent review.','atlas_self_inspected':True}
index_path.write_text(json.dumps(index,indent=2)+'\n')
(OUT/'raw'/'training-dummy-plan-correction.recipe.json').write_text(json.dumps({'raw_atlas':raw_rel,'grid':{'columns':2,'rows':1,'views':['top','bottom']},'alpha_threshold':245,'shared_scale':.24,'anchor_px':[128,128],'changes':changes},indent=2)+'\n')
print(json.dumps(changes))
