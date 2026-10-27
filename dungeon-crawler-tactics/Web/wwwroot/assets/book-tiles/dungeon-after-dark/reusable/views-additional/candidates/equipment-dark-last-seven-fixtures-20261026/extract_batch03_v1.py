from PIL import Image
import numpy as np,json,hashlib
from scipy import ndimage
B='/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/dungeon-after-dark/reusable/views-additional/candidates/equipment-dark-last-seven-fixtures-20261026';R=B+'/raw/batch03-v1.png';a=np.array(Image.open(R).convert('RGBA'));H,W=a.shape[:2];vs=['front','top','right','left','bottom','rear'];items=[]
for oid,row,targets,scale in [('race-circuits-race-descent-checkpoint',0,['right','left','bottom'],0.607),('safe-services-restaurant-dining-booth',1,['bottom'],0.664)]:
 for v in targets:
  c=vs.index(v);x0=round(c*W/6);x1=round((c+1)*W/6);y0=round(row*H/2);y1=round((row+1)*H/2);cell=a[y0:y1,x0:x1];lab,n=ndimage.label(cell[:,:,3]>=16,structure=np.ones((3,3),dtype=np.uint8));objs=ndimage.find_objects(lab);cs=[]
  for k,sl in enumerate(objs,1):
   if sl is None:continue
   area=int((lab[sl]==k).sum())
   if area>20:cs.append((area,k,(sl[1].start,sl[0].start,sl[1].stop,sl[0].stop)))
  cs.sort(reverse=True);main=cs[0];bx0,by0,bx1,by1=main[2];keep=[]
  for area,k,(cx0,cy0,cx1,cy1) in cs:
   gapx=max(0,bx0-cx1,cx0-bx1);gapy=max(0,by0-cy1,cy0-by1)
   if k==main[1] or (gapx<=18 and gapy<=18):keep.append(k)
  mask=np.isin(lab,keep);yy,xx=np.where(mask);box=[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)];crop=cell[box[1]:box[3],box[0]:box[2]].copy();crop[~mask[box[1]:box[3],box[0]:box[2]]]=0;im=Image.fromarray(crop,'RGBA');size=[round(im.width*scale),round(im.height*scale)];im=im.resize(size,Image.Resampling.NEAREST);canvas=Image.new('RGBA',(256,256),(0,0,0,0));pos=[128-size[0]//2,128-size[1]//2];canvas.alpha_composite(im,tuple(pos));p=B+f'/images/{oid}.{v}.png';canvas.save(p);items.append({'object_id':oid,'view':v,'path':p,'sha256':hashlib.sha256(open(p,'rb').read()).hexdigest(),'cell_xyxy':[x0,y0,x1,y1],'crop_local_xyxy':box,'alpha_threshold':16,'connectivity':8,'main_area':main[0],'included_areas':[area for area,k,b in cs if k in keep],'uniform_scale':scale,'resized_dimensions':size,'canvas':[256,256],'anchor_px':[128,128],'offset_px':pos})
json.dump({'raw_atlas':R,'raw_atlas_sha256':hashlib.sha256(open(R,'rb').read()).hexdigest(),'normalizer':'extract_batch03_v1.py','assets':items},open(B+'/batch03-v1-recipe.json','w'),indent=2);print(json.dumps(items,indent=2))
