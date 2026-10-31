from PIL import Image
import numpy as np,json,hashlib
from scipy import ndimage
from pathlib import Path
B=Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/dungeon-after-dark/reusable/views-additional/candidates/equipment-dark-last-seven-fixtures-20261026');p=B/'raw/booth-bottom-repaired-v6.png';a=np.array(Image.open(p).convert('RGBA'));mask0=a[:,:,3]>=64;lab,n=ndimage.label(mask0,structure=np.ones((3,3),dtype=np.uint8));cs=[]
for k,sl in enumerate(ndimage.find_objects(lab),1):
 if sl is None:continue
 area=int((lab[sl]==k).sum());
 if area>20:cs.append((area,k,sl))
cs.sort(reverse=True);area,k,sl=cs[0];keep=[k]
for ar,kk,s in cs[1:]:
 gapx=max(0,sl[1].start-s[1].stop,s[1].start-sl[1].stop);gapy=max(0,sl[0].start-s[0].stop,s[0].start-sl[0].stop)
 if gapx<=16 and gapy<=16:keep.append(kk)
mask=np.isin(lab,keep);yy,xx=np.where(mask);box=[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)];crop=a[box[1]:box[3],box[0]:box[2]].copy();crop[~mask[box[1]:box[3],box[0]:box[2]]]=0;im=Image.fromarray(crop,'RGBA');scale=193/max(im.size);size=(round(im.width*scale),round(im.height*scale));im=im.resize(size,Image.Resampling.NEAREST);canvas=Image.new('RGBA',(256,256),(0,0,0,0));off=(128-size[0]//2,128-size[1]//2);canvas.alpha_composite(im,off);out=B/'images/safe-services-restaurant-dining-booth.bottom.focused-v6.png';canvas.save(out)
rec={'object_id':'safe-services-restaurant-dining-booth','view':'bottom','raw_path':str(p),'raw_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'alpha_threshold':64,'connectivity':8,'selected_components':[{'area':ar,'bbox_local_xyxy':[s[1].start,s[0].start,s[1].stop,s[0].stop]}for ar,kk,s in cs if kk in keep],'crop_local_xyxy':box,'uniform_scale':scale,'resized_wh':size,'offset_xy':off,'anchor_px':[128,128],'output_path':str(out),'output_sha256':hashlib.sha256(out.read_bytes()).hexdigest()};rp=B/'booth-bottom-v6-recipe.json';rp.write_text(json.dumps(rec,indent=2)+'\n');print(json.dumps(rec,indent=2))
