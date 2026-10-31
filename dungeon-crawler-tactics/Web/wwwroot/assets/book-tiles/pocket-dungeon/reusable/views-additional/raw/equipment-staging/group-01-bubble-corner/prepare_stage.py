#!/usr/bin/env python3
"""Prepare an offline normalized candidate and source+six contact; writes staging only."""
import hashlib,json,struct
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage
PACK=Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/pocket-dungeon')
HANDOFF=Path('/workspace/scratch/pocket-equipment-staging-handoff.json')
OID='bubble-airship-riveted-scrap-hull-outer-corner'
STAGE=PACK/'reusable/views-additional/raw/equipment-staging/group-01-bubble-corner'
RAW=STAGE/'raw-atlas.png'
VIEWS=['front','top','right','left','bottom','rear']
ELEVATIONS=['front','right','left','rear']

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba_sha(im):
 im=im.convert('RGBA');return hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest()
def fit_rgba(src,box):
 bg=Image.new('RGBA',box,(0,0,0,0)); im=src.convert('RGBA');im.thumbnail(box,Image.Resampling.NEAREST);bg.alpha_composite(im,((box[0]-im.width)//2,(box[1]-im.height)//2));return bg

handoff=json.loads(HANDOFF.read_text());entry=next(x for x in handoff['sets'] if x['object_id']==OID)
source=PACK/entry['source']['path']
assert sha(source)==entry['source']['sha256'],'source hash changed since handoff'
for v in VIEWS:
 p=PACK/'reusable/views-additional'/f'{OID}.{v}.png'
 assert sha(p)==entry['views'][v]['sha256'],f'{v} changed since handoff'

atlas=Image.open(RAW).convert('RGBA'); aw,ah=atlas.size
assert aw%4==0,(aw,ah)
cellw=aw//4
metas=[]
for i,v in enumerate(ELEVATIONS):
 bounds=(i*cellw,0,(i+1)*cellw,ah);cell=atlas.crop(bounds);arr=np.asarray(cell).copy(); labels,n=ndimage.label(arr[:,:,3]>32);parts=[]
 for label,sl in enumerate(ndimage.find_objects(labels),1):
  if sl is None:continue
  yy,xx=sl;area=int(np.count_nonzero(labels[sl]==label))
  if area<24:continue
  bb=(xx.start,yy.start,xx.stop,yy.stop);touches=xx.start<=1 or yy.start<=1 or xx.stop>=cellw-1 or yy.stop>=ah-1
  parts.append({'label':label,'area':area,'bbox':bb,'touches':touches})
 if not parts:raise ValueError(f'{v}: empty cell')
 largest=max(x['area'] for x in parts);chosen=[x for x in parts if not x['touches'] and x['area']>=largest*.005]
 if not chosen:chosen=[max(parts,key=lambda x:x['area'])]
 x0=min(x['bbox'][0] for x in chosen);y0=min(x['bbox'][1] for x in chosen);x1=max(x['bbox'][2] for x in chosen);y1=max(x['bbox'][3] for x in chosen)
 mask=np.isin(labels,[x['label'] for x in chosen]);crop=Image.fromarray(np.where(mask[:,:,None],arr,0).astype(np.uint8),'RGBA').crop((x0,y0,x1,y1))
 maxdim=212;scale=min(1,maxdim/max(crop.size));nw,nh=round(crop.width*scale),round(crop.height*scale);resized=crop.resize((nw,nh),Image.Resampling.NEAREST)
 canvas=Image.new('RGBA',(256,256),(0,0,0,0));canvas.alpha_composite(resized,((256-nw)//2,248-nh))
 op=STAGE/'candidate-views'/f'{OID}.{v}.png';op.parent.mkdir(parents=True,exist_ok=True);canvas.save(op,optimize=True)
 current=PACK/'reusable/views-additional'/f'{OID}.{v}.png'
 meta={'object_id':OID,'view':v,'asset_id':f'{OID}.{v}','candidate_path':op.relative_to(PACK).as_posix(),'candidate_sha256':sha(op),'candidate_rgba_sha256':rgba_sha(canvas),'canonical_source':entry['source']['path'],'canonical_source_sha256':sha(source),'current_view_path':current.relative_to(PACK).as_posix(),'current_view_sha256':sha(current),'generated_atlas':RAW.relative_to(PACK).as_posix(),'generated_atlas_sha256':sha(RAW),'prompt_path':(STAGE/'prompt.txt').relative_to(PACK).as_posix(),'prompt_sha256':sha(STAGE/'prompt.txt'),'geometry_guide':'reusable/views-additional/raw/equipment-staging/group-01-bubble-corner/geometry-guide-dark061-four-elevations.png','geometry_guide_sha256':sha(STAGE/'geometry-guide-dark061-four-elevations.png'),'source_contact_sheet':'reusable/views-additional/raw/equipment-staging/group-01-bubble-corner/source-six.png','source_contact_sheet_sha256':sha(STAGE/'source-six.png'),'cell_bounds':list(bounds),'alpha_bounds_local':[x0,y0,x1-x0,y1-y0],'selected_components':[{'label':x['label'],'area':x['area']} for x in chosen],'normalization':{'alpha_threshold':32,'min_component_area':24,'component_area_ratio':.005,'shared_scale':scale,'max_output_dimension':maxdim,'render_size':[nw,nh],'canvas':[256,256],'anchor_px':[128,248],'resampling':'NEAREST'},'status':'candidate-staged-for-root-review'}
 (STAGE/'candidate-views'/f'{OID}.{v}.json').write_text(json.dumps(meta,indent=2)+'\n');metas.append(meta)

# Proposed source plus six; source & unaffected current views are copied unchanged in the contact only.
W,H=200,218;sheet=Image.new('RGB',(W*7,H),'#d8d8d8');draw=ImageDraw.Draw(sheet)
thumbs=[source]+[STAGE/'candidate-views'/f'{OID}.{v}.png' if v in ELEVATIONS else PACK/'reusable/views-additional'/f'{OID}.{v}.png' for v in VIEWS]
labels=['SOURCE']+VIEWS
for i,(p,label) in enumerate(zip(thumbs,labels)):
 x=i*W;draw.text((x+4,2),label,fill='#111')
 for yy in range(26,H,12):
  for xx in range(x,W*(i+1),12):
   draw.rectangle((xx,yy,xx+11,yy+11),fill='#eeeeee' if ((xx//12+yy//12)%2==0) else '#ffffff')
 im=fit_rgba(Image.open(p),(W-8,H-36));sheet.paste(im,(x+4,28),im)
contact=STAGE/'candidate-source-plus-six.png';sheet.save(contact,optimize=True)
manifest={'schema_version':1,'scope':'book-tiles/pocket-dungeon','object_id':OID,'status':'candidate-only','reviewer':'root','install_owner':'views_scenery','canonical_source':entry['source']['path'],'canonical_source_sha256':sha(source),'prior_source_six_contact':'source-six.png','prior_source_six_contact_sha256':sha(STAGE/'source-six.png'),'candidate_source_plus_six_contact':contact.relative_to(PACK).as_posix(),'candidate_source_plus_six_contact_sha256':sha(contact),'raw_atlas':RAW.relative_to(PACK).as_posix(),'raw_atlas_sha256':sha(RAW),'output_hint':'/workspace/generated_images/exec-689aaf21-2397-4251-8cce-79a5acbe7723.png','request':'request.json','prompt':'prompt.txt','prompt_sha256':sha(STAGE/'prompt.txt'),'geometry_guide':metas[0]['geometry_guide'],'geometry_guide_sha256':metas[0]['geometry_guide_sha256'],'candidates':metas,'notes':'Generated four elevation candidate views using the approved DAD061 corner geometry guide as primary shape authority and Pocket source as material authority. TOP/BOTTOM and canonical source were not modified. Candidate cell art retains four similarly sized metal corner faces; root should confirm distinct orthographic axes and scale before scenery installs.'}
(STAGE/'candidate-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'contact':str(contact),'sha':sha(contact),'views':[(m['view'],m['normalization']['render_size'],m['candidate_sha256']) for m in metas]},indent=2))
