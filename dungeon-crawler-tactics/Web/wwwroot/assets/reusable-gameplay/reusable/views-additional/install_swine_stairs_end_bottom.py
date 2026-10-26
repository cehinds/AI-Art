"""Install corrected stair end elevations and opaque underside from retained atlases."""
from pathlib import Path
import hashlib,json,struct
from PIL import Image
import numpy as np
from scipy import ndimage
HERE=Path(__file__).resolve().parent;PACK=HERE.parents[1];INDEX=HERE/'set-index.json';OBJECT='concepts-boss-swine-concept-stairs'
ATLAS_REL='reusable/views-additional/raw/swine-stairs-end-bottom-corrections-atlas.png';BOTTOM_REL='reusable/views-additional/raw/swine-stairs-bottom-underside-atlas-v3.png';SRC_CTX=Path('/workspace/scratch/scene-proxy-references/gameplay/concepts-boss-swine-concept-stairs.png');CTX_REL='reusable/views-additional/raw/swine-stairs-source-context-reference.png'
REQUESTS={'front':'exec-959fb18c-64af-420a-a60c-a0096cf52aa3','rear':'exec-959fb18c-64af-420a-a60c-a0096cf52aa3','bottom':'exec-bb049c54-0c6a-43ff-aea5-3c14315984ca'};THRESHOLD=245
def sha(b):return hashlib.sha256(b).hexdigest()
def rgba(im):return sha(struct.pack('>II',256,256)+im.convert('RGBA').tobytes())
idx=json.loads(INDEX.read_text());assets={a['id']:a for a in idx['assets']};atlases={'front':(ATLAS_REL,Image.open(PACK/ATLAS_REL).convert('RGBA'),0),'rear':(ATLAS_REL,Image.open(PACK/ATLAS_REL).convert('RGBA'),2),'bottom':(BOTTOM_REL,Image.open(PACK/BOTTOM_REL).convert('RGBA'),None)}
ctx=PACK/CTX_REL;ctx.write_bytes(SRC_CTX.read_bytes());ctxsha=sha(ctx.read_bytes())
# Common target dimensions come from the accepted TOP and side projections.
top=Image.open(PACK/assets[f'{OBJECT}.top']['image']['path']).convert('RGBA').getchannel('A').getbbox();side=Image.open(PACK/assets[f'{OBJECT}.right']['image']['path']).convert('RGBA').getchannel('A').getbbox();target_x=top[2]-top[0];target_y=top[3]-top[1];target_z=side[3]-side[1];summary={}
for view,(atlas_rel,atlas,col) in atlases.items():
 arr=np.asarray(atlas);H,W=arr.shape[:2];labels,n=ndimage.label(arr[:,:,3]>=THRESHOLD,np.ones((3,3),dtype=np.uint8))
 if col is None:
  counts=np.bincount(labels.ravel());counts[0]=0;lab=int(counts.argmax())
 else:
  x0=round(col*W/3);x1=round((col+1)*W/3);local=labels[:,x0:x1];counts=np.bincount(local.ravel());counts[0]=0;ll=int(counts.argmax());ys0,xs0=np.where(local==ll);sx=int(xs0[len(xs0)//2]+x0);sy=int(ys0[len(ys0)//2]);lab=int(labels[sy,sx])
 ys,xs=np.where(labels==lab);bounds=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)];mask=labels[bounds[1]:bounds[3],bounds[0]:bounds[2]]==lab;piece=atlas.crop(tuple(bounds));piece.putalpha(Image.fromarray((mask*255).astype('uint8')))
 target_height=target_z if view in ('front','rear') else target_y;scale=target_height/piece.height;w=max(1,round(piece.width*scale));h=max(1,round(piece.height*scale));piece=piece.resize((w,h),Image.Resampling.NEAREST);offset=(128-w//2,128-h//2);frame=Image.new('RGBA',(256,256));frame.alpha_composite(piece,offset)
 aid=f'{OBJECT}.{view}';meta=json.loads((PACK/assets[aid]['metadata_path']).read_text());out=PACK/meta['image']['path'];frame.save(out,optimize=True);encoded=out.read_bytes();meta['image']['sha256']=sha(encoded);meta['image']['rgba_sha256']=rgba(frame);crop_rel=f'reusable/views-additional/raw/swine-stairs-{view}-projection.png';crop=PACK/crop_rel;piece.save(crop,optimize=True);recipe_rel=f'reusable/views-additional/raw/swine-stairs-{view}-projection.recipe.json';notes=f'Inferred orthographic {view} of the source staircase. End views show level riser courses and fixed thin rail edges; underside shows the full opaque stone footprint, not upper treads. Hidden stone construction is illustrative, not recovered pixels.'
 pr=meta['provenance'];pr.update({'source_atlas':atlas_rel,'source_atlas_sha256':sha((PACK/atlas_rel).read_bytes()),'generation_recipe':recipe_rel,'source_crop_path':crop_rel,'source_crop_sha256':sha(crop.read_bytes()),'reference_source_image':CTX_REL,'reference_source_sha256':ctxsha,'notes':notes,'crop_bounds_px':{'selection_mode':'largest_component_alpha_ge_245','alpha_bounds_global':bounds,'component_labels':[lab],'nominal_cell':{'column':col,'row':0} if col is not None else None,'resized_bounds_px':[w,h],'canvas_offset_px':list(offset),'uniform_scale':scale,'target_physical_extent_px':{'z':target_z,'y':target_y},'anchor_px':[128,128]}})
 recipe={'operation':'extract-largest-component-uniform-nearest-fit','request_id':REQUESTS[view],'input_atlas':atlas_rel,'input_sha256':sha((PACK/atlas_rel).read_bytes()),'alpha_threshold':THRESHOLD,'view':view,'global_component_label':lab,'component_bounds_px':bounds,'uniform_scale':scale,'target_size_px':[w,h],'canvas_offset_px':list(offset),'anchor_px':[128,128],'reference_source_image':CTX_REL,'reference_source_sha256':ctxsha,'accepted_axis_references':{'top_size_px':[target_x,target_y],'side_height_px':target_z},'output_crop':crop_rel,'output_id':aid,'notes':notes}
 (PACK/recipe_rel).write_text(json.dumps(recipe,indent=2)+'\n');(PACK/meta['metadata_path']).write_text(json.dumps(meta,indent=2)+'\n');assets[aid]=meta;summary[view]={'bbox':frame.getchannel('A').getbbox(),'size':[w,h],'scale':scale,'sha256':meta['image']['sha256']}
for g in idx['view_sets']:
 if g['object_id']==OBJECT:g['complete']=False;g['geometry_qa']={'status':'pending-review','views':['front','bottom','rear'],'notes':'Level end elevations and full opaque underside await independent review.','atlas_self_inspected':True};g['notes']='Targeted front/rear/bottom corrections; accepted top and side views preserved.'
idx['assets']=[assets[a['id']] for a in idx['assets']];INDEX.write_text(json.dumps(idx,indent=2)+'\n');print(json.dumps({'object_id':OBJECT,'targets':{'x':target_x,'y':target_y,'z':target_z},'views':summary},indent=2))
