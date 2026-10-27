#!/usr/bin/env python3
from PIL import Image
import hashlib,json,os
BASE='/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/dungeon-after-dark';C=BASE+'/reusable/views-additional/candidates/equipment-dark-stairs-successor-20261026';H=json.load(open('/workspace/scratch/equipment-dark-eight-stairs-successor-handoff-20261026.json'));ids=['iron-trains-railcar-metal-stairs-up','iron-trains-railcar-metal-stairs-down'];V=['bottom','rear'];bottomraw=C+'/raw/iron-bottom-single-v2.png';rearraw=C+'/raw/iron-rear-single-v1.png'
def sha(p):return hashlib.sha256(open(p,'rb').read()).hexdigest()
raws={'bottom':bottomraw,'rear':rearraw};bboxes={v:Image.open(p).convert('RGBA').getchannel('A').point(lambda q:255 if q>=64 else 0).getbbox() for v,p in raws.items()}
assets=[];records=[]
for i,oid in enumerate(ids):
 obj=next(o for o in H['objects'] if o['object_id']==oid)
 for v in V:
  raw=raws[v];im=Image.open(raw).convert('RGBA');b=bboxes[v];part=im.crop(b)
  if v=='bottom':
   targets=[]
   for vv in ['top','bottom','front']:
    bb=Image.open(obj['views'][vv]['path']).convert('RGBA').getchannel('A').point(lambda q:255 if q>=64 else 0).getbbox();targets.append(bb[2]-bb[0])
   target=round(sum(targets)/len(targets));scale=target/part.width;sz=(target,round(part.height*scale));target_z=None
  else:
   heights=[]
   for vv in ['front','right','left']:
    bb=Image.open(obj['views'][vv]['path']).convert('RGBA').getchannel('A').point(lambda q:255 if q>=64 else 0).getbbox();heights.append(bb[3]-bb[1])
   target_z=round(sum(heights)/len(heights));scale=target_z/part.height;sz=(round(part.width*scale),target_z);target=target_z
  res=part.resize(sz,Image.Resampling.NEAREST);can=Image.new('RGBA',(256,256),(0,0,0,0));can.alpha_composite(res,((256-sz[0])//2,(256-sz[1])//2));out=f'{C}/images/{oid}.{v}.png';can.save(out);src=obj['source']
  geom={'path':'../../style-packs/ink-and-lanterns/reusable/views-additional/stairs.bottom.png','sha256':'be80283788cda49da92898925bd548c2f8fb8026c8a235bfaedd73d4be211fac','role':'bottom camera geometry only'} if v=='bottom' else {'path':'reusable/views-additional/candidates/equipment-dark-stairs-successor-20261026/images/personal-space-warm-wood-plank-stairs-up.rear.png','sha256':sha(BASE+'/reusable/views-additional/candidates/equipment-dark-stairs-successor-20261026/images/personal-space-warm-wood-plank-stairs-up.rear.png'),'role':'Page-accepted same-pack rear-support geometry only'}
  asset={'asset_id':oid+'.'+v,'object_id':oid,'view':v,'candidate_path':'images/'+oid+'.'+v+'.png','sha256':sha(out),'width':256,'height':256,'anchor_px':[128,128],'provenance':{'method':'generated' if i==0 else 'reused','source_image':os.path.relpath(src['path'],BASE),'source_sha256':src['sha256'],'generated_atlas_path':'raw/iron-bottom-single-v2.png' if v=='bottom' else 'raw/iron-rear-single-v1.png','generated_atlas_sha256':sha(raw),'geometry_guide':geom,'inferred_symmetry_alias_of':ids[0]+'.'+v if i else None,'notes':'Inferred dark riveted steel and yellow rail reverse construction; same hidden up/down support is reused because source shows the same frame/material and no asymmetric hidden feature.'},'normalization':{'raw_alpha_bbox_xyxy':list(b),'raw_alpha_threshold':64,'target_extent_px':target,'target_z_px':target_z,'uniform_isotropic_scale':scale,'resampling':'NEAREST','normalized_size_px':list(sz),'offset_px':[(256-sz[0])//2,(256-sz[1])//2]}}
  assets.append(asset);records.append({'object_id':oid,'view':v,'bbox':list(b),'target':target,'size':list(sz),'scale':scale,'sha256':asset['sha256']})
man={'created_at':'2026-10-26','scope':'book-tiles/dungeon-after-dark','assignment':'candidate-only; Page sole reviewer, Dark sole installer','batch':'equipment-dark-stairs-iron-bottom-rear-v1','raw_manifest':'raw/iron-bottom-request-v2.json','assets':assets,'normalization_records':records,'source_bindings':{}}
for oid in ids:
 o=next(x for x in H['objects'] if x['object_id']==oid);man['source_bindings'][oid]={'source':o['source'],'base_views':o['views']}
p=C+'/iron-bottom-rear-v1-candidate.json';json.dump(man,open(p,'w'),indent=2);print(p,sha(p))
