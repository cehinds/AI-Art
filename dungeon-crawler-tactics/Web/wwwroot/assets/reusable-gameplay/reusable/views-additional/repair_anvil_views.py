from pathlib import Path
from PIL import Image
import hashlib, io, json, struct
import numpy as np
from scipy import ndimage

HERE=Path(__file__).resolve().parent
PACK=HERE.parents[1]
OBJECT='menu-concepts-safe-room-services--crafting-anvil'
ATLAS_REL='reusable/views-additional/raw/crafting-anvil-end-views-atlas.png'
ATLAS=PACK/ATLAS_REL
REQUEST='exec-3a9724ef-050d-492a-b789-3e80b188f968'

def sha(data): return hashlib.sha256(data).hexdigest()
def png_bytes(im):
    b=io.BytesIO(); im.save(b,format='PNG',optimize=True); return b.getvalue()
def rgba_hash(im): return sha(struct.pack('>II',im.width,im.height)+im.convert('RGBA').tobytes())
def save_meta(meta, view, frame, src_crop, crop_path, recipe_path, crop_data, notes):
    png=png_bytes(frame); (PACK/meta['image']['path']).write_bytes(png)
    meta['image']['sha256']=sha(png); meta['image']['rgba_sha256']=rgba_hash(frame)
    src_crop.save(PACK/crop_path,optimize=True)
    pr=meta.setdefault('provenance',{})
    pr.update({'source_atlas':ATLAS_REL,'source_atlas_sha256':sha(ATLAS.read_bytes()),
               'generation_recipe':recipe_path,'source_crop_path':crop_path,
               'source_crop_sha256':sha((PACK/crop_path).read_bytes()),
               'notes':notes})
    pr['crop_bounds_px']=crop_data
    recipe={'operation':'extract-alpha-component-uniform-scale-anchor','request_id':REQUEST,
            'input_atlas':ATLAS_REL,'input_sha256':sha(ATLAS.read_bytes()),
            'view':view,'crop_bounds_px':crop_data,'output_crop':crop_path,
            'output_id':meta['id'],'output_canvas':[256,256],
            'anchor_px':[128,128],'notes':notes}
    (PACK/recipe_path).write_text(json.dumps(recipe,indent=2)+'\n')
    (PACK/meta['metadata_path']).write_text(json.dumps(meta,indent=2)+'\n')
    return meta

idx_path=HERE/'set-index.json'; idx=json.loads(idx_path.read_text())
metas={a['view']:a for a in idx['assets'] if a.get('object_id')==OBJECT}
assert set(metas)=={'front','top','right','left','bottom','rear'}
raw=Image.open(ATLAS).convert('RGBA'); rgba=np.asarray(raw); alpha=rgba[:,:,3]
rows=[]
for col,view in enumerate(('right','left')):
    x0=col*887; x1=(col+1)*887 if col==0 else raw.width
    cell=alpha[:,x0:x1]>=245
    labels,n=ndimage.label(cell,np.ones((3,3),dtype=np.uint8))
    counts=np.bincount(labels.ravel()); counts[0]=0; lab=int(counts.argmax())
    ys,xs=np.where(labels==lab)
    bounds=[int(xs.min()+x0),int(ys.min()),int(xs.max()+x0+1),int(ys.max()+1)]
    mask=labels[ys.min():ys.max()+1,xs.min():xs.max()+1]==lab
    piece=raw.crop(tuple(bounds)); piece.putalpha(Image.fromarray((mask*255).astype('uint8')))
    scale=119/piece.height
    w=max(1,round(piece.width*scale)); h=max(1,round(piece.height*scale))
    piece=piece.resize((w,h),Image.Resampling.NEAREST)
    offset=((256-w)//2,187-h)
    frame=Image.new('RGBA',(256,256)); frame.alpha_composite(piece,offset)
    crop_rel=f'reusable/views-additional/raw/crafting-anvil-{view}-projection.png'
    recipe_rel=f'reusable/views-additional/raw/crafting-anvil-{view}-projection.recipe.json'
    piece_rel=crop_rel
    cdata={'selection_mode':'largest_component_alpha_ge_245','alpha_bounds_global':bounds,
           'component_labels':[lab],'resized_bounds_px':[w,h],'canvas_offset_px':list(offset),
           'uniform_scale':scale,'anchor_px':[128,128]}
    notes='Inferred orthographic end elevation looking along the anvil horn axis; unseen end detail is illustrative, not recovered pixels. Isolated generated projection; uniform scale and ground anchor matched to accepted elevation height.'
    meta=save_meta(metas[view],view,frame,piece,piece_rel,recipe_rel,cdata,notes)
    rows.append((view,bounds,frame.getchannel('A').getbbox(),meta['image']['sha256']))

# The existing overhead view has the correct geometry but points the horn the
# opposite way from the accepted FRONT; a rigid half-turn corrects the world-X.
view='top'; meta=metas[view]
source=Image.open(PACK/meta['image']['path']).convert('RGBA')
frame=source.transpose(Image.Transpose.ROTATE_180)
crop_rel='reusable/views-additional/raw/crafting-anvil-top-rotated-crop.png'
recipe_rel='reusable/views-additional/raw/crafting-anvil-top-rotated-crop.recipe.json'
crop=frame.copy()
cdata={'selection_mode':'full_canvas_rigid_rotation','source_image_path':meta['image']['path'],
       'source_image_sha256':sha((PACK/meta['image']['path']).read_bytes()),
       'rotation_degrees':180,'resized_bounds_px':[256,256],'canvas_offset_px':[0,0],
       'anchor_px':[128,128]}
notes='Inferred overhead view; rigid 180-degree in-plane rotation aligns the horn toward world-X left as established by FRONT. No scale or geometry change; hidden surfaces remain illustrative.'
meta=save_meta(meta,view,frame,crop,crop_rel,recipe_rel,cdata,notes)
for i,a in enumerate(idx['assets']):
    if a['id'] in {metas['right']['id'],metas['left']['id'],metas['top']['id']}:
        v=a['view']; idx['assets'][i]=metas[v]
idx_path.write_text(json.dumps(idx,indent=2)+'\n')
print(json.dumps({'updated':rows,'top_bbox':frame.getchannel('A').getbbox(),'top_sha':metas['top']['image']['sha256']}))
