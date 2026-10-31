from PIL import Image, ImageDraw
from pathlib import Path
import json,hashlib,os
BASE=Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/dungeon-after-dark')
C=BASE/'reusable/views-additional/candidates/equipment-dark-stairs-successor-20261026'
RAW=C/'raw'; OUT=C/'images'
H=json.load(open('/workspace/scratch/equipment-dark-eight-stairs-successor-handoff-20261026.json'))

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def alpha_bbox(im): return im.convert('RGBA').getchannel('A').point(lambda q:255 if q>=64 else 0).getbbox()
def cell(raw,cols,rows,row,col):
 im=Image.open(raw).convert('RGBA'); w,h=im.size
 reg=(col*w//cols,row*h//rows,(col+1)*w//cols,(row+1)*h//rows)
 part=im.crop(reg); bb=alpha_bbox(part)
 if not bb: raise ValueError(f'empty {raw} {reg}')
 return part.crop(bb), {'atlas_path':str(Path(raw).relative_to(BASE)),'atlas_sha256':sha(raw),'grid':[cols,rows],'cell_row_col':[row,col],'cell_rect_xyxy':list(reg),'alpha_bbox_cell_xyxy':list(bb),'alpha_threshold':64}
def norm(part,target_w,target_h=None):
 w,h=part.size
 scale=target_w/w if target_h is None else min(target_w/w,target_h/h)
 sz=(round(w*scale),round(h*scale)); res=part.resize(sz,Image.Resampling.NEAREST)
 can=Image.new('RGBA',(256,256),(0,0,0,0)); xy=((256-sz[0])//2,(256-sz[1])//2); can.alpha_composite(res,xy)
 return can,{'uniform_scale':scale,'normalized_size_px':list(sz),'offset_px':list(xy),'resampling':'NEAREST'}
def target_dimensions(obj):
 top=Image.open(obj['views']['top']['path']).convert('RGBA'); b=alpha_bbox(top)
 return b[2]-b[0],b[3]-b[1]

# Verify the exact assigned base before writing candidates.
for obj in H['objects']:
 if obj['object_id'].startswith(('masquerade-white-marble-stairs-','early-arenas-arena-stone-stairs-')):
  assert sha(obj['source']['path'])==obj['source']['sha256'],obj['object_id']+' source changed'
  for view,entry in obj['views'].items(): assert sha(entry['path'])==entry['sha256'],obj['object_id']+' '+view+' changed'

specs={
 'early-arenas-arena-stone-stairs-up': {'family':'early','row':0,'views':['front','right','left','bottom','rear']},
 'early-arenas-arena-stone-stairs-down': {'family':'early','row':1,'views':['front','right','left','bottom','rear']},
 'masquerade-white-marble-stairs-up': {'family':'masq','row':0,'views':['front','bottom','rear']},
 'masquerade-white-marble-stairs-down': {'family':'masq','row':1,'views':['front','bottom','rear']},
}
assets=[]; records=[]; mappings={}
for oid,spec in specs.items():
 obj=next(o for o in H['objects'] if o['object_id']==oid); tx,ty=target_dimensions(obj); family=spec['family']; row=spec['row']
 for view in spec['views']:
  if family=='early':
   if view in ('front','rear'):
    raw=RAW/'early-arenas-endfaces-atlas-v2.png'; part,cellrec=cell(raw,2,2,row,1) # flat end-wall candidate, symmetrically reused front/rear
   else:
    raw=RAW/'early-arenas-held-atlas-v1.png'; col={'right':1,'left':2,'bottom':3}[view]; part,cellrec=cell(raw,5,2,row,col)
   width={'front':tx,'rear':tx,'right':ty,'left':ty,'bottom':tx}[view]
   height=ty if view=='bottom' else None
  else:
   if view in ('front','rear'):
    raw=RAW/'masquerade-endfaces-atlas-v3.png'; part,cellrec=cell(raw,2,2,row,1)
    width=tx; height=None
   else:
    raw=RAW/'masquerade-held-atlas-v1.png'; part,cellrec=cell(raw,3,2,row,2)
    width=tx; height=ty
  can,normrec=norm(part,width,height)
  out=OUT/f'{oid}.{view}.png'; can.save(out)
  record={'asset_id':oid+'.'+view,'object_id':oid,'view':view,'candidate_path':'images/'+out.name,'sha256':sha(out),'width':256,'height':256,'anchor_px':[128,128],
   'provenance':{'method':'generated','source_image':str(Path(obj['source']['path']).relative_to(BASE)),'source_sha256':obj['source']['sha256'],'generated_atlas_path':cellrec['atlas_path'],'generated_atlas_sha256':cellrec['atlas_sha256'],'geometry_guide':{'path':'reusable/views-additional/candidates/equipment-dark-stairs-successor-20261026/raw/ink-stairs-geometry-guide-contact.png','sha256':sha(RAW/'ink-stairs-geometry-guide-contact.png'),'role':'geometry only; no foreign pixels reused'},'notes':'Inferred orthographic hidden construction; imagegen candidate, not recovered pixels. Source-specific target palette and visible identity retained.'},
   'normalization':{**cellrec,**normrec,'target_world_extent_px':[tx,ty]}}
  reqname = ('early-arenas-endfaces-request-v2.json' if view in ('front','rear') else 'early-arenas-repair-request-v1.json') if family=='early' else ('masquerade-endfaces-request-v3.json' if view in ('front','rear') else 'masquerade-repair-request-v1.json')
  req=RAW/reqname
  record['provenance']['generation_request_path']='reusable/views-additional/candidates/equipment-dark-stairs-successor-20261026/raw/'+reqname
  record['provenance']['generation_request_sha256']=sha(req)
  record['provenance']['prompt_sha256']=json.load(open(req))['prompt_sha256']
  assets.append(record); records.append({'asset_id':record['asset_id'],'source_crop':cellrec,'normalization':normrec}); mappings.setdefault(oid,{})[view]=out

manifest={'created_at':'2026-10-26','scope':'book-tiles/dungeon-after-dark','assignment':'candidate-only staging; Page sole reviewer; Dark sole installer','batch':'equipment-dark-stairs-successor-candidates-v1','assets':assets,'normalization_records':records,'source_bindings':{},'unresolved_notes':{'masquerade-white-marble-stairs-up':'Native source visibly contains four corner caps in TOP. Current QA note says two high-end caps; candidate leaves TOP unchanged pending adjudication.','early-arenas-arena-stone-stairs-up':'F/R generated as flat symmetric end-wall candidate; Page to verify relation to accepted rise/heading.'}}
for oid in mappings:
 obj=next(o for o in H['objects'] if o['object_id']==oid)
 manifest['source_bindings'][oid]={'source':obj['source'],'base_views':obj['views'],'affected_views':specs[oid]['views']}
path=C/'masquerade-early-candidates-v1.json'; json.dump(manifest,open(path,'w'),indent=2)
print('manifest',path,'sha',sha(path),'assets',len(assets))

# Source/current proof contacts paired with staged candidate full sets.
for oid in mappings:
 obj=next(o for o in H['objects'] if o['object_id']==oid)
 panels=[]
 src=Image.open(obj['source']['path']).convert('RGBA'); src.thumbnail((220,220),Image.Resampling.NEAREST); panels.append(('source',src))
 for v in ['front','top','right','left','bottom','rear']:
  p= mappings[oid].get(v,Path(obj['views'][v]['path']))
  im=Image.open(p).convert('RGBA'); im.thumbnail((220,220),Image.Resampling.NEAREST)
  panels.append((v+(' candidate' if v in mappings[oid] else ' current'),im))
 W=7*250; Hh=2*260; contact=Image.new('RGBA',(W,Hh),(235,235,235,255)); d=ImageDraw.Draw(contact)
 for i,(label,im) in enumerate(panels):
  x=i*250+(250-im.width)//2; y=25+(220-im.height)//2 if i<7 else 285+(220-im.height)//2
  contact.alpha_composite(im,(x,y)); d.text((i*250+6,6 if i<7 else 266),label,fill=(0,0,0,255))
 contact.save(C/f'{oid}-candidate-source-six-contact.png')
print('contacts ready')
