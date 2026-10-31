from PIL import Image
import numpy as np, os, json, hashlib
from scipy import ndimage
ROOT='/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/dungeon-after-dark'
BASE=ROOT+'/reusable/views-additional/candidates/equipment-dark-last-seven-fixtures-20261026'
HND='/workspace/scratch/equipment-dark-last-seven-fixtures-handoff-20261026.json'
h=json.load(open(HND)); oid='over-city-venues-painted-civic-stone-wall-northeast';obj=next(x for x in h['objects'] if x['object_id']==oid)
source=obj['source']['path']; im=Image.open(source).convert('RGBA'); a=np.array(im); lab,n=ndimage.label(a[:,:,3]>=16,structure=np.ones((3,3),dtype=np.uint8)); sizes=np.bincount(lab.ravel()); sizes[0]=0; k=int(sizes.argmax()); sy,sx=np.where(lab==k); box=(sx.min(),sy.min(),sx.max()+1,sy.max()+1); crop=im.crop(box)
# Source-faithful native narrow end face: isotropic calibration to the accepted elevation height.
face_scale=189/crop.height; size=(round(crop.width*face_scale),round(crop.height*face_scale));
for view,objim in [('front',crop),('rear',crop.transpose(Image.Transpose.FLIP_LEFT_RIGHT))]:
 r=objim.resize(size,Image.Resampling.NEAREST); canvas=Image.new('RGBA',(256,256),(0,0,0,0)); pos=(128-size[0]//2,128-size[1]//2); canvas.alpha_composite(r,pos); canvas.save(BASE+f'/images/{oid}.{view}.png')
# Source-supported roof/cap plan derived by rigidly rotating generated horizontal cap/edge strip 90 degrees.
raw=Image.open(BASE+'/raw/batch01-v1.png').convert('RGBA'); rw,rh=raw.size
cell=(round(rw/6),round(2*rh/3),round(2*rw/6),round(rh))
x0,y0,x1,y1=cell; ar=np.array(raw.crop(cell)); mask=ar[:,:,3]>=16; l,n=ndimage.label(mask,structure=np.ones((3,3),dtype=np.uint8)); sz=np.bincount(l.ravel());sz[0]=0;k=int(sz.argmax()); yy,xx=np.where(l==k);bb=(xx.min(),yy.min(),xx.max()+1,yy.max()+1); strip=Image.fromarray(ar[bb[1]:bb[3],bb[0]:bb[2]]).rotate(90,expand=True)
top_scale=0.82; dims=(round(strip.width*top_scale),round(strip.height*top_scale)); strip=strip.resize(dims,Image.Resampling.NEAREST);canvas=Image.new('RGBA',(256,256),(0,0,0,0)); pos=(128-dims[0]//2,128-dims[1]//2);canvas.alpha_composite(strip,pos);canvas.save(BASE+f'/images/{oid}.top.png')
rec={'object_id':oid,'source':source,'source_sha256':hashlib.sha256(open(source,'rb').read()).hexdigest(),'raw_atlas':BASE+'/raw/batch01-v1.png','raw_atlas_sha256':hashlib.sha256(open(BASE+'/raw/batch01-v1.png','rb').read()).hexdigest(),'source_crop_xyxy':[int(v) for v in box],'front_rear':{'source_selection':'largest 8-connected alpha>=16 component from canonical source','scale':float(face_scale),'canvas':[256,256],'anchor_px':[128,128],'placement':[int(pos[0]),int(pos[1])],'rear_transform':'horizontal flip; explicitly inferred unmarked reverse face'},'top':{'source_cell_xyxy':[int(v) for v in cell],'crop_xyxy_local':[int(v) for v in bb],'alpha_threshold':16,'connectivity':8,'transform':'rotate90ccw','uniform_scale':float(top_scale),'canvas':[256,256],'anchor_px':[128,128],'placement':[int(pos[0]),int(pos[1])],'notes':'inferred long-Y cap/roof footprint; transformed generated cap strip, not native front-face copy'}}
for v in ['front','top','rear']:
 p=BASE+f'/images/{oid}.{v}.png';rec.setdefault('candidates',{})[v]={'path':p,'sha256':hashlib.sha256(open(p,'rb').read()).hexdigest()}
json.dump(rec,open(BASE+'/wall-v2-recipe.json','w'),indent=2)
print(json.dumps(rec,indent=2))
