#!/usr/bin/env python3
"""Versioned, pixel-exact candidate normalizer for the six ground/platform set."""
from PIL import Image, ImageDraw
import numpy as np
from scipy import ndimage
import json, hashlib, os, struct

PACK='/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/dungeon-after-dark'
BASE=os.path.join(PACK,'reusable/views-additional')
CAND=os.path.join(BASE,'candidates/equipment-dark-six-ground-platforms-20261026')
HAND='/workspace/scratch/equipment-dark-six-ground-platforms-handoff-20261026.json'
HAND_SHA='322d4973ff94801647c5094eda70c11347a20325b66dd0f61c62c4ccff7eb0d9'
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def bounds_alpha(im,threshold=64):
 a=im.convert('RGBA').getchannel('A').point(lambda v:255 if v>=threshold else 0)
 return a.getbbox()
def crop_main_component(path,cols,rows,index):
 im=Image.open(path).convert('RGBA'); w,h=im.size
 col=index%cols; row=index//cols
 x0=round(col*w/cols); x1=round((col+1)*w/cols); y0=round(row*h/rows); y1=round((row+1)*h/rows)
 cell=im.crop((x0,y0,x1,y1)); arr=np.array(cell); alpha=arr[:,:,3]
 labels,n=ndimage.label(alpha>=64,structure=np.ones((3,3),dtype=np.uint8))
 sizes=np.bincount(labels.ravel()); sizes[0]=0
 if not sizes.max(): raise RuntimeError(f'no alpha in {path} cell {index}')
 lab=int(sizes.argmax()); mask=(labels==lab)
 # Include antialiased fringe attached to the selected 8-connected component.
 mask=ndimage.binary_dilation(mask,structure=np.ones((3,3),dtype=bool))
 arr[:,:,3]=np.where(mask,alpha,0).astype(np.uint8)
 out=Image.fromarray(arr,'RGBA'); bb=out.getchannel('A').point(lambda v:255 if v>=64 else 0).getbbox()
 allcomps=[]
 for k in range(1,n+1):
  yy,xx=np.where(labels==k)
  if len(xx):allcomps.append({'label':k,'pixels_alpha_ge_64':int(len(xx)),'bbox_global':[x0+int(xx.min()),y0+int(yy.min()),x0+int(xx.max())+1,y0+int(yy.max())+1]})
 crop=out.crop(bb)
 return crop,[x0+bb[0],y0+bb[1],x0+bb[2],y0+bb[3]],[x0,y0,x1,y1],sorted(allcomps,key=lambda x:x['pixels_alpha_ge_64'],reverse=True)
def crop_source(path):
 im=Image.open(path).convert('RGBA'); bb=bounds_alpha(im,64)
 if not bb: raise RuntimeError('empty native source')
 return im.crop(bb),list(bb)
def place(crop,max_w,max_h,center=(128,128)):
 w,h=crop.size; s=min(max_w/w,max_h/h,1.0)
 nw=max(1,round(w*s));nh=max(1,round(h*s));scaled=crop.resize((nw,nh),Image.Resampling.NEAREST)
 xy=(round(center[0]-nw/2),round(center[1]-nh/2)); out=Image.new('RGBA',(256,256),(0,0,0,0));out.alpha_composite(scaled,xy)
 return out,s,[nw,nh],xy

hand=json.load(open(HAND)); assert sha(HAND)==HAND_SHA
objects={x['object_id']:x for x in hand['objects']}
cfg={
 'industry-menagerie-industrial-brick-edge-transition':('industry-atlas-v2.png',2,2,['front','right','left'],216,95),
 'iron-stations-platform-edge-segment':('station-edge-atlas-v2.png',2,2,['front','right','left','rear'],216,95),
 'iron-stations-platform-end-ramp':('ramp-ends-atlas-v2.png',2,1,['front','rear'],210,128),
 'over-city-city-cobblestone-corner-transition':('overcity-corner-atlas-v2.png',3,1,['front','right','left'],216,95),
 'over-city-city-cobblestone-edge-transition':('overcity-edge-atlas-v2.png',3,1,['front','right','left'],216,95),
 'over-city-venues-civic-stone-tile-corner-transition':('civic-corner-front-atlas-v1.png',1,1,['front'],216,95),
}
manifest={'candidate_id':'equipment-dark-six-ground-platforms-v2','candidate_only':True,'scope':'book-tiles/dungeon-after-dark','candidate_owner':'views_equipment','reviewer':'page_inventory','installer':'views_dark_books','handoff_path':HAND,'handoff_sha256':HAND_SHA,'activation_proof_path':'/tmp/page-qa-dark-unowned-twelve-current-20261026-01.png.json','activation_proof_sha256':'1be1842a0e85b06a7739ad2c53f97412b03f8f90ea5611008fc4eb11502d0e3d','normalizer_path':'reusable/views-additional/candidates/equipment-dark-six-ground-platforms-20261026/raw/prepare_ground_candidates_v2.py','sets':[]}
contacts=[]
for oid,(rawname,cols,rows,views,maxw,maxh) in cfg.items():
 o=objects[oid];raw=os.path.join(CAND,'raw',rawname);rsha=sha(raw);src=o['source']['path'];srcsha=sha(src)
 entry={'object_id':oid,'source_path':src,'source_sha256':srcsha,'affected_views':[],'base_current_views':{},'candidates':{},'notes':'Generated orthographic views are inferred illustrations of unseen surfaces. Candidate only; no production assets changed.'}
 for v in ('front','top','right','left','bottom','rear'):
  p=o['views'][v]['path'];bsha=sha(p); assert bsha==o['views'][v]['sha256'],f'{oid}.{v} changed since activated handoff';entry['base_current_views'][v]={'path':p,'sha256':bsha}
 assert srcsha==o['source']['sha256'],f'{oid} source changed since handoff'
 for i,v in enumerate(views):
  crop,bb,cellbbox,components=crop_main_component(raw,cols,rows,i)
  out,s,size,xy=place(crop,maxw,maxh)
  dest=os.path.join(CAND,'images',oid+'.'+v+'.candidate-v2.png');out.save(dest,optimize=False)
  request_name={'industry-atlas-v2.png':'industry-request-v2.json','station-edge-atlas-v2.png':'station-edge-request-v2.json','ramp-ends-atlas-v2.png':'ramp-request-v2.json','overcity-corner-atlas-v2.png':'overcity-corner-request-v2.json','overcity-edge-atlas-v2.png':'overcity-edge-request-v2.json','civic-corner-front-atlas-v1.png':'civic-corner-request-v1.json'}[rawname]
  request=os.path.join(CAND,'raw',request_name)
  entry['candidates'][v]={'path':dest,'sha256':sha(dest),'method':'generated-atlas-cell-main-component','generated_atlas':raw,'generated_atlas_sha256':rsha,'request_path':request,'request_sha256':sha(request),'cell_index':i,'cell_grid':[cols,rows],'cell_order':views,'nominal_cell_global_bbox':cellbbox,'selected_alpha64_component_bbox_global':bb,'components_alpha64_in_cell':components,'normalization':{'threshold_alpha_ge':64,'selection':'largest 8-connected alpha>=64 component; preserve its attached antialias fringe by one-pixel dilation','filter':'NEAREST','uniform_scale':s,'resized_dimensions':size,'canvas':[256,256],'anchor_px':[128,128],'placement_xy':xy}}
  entry['affected_views'].append(v)
 # Native source plans are isotropically normalized (preserve all source pixels and aspect ratio).
 if oid in ('industry-menagerie-industrial-brick-edge-transition','over-city-city-cobblestone-edge-transition'):
  crop,bb=crop_source(src); out,s,size,xy=place(crop,180,180)
  dest=os.path.join(CAND,'images',oid+'.top.candidate-v2.png');out.save(dest,optimize=False)
  entry['candidates']['top']={'path':dest,'sha256':sha(dest),'method':'source-pixel-copy-uniform-nearest-calibration','donor_path':src,'donor_sha256':srcsha,'source_alpha64_crop_bbox':bb,'normalization':{'filter':'NEAREST','uniform_scale':s,'resized_dimensions':size,'canvas':[256,256],'anchor_px':[128,128],'placement_xy':xy}}
  entry['affected_views'].append('top')
 manifest['sets'].append(entry)
 labs=['SOURCE','FRONT','TOP','RIGHT','LEFT','BOTTOM','REAR']; ims=[Image.open(src).convert('RGBA')]
 for v in ('front','top','right','left','bottom','rear'):
  ims.append(Image.open(entry['candidates'][v]['path']).convert('RGBA') if v in entry['candidates'] else Image.open(o['views'][v]['path']).convert('RGBA'))
 contacts.append((oid,labs,ims))
mp=os.path.join(CAND,'candidate-manifest-v2.json');open(mp,'w').write(json.dumps(manifest,indent=2)+'\n')
tw=170;th=170;lh=26;pad=8;rh=th+lh+pad
sheet=Image.new('RGBA',(pad+7*(tw+pad),pad+len(contacts)*rh),(34,34,40,255));dr=ImageDraw.Draw(sheet)
for ri,(oid,labs,ims) in enumerate(contacts):
 y=pad+ri*rh;dr.text((pad,y),oid,fill='white');ty=y+lh
 for ci,(lab,im) in enumerate(zip(labs,ims)):
  x=pad+ci*(tw+pad);im.thumbnail((tw,th),Image.Resampling.NEAREST);sheet.alpha_composite(im,(x+(tw-im.width)//2,ty+(th-im.height)//2));dr.text((x,ty+th),lab,fill='white')
cp=os.path.join(CAND,'contacts','source-six-candidate-v2.png');sheet.save(cp)
receipt={'candidate_manifest_path':os.path.relpath(mp,PACK),'candidate_manifest_sha256':sha(mp),'contact_path':cp,'contact_sha256':sha(cp),'candidate_only':True,'install_authorized':False}
rp=os.path.join(CAND,'contact-receipt-v2.json');open(rp,'w').write(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'manifest':mp,'manifest_sha256':sha(mp),'contact':cp,'contact_sha256':sha(cp),'sets':len(manifest['sets']),'directions':sum(len(x['candidates']) for x in manifest['sets'])},indent=2))
