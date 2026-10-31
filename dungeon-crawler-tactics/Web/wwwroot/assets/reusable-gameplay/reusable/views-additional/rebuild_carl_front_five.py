"""Extract the five targeted Carl FRONT poses from retained atlas, dropping transparent glow."""
from pathlib import Path
import hashlib,json,struct,shutil
import numpy as np
from PIL import Image
from scipy import ndimage
OUT=Path(__file__).resolve().parent;PACK=OUT.parents[1];raw_rel='reusable/views-additional/raw/carl-front-five-poses-atlas.png';raw=PACK/raw_rel;atlas=Image.open(raw).convert('RGBA');arr=np.asarray(atlas);mask=arr[:,:,3]>=245;labels,n=ndimage.label(mask,np.ones((3,3),dtype=np.uint8));objects=['revamp--characters--carl','revamp--characters--carl--idle2','revamp--characters--carl--walk1','revamp--characters--carl--walk2','revamp--characters--carl--walk3'];height,width=mask.shape
components=[]
for label in range(1,n+1):
 ys,xs=np.where(labels==label)
 if len(xs)>=100:components.append((float(ys.mean()),label))
components.sort();
if len(components)!=5:raise RuntimeError(f'expected exactly five large pose components, found {len(components)}')
idxp=OUT/'set-index.json';idx=json.loads(idxp.read_text());assets={a['id']:a for a in idx['assets']};backup=OUT/'raw'/'callback-inputs';backup.mkdir(parents=True,exist_ok=True);changes=[]
for (cy,label),oid in zip(components,objects):
 ys,xs=np.where(labels==label);bounds=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)];piece=atlas.crop(bounds);local=np.asarray(piece).copy();local[:,:,3]=(local[:,:,3]>=245).astype('uint8')*255;piece=Image.fromarray(local,'RGBA');aid=f'{oid}.front';meta=assets[aid];dest=PACK/meta['image']['path'];old=dest.read_bytes();oldhash=hashlib.sha256(old).hexdigest();bp=backup/f'{aid}.before-headon-front.png';
 if not bp.exists():shutil.copy2(dest,bp)
 oldimg=Image.open(bp).convert('RGBA');oldbox=oldimg.getchannel('A').getbbox();target_h=oldbox[3]-oldbox[1];scale=target_h/piece.height;nw,nh=round(piece.width*scale),target_h;piece=piece.resize((nw,nh),Image.Resampling.NEAREST);frame=Image.new('RGBA',(256,256));offset=(128-nw//2,128-nh//2);frame.alpha_composite(piece,offset);frame.save(dest,optimize=True)
 meta['image']['sha256']=hashlib.sha256(dest.read_bytes()).hexdigest();meta['image']['rgba_sha256']=hashlib.sha256(struct.pack('>II',256,256)+frame.tobytes()).hexdigest();meta['provenance'].update({'source_atlas':raw_rel,'source_atlas_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'generation_recipe':'reusable/views-additional/raw/carl-front-five-poses.recipe.json','notes':'Inferred head-on orthographic front projection; exact source pose phase and costume preserved, unseen surfaces inferred.','crop_bounds_px':{'component_label':label,'alpha_threshold':245,'alpha_bounds_global':bounds,'resized_bounds_px':[nw,nh],'canvas_offset_px':list(offset),'uniform_scale':scale,'target_z_extent_px':target_h}});(OUT/f'{aid}.json').write_text(json.dumps(meta,indent=2)+'\n')
 for i,a in enumerate(idx['assets']):
  if a['id']==aid:idx['assets'][i]=meta
 group=next(g for g in idx['view_sets'] if g['object_id']==oid);group['complete']=False;group['notes']='Targeted head-on FRONT correction awaits independent review; other five directions preserved.';group['geometry_qa']={'status':'pending-review','views':['front'],'notes':'Head-on world-Y camera basis aligned to approved Carl pilot; pose-specific walking/idle phase retained.','atlas_self_inspected':True};changes.append({'id':aid,'row_centroid_y':cy,'label':label,'alpha_bounds':bounds,'height':target_h,'size':[nw,nh],'old_sha256':oldhash,'new_sha256':meta['image']['sha256']})
idxp.write_text(json.dumps(idx,indent=2)+'\n');(OUT/'raw'/'carl-front-five-poses.recipe.json').write_text(json.dumps({'raw_atlas':raw_rel,'grid':{'columns':1,'rows':5,'row_order':objects},'alpha_threshold':245,'anchor_px':[128,128],'changes':changes},indent=2)+'\n');print(json.dumps(changes))
