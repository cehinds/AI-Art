"""Extract one consistent six-view set for the source open-top green X-braced crate."""
from pathlib import Path
import hashlib, json, struct
from PIL import Image
import numpy as np
from scipy import ndimage
HERE=Path(__file__).resolve().parent; PACK=HERE.parents[1]; INDEX=HERE/'set-index.json'; RAW=HERE/'raw'
OBJECT='concepts-boss-hoarder-concept-crate'; ATLAS_REL='reusable/views-additional/raw/hoarder-open-crate-six-view-atlas.png'; SOURCE_CROP='/workspace/scratch/scene-proxy-references/gameplay/concepts-boss-hoarder-concept-crate.png'; REF_REL='reusable/views-additional/raw/hoarder-open-crate-source-reference.png'; REQUEST='exec-22a754dc-a4f1-4880-a018-64122311430c'
VIEWS=('front','top','right','left','bottom','rear'); CELL_W=362; CELL_H=724; THRESHOLD=245; SCALE=134/311

def sha(b):return hashlib.sha256(b).hexdigest()
def rgba_hash(im):return sha(struct.pack('>II',im.width,im.height)+im.convert('RGBA').tobytes())
idxp=INDEX;idx=json.loads(idxp.read_text());current={a['view']:a for a in idx['assets'] if a.get('object_id')==OBJECT};assert set(current)==set(VIEWS)
atlas=Image.open(PACK/ATLAS_REL).convert('RGBA');pixels=np.asarray(atlas);assert atlas.width==CELL_W*6
global_labels,_=ndimage.label(pixels[:,:,3]>=THRESHOLD,np.ones((3,3),dtype=np.uint8))
source_path=Path(SOURCE_CROP);source_bytes=source_path.read_bytes();(PACK/REF_REL).write_bytes(source_bytes)
scale_record={}
for col,view in enumerate(VIEWS):
    x0=col*CELL_W;x1=(col+1)*CELL_W;region=pixels[:,x0:x1,3]>=THRESHOLD;labels,n=ndimage.label(region,np.ones((3,3),dtype=np.uint8));counts=np.bincount(labels.ravel());counts[0]=0;label=int(counts.argmax())
    if counts[label]<10000:raise RuntimeError(f'{view}: weak/empty cell component {counts[label]}')
    ys,xs=np.where(labels==label);sample_y=int(ys[len(ys)//2]);sample_x=int(xs[len(xs)//2])+x0;global_label=int(global_labels[sample_y,sample_x]);gy,gx=np.where(global_labels==global_label);bounds=[int(gx.min()),int(gy.min()),int(gx.max()+1),int(gy.max()+1)];local=global_labels[bounds[1]:bounds[3],bounds[0]:bounds[2]]==global_label
    piece=atlas.crop(tuple(bounds));piece.putalpha(Image.fromarray((local*255).astype('uint8')))
    w=max(1,round(piece.width*SCALE));h=max(1,round(piece.height*SCALE));piece=piece.resize((w,h),Image.Resampling.NEAREST);offset=(128-w//2,128-h//2);frame=Image.new('RGBA',(256,256));frame.alpha_composite(piece,offset)
    pngpath=PACK/current[view]['image']['path'];frame.save(pngpath,optimize=True);encoded=pngpath.read_bytes()
    meta=json.loads((PACK/current[view]['metadata_path']).read_text());meta['image']['sha256']=sha(encoded);meta['image']['rgba_sha256']=rgba_hash(frame)
    meta['name']=f'Open Green Cross-Braced Crate {view.title()}'
    pr=meta['provenance'];recipe_rel=f'reusable/views-additional/raw/hoarder-open-crate-{view}.recipe.json'
    pr.update({'source_atlas':ATLAS_REL,'source_atlas_sha256':sha((PACK/ATLAS_REL).read_bytes()),'generation_recipe':recipe_rel,
       'source_image':meta['provenance'].get('source_image','reusable/sources/concepts/boss-hoarder-concept.png'),
       'reference_source_image':REF_REL,'reference_source_sha256':sha(source_bytes),
       'crop_bounds_px':{'selection_mode':'largest_component_alpha_ge_245','nominal_cell':{'column':col,'row':0,'bounds':[x0,0,x1,CELL_H]},
          'alpha_bounds_global':bounds,'component_labels':[global_label],'resized_bounds_px':[w,h],'canvas_offset_px':list(offset),
          'shared_scale':SCALE,'anchor_px':[128,128] },
       'notes':'Inferred orthographic view of the canonical open-top green wooden crate with X-braced open sides. The cavity remains open; no lid is present. Unseen interior/base details are illustrative, not recovered pixels.'})
    recipe={'operation':'largest-threshold-component-per-view-cell-uniform-nearest-scale','request_id':REQUEST,'input_atlas':ATLAS_REL,'input_sha256':sha((PACK/ATLAS_REL).read_bytes()),'alpha_threshold':THRESHOLD,'view':view,'nominal_cell':[x0,0,x1,CELL_H],'selected_component_bounds':bounds,'selected_component_label':label,'uniform_scale':SCALE,'resized_bounds_px':[w,h],'canvas_offset_px':list(offset),'anchor_px':[128,128],'reference_source_image':REF_REL,'reference_source_sha256':sha(source_bytes),'notes':pr['notes']}
    (PACK/recipe_rel).write_text(json.dumps(recipe,indent=2)+'\n');(PACK/meta['metadata_path']).write_text(json.dumps(meta,indent=2)+'\n');current[view]=meta;scale_record[view]={'bounds':bounds,'output_size':[w,h],'bbox':frame.getchannel('A').getbbox(),'sha256':meta['image']['sha256']}
for i,a in enumerate(idx['assets']):
    if a['id'] in {current[v]['id'] for v in VIEWS}:idx['assets'][i]=current[a['view']]
for g in idx['view_sets']:
    if g['object_id']==OBJECT:
        g['complete']=False;g['geometry_qa']={'status':'pending-review','views':list(VIEWS),'notes':'Source-faithful open crate identity regenerated; pending independent source-plus-six review.','atlas_self_inspected':True};g['notes']='Open-top crate projections await independent source-plus-six review.';break
idxp.write_text(json.dumps(idx,indent=2)+'\n')
print(json.dumps({'object_id':OBJECT,'source_crop_sha256':sha(source_bytes),'atlas_sha256':sha((PACK/ATLAS_REL).read_bytes()),'views':scale_record},indent=2))
