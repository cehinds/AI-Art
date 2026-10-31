from PIL import Image
import numpy as np, os,json,hashlib
from scipy import ndimage
BASE='/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/dungeon-after-dark/reusable/views-additional/candidates/equipment-dark-last-seven-fixtures-20261026';RAW=BASE+'/raw/batch02-v1.png';a=np.array(Image.open(RAW).convert('RGBA'));H,W=a.shape[:2]
rows={'over-city-venues-tavern-bar':(0,['bottom','rear'],0.687719298245614),'race-circuits-pit-service-grating-floor':(1,['front','right','left','rear'],0.758364312267658)}
views=['front','top','right','left','bottom','rear'];items=[]
for oid,(row,target_views,scale) in rows.items():
 for view in target_views:
  col=views.index(view);x0=round(col*W/6);x1=round((col+1)*W/6);y0=round(row*H/2);y1=round((row+1)*H/2);cell=a[y0:y1,x0:x1];lab,n=ndimage.label(cell[:,:,3]>=16,structure=np.ones((3,3),dtype=np.uint8));objs=ndimage.find_objects(lab); comps=[]
  for k,sl in enumerate(objs,1):
   if sl is None:continue
   area=int((lab[sl]==k).sum())
   if area>20:comps.append((area,k,(sl[1].start,sl[0].start,sl[1].stop,sl[0].stop)))
  comps.sort(reverse=True);main=comps[0];bx0,by0,bx1,by1=main[2];keepids=[]
  for area,k,(cx0,cy0,cx1,cy1) in comps:
   gapx=max(0,bx0-cx1,cx0-bx1);gapy=max(0,by0-cy1,cy0-by1)
   if k==main[1] or (gapx<=16 and gapy<=16):keepids.append(k)
  mask=np.isin(lab,keepids);yy,xx=np.where(mask);box=(int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1));crop=cell[box[1]:box[3],box[0]:box[2]].copy();crop[~mask[box[1]:box[3],box[0]:box[2]]]=0;im=Image.fromarray(crop,'RGBA');sz=(round(im.width*scale),round(im.height*scale));im=im.resize(sz,Image.Resampling.NEAREST);canvas=Image.new('RGBA',(256,256),(0,0,0,0));pos=(128-sz[0]//2,128-sz[1]//2);canvas.alpha_composite(im,pos);out=BASE+f'/images/{oid}.{view}.png';canvas.save(out)
  items.append({'object_id':oid,'view':view,'path':out,'sha256':hashlib.sha256(open(out,'rb').read()).hexdigest(),'cell_xyxy':[x0,y0,x1,y1],'crop_local_xyxy':box,'alpha_threshold':16,'connectivity':8,'main_component_area':main[0],'kept_component_areas':[area for area,k,b in comps if k in keepids],'uniform_scale':scale,'resized_dimensions':list(sz),'canvas':[256,256],'anchor_px':[128,128],'offset_px':list(pos)})
json.dump({'raw_atlas':RAW,'raw_atlas_sha256':hashlib.sha256(open(RAW,'rb').read()).hexdigest(),'normalizer':'extract_batch02_v1.py','assets':items},open(BASE+'/batch02-v1-recipe.json','w'),indent=2)
print(json.dumps(items,indent=2))
