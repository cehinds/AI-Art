"""Install the two generated rug footprint pairs from retained atlas cells."""
from pathlib import Path
import hashlib,json,struct
import numpy as np
from PIL import Image
from scipy import ndimage
HERE=Path(__file__).resolve().parent; PACK=HERE.parents[1]; INDEX=HERE/'set-index.json'
ATLAS_REL='reusable/views-additional/raw/gameplay-rugs-repair-atlas.png'; THRESHOLD=245
ROWS={'menu-concepts-safe-room-services--donut-flower-rug':0,'menu-concepts-safe-room-services--social-rug':1}
REQ='exec-043131c3-77e2-40fe-aa45-1e2dfa758065'
def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def file_sha(p):return sha_bytes(p.read_bytes())
def rgba_sha(im):return sha_bytes(struct.pack('>II',*im.size)+im.convert('RGBA').tobytes())
atlas_path=PACK/ATLAS_REL; atlas=Image.open(atlas_path).convert('RGBA'); arr=np.asarray(atlas)
labels,_=ndimage.label(arr[:,:,3]>=THRESHOLD,np.ones((3,3),dtype=np.uint8))
idx=json.loads(INDEX.read_text()); assets={a['id']:a for a in idx['assets']}
summary={}
for oid,row in ROWS.items():
    # Reuse the established TOP X extent as the shared physical width of both plan views.
    top_path=PACK/assets[f'{oid}.top']['image']['path']
    current_top=Image.open(top_path).convert('RGBA').getchannel('A').getbbox()
    target_x=current_top[2]-current_top[0]
    for view,col in [('top',1),('bottom',4)]:
        x0=round(col*atlas.width/6);x1=round((col+1)*atlas.width/6)
        y0=round(row*atlas.height/2);y1=round((row+1)*atlas.height/2)
        local=labels[y0:y1,x0:x1]; counts=np.bincount(local.ravel());counts[0]=0
        label=int(counts.argmax()); yy,xx=np.where(local==label)
        sx=int(xx[len(xx)//2]+x0);sy=int(yy[len(yy)//2]+y0); global_label=int(labels[sy,sx])
        yy,xx=np.where(labels==global_label)
        bounds=[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)]
        component=labels[bounds[1]:bounds[3],bounds[0]:bounds[2]]==global_label
        piece=atlas.crop(tuple(bounds));piece.putalpha(Image.fromarray((component*255).astype(np.uint8)))
        scale=target_x/piece.width;size=(target_x,max(1,round(piece.height*scale)))
        piece=piece.resize(size,Image.Resampling.LANCZOS)
        crop_rel=f'reusable/views-additional/raw/{oid.rsplit("--",1)[-1]}-{view}-corrected-projection.png'
        crop_path=PACK/crop_rel;piece.save(crop_path,optimize=True)
        offset=(128-size[0]//2,128-size[1]//2);frame=Image.new('RGBA',(256,256));frame.alpha_composite(piece,offset)
        aid=f'{oid}.{view}';meta=json.loads((PACK/assets[aid]['metadata_path']).read_text());out=PACK/meta['image']['path'];frame.save(out,optimize=True)
        recipe_rel=f'reusable/views-additional/raw/{oid.rsplit("--",1)[-1]}-{view}-corrected-projection.recipe.json'
        note=('Generated horizontal rug projection. The TOP preserves the source rug footprint and decoration; the BOTTOM uses an inferred woven underside with the same footprint. Hidden underside details are illustrative, not recovered pixels.')
        meta['image']['sha256']=file_sha(out);meta['image']['rgba_sha256']=rgba_sha(frame)
        prov=meta.setdefault('provenance',{});prov.update({'method':'generated','source_image':prov.get('source_image',''),'source_atlas':ATLAS_REL,'source_atlas_sha256':file_sha(atlas_path),'generation_request_id':REQ,'generation_recipe':recipe_rel,'source_crop_path':crop_rel,'source_crop_sha256':file_sha(crop_path),'crop_bounds_px':{'selection_mode':'global_alpha_component','alpha_threshold':THRESHOLD,'global_component_label':global_label,'alpha_bounds_global':bounds,'atlas_cell':{'column':col,'row':row,'columns':6,'rows':2},'uniform_scale':scale,'resized_bounds_px':list(size),'canvas_offset_px':list(offset),'anchor_px':[128,128]},'reference_images':['/workspace/scratch/scene-proxy-references/gameplay/menu-concepts-safe-room-services--donut-flower-rug.png','/workspace/scratch/scene-proxy-references/gameplay/menu-concepts-safe-room-services--social-rug.png'],'notes':note})
        recipe={'operation':'extract-alpha-component-uniform-plan-scale','request_id':REQ,'input_atlas':ATLAS_REL,'input_sha256':file_sha(atlas_path),'alpha_threshold':THRESHOLD,'cell':{'column':col,'row':row,'columns':6,'rows':2},'global_component_label':global_label,'component_bounds_px':bounds,'uniform_scale':scale,'target_size_px':list(size),'canvas_offset_px':list(offset),'anchor_px':[128,128],'target_width_from_existing_top_px':target_x,'output_crop':crop_rel,'output_id':aid,'notes':note}
        (PACK/recipe_rel).write_text(json.dumps(recipe,indent=2)+'\n');(PACK/meta['metadata_path']).write_text(json.dumps(meta,indent=2)+'\n');assets[aid]=meta
        summary[aid]={'bbox':frame.getchannel('A').getbbox(),'size':list(size),'sha256':meta['image']['sha256']}
for group in idx['view_sets']:
    if group['object_id'] in ROWS:
        group['complete']=False;group['geometry_qa']={'status':'pending-review','views':['top','bottom'],'atlas_self_inspected':True,'notes':'Source-shaped rug footprints and inferred undersides await independent source+six review; four edge views preserved.'}
        group['notes']='Targeted TOP/BOTTOM footprint corrections; FRONT/RIGHT/LEFT/REAR retained.'
idx['assets']=[assets[a['id']] for a in idx['assets']];INDEX.write_text(json.dumps(idx,indent=2)+'\n')
print(json.dumps(summary,indent=2))
