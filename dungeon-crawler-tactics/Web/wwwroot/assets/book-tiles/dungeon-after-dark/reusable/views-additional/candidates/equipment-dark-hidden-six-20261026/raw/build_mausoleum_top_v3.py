#!/usr/bin/env python3
"""Rebuild the v3 inferred Mausoleum TOP from the exact retained generated atlas."""
from pathlib import Path
from PIL import Image
import numpy as np,hashlib,json
from scipy.ndimage import label,generate_binary_structure
R=Path(__file__).resolve().parent; BASE=R.parent
raw=R/'mausoleum-top-correction-output-v4.png'; out=BASE/'images/ghost-cemetery-mausoleum-facade.top.candidate-v3.png'
im=Image.open(raw).convert('RGBA'); alpha=np.asarray(im.getchannel('A')); labels,n=label(alpha>=64,structure=generate_binary_structure(2,2))
comps=[]
for idx in range(1,n+1):
 y,x=np.where(labels==idx)
 if len(x)>500: comps.append((len(x),idx,(int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1))))
area,idx,box=max(comps);x0,y0,x1,y1=box
crop=im.crop(box);mask=Image.fromarray(np.where(labels[y0:y1,x0:x1]==idx,255,0).astype('uint8')); crop.putalpha(Image.fromarray(np.minimum(np.asarray(crop.getchannel('A')),np.asarray(mask)).astype('uint8')))
scale=204/max(crop.size);size=(round(crop.width*scale),round(crop.height*scale));res=crop.resize(size,Image.Resampling.NEAREST)
offset=((256-size[0])//2,(256-size[1])//2);canvas=Image.new('RGBA',(256,256),(0,0,0,0));canvas.alpha_composite(res,offset);out.parent.mkdir(parents=True,exist_ok=True);canvas.save(out)
record={'raw_path':'raw/'+raw.name,'raw_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'threshold':64,'connectivity':8,'bbox_xyxy':list(box),'component_area':area,'scale_isotropic':scale,'resampling':'PIL.Image.Resampling.NEAREST','resized_wh':list(size),'offset_xy':list(offset),'anchor_px':[128,128],'candidate_path':'images/'+out.name,'candidate_sha256':hashlib.sha256(out.read_bytes()).hexdigest()}
(BASE/'mausoleum-top-normalization-v3.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
