#!/usr/bin/env python3
"""Replace one inferred direction for listed source IDs from a retained atlas recipe."""
import hashlib,json,math,os,pathlib,struct,tempfile
import numpy as np
from PIL import Image
from scipy import ndimage
OUT=pathlib.Path(__file__).resolve().parent;PACK=OUT.parents[1]

def atomic_json(path,value):
 fd,tmp=tempfile.mkstemp(dir=path.parent,prefix=path.name+'.',suffix='.tmp')
 try:
  with os.fdopen(fd,'w',encoding='utf-8') as f:json.dump(value,f,indent=2,ensure_ascii=False);f.write('\n');f.flush();os.fsync(f.fileno())
  os.replace(tmp,path)
 except BaseException:
  try:os.unlink(tmp)
  except FileNotFoundError:pass
  raise

def main(recipe_path):
 rp=pathlib.Path(recipe_path)
 if not rp.is_absolute():rp=OUT/rp
 recipe=json.loads(rp.read_text());atlas_path=OUT/'raw'/recipe['atlas'];atlas=Image.open(atlas_path).convert('RGBA');arr=np.asarray(atlas);alpha=arr[:,:,3]>=16
 labels,n=ndimage.label(alpha,np.ones((3,3),dtype=np.uint8));counts=np.bincount(labels.ravel(),minlength=n+1);h,w=alpha.shape
 cols,rows=recipe['grid']['columns'],recipe['grid']['rows'];source_ids=recipe['source_ids'];direction=recipe['corrected_view']
 if len(source_ids)!=cols*rows:raise ValueError('source_ids must match atlas grid')
 assigned={i:[] for i in range(cols*rows)};boxes={};centers=[((c+.5)*w/cols,(r+.5)*h/rows) for r in range(rows) for c in range(cols)]
 for lab in range(1,n+1):
  if counts[lab]<4:continue
  ys,xs=np.where(labels==lab);cx=float(xs.mean());cy=float(ys.mean());idx=min(range(len(centers)),key=lambda i:((cx-centers[i][0])/(w/cols))**2+((cy-centers[i][1])/(h/rows))**2)
  assigned[idx].append(lab);boxes[lab]=(int(xs.min()),int(ys.min()),int(xs.max())+1,int(ys.max())+1)
 index_path=OUT/'set-index.json';index=json.loads(index_path.read_text());asset_map={a['id']:a for a in index['assets']};set_map={s.get('source_id',s['object_id']):s for s in index['view_sets']};raw_sha=hashlib.sha256(atlas_path.read_bytes()).hexdigest()
 for idx,source_id in enumerate(source_ids):
  object_id=source_id.removesuffix('--native')
  labs=assigned[idx]
  if not labs:raise ValueError(f'no components for {source_id} in cell {idx}')
  center=centers[idx];main_label=max(labs,key=lambda lab:counts[lab]);main_box=boxes[main_label]
  def gap(a,b):
   dx=max(0,b[0]-a[2],a[0]-b[2]);dy=max(0,b[1]-a[3],a[1]-b[3]);return math.hypot(dx,dy)
  radius=min(w/cols,h/rows)*.1
  keep=[lab for lab in labs if lab==main_label or counts[lab]>=counts[main_label]*.02 or gap(main_box,boxes[lab])<=radius]
  bounds=[min(boxes[x][0] for x in keep),min(boxes[x][1] for x in keep),max(boxes[x][2] for x in keep),max(boxes[x][3] for x in keep)]
  mask=np.isin(labels,keep);crop=atlas.crop(tuple(bounds));local=mask[bounds[1]:bounds[3],bounds[0]:bounds[2]];crop.putalpha(Image.fromarray(np.where(local,np.asarray(crop.getchannel('A')),0).astype('uint8')))
  src_path=PACK/recipe['source_images'][idx]
  other_sizes=[]
  for other_view in ('front','top','right','left','bottom','rear'):
   if other_view==direction: continue
   other_path=OUT/f'{object_id}.{other_view}.png'
   if other_path.exists():
    other=Image.open(other_path).convert('RGBA');bb=other.getchannel('A').getbbox()
    if bb: other_sizes.append(max(bb[2]-bb[0],bb[3]-bb[1]))
  target=max(other_sizes) if other_sizes else 232
  fixed_dimension=recipe.get('target_dimension_px')
  if isinstance(fixed_dimension,list): fixed_dimension=fixed_dimension[idx]
  target_axis=recipe.get('target_dimension_axis','max')
  if fixed_dimension is not None:
   if target_axis=='width': scale=float(fixed_dimension)/crop.width
   elif target_axis=='height': scale=float(fixed_dimension)/crop.height
   elif target_axis=='max': scale=float(fixed_dimension)/max(crop.size)
   else: raise ValueError(f'unsupported target_dimension_axis: {target_axis}')
  else: scale=target/max(crop.size)
  nw,nh=max(1,round(crop.width*scale)),max(1,round(crop.height*scale));resampling={'nearest':Image.Resampling.NEAREST,'lanczos':Image.Resampling.LANCZOS}.get(recipe.get('resampling','lanczos'))
  if resampling is None:raise ValueError(f"unsupported resampling: {recipe.get('resampling')}")
  piece=crop.resize((nw,nh),resampling)
  frame=Image.new('RGBA',(256,256),(0,0,0,0));offset=(128-nw//2,128-nh//2);frame.alpha_composite(piece,offset)
  asset_id=f'{object_id}.{direction}';filename=f'{asset_id}.png';dest=OUT/filename;frame.save(dest,optimize=True)
  sha=hashlib.sha256(dest.read_bytes()).hexdigest();rgba_sha=hashlib.sha256(struct.pack('>II',256,256)+frame.tobytes()).hexdigest()
  meta_path=OUT/f'{asset_id}.json';meta=json.loads(meta_path.read_text());meta['image'].update({'path':f'reusable/views-additional/{filename}','width':256,'height':256,'sha256':sha,'rgba_sha256':rgba_sha})
  source_meta=json.loads(src_path.with_suffix('.json').read_text());meta['provenance']={'method':recipe.get('method','generated'),'source_image':recipe['source_images'][idx],'source_sha256':source_meta['image']['sha256'],'notes':recipe.get('provenance_notes','inferred orthographic view, not recovered pixels; not calibrated 3D'),'source_atlas':str(atlas_path.relative_to(PACK)),'source_atlas_sha256':raw_sha,'generation_recipe':rp.relative_to(PACK).as_posix(),'crop_bounds_px':{'nominal_cell':{'row':idx//cols,'column':idx%cols,'bounds':[round((idx%cols)*w/cols),round((idx//cols)*h/rows),round((idx%cols+1)*w/cols),round((idx//cols+1)*h/rows)]},'alpha_bounds_global':bounds,'component_labels':keep,'resized_bounds_px':[nw,nh],'canvas_offset_px':list(offset),'shared_scale':scale}}
  atomic_json(meta_path,meta);asset_map[asset_id].update({'image':meta['image'],'provenance':meta['provenance']})
  if source_id not in set_map:raise KeyError(f'missing view set {source_id}')
  set_map[source_id]['complete']=False
 value={'assets':list(asset_map.values()),'view_sets':list(set_map.values())};atomic_json(index_path,value)
 manifest=json.loads((PACK/'manifest.json').read_text())['assets'];present={s.get('source_id',s['object_id']) for s in value['view_sets']};progress={'schema_version':1,'total_objects':len(manifest),'indexed_objects':len(present),'indexed_view_assets':len(value['assets']),'complete_sets':sum(1 for s in value['view_sets'] if s.get('complete')),'incomplete_sets':sum(1 for s in value['view_sets'] if not s.get('complete')),'missing_source_ids':[x['id'] for x in manifest if x['id'] not in present]};atomic_json(OUT/'progress.json',progress)
 print(json.dumps({'updated_ids':source_ids,'direction':direction,'atlas_sha256':raw_sha}))
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('recipe');main(p.parse_args().recipe)
