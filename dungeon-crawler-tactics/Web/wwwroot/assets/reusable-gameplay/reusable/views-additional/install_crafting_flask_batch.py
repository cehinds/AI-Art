"""Install the three source-faithful crafting flask six-view rows from one retained atlas."""
from pathlib import Path
import hashlib,io,json,struct
from PIL import Image
import numpy as np
from scipy import ndimage
HERE=Path(__file__).resolve().parent;PACK=HERE.parents[1];INDEX=HERE/'set-index.json'
ATLAS_REL='reusable/views-additional/raw/crafting-three-flasks-sixview-atlas.png';ATLAS=PACK/ATLAS_REL
OBJECTS=[
 ('menu-concepts-safe-room-services--crafting-blue-bottle','Pale Lavender Pear Flask',97),
 ('menu-concepts-safe-room-services--crafting-green-round-bottle','Emerald Round Flask',114),
 ('menu-concepts-safe-room-services--crafting-purple-flask','Magenta Spherical Flask',120),
]
VIEWS=('front','top','right','left','bottom','rear');THRESHOLD=245;REQUEST='exec-fafac2b6-9be9-445b-9bb0-a56858e0220f'
def sha(b):return hashlib.sha256(b).hexdigest()
def rgba_hash(im):return sha(struct.pack('>II',im.width,im.height)+im.convert('RGBA').tobytes())
idx=json.loads(INDEX.read_text());assets={a['id']:a for a in idx['assets']};groups={g['object_id']:g for g in idx['view_sets']};atlas=Image.open(ATLAS).convert('RGBA');arr=np.asarray(atlas);H,W=arr.shape[:2];assert (H,W)==(887,1774)
labels,n=ndimage.label(arr[:,:,3]>=THRESHOLD,np.ones((3,3),dtype=np.uint8));summary={}
for row,(obj,name,target_front_h) in enumerate(OBJECTS):
 front_bounds=None
 for col,view in enumerate(VIEWS):
  x0=round(col*W/6);x1=round((col+1)*W/6);y0=round(row*H/3);y1=round((row+1)*H/3)
  local=labels[y0:y1,x0:x1];counts=np.bincount(local.ravel());counts[0]=0;label=int(counts.argmax());
  if counts[label]<1000:raise RuntimeError(f'{obj}.{view}: empty/weak cell')
  local_y,local_x=np.where(local==label);sx=int(local_x[len(local_x)//2]+x0);sy=int(local_y[len(local_y)//2]+y0);global_label=int(labels[sy,sx]);ys,xs=np.where(labels==global_label);bounds=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)];mask=labels[bounds[1]:bounds[3],bounds[0]:bounds[2]]==global_label
  piece=atlas.crop(tuple(bounds));piece.putalpha(Image.fromarray((mask*255).astype('uint8')))
  if view=='front':scale=target_front_h/piece.height;front_bounds=bounds
  w=max(1,round(piece.width*scale));h=max(1,round(piece.height*scale));piece=piece.resize((w,h),Image.Resampling.NEAREST);offset=(128-w//2,128-h//2);frame=Image.new('RGBA',(256,256));frame.alpha_composite(piece,offset)
  aid=f'{obj}.{view}';meta=json.loads((PACK/assets[aid]['metadata_path']).read_text());png_path=PACK/meta['image']['path'];frame.save(png_path,optimize=True);encoded=png_path.read_bytes();meta['image']['sha256']=sha(encoded);meta['image']['rgba_sha256']=rgba_hash(frame);meta['name']=f'{name} {view.title()}'
  native_rel=f'reusable/native/{obj}.png';native_sha=sha((PACK/native_rel).read_bytes());crop_rel=f'reusable/views-additional/raw/crafting-flask-{row+1}-{view}-component.png';crop_path=PACK/crop_rel;piece.save(crop_path,optimize=True)
  notes=f'Inferred orthographic {view} of {name}. Identity, reservoir silhouette, gray neck/rim and color follow the canonical source crop; unseen contents and surfaces are not recovered pixels.'
  recipe_rel=f'reusable/views-additional/raw/crafting-flask-{row+1}-{view}.recipe.json'
  pr=meta['provenance'];pr.update({'method':'generated','source_image':native_rel,'native_front':native_rel,'native_front_sha256':native_sha,'reference_source_image':native_rel,'reference_source_sha256':native_sha,'source_atlas':ATLAS_REL,'source_atlas_sha256':sha(ATLAS.read_bytes()),'generation_recipe':recipe_rel,'source_crop_path':crop_rel,'source_crop_sha256':sha(crop_path.read_bytes()),'notes':notes,'crop_bounds_px':{'selection_mode':'largest_component_alpha_ge_245','nominal_cell':{'column':col,'row':row,'bounds':[x0,y0,x1,y1]},'alpha_bounds_global':bounds,'component_labels':[global_label],'resized_bounds_px':[w,h],'canvas_offset_px':list(offset),'shared_scale':scale,'anchor_px':[128,128]}})
  recipe={'operation':'largest-global-component-per-atlas-cell-uniform-nearest-fit','request_id':REQUEST,'input_atlas':ATLAS_REL,'input_sha256':sha(ATLAS.read_bytes()),'row':row,'column':col,'view':view,'alpha_threshold':THRESHOLD,'global_component_label':global_label,'component_bounds_px':bounds,'uniform_scale':scale,'target_size_px':[w,h],'canvas_offset_px':list(offset),'anchor_px':[128,128],'reference_source':native_rel,'reference_source_sha256':native_sha,'output_crop':crop_rel,'output_id':aid,'notes':notes}
  (PACK/recipe_rel).write_text(json.dumps(recipe,indent=2)+'\n');(PACK/meta['metadata_path']).write_text(json.dumps(meta,indent=2)+'\n');assets[aid]=meta
  summary.setdefault(obj,{})[view]={'bbox':frame.getchannel('A').getbbox(),'size':[w,h],'sha256':meta['image']['sha256']}
 group=groups[obj];group['complete']=False;group['geometry_qa']={'status':'pending-review','views':list(VIEWS),'notes':'Canonical three-flask identity/proportion correction awaits independent source-plus-six review.','atlas_self_inspected':True};group['notes']='Three distinct crafting flasks rebuilt source-faithfully; pending independent review.'
idx['assets']=[assets[a['id']] for a in idx['assets']];idx['view_sets']=[groups[g['object_id']] for g in idx['view_sets']];INDEX.write_text(json.dumps(idx,indent=2)+'\n')
print(json.dumps({'atlas_sha256':sha(ATLAS.read_bytes()),'source_rows':OBJECTS,'views':summary},indent=2))
