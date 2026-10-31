"""Install the source-faithful two end elevations from a retained transparent atlas."""
from pathlib import Path
import hashlib, json, struct
import numpy as np
from PIL import Image
from scipy import ndimage
HERE=Path(__file__).resolve().parent
PACK=HERE.parents[1]
INDEX=HERE/'set-index.json'
ATLAS_REL='reusable/views-additional/raw/swine-stairs-fixed-endviews-atlas.png'
OBJECT='concepts-boss-swine-concept-stairs'
THRESHOLD=245

def file_sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def rgba_sha(im):
    im=im.convert('RGBA')
    return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()

atlas_path=PACK/ATLAS_REL
atlas=Image.open(atlas_path).convert('RGBA')
a=np.asarray(atlas)
labels,n=ndimage.label(a[:,:,3]>=THRESHOLD,np.ones((3,3),dtype=np.uint8))
idx=json.loads(INDEX.read_text())
assets={a['id']:a for a in idx['assets']}
# Physical Z height is calibrated to the already accepted right/left elevations.
side=Image.open(PACK/assets[f'{OBJECT}.right']['image']['path']).convert('RGBA').getchannel('A').getbbox()
target_z=side[3]-side[1]
requests={'front':'exec-e3f52fd1-21be-485b-a0bc-88dd9e89223d','rear':'exec-e3f52fd1-21be-485b-a0bc-88dd9e89223d'}
summary={}
for view,col in [('front',0),('rear',1)]:
    x0=round(col*atlas.width/2); x1=round((col+1)*atlas.width/2)
    local=labels[:,x0:x1]
    counts=np.bincount(local.ravel()); counts[0]=0
    label=int(counts.argmax())
    ys,xs=np.where(local==label)
    # Convert local cell coordinates to atlas coordinates and keep the whole globally connected silhouette.
    sx=int(xs[len(xs)//2]+x0); sy=int(ys[len(ys)//2])
    global_label=int(labels[sy,sx])
    ys,xs=np.where(labels==global_label)
    bounds=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)]
    component=(labels[bounds[1]:bounds[3],bounds[0]:bounds[2]]==global_label)
    crop=atlas.crop(tuple(bounds))
    crop.putalpha(Image.fromarray((component*255).astype(np.uint8)))
    scale=target_z/crop.height
    size=(max(1,round(crop.width*scale)),target_z)
    crop=crop.resize(size,Image.Resampling.LANCZOS)
    offset=(128-size[0]//2,128-size[1]//2)
    frame=Image.new('RGBA',(256,256)); frame.alpha_composite(crop,offset)
    aid=f'{OBJECT}.{view}'
    meta=json.loads((PACK/assets[aid]['metadata_path']).read_text())
    out=PACK/meta['image']['path']; out.parent.mkdir(parents=True,exist_ok=True)
    frame.save(out,optimize=True)
    crop_rel=f'reusable/views-additional/raw/swine-stairs-{view}-projection-v2.png'
    crop_path=PACK/crop_rel; crop.save(crop_path,optimize=True)
    recipe_rel=f'reusable/views-additional/raw/swine-stairs-{view}-projection-v2.recipe.json'
    notes=('Inferred orthographic end elevation from a transparent generated atlas. The staircase has a constant-width, level stone riser/back-support face. Its single rail is on one world-X side: screen-right in FRONT and screen-left in REAR, with the far post occluded. No recovered pixels are claimed for hidden surfaces.')
    meta['image']['sha256']=file_sha(out)
    meta['image']['rgba_sha256']=rgba_sha(frame)
    p=meta.setdefault('provenance',{})
    p.update({'method':'generated','source_image':'reusable/native/concepts-boss-swine-concept-stairs.png','source_atlas':ATLAS_REL,'source_atlas_sha256':file_sha(atlas_path),'generation_request_id':requests[view],'generation_recipe':recipe_rel,'source_crop_path':crop_rel,'source_crop_sha256':file_sha(crop_path),'crop_bounds_px':{'selection_mode':'global_alpha_components_at_threshold','threshold':THRESHOLD,'global_component_label':global_label,'alpha_bounds_global':bounds,'atlas_cell':{'column':col,'columns':2,'row':0,'rows':1},'uniform_scale':scale,'output_size_px':list(size),'resized_bounds_px':list(size),'canvas_offset_px':list(offset),'anchor_px':[128,128]},'notes':notes})
    recipe={'operation':'extract-global-connected-alpha-component-and-uniform-fit','request_id':requests[view],'input_atlas':ATLAS_REL,'input_sha256':file_sha(atlas_path),'alpha_threshold':THRESHOLD,'cell':{'column':col,'columns':2,'row':0,'rows':1},'global_component_label':global_label,'component_bounds_px':bounds,'uniform_scale':scale,'target_size_px':list(size),'canvas_offset_px':list(offset),'anchor_px':[128,128],'target_z_px':target_z,'source_image':'reusable/native/concepts-boss-swine-concept-stairs.png','output_crop':crop_rel,'output_id':aid,'notes':notes}
    (PACK/recipe_rel).write_text(json.dumps(recipe,indent=2)+'\n')
    (PACK/meta['metadata_path']).write_text(json.dumps(meta,indent=2)+'\n')
    assets[aid]=meta
    summary[view]={'bbox':frame.getchannel('A').getbbox(),'size':list(size),'scale':scale,'sha256':meta['image']['sha256'],'rgba_sha256':meta['image']['rgba_sha256']}
for group in idx['view_sets']:
    if group['object_id']==OBJECT:
        group['complete']=False
        group['geometry_qa']={'status':'pending-review','views':['front','rear'],'atlas_self_inspected':True,'notes':'New constant-width level end elevations await independent source+six review; top/right/left/bottom preserved.'}
        group['notes']='Targeted FRONT/REAR corrections; accepted TOP/RIGHT/LEFT/BOTTOM retained.'
idx['assets']=[assets[a['id']] for a in idx['assets']]
INDEX.write_text(json.dumps(idx,indent=2)+'\n')
print(json.dumps({'object_id':OBJECT,'target_z_px':target_z,'views':summary},indent=2))
