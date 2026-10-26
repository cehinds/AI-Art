"""Rebuild dummy FRONT/RIGHT/LEFT/REAR with square wood support and plain rear."""
from pathlib import Path
import hashlib,json,struct,shutil
import numpy as np
from PIL import Image
from scipy import ndimage
OUT=Path(__file__).resolve().parent;PACK=OUT.parents[1];OID='menu-concepts-safe-room-services--training-dummy'
primary_rel='reusable/views-additional/raw/training-dummy-elevations-atlas.png';rear_rel='reusable/views-additional/raw/training-dummy-rear-plain-atlas.png'
primary=Image.open(PACK/primary_rel).convert('RGBA'); arr=np.asarray(primary);h,w=arr.shape[:2];mask=arr[:,:,3]>=245;labels,n=ndimage.label(mask,np.ones((3,3),dtype=np.uint8));
# Each component centroid falls into its requested camera's atlas column; retain full component bounds across cell seams.
centers=[(w/8,h/2),(3*w/8,h/2),(5*w/8,h/2),(7*w/8,h/2)]; chosen={}
for label in range(1,n+1):
 ys,xs=np.where(labels==label)
 if len(xs)<100:continue
 cx=float(xs.mean()); k=min(range(4),key=lambda i:abs(cx-centers[i][0]))
 if k not in chosen or len(xs)>chosen[k][0]:chosen[k]=(len(xs),label)
if set(chosen)!={0,1,2,3}:raise RuntimeError(f'missing primary view components {chosen}')
rear_im=Image.open(PACK/rear_rel).convert('RGBA');ra=np.asarray(rear_im);rm=ra[:,:,3]>=245;rys,rxs=np.where(rm);rear_bounds=[int(rxs.min()),int(rys.min()),int(rxs.max()+1),int(rys.max()+1)]
# Match accepted sibling vertical world extent (current FRONT alpha height 196px) with isotropic rescaling.
front_box=Image.open(OUT/f'{OID}.front.png').convert('RGBA').getchannel('A').getbbox(); target_h=front_box[3]-front_box[1]
idxp=OUT/'set-index.json';idx=json.loads(idxp.read_text());assets={a['id']:a for a in idx['assets']};back=OUT/'raw'/'callback-inputs';back.mkdir(parents=True,exist_ok=True);changes=[]
for view,col in zip(('front','right','left'),range(3)):
 cnt,label=chosen[col];ys,xs=np.where(labels==label);bounds=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)]
 piece=primary.crop(bounds);arrp=np.asarray(piece).copy();arrp[:,:,3]=(arrp[:,:,3]>=245).astype('uint8')*255;piece=Image.fromarray(arrp,'RGBA');scale=target_h/piece.height;nw,nh=round(piece.width*scale),target_h;piece=piece.resize((nw,nh),Image.Resampling.NEAREST)
 aid=f'{OID}.{view}';meta=assets[aid];dest=PACK/meta['image']['path'];old=dest.read_bytes();old_hash=hashlib.sha256(old).hexdigest();bp=back/f'{aid}.before-square-platform-elevations.png';
 if not bp.exists():shutil.copy2(dest,bp)
 frame=Image.new('RGBA',(256,256));offset=(128-nw//2,128-nh//2);frame.alpha_composite(piece,offset);frame.save(dest,optimize=True)
 rawpath=PACK/primary_rel;meta['image']['sha256']=hashlib.sha256(dest.read_bytes()).hexdigest();meta['image']['rgba_sha256']=hashlib.sha256(struct.pack('>II',256,256)+frame.tobytes()).hexdigest();meta['provenance'].update({'source_atlas':primary_rel,'source_atlas_sha256':hashlib.sha256(rawpath.read_bytes()).hexdigest(),'generation_recipe':'reusable/views-additional/raw/training-dummy-elevations.recipe.json','notes':'Inferred orthographic elevation with square plank support grounded in visible native source; camera-facing unseen surfaces remain inferred.','crop_bounds_px':{'component_label':label,'alpha_threshold':245,'alpha_bounds_global':bounds,'resized_bounds_px':[nw,nh],'canvas_offset_px':list(offset),'uniform_scale':scale,'target_z_extent_px':target_h}});(OUT/f'{aid}.json').write_text(json.dumps(meta,indent=2)+'\n');changes.append({'id':aid,'old_sha256':old_hash,'new_sha256':meta['image']['sha256'],'bounds':bounds,'size':[nw,nh]})
# Rear separate generation explicitly shows a plain back; retain its full silhouette.
piece=rear_im.crop(rear_bounds); ar=np.asarray(piece).copy();ar[:,:,3]=(ar[:,:,3]>=245).astype('uint8')*255;piece=Image.fromarray(ar,'RGBA');scale=target_h/piece.height;nw,nh=round(piece.width*scale),target_h;piece=piece.resize((nw,nh),Image.Resampling.NEAREST);view='rear';aid=f'{OID}.{view}';meta=assets[aid];dest=PACK/meta['image']['path'];old=dest.read_bytes();old_hash=hashlib.sha256(old).hexdigest();bp=back/f'{aid}.before-square-platform-elevations.png';
if not bp.exists():shutil.copy2(dest,bp)
frame=Image.new('RGBA',(256,256));offset=(128-nw//2,128-nh//2);frame.alpha_composite(piece,offset);frame.save(dest,optimize=True);rawpath=PACK/rear_rel;meta['image']['sha256']=hashlib.sha256(dest.read_bytes()).hexdigest();meta['image']['rgba_sha256']=hashlib.sha256(struct.pack('>II',256,256)+frame.tobytes()).hexdigest();meta['provenance'].update({'source_atlas':rear_rel,'source_atlas_sha256':hashlib.sha256(rawpath.read_bytes()).hexdigest(),'generation_recipe':'reusable/views-additional/raw/training-dummy-rear-plain.recipe.json','notes':'Inferred orthographic rear projection: plain back surfaces and square support; hidden source surfaces are inferred.','crop_bounds_px':{'alpha_threshold':245,'alpha_bounds_global':rear_bounds,'resized_bounds_px':[nw,nh],'canvas_offset_px':list(offset),'uniform_scale':scale,'target_z_extent_px':target_h}});(OUT/f'{aid}.json').write_text(json.dumps(meta,indent=2)+'\n');changes.append({'id':aid,'old_sha256':old_hash,'new_sha256':meta['image']['sha256'],'bounds':rear_bounds,'size':[nw,nh]})
for i,a in enumerate(idx['assets']):
 if a['id'] in assets:idx['assets'][i]=assets[a['id']]
for g in idx['view_sets']:
 if g['object_id']==OID:g['complete']=False;g['notes']='Square support corrections in four elevations await fresh independent review; TOP/BOTTOM retained.';g['geometry_qa']={'status':'pending-review','views':['front','right','left','rear'],'notes':'Square plank support follows source evidence; plain rear face and hidden construction inferred. Awaiting independent review.','atlas_self_inspected':True}
idxp.write_text(json.dumps(idx,indent=2)+'\n');(OUT/'raw'/'training-dummy-elevations.recipe.json').write_text(json.dumps({'raw_atlases':[primary_rel,rear_rel],'primary_grid':{'columns':4,'rows':1,'views':['front','right','left','rear']},'alpha_threshold':245,'target_z_extent_px':target_h,'anchor_px':[128,128],'changes':changes},indent=2)+'\n');print(json.dumps(changes))
