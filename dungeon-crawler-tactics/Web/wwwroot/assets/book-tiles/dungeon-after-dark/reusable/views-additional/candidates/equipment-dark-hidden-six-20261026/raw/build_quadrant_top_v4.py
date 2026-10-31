#!/usr/bin/env python3
"""Replay the generated Quadrant TOP v4 from the retained full transparent output."""
from pathlib import Path
from PIL import Image
import numpy as np,hashlib,json
from scipy.ndimage import label,generate_binary_structure
ROOT=Path(__file__).resolve().parent.parent; raw=ROOT/'raw/quadrant-top-correction-output-v8.png'; out=ROOT/'images/thresholds-quadrant-selection-wheel.top.candidate-v4.png'
im=Image.open(raw).convert('RGBA'); a=np.asarray(im.getchannel('A'));lab,n=label(a>=64,structure=generate_binary_structure(2,2)); comps=[]
for i in range(1,n+1):
 y,x=np.where(lab==i)
 if len(x)>500: comps.append((len(x),i,(int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1))))
area,i,box=max(comps);x0,y0,x1,y1=box;crop=im.crop(box)
mask=Image.fromarray(np.where(lab[y0:y1,x0:x1]==i,255,0).astype('uint8'));crop.putalpha(Image.fromarray(np.minimum(np.asarray(crop.getchannel('A')),np.asarray(mask)).astype('uint8')))
scale=181/max(crop.size);size=(round(crop.width*scale),round(crop.height*scale));res=crop.resize(size,Image.Resampling.NEAREST);offset=((256-size[0])//2,(256-size[1])//2)
can=Image.new('RGBA',(256,256),(0,0,0,0));can.alpha_composite(res,offset);out.parent.mkdir(parents=True,exist_ok=True);can.save(out)
record={'raw_path':'raw/'+raw.name,'raw_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'threshold':64,'connectivity':8,'selected_component':'largest component >500 pixels','component_area':area,'bbox_xyxy':list(box),'resampling':'PIL.Image.Resampling.NEAREST','scale_isotropic':scale,'resized_wh':list(size),'offset_xy':list(offset),'anchor_px':[128,128],'candidate_path':'images/'+out.name,'candidate_sha256':hashlib.sha256(out.read_bytes()).hexdigest()}
(ROOT/'raw/quadrant-top-normalization-v4.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
