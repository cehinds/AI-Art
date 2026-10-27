#!/usr/bin/env python3
"""Exact offline replay of the accepted Jungle OPEN TOP candidate v3.
Input is the retained full RGBA image-generation PNG. We label alpha>=64 with
8-connectivity, choose the largest component among those >500 pixels, crop its
full bounding box, keep original alpha for pixels in that component (zero alpha
for everything outside it), then isotropically resize to 202px width with
PIL NEAREST and center on a transparent 256x256 canvas. There is no painting,
reflection or anisotropic distortion. `--out` allows a noncanonical replay test.
"""
from pathlib import Path
import argparse,hashlib,json
from PIL import Image
import numpy as np
from scipy.ndimage import label,generate_binary_structure
ROOT=Path(__file__).resolve().parent.parent; raw=ROOT/'raw/jungle-open-top-output-v3.png'; default=ROOT/'images/hunting-jungle-vine-covered-ruin-stone-open-doorway.top.candidate-v3.png'
ap=argparse.ArgumentParser();ap.add_argument('--out',default=str(default));args=ap.parse_args()
im=Image.open(raw).convert('RGBA');a=np.asarray(im.getchannel('A'));lab,n=label(a>=64,structure=generate_binary_structure(2,2));comps=[]
for i in range(1,n+1):
 yy,xx=np.where(lab==i)
 if len(xx)>500:comps.append((len(xx),i,(int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1))))
if not comps:raise RuntimeError('no foreground component')
area,i,box=max(comps);x0,y0,x1,y1=box;crop=im.crop(box);cm=lab[y0:y1,x0:x1]
mask=Image.fromarray(np.where(cm==i,255,0).astype('uint8'));crop.putalpha(Image.fromarray(np.minimum(np.asarray(crop.getchannel('A')),np.asarray(mask)).astype('uint8')))
scale=202/max(crop.size);size=(round(crop.width*scale),round(crop.height*scale));res=crop.resize(size,Image.Resampling.NEAREST);offset=((256-size[0])//2,(256-size[1])//2)
can=Image.new('RGBA',(256,256),(0,0,0,0));can.alpha_composite(res,offset);out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True);can.save(out)
result={'raw_path':'raw/'+raw.name,'raw_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'threshold':64,'connectivity':8,'component_area':area,'component_bbox_xyxy':list(box),'alpha_operation':'retain original alpha inside selected component; set all other crop alpha to zero','scale_isotropic':scale,'resampler':'PIL.Image.Resampling.NEAREST','resized_wh':list(size),'offset_xy':list(offset),'anchor_px':[128,128],'candidate_sha256':hashlib.sha256(out.read_bytes()).hexdigest()}
print(json.dumps(result,indent=2))
