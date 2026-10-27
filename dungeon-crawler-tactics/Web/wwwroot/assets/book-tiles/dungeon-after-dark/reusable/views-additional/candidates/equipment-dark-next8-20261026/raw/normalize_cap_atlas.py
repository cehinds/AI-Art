#!/usr/bin/env python3
"""Rebuild candidate-only cap projections from reviewed 6x4 generation atlas.
Cell boundaries are fixed 256px; extraction rejects any alpha crossing a cell edge.
Each view is isotropically calibrated to a shared maximum footprint, NEAREST.
"""
from PIL import Image
import hashlib,json,os,sys
BASE='/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/dungeon-after-dark'
CAND=BASE+'/reusable/views-additional/candidates/equipment-dark-next8-20261026'
ATLAS=CAND+'/raw/cap-family-atlas-v1.png'
OBJECTS=[
 'faction-battlefield-reinforced-field-fortification-north-cap',
 'faction-battlefield-reinforced-field-fortification-west-cap'
]
VIEWS=['front','top','right','left','bottom','rear']
MAX_EXTENT=176

def sha(p):
 h=hashlib.sha256();
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()

def main():
 atlas=Image.open(ATLAS).convert('RGBA')
 assert atlas.size==(1536,1024),atlas.size
 ah=sha(ATLAS)
 assets=[]; records=[]
 for ri,oid in enumerate(OBJECTS):
  row=ri
  for ci,view in enumerate(VIEWS):
   cell=atlas.crop((ci*256,row*256,(ci+1)*256,(row+1)*256))
   alpha=cell.getchannel('A'); bbox=alpha.point(lambda p:255 if p>=64 else 0).getbbox()
   assert bbox, (oid,view,'empty')
   x0,y0,x1,y1=bbox
   # strict source-cell boundary test before normalization
   edges=(alpha.crop((0,0,256,1)).getextrema()[1],alpha.crop((0,255,256,256)).getextrema()[1],alpha.crop((0,0,1,256)).getextrema()[1],alpha.crop((255,0,256,256)).getextrema()[1])
   assert max(edges)<64,(oid,view,'cell spill',edges)
   part=cell.crop(bbox)
   scale=MAX_EXTENT/max(part.size)
   size=(max(1,round(part.width*scale)),max(1,round(part.height*scale)))
   part=part.resize(size,Image.Resampling.NEAREST)
   canvas=Image.new('RGBA',(256,256),(0,0,0,0)); canvas.alpha_composite(part,((256-size[0])//2,(256-size[1])//2))
   out=f'{CAND}/images/{oid}.{view}.png'; canvas.save(out)
   asset={
    'asset_id':f'{oid}.{view}','object_id':oid,'view':view,
    'candidate_path':f'images/{oid}.{view}.png','sha256':sha(out),'width':256,'height':256,'anchor_px':[128,128],
    'provenance':{'method':'generated','source_image':os.path.relpath(next(o['source']['path'] for o in json.load(open('/workspace/scratch/equipment-dark-next8-candidate-handoff-20261026.json'))['objects'] if o['object_id']==oid),BASE),'source_sha256':next(o['source']['sha256'] for o in json.load(open('/workspace/scratch/equipment-dark-next8-candidate-handoff-20261026.json'))['objects'] if o['object_id']==oid),'generated_atlas_path':'raw/cap-family-atlas-v1.png','generated_atlas_sha256':ah,'notes':'Generated inferred orthographic cap view; hidden material surfaces are illustrative, not recovered pixels.'},
    'normalization':{'raw_cell_xyxy':[ci*256,row*256,(ci+1)*256,(row+1)*256],'raw_alpha_bbox_xyxy':[x0,y0,x1,y1],'raw_alpha_threshold':64,'shared_world_max_extent_px':MAX_EXTENT,'uniform_isotropic_scale':scale,'resampling':'NEAREST','offset_px':[(256-size[0])//2,(256-size[1])//2],'cell_edge_alpha_pixels':0}
   }
   assets.append(asset); records.append({'object_id':oid,'view':view,'raw_bbox':[x0,y0,x1,y1],'normalized_size':size,'scale':scale,'sha256':asset['sha256']})
 m={'created_at':'2026-10-26','scope':'book-tiles/dungeon-after-dark','assignment':'candidate-only; Page sole reviewer, Dark sole installer','batch':'equipment-dark-next8-cap-family-v1','raw_manifest':'raw/cap-family-request-v1.json','source_bindings':{},'assets':assets,'normalization_records':records}
 h=json.load(open('/workspace/scratch/equipment-dark-next8-candidate-handoff-20261026.json'))
 for oid in OBJECTS:
  obj=next(x for x in h['objects'] if x['object_id']==oid)
  m['source_bindings'][oid]={'source':obj['source'],'base_views':obj['views']}
 out=CAND+'/cap-family-v1-candidate.json'; json.dump(m,open(out,'w'),indent=2)
 print(out,sha(out))
 for x in records: print(x)
if __name__=='__main__':main()
