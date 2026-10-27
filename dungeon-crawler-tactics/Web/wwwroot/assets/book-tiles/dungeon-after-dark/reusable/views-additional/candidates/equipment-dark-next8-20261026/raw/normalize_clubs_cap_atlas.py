#!/usr/bin/env python3
from PIL import Image
import hashlib,json,os
BASE='/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/dungeon-after-dark';CAND=BASE+'/reusable/views-additional/candidates/equipment-dark-next8-20261026';ATLAS=CAND+'/raw/clubs-cap-atlas-v1.png'
OBJECTS=['clubs-guilds-dark-polished-club-panel-endcap-northwest','clubs-guilds-dark-polished-club-panel-endcap-northeast'];VIEWS=['front','top','right','left','bottom','rear'];EXTENT=176
H=json.load(open('/workspace/scratch/equipment-dark-next8-candidate-handoff-20261026.json'))
def sha(p):return hashlib.sha256(open(p,'rb').read()).hexdigest()
im=Image.open(ATLAS).convert('RGBA');assert im.size==(2172,724)
assets=[];records=[]
for ri,oid in enumerate(OBJECTS):
 for ci,v in enumerate(VIEWS):
  x0=round(ci*im.width/6);x1=round((ci+1)*im.width/6);y0=round(ri*im.height/2);y1=round((ri+1)*im.height/2)
  c=im.crop((x0,y0,x1,y1));a=c.getchannel('A');bbox=a.point(lambda p:255 if p>=64 else 0).getbbox();assert bbox
  assert max(a.crop((0,0,c.width,1)).getextrema()[1],a.crop((0,c.height-1,c.width,c.height)).getextrema()[1],a.crop((0,0,1,c.height)).getextrema()[1],a.crop((c.width-1,0,c.width,c.height)).getextrema()[1])<64,(oid,v,'spill')
  x,y,X,Y=bbox;part=c.crop(bbox);scale=EXTENT/max(part.size);sz=(round(part.width*scale),round(part.height*scale));part=part.resize(sz,Image.Resampling.NEAREST)
  canvas=Image.new('RGBA',(256,256),(0,0,0,0));canvas.alpha_composite(part,((256-sz[0])//2,(256-sz[1])//2));path=f'{CAND}/images/{oid}.{v}.png';canvas.save(path)
  src=next(o['source'] for o in H['objects'] if o['object_id']==oid)
  assets.append({'asset_id':oid+'.'+v,'object_id':oid,'view':v,'candidate_path':'images/'+oid+'.'+v+'.png','sha256':sha(path),'width':256,'height':256,'anchor_px':[128,128],'provenance':{'method':'generated','source_image':os.path.relpath(src['path'],BASE),'source_sha256':src['sha256'],'generated_atlas_path':'raw/clubs-cap-atlas-v1.png','generated_atlas_sha256':sha(ATLAS),'notes':'Inferred cuboid cap projections painted from the native cap source; NW plain charcoal/gold, NE red-gold plus only on TOP; hidden surfaces are illustrative.'},'normalization':{'raw_cell_xyxy':[x0,y0,x1,y1],'raw_alpha_bbox_xyxy':[x,y,X,Y],'raw_alpha_threshold':64,'shared_world_max_extent_px':EXTENT,'uniform_isotropic_scale':scale,'resampling':'NEAREST','offset_px':[(256-sz[0])//2,(256-sz[1])//2]}})
  records.append({'object_id':oid,'view':v,'bbox':[x,y,X,Y],'size':sz,'scale':scale,'sha256':assets[-1]['sha256']})
manifest={'created_at':'2026-10-26','scope':'book-tiles/dungeon-after-dark','assignment':'candidate-only; Page sole reviewer, Dark sole installer','batch':'equipment-dark-next8-clubs-cap-v1','raw_manifest':'raw/clubs-cap-request-v1.json','assets':assets,'normalization_records':records}
for oid in OBJECTS:
 o=next(x for x in H['objects'] if x['object_id']==oid);manifest.setdefault('source_bindings',{})[oid]={'source':o['source'],'base_views':o['views']}
out=CAND+'/clubs-cap-v1-candidate.json';json.dump(manifest,open(out,'w'),indent=2);print(out,sha(out))
