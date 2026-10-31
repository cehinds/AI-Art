from PIL import Image
import numpy as np,json,hashlib
from scipy import ndimage
from pathlib import Path
B=Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/dungeon-after-dark/reusable/views-additional/candidates/equipment-dark-last-seven-fixtures-20261026')
rp=B/'raw/booth-sides-geometry-guided-v4.png'; a=np.array(Image.open(rp).convert('RGBA'));H,W=a.shape[:2];result=[]
for i,view in [(0,'right'),(1,'left')]:
 x0=round(W*i/2);x1=round(W*(i+1)/2);cell=a[:,x0:x1];lab,n=ndimage.label(cell[:,:,3]>=64,structure=np.ones((3,3),dtype=np.uint8));cc=[]
 for k,sl in enumerate(ndimage.find_objects(lab),1):
  if sl is None:continue
  ar=int((lab[sl]==k).sum());bb=(sl[1].start,sl[0].start,sl[1].stop,sl[0].stop)
  if ar>=100:cc.append((ar,k,bb))
 cc.sort(reverse=True);main=cc[0];keep=[z for z in cc if z[1]==main[1] or (max(0,main[2][0]-z[2][2],z[2][0]-main[2][2])<=16 and max(0,main[2][1]-z[2][3],z[2][1]-main[2][3])<=16)];mask=np.isin(lab,[k for _,k,_ in keep]);yy,xx=np.where(mask);box=[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)];crop=cell[box[1]:box[3],box[0]:box[2]].copy();crop[~mask[box[1]:box[3],box[0]:box[2]]]=0;im=Image.fromarray(crop,'RGBA');scale=126/max(im.size);size=(round(im.width*scale),round(im.height*scale));im=im.resize(size,Image.Resampling.NEAREST);canvas=Image.new('RGBA',(256,256),(0,0,0,0));off=(128-size[0]//2,128-size[1]//2);canvas.alpha_composite(im,off);out=B/f'images/safe-services-restaurant-dining-booth.{view}.focused-v5.png';canvas.save(out)
 result.append({'object_id':'safe-services-restaurant-dining-booth','view':view,'output_path':str(out),'output_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'raw_path':str(rp),'raw_sha256':hashlib.sha256(rp.read_bytes()).hexdigest(),'cell_xyxy':[x0,0,x1,H],'alpha_threshold':64,'connectivity':8,'component_area':main[0],'crop_local_xyxy':box,'uniform_scale':scale,'resized_wh':size,'offset_xy':off,'anchor_px':[128,128]})
json.dump({'recipe_version':'5','operation':'8-connected alpha component extraction, full bbox, NEAREST uniform scale to 126px elevation height, centered on shared anchor','assets':result},open(B/'booth-sides-v5-recipe.json','w'),indent=2)
print(json.dumps(result,indent=2))
