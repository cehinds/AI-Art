from pathlib import Path
import hashlib,json,struct
import numpy as np
from PIL import Image
from scipy import ndimage
OUT=Path(__file__).resolve().parent; PACK=OUT.parents[1]; INDEX=OUT/'set-index.json'
OID='menu-concepts-safe-room-services--training-wall-weapon-rack'; RECIPE_REL='reusable/views-additional/raw/training-wall-weapon-rack-six-view.recipe.json'; recipe=json.loads((PACK/RECIPE_REL).read_text()); atlas_rel=recipe['source_atlas']; atlas_path=PACK/atlas_rel; atlas_bytes=atlas_path.read_bytes(); atlas_sha=hashlib.sha256(atlas_bytes).hexdigest(); atlas=Image.open(atlas_path).convert('RGBA'); rgba=np.asarray(atlas); labels,count=ndimage.label(rgba[:,:,3]>=recipe['alpha_threshold'],np.ones((3,3),dtype=np.uint8)); index=json.loads(INDEX.read_text()); assets={a['id']:a for a in index['assets']}; views=['front','top','right','left','bottom','rear']; log=[]

def sha(b): return hashlib.sha256(b).hexdigest()
def install(view,col):
    x0=round(col*atlas.width/6);x1=round((col+1)*atlas.width/6); y0=0;y1=atlas.height; cx=(x0+x1)/2; cy=atlas.height/2
    candidates=[]
    for label in range(1,count+1):
        yy,xx=np.where(labels==label)
        if len(xx)<2500: continue
        bbox=(int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1));
        if bbox[0]<=0 or bbox[1]<=0 or bbox[2]>=atlas.width or bbox[3]>=atlas.height: continue
        center=((float(xx.mean())-cx)/(x1-x0))**2+((float(yy.mean())-cy)/(y1-y0))**2
        candidates.append((center,label,bbox,len(xx)))
    if not candidates: raise RuntimeError(f'{view}: no isolated projection in cell {col}')
    _,label,(bx0,by0,bx1,by1),area=min(candidates)
    # Each cell-center receives a distinct, complete global component; reject duplicate assignment.
    if any(x['component_label']==int(label) for x in log): raise RuntimeError(f'{view}: component reused from another view')
    mask=labels[by0:by1,bx0:bx1]==label; piece=atlas.crop((bx0,by0,bx1,by1)); alpha=np.asarray(piece.getchannel('A')); piece.putalpha(Image.fromarray(np.where(mask,alpha,0).astype('uint8')))
    scale=float(recipe['shared_scale']); nw=max(1,round(piece.width*scale));nh=max(1,round(piece.height*scale));piece=piece.resize((nw,nh),Image.Resampling.NEAREST)
    frame=Image.new('RGBA',(256,256));ox,oy=128-nw//2,128-nh//2
    if ox<0 or oy<0 or ox+nw>256 or oy+nh>256: raise RuntimeError(f'{view}: clipping {nw}x{nh}')
    frame.alpha_composite(piece,(ox,oy)); asset=assets[f'{OID}.{view}']; image_rel=asset['image']['path']; encoded=PACK.joinpath(image_rel);encoded.parent.mkdir(parents=True,exist_ok=True);frame.save(encoded,optimize=True);png=encoded.read_bytes(); meta=dict(asset)
    meta['image']={'path':image_rel,'width':256,'height':256,'sha256':sha(png),'rgba_sha256':hashlib.sha256(struct.pack('>II',256,256)+frame.tobytes()).hexdigest()};meta['anchor_px']=[128,128]
    prov=dict(meta.get('provenance',{}));prov.update({'method':'generated','source_image':'reusable/native/'+OID+'.png','native_front':'reusable/native/'+OID+'.png','native_front_sha256':hashlib.sha256((PACK/'reusable/native'/f'{OID}.png').read_bytes()).hexdigest(),'notes':'Inferred orthographic view of the source sword/blade wall rack; two rails, iron brackets and the same blade row retained. Unseen rear hardware is conservative inference, not recovered pixels.','source_atlas':atlas_rel,'source_atlas_sha256':atlas_sha,'generation_recipe':RECIPE_REL,'prompt_path':recipe['prompt'],'prompt_sha256':hashlib.sha256((PACK/recipe['prompt']).read_bytes()).hexdigest(),'crop_bounds_px':{'nominal_cell':{'column':col,'row':0,'bounds':[x0,0,x1,atlas.height]},'alpha_bounds_global':[bx0,by0,bx1,by1],'component_labels':[int(label)],'resized_bounds_px':[nw,nh],'canvas_offset_px':[ox,oy],'shared_scale':scale}});meta['provenance']=prov;(PACK/meta['metadata_path']).write_text(json.dumps(meta,indent=2)+'\n');assets[meta['id']]=meta;log.append({'view':view,'component_label':int(label),'area':int(area),'crop_xyxy':[bx0,by0,bx1,by1],'resized_bounds_px':[nw,nh],'canvas_offset_px':[ox,oy],'sha256':meta['image']['sha256']})
for col,view in enumerate(views): install(view,col)
index['assets']=[assets[a['id']] for a in index['assets']];INDEX.write_text(json.dumps(index,indent=2)+'\n');(PACK/'reusable/views-additional/raw/training-wall-weapon-rack-six-view-installed.json').write_text(json.dumps({'object_id':OID,'atlas_sha256':atlas_sha,'views':log},indent=2)+'\n');print(json.dumps(log,indent=2))
