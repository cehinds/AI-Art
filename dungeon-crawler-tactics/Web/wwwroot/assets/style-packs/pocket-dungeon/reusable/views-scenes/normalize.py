#!/usr/bin/env python3
"""Offline normalization of retained inferred-view atlases. No art is drawn.
Run in place: python normalize.py (rebuilds PNGs + metadata from generation.json).
"""
from pathlib import Path
import json,hashlib,struct
import numpy as np
from PIL import Image
from scipy import ndimage
OUT=Path(__file__).resolve().parent;PACK=OUT.parents[1];VIEWS=['front','top','right','left','bottom','rear']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def borders(count,n,radius):
 out=[0]
 for k in range(1,n):
  ideal=round(len(count)*k/n);a=max(out[-1]+1,ideal-radius);b=min(len(count)-1,ideal+radius);best=min(range(a,b),key=lambda q:(count[q],abs(q-ideal)));out.append(best)
 return out+[len(count)]
def auxiliary_meta(path,kind,provenance):
 image=Image.open(path).convert('RGBA');rel=path.relative_to(PACK).as_posix();meta=path.with_suffix('.json');dump(meta,{'id':path.stem,'name':path.stem,'kind':kind,'reusable':False,'tags':['pipeline-artifact'],'image':{'path':rel,'width':image.width,'height':image.height,'sha256':sha(path),'rgba_sha256':hashlib.sha256(struct.pack('>II',*image.size)+image.tobytes()).hexdigest()},'metadata_path':meta.relative_to(PACK).as_posix(),'anchor_px':[0,0],'views':{'applicable':False,'complete':True,'reason':'pipeline atlas or contact sheet, not a placed object'},'provenance':provenance})
assets=[];sets=[]
for batch in json.loads((OUT/'generation.json').read_text()):
 raw=OUT/batch['raw'];im=Image.open(raw).convert('RGBA');arr=np.asarray(im);mask=arr[:,:,3]>=245;rows=borders(mask.sum(axis=1),len(batch['objects']),80);recipes=[]
 labels,n=ndimage.label(mask,np.ones((3,3)));counts=np.bincount(labels.ravel());major=sorted(range(1,n+1),key=lambda k:counts[k],reverse=True)[:len(batch['objects'])*6];components=[]
 for k in major:
  yy,xx=np.where(labels==k);components.append({'label':k,'cx':float(xx.mean()),'cy':float(yy.mean()),'bbox':[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)]})
 components.sort(key=lambda a:a['cy'])
 for row,oid in enumerate(batch['objects']):
  chosen=sorted(components[row*6:(row+1)*6],key=lambda a:a['cx']);y0=min(a['bbox'][1] for a in chosen);y1=max(a['bbox'][3] for a in chosen);cols=[];crops=[];rects=[];boxes=[]
  for comp in chosen:
   x0,ya,x1,yb=comp['bbox'];cell=im.crop((x0,ya,x1,yb));keep=labels[ya:yb,x0:x1]==comp['label'];cell.putalpha(Image.fromarray((keep*255).astype('uint8')));crops.append(cell);rects.append([x0,ya,x1-x0,yb-ya]);boxes.append([0,0,x1-x0,yb-ya]);cols.append([x0,x1])
  scale=220/max(max(c.size) for c in crops);views={}
  for col,(view,crop) in enumerate(zip(VIEWS,crops)):
   sz=[max(1,round(v*scale)) for v in crop.size];frame=Image.new('RGBA',(256,256));frame.alpha_composite(crop.resize(sz,Image.Resampling.NEAREST),((256-sz[0])//2,248-sz[1]));aid=oid+'.'+view;dst=OUT/(aid+'.png');frame.save(dst);rel=dst.relative_to(PACK).as_posix();meta=dst.with_suffix('.json');d={'id':aid,'name':oid.replace('-scene-patch','').replace('-',' ').title()+' '+view,'kind':'sprite','tags':['scene-object','isolated','orthographic','inferred-view',view],'object_id':oid,'view':view,'reusable':True,'image':{'path':rel,'width':256,'height':256,'sha256':sha(dst),'rgba_sha256':hashlib.sha256(struct.pack('>II',256,256)+frame.tobytes()).hexdigest()},'metadata_path':meta.relative_to(PACK).as_posix(),'anchor_px':[128,248],'views':{'applicable':False,'complete':True,'reason':'single directional sprite; belongs to six-view object set'},'provenance':{'method':'generated','source_image':'reusable/scene-assets/'+oid+'.png','generated_atlas':raw.relative_to(PACK).as_posix(),'generated_atlas_sha256':sha(raw),'generation_parameters':{'tool':'image_gen.imagegen','transparent_background':True,'prompt':batch['prompt'],'reference_images':batch['reference_images']},'normalization':{'cell_rect':rects[col],'alpha_threshold':245,'connected_component_policy':'global-major-components-ordered-by-row-and-column','alpha_bbox':boxes[col],'shared_scale':scale,'render_size_px':sz,'canvas':[256,256],'resampling':'NEAREST','anchor_px':[128,248]},'notes':'Generated isolation and inferred hidden surfaces. Not exact recovered pixels, not source geometry. Soft alpha haze removed by deterministic threshold.'}};dump(meta,d);assets.append(d);views[view]=aid
  sets.append({'object_id':oid,'views':views,'complete':True,'notes':'Six generated principal views with inferred hidden surfaces; clean front is reusable proxy for baked scene patch.'});recipes.append({'object_id':oid,'row':row,'row_bounds':[y0,y1],'column_bounds':cols})
 auxiliary_meta(raw,'generated_atlas',{'method':'generated','generation_parameters':{'tool':'image_gen.imagegen','transparent_background':True,'prompt':batch['prompt'],'reference_images':batch['reference_images']}})
 dump(raw.with_suffix('.recipe.json'),{'atlas_sha256':sha(raw),'objects':recipes,'normalizer':'reusable/views-scenes/normalize.py'})
dump(OUT/'set-index.json',{'assets':assets,'view_sets':sets})
# Preview contact sheet; it is a derived layout of unmodified sprite frames.
preview=Image.new('RGBA',(6*256,len(sets)*256))
for r,s in enumerate(sets):
 for c,v in enumerate(VIEWS):preview.alpha_composite(Image.open(OUT/(s['views'][v]+'.png')),(c*256,r*256))
preview.save(OUT/'preview.png');auxiliary_meta(OUT/'preview.png','contact_sheet',{'method':'composed','source_images':[a['image']['path'] for a in assets]});print(len(assets),'sprites;',len(sets),'complete sets')
