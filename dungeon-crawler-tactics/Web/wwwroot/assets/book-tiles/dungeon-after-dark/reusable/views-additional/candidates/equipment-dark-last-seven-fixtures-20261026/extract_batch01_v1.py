from PIL import Image
import numpy as np, os, json, hashlib
from scipy import ndimage
ROOT='/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/dungeon-after-dark'
BASE=ROOT+'/reusable/views-additional/candidates/equipment-dark-last-seven-fixtures-20261026'
RAW=BASE+'/raw/batch01-v1.png'
ATLAS=Image.open(RAW).convert('RGBA')
a=np.array(ATLAS)
H,W=a.shape[:2]
# Explicit equal 6x3 atlas cells; retaining dominant foreground CC and any components close to it.
rows={
 'great-race-transition-fractured-maze-slab': (0, {'top':1,'bottom':4}, 0.94),
 'hunting-shrines-hunter-trap-mechanism': (1, {'top':1,'bottom':4}, 0.80),
 'over-city-venues-painted-civic-stone-wall-northeast': (2, {'front':0,'rear':5}, 0.82),
}
assets=[]
for oid,(row,views,scale) in rows.items():
 for view,col in views.items():
  x0=round(col*W/6); x1=round((col+1)*W/6); y0=round(row*H/3); y1=round((row+1)*H/3)
  cell=a[y0:y1,x0:x1]
  mask=cell[:,:,3]>=16
  lab,n=ndimage.label(mask,structure=np.ones((3,3),dtype=np.uint8))
  objs=ndimage.find_objects(lab)
  comps=[]
  for idx,sl in enumerate(objs,1):
   if sl is None: continue
   area=int((lab[sl]==idx).sum())
   if area>=20:
    comps.append((area,idx,(sl[1].start,sl[0].start,sl[1].stop,sl[0].stop)))
  if not comps: raise ValueError((oid,view,'empty cell'))
  comps.sort(reverse=True); main=comps[0]
  bx0,by0,bx1,by1=main[2]
  kept=[]
  for area,idx,(cx0,cy0,cx1,cy1) in comps:
   gapx=max(0,bx0-cx1,cx0-bx1); gapy=max(0,by0-cy1,cy0-by1)
   if idx==main[1] or (gapx<=18 and gapy<=18): kept.append(idx)
  keep=np.isin(lab,kept)
  ys,xs=np.where(keep)
  bx0,by0,bx1,by1=xs.min(),ys.min(),xs.max()+1,ys.max()+1
  crop=cell[by0:by1,bx0:bx1].copy()
  local=keep[by0:by1,bx0:bx1]
  crop[~local]=0
  im=Image.fromarray(crop,'RGBA')
  nw=max(1,round(im.width*scale)); nh=max(1,round(im.height*scale))
  im=im.resize((nw,nh),Image.Resampling.NEAREST)
  canvas=Image.new('RGBA',(256,256),(0,0,0,0))
  px=128-nw//2; py=128-nh//2
  canvas.alpha_composite(im,(px,py))
  out=BASE+f'/images/{oid}.{view}.png'; canvas.save(out)
  assets.append({'object_id':oid,'view':view,'path':out,'sha256':hashlib.sha256(open(out,'rb').read()).hexdigest(),
    'crop':{'atlas_cell_xyxy':[x0,y0,x1,y1],'crop_xyxy_local':[int(bx0),int(by0),int(bx1),int(by1)],'alpha_threshold':16,'connectivity':8,'main_component_area':main[0],'included_component_areas':[area for area,idx,b in comps if idx in kept]},
    'scale':scale,'offset_px':[px,py],'size_px':[nw,nh]})
with open(BASE+'/batch01-v1-recipe.json','w') as f: json.dump({'atlas':RAW,'atlas_sha256':hashlib.sha256(open(RAW,'rb').read()).hexdigest(),'extractor':'extract_batch01_v1.py','assets':assets},f,indent=2)
print(json.dumps(assets,indent=2))
