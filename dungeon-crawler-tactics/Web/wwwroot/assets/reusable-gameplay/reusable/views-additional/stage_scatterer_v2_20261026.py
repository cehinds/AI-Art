#!/usr/bin/env python3
"""Deterministically stage six normalized Scatterer candidates without modifying live metadata."""
from pathlib import Path
from PIL import Image, ImageDraw
import hashlib, json, struct
import numpy as np
from scipy import ndimage

HERE=Path(__file__).resolve().parent
RAW=HERE/'raw'
OID='scenario-props--scatterer'
ATLAS=RAW/'scatterer-six-view-v2-20261026.png'
ORDER=['front','top','right','left','bottom','rear']
REQUEST='exec-c216806a-c081-451f-a124-e75f5b890c9c'
OUT=RAW/'scatterer-v2-candidates'
OUT.mkdir(exist_ok=True)
def sha(b): return hashlib.sha256(b).hexdigest()
def rgba_hash(im): return sha(struct.pack('>II',*im.size)+im.convert('RGBA').tobytes())
atlas_bytes=ATLAS.read_bytes(); atlas=Image.open(ATLAS).convert('RGBA')
assert atlas.size==(2172,724), atlas.size
native=HERE.parents[0]/'native'/f'{OID}.png'; source_sha=sha(native.read_bytes())
old=[]
for v in ('front','right','left','rear'):
 a=Image.open(HERE/f'{OID}.{v}.png').convert('RGBA').getchannel('A')
 box=a.getbbox(); old.append(box[3]-box[1])
target_z=sum(old)/len(old)
cw=atlas.width//6; crops=[]; newz=[]
for i,v in enumerate(ORDER):
 cell=atlas.crop((i*cw,0,(i+1)*cw,atlas.height))
 alpha=cell.getchannel('A').point(lambda a:255 if a>=16 else 0)
 box=alpha.getbbox()
 if not box: raise RuntimeError(f'empty cell {v}')
 # no silhouette may approach or touch the square cell bounds
 if box[0]<=3 or box[1]<=3 or box[2]>=cw-3 or box[3]>=atlas.height-3: raise RuntimeError(f'unsafe margin {v}: {box}')
 crop=cell.crop(box); crops.append((v,i*cw,box,crop))
 if v in ('front','right','left','rear'): newz.append(crop.height)
scale=target_z/(sum(newz)/len(newz))
records=[]
for v,x0,box,crop in crops:
 size=(round(crop.width*scale),round(crop.height*scale))
 resized=crop.resize(size,Image.Resampling.LANCZOS)
 # Remove only disconnected one-pixel specks at alpha>=16; preserve all antennae and other components.
 if v=='left':
  arr=np.array(resized).copy(); labels,count=ndimage.label(arr[:,:,3]>=16); sizes=np.bincount(labels.ravel());
  for lab in range(1,len(sizes)):
   if sizes[lab]==1: arr[labels==lab,3]=0
  resized=Image.fromarray(arr,'RGBA')
 canvas=Image.new('RGBA',(256,256),(0,0,0,0))
 offset=(128-size[0]//2,128-size[1]//2); canvas.alpha_composite(resized,offset)
 path=OUT/f'{OID}.{v}.candidate.png'; canvas.save(path,format='PNG',optimize=False)
 records.append({'view':v,'candidate_path':str(path.relative_to(HERE)),'png_sha256':sha(path.read_bytes()),'rgba_sha256':rgba_hash(canvas),'cell_bounds_xywh':[x0,0,cw,atlas.height],'alpha_bbox_local_xyxy':list(box),'normalized_alpha_bbox_xyxy':list(canvas.getchannel('A').getbbox()),'resized_wh':list(size),'canvas_offset_xy':[offset[0],offset[1]],'uniform_scale':scale})
# Contact includes canonical native source plus six principal candidates.
contact=Image.new('RGBA',(7*240,280),(48,48,52,255)); draw=ImageDraw.Draw(contact)
src=Image.open(native).convert('RGBA'); src.thumbnail((210,220),Image.Resampling.NEAREST)
contact.alpha_composite(src,(15+(210-src.width)//2,38+(220-src.height)//2)); draw.text((8,10),'CANONICAL SOURCE',fill='white')
for i,r in enumerate(records):
 im=Image.open(HERE/r['candidate_path']).convert('RGBA'); im.thumbnail((210,220),Image.Resampling.NEAREST)
 x=(i+1)*240+15+(210-im.width)//2; y=38+(220-im.height)//2
 contact.alpha_composite(im,(x,y)); draw.text(((i+1)*240+8,10),r['view'].upper(),fill='white')
contact_path=OUT/'scatterer-v2-source-six-contact.png'; contact.save(contact_path,format='PNG',optimize=False)
report={'object_id':OID,'source_image':'reusable/native/'+native.name,'source_image_sha256':source_sha,'source_native_wh':list(Image.open(native).size),'live_base_png_sha256':{v:sha((HERE/f'{OID}.{v}.png').read_bytes()) for v in ORDER},'source_atlas':'reusable/views-additional/raw/'+ATLAS.name,'source_atlas_sha256':sha(atlas_bytes),'generation_request_id':REQUEST,'generation_output':'/workspace/generated_images/exec-c216806a-c081-451f-a124-e75f5b890c9c.png','generation_output_sha256':sha(atlas_bytes),'generation_prompt':'reusable/views-additional/raw/scatterer-six-view-v2-20261026.prompt.txt','cell_coordinate_format':'xywh','alpha_bbox_coordinate_format':'xyxy','normalized_alpha_bbox_coordinate_format':'xyxy','cell_wh':[cw,atlas.height],'bbox_coordinate_format':'xyxy','alpha_threshold':16,'previous_elevation_height_px':old,'target_z_px':target_z,'scale_calibration':'one shared isotropic scale calibrated from existing accepted F/R/R/L/REAR elevation Z extents','anchor_px':[128,128],'candidates':records,'contact_path':str(contact_path),'contact_sha256':sha(contact_path.read_bytes())}
(OUT/'scatterer-v2-stage-report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'scale':scale,'contact':str(contact_path),'contact_sha256':report['contact_sha256'],'views':[{x['view']:x['normalized_alpha_bbox_xyxy']} for x in records]},indent=2))
