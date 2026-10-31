from PIL import Image
import numpy as np, json, hashlib
from scipy import ndimage
from pathlib import Path
B=Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/dungeon-after-dark/reusable/views-additional/candidates/equipment-dark-last-seven-fixtures-20261026')
rp=B/'raw/booth-bottom-v4.png';a=np.array(Image.open(rp).convert('RGBA'));alpha=a[:,:,3];lab,n=ndimage.label(alpha>=64,structure=np.ones((3,3),dtype=np.uint8));items=[]
for k,sl in enumerate(ndimage.find_objects(lab),1):
 if sl is None:continue
 area=int((lab[sl]==k).sum())
 if area>=100:items.append((k,area,sl))
# Keep both large seat-base pads and the smaller central pedestal foot; all are meaningful disconnected assembly parts.
mask=np.isin(lab,[k for k,_,_ in items]);yy,xx=np.where(mask);box=[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)];crop=a[box[1]:box[3],box[0]:box[2]].copy();crop[~mask[box[1]:box[3],box[0]:box[2]]]=0;im=Image.fromarray(crop,'RGBA');scale=193/max(im.size);size=(round(im.width*scale),round(im.height*scale));im=im.resize(size,Image.Resampling.NEAREST);canvas=Image.new('RGBA',(256,256),(0,0,0,0));off=(128-size[0]//2,128-size[1]//2);canvas.alpha_composite(im,off);out=B/'images/safe-services-restaurant-dining-booth.bottom.focused-v4b.png';canvas.save(out)
json.dump({'object_id':'safe-services-restaurant-dining-booth','view':'bottom','raw_path':str(rp),'raw_sha256':hashlib.sha256(rp.read_bytes()).hexdigest(),'alpha_threshold':64,'connectivity':8,'kept_components':[{'area':area,'bbox_local_xyxy':[sl[1].start,sl[0].start,sl[1].stop,sl[0].stop]} for k,area,sl in items],'crop_local_xyxy':box,'uniform_scale':scale,'resized_wh':size,'offset_xy':off,'canvas':[256,256],'anchor_px':[128,128],'output':str(out),'output_sha256':hashlib.sha256(out.read_bytes()).hexdigest()},open(B/'booth-bottom-v4b-recipe.json','w'),indent=2)
