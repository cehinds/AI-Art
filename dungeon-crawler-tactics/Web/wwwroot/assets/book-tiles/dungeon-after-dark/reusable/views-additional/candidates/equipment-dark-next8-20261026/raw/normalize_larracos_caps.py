#!/usr/bin/env python3
from PIL import Image
import hashlib,json,os
BASE='/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/dungeon-after-dark';CAND=BASE+'/reusable/views-additional/candidates/equipment-dark-next8-20261026';ATLAS=CAND+'/raw/larracos-cap-atlas-v1.png';VIEWS=['front','top','right','left','bottom','rear'];EXTENT=176
H=json.load(open('/workspace/scratch/equipment-dark-next8-candidate-handoff-20261026.json'))
def sha(p):return hashlib.sha256(open(p,'rb').read()).hexdigest()
im=Image.open(ATLAS).convert('RGBA');assert im.size==(2172,724)
objects=['faction-larracos-ancient-city-masonry-north-cap','faction-larracos-ancient-city-masonry-west-cap'];assets=[];records=[]
for ri,oid in enumerate(objects):
 # New side atlas cells 2 and 3 are orthographic broad block elevations; reuse opposite surfaces for square cap symmetry.
 colmap={'front':2,'top':1,'right':2,'left':3,'bottom':4,'rear':3}
 bboxes={};parts={}
 for v,ci in colmap.items():
  x0=round(ci*im.width/6);x1=round((ci+1)*im.width/6);y0=round(ri*im.height/2);y1=round((ri+1)*im.height/2)
  c=im.crop((x0,y0,x1,y1));a=c.getchannel('A');bbox=a.point(lambda p:255 if p>=64 else 0).getbbox();assert bbox
  x,y,X,Y=bbox;assert max(a.crop((0,0,c.width,1)).getextrema()[1],a.crop((0,c.height-1,c.width,c.height)).getextrema()[1],a.crop((0,0,1,c.height)).getextrema()[1],a.crop((c.width-1,0,c.width,c.height)).getextrema()[1])<64
  parts[v]=c.crop(bbox);bboxes[v]=(x0,y0,x1,y1,bbox)
 scale=EXTENT/max(max(p.size) for p in parts.values())
 for v in VIEWS:
  part=parts[v];sz=(max(1,round(part.width*scale)),max(1,round(part.height*scale)));part=part.resize(sz,Image.Resampling.NEAREST);can=Image.new('RGBA',(256,256),(0,0,0,0));can.alpha_composite(part,((256-sz[0])//2,(256-sz[1])//2))
  out=f'{CAND}/images/{oid}.{v}.png';can.save(out);src=next(o['source'] for o in H['objects'] if o['object_id']==oid); source_image=os.path.relpath(src['path'],BASE)
  alias={'front':'right','right':None,'left':None,'rear':'left','top':None,'bottom':None}.get(v)
  asset={'asset_id':oid+'.'+v,'object_id':oid,'view':v,'candidate_path':'images/'+oid+'.'+v+'.png','sha256':sha(out),'width':256,'height':256,'anchor_px':[128,128],'provenance':{'method':'reused' if alias else 'generated','source_image':source_image,'source_sha256':src['sha256'],'generated_atlas_path':'raw/larracos-cap-atlas-v1.png','generated_atlas_sha256':sha(ATLAS),'inferred_symmetry_alias_of':alias,'notes':'Illustrative inferred square cap: generated broad block elevations reused around the four symmetric sides; TOP retains source gold knob and accent layout; BOTTOM is plain inferred underside without top ornament.'},'normalization':{'raw_cell_xyxy':list(bboxes[v][:4]),'raw_alpha_bbox_xyxy':list(bboxes[v][4]),'raw_alpha_threshold':64,'shared_isotropic_scale':scale,'shared_world_max_extent_px':EXTENT,'resampling':'NEAREST','offset_px':[(256-sz[0])//2,(256-sz[1])//2]}}
  assets.append(asset);records.append({'object_id':oid,'view':v,'source_cell':list(bboxes[v][:4]),'source_bbox':list(bboxes[v][4]),'scale':scale,'size':sz,'sha256':asset['sha256'],'alias_of':alias})
manifest={'created_at':'2026-10-26','scope':'book-tiles/dungeon-after-dark','assignment':'candidate-only; Page sole reviewer, Dark sole installer','batch':'equipment-dark-next8-larracos-cap-v1','raw_manifest':'raw/larracos-cap-request-v1.json','assets':assets,'normalization_records':records}
for oid in objects:
 o=next(x for x in H['objects'] if x['object_id']==oid);manifest.setdefault('source_bindings',{})[oid]={'source':o['source'],'base_views':o['views']}
out=CAND+'/larracos-cap-v1-candidate.json';json.dump(manifest,open(out,'w'),indent=2);print(out,sha(out))
