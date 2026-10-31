"""Rebuild only the generated right/left mat side projections from retained atlas."""
from pathlib import Path
import hashlib,json,struct,shutil
import numpy as np
from PIL import Image
OUT=Path(__file__).resolve().parent;PACK=OUT.parents[1]
raw_rel='reusable/views-additional/raw/training-mats-side-projections-atlas.png';raw=PACK/raw_rel;atlas=Image.open(raw).convert('RGBA');arr=np.asarray(atlas);h,w=arr.shape[:2]
objects=['menu-concepts-safe-room-services--training-blue-mat','menu-concepts-safe-room-services--training-red-mat'];views=['right','left'];idxp=OUT/'set-index.json';idx=json.loads(idxp.read_text());assets={a['id']:a for a in idx['assets']};backup=OUT/'raw'/'callback-inputs';backup.mkdir(parents=True,exist_ok=True);changes=[]
for row,oid in enumerate(objects):
 for col,view in enumerate(views):
  x0=round(col*w/2);x1=round((col+1)*w/2);y0=round(row*h/2);y1=round((row+1)*h/2)
  cell=atlas.crop((x0,y0,x1,y1));ca=np.asarray(cell);mask=ca[:,:,3]>=245;ys,xs=np.where(mask)
  if not len(xs):raise RuntimeError(f'no opaque pixels in row{row} col{col}')
  bounds=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)]
  local=np.asarray(cell.crop(bounds)).copy();local[:,:,3]=(local[:,:,3]>=245).astype('uint8')*255;crop=Image.fromarray(local,'RGBA')
  scale=.17;nw,nh=round(crop.width*scale),round(crop.height*scale);crop=crop.resize((nw,nh),Image.Resampling.NEAREST)
  frame=Image.new('RGBA',(256,256));offset=(128-nw//2,128-nh//2);frame.alpha_composite(crop,offset)
  aid=f'{oid}.{view}';meta=assets[aid];dest=PACK/meta['image']['path'];backup_file=backup/f'{aid}.before-side-projection-fix.png';old=dest.read_bytes();old_hash=hashlib.sha256(old).hexdigest()
  if not backup_file.exists():shutil.copy2(dest,backup_file)
  frame.save(dest,optimize=True);meta['image']['sha256']=hashlib.sha256(dest.read_bytes()).hexdigest();meta['image']['rgba_sha256']=hashlib.sha256(struct.pack('>II',256,256)+frame.tobytes()).hexdigest()
  meta['provenance'].update({'source_atlas':raw_rel,'source_atlas_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'generation_recipe':'reusable/views-additional/raw/training-mats-side-projections.recipe.json','notes':'Inferred orthographic side edge for a flat rectangular training mat; unseen surface details remain inferred.','crop_bounds_px':{'nominal_cell':{'column':col,'row':row,'bounds':[x0,y0,x1,y1]},'alpha_bounds_global':[x0+bounds[0],y0+bounds[1],x0+bounds[2],y0+bounds[3]],'cell_alpha_bounds':bounds,'alpha_threshold':245,'resized_bounds_px':[nw,nh],'canvas_offset_px':list(offset),'shared_scale':scale},'postprocess':{'operation':'threshold-alpha-crop-isotropic-nearest-resize','input_sha256':hashlib.sha256(raw.read_bytes()).hexdigest()}})
  (OUT/f'{aid}.json').write_text(json.dumps(meta,indent=2)+'\n');changes.append({'id':aid,'old_sha256':old_hash,'new_sha256':meta['image']['sha256'],'crop_bounds':bounds,'size':[nw,nh]})
for i,a in enumerate(idx['assets']):
 if a['id'] in assets:idx['assets'][i]=assets[a['id']]
for g in idx['view_sets']:
 if g['object_id'] in objects:g['complete']=False;g['notes']='Targeted mat edge-view correction awaits independent review.';g['geometry_qa']={'status':'pending-review','views':['right','left'],'notes':'Generated side elevations calibrated to the mat short Y-depth from the accepted plan; fresh independent review required.','atlas_self_inspected':True}
idxp.write_text(json.dumps(idx,indent=2)+'\n');(OUT/'raw'/'training-mats-side-projections.recipe.json').write_text(json.dumps({'raw_atlas':raw_rel,'grid':{'columns':2,'rows':2,'columns_are':['right','left'],'rows_are':objects},'alpha_threshold':245,'shared_scale':.17,'anchor_px':[128,128],'changes':changes},indent=2)+'\n');print(json.dumps(changes))
