#!/usr/bin/env python3
from PIL import Image
import hashlib,json,os
BASE='/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/dungeon-after-dark';CAND=BASE+'/reusable/views-additional/candidates/equipment-dark-next8-20261026';ATLAS=CAND+'/raw/personal-wall-atlas-v1.png';OID='personal-space-plaster-and-timber-wall-northeast';VIEWS=['front','top','right','left','bottom','rear'];EXTENT=176
H=json.load(open('/workspace/scratch/equipment-dark-next8-candidate-handoff-20261026.json'));src=next(o['source'] for o in H['objects'] if o['object_id']==OID)
def sha(p):return hashlib.sha256(open(p,'rb').read()).hexdigest()
im=Image.open(ATLAS).convert('RGBA');assert im.size==(2172,724);cells=[];boxes=[]
for ci,v in enumerate(VIEWS):
 x0=round(ci*im.width/6);x1=round((ci+1)*im.width/6);c=im.crop((x0,0,x1,im.height));a=c.getchannel('A');bbox=a.point(lambda p:255 if p>=64 else 0).getbbox();assert bbox
 assert max(a.crop((0,0,c.width,1)).getextrema()[1],a.crop((0,c.height-1,c.width,c.height)).getextrema()[1],a.crop((0,0,1,c.height)).getextrema()[1],a.crop((c.width-1,0,c.width,c.height)).getextrema()[1])<64,(v,'cell spill')
 cells.append(c.crop(bbox));boxes.append((x0,0,x1,im.height,bbox))
scale=EXTENT/max(max(c.size) for c in cells)
assets=[];records=[]
for v,c,box in zip(VIEWS,cells,boxes):
 sz=(round(c.width*scale),round(c.height*scale));c=c.resize(sz,Image.Resampling.NEAREST);can=Image.new('RGBA',(256,256),(0,0,0,0));can.alpha_composite(c,((256-sz[0])//2,(256-sz[1])//2));out=f'{CAND}/images/{OID}.{v}.png';can.save(out)
 x0,y0,x1,y1,bbox=box;assets.append({'asset_id':OID+'.'+v,'object_id':OID,'view':v,'candidate_path':'images/'+OID+'.'+v+'.png','sha256':sha(out),'width':256,'height':256,'anchor_px':[128,128],'provenance':{'method':'generated','source_image':os.path.relpath(src['path'],BASE),'source_sha256':src['sha256'],'generated_atlas_path':'raw/personal-wall-atlas-v1.png','generated_atlas_sha256':sha(ATLAS),'notes':'Inferred orthographic timber/plaster wall faces based on native wood frame, cream infill and diagonal brace; reverse face and hidden construction are illustrative.'},'normalization':{'raw_cell_xyxy':[x0,y0,x1,y1],'raw_alpha_bbox_xyxy':list(bbox),'raw_alpha_threshold':64,'shared_isotropic_scale':scale,'shared_world_max_extent_px':EXTENT,'resampling':'NEAREST','offset_px':[(256-sz[0])//2,(256-sz[1])//2]}});records.append({'view':v,'cell':[x0,y0,x1,y1],'bbox':list(bbox),'size':sz,'scale':scale,'sha256':assets[-1]['sha256']})
o=next(o for o in H['objects'] if o['object_id']==OID)
man={'created_at':'2026-10-26','scope':'book-tiles/dungeon-after-dark','assignment':'candidate-only; Page sole reviewer, Dark sole installer','batch':'equipment-dark-next8-personal-wall-v1','raw_manifest':'raw/personal-wall-request-v1.json','assets':assets,'normalization_records':records,'source_bindings':{OID:{'source':o['source'],'base_views':o['views']}}};out=CAND+'/personal-wall-v1-candidate.json';json.dump(man,open(out,'w'),indent=2);print(out,sha(out));print('scale',scale)
