#!/usr/bin/env python3
"""Stage source-bound NE wall axis candidates; no live pack paths are written."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,os
HERE=Path(__file__).resolve().parent;PACK=HERE.parents[3];OUT=HERE/'candidates';OUT.mkdir(exist_ok=True)
HANDOFF=json.loads(Path('/workspace/scratch/inkbook-core-ne-wall-staging-handoff.json').read_text())
MERGED=json.loads(Path('/workspace/scratch/view-review-merged.json').read_text());LIB=next(x for x in MERGED['libraries'] if x['scope']=='book-tiles/ink-and-lanterns');MERGED_SETS={x['object_id']:x for x in LIB['sets']}
VIEW_INDEX=json.loads((PACK/'reusable/views-additional/set-index.json').read_text()); LEAF={x['id']:x for x in VIEW_INDEX['assets']}
VIEWS=['front','top','right','left','bottom','rear']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rotate90(im):return im.transpose(Image.Transpose.ROTATE_270)
def mirror_h(im):return im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
def box(im):return im.getchannel('A').getbbox()
def crop_keep_canvas(im, b):
 # crop the alpha bbox to selected segment coordinates and put back at common anchor.
 return im.crop(b)
def set_files(item):
 oid=item['object_id'];cur={v:PACK/item['current_views'][v]['path'] for v in VIEWS};src=PACK/item['source']['path'];return oid,src,cur
# Recheck all 13 supplied current source/view hashes immediately before staging.
for item in HANDOFF['sets']:
 oid,src,cur=set_files(item)
 if sha(src)!=item['source']['sha256']:raise SystemExit(f'NE source changed: {oid}')
 for v,p in cur.items():
  if sha(p)!=item['current_views'][v]['sha256']:raise SystemExit(f'NE live hash changed: {oid}.{v}')

# Full 90-degree basis correction from a passed same-kit NW wall: NW long-X -> NE long-Y.
full_axis={x['object_id'] for x in HANDOFF['sets'][:7]} | {'personal-space-plaster-and-timber-wall-northeast'}
# Every candidate is one of an exact copy, rigid 90-degree turn, mirror/crop of retained evidence.
records=[]
for item in HANDOFF['sets']:
 oid,src,cur=set_files(item); staged={}; descriptions={}; guide_id=item.get('suggested_same_kit_nw_object'); guide=MERGED_SETS.get(guide_id) if guide_id else None
 def nwimg(v):
  if not guide or guide.get('status')!='passed':raise RuntimeError(f'no passed NW guide for {oid}')
  rec=guide['views'][v]; p=PACK/rec['path']
  if sha(p)!=rec['sha256']:raise RuntimeError(f'NW current hash mismatch {guide_id}.{v}')
  return Image.open(p).convert('RGBA'),rec
 def from_nw(target, donor, transform='copy'):
  im,rec=nwimg(donor)
  if transform=='cw90': im=rotate90(im)
  staged[target]=im;descriptions[target]={'method':'rigid-axis-remap','guide_object_id':guide_id,'guide_view':donor,'guide_path':rec['path'],'guide_sha256':rec['sha256'],'transform':transform,'binding':'target NE canonical source retained; NW pixels are same-kit material/geometry guide, not recovered NE pixels'}
 def from_current(target, donor, transform='copy'):
  p=cur[donor]; im=Image.open(p).convert('RGBA')
  if transform=='cw90':im=rotate90(im)
  elif transform=='mirror_h':im=mirror_h(im)
  staged[target]=im;descriptions[target]={'method':'rigid-axis-remap','guide_object_id':oid,'guide_view':donor,'guide_path':item['current_views'][donor]['path'],'guide_sha256':item['current_views'][donor]['sha256'],'transform':transform,'binding':'target NE canonical source retained'}
 if oid in full_axis:
  # front/rear become short ends from NW opposing profiles; side cameras become broad NW faces.
  from_nw('front','right');from_nw('rear','left');from_nw('right','front');from_nw('left','rear')
  from_nw('top','top','cw90');from_nw('bottom','bottom','cw90')
 elif oid=='hunting-zockau-painted-town-brick-wall-northeast':
  from_nw('front','right');from_nw('rear','left')
 elif oid=='industry-menagerie-soot-stained-brick-wall-northeast':
  from_current('top','bottom');from_current('rear','front','mirror_h')
 elif oid=='safe-services-cream-service-tile-wall-northeast':
  from_nw('top','top','cw90');from_nw('bottom','bottom','cw90')
 elif oid=='starter-dungeon-dark-stone-block-wall-northeast':
  # Existing source-specific five-block plan is trimmed to the three-block NE wall span; keep central original pixels.
  for view in ('top','bottom'):
   im=Image.open(cur[view]).convert('RGBA');b=box(im)
   if not b:raise RuntimeError(f'empty {oid}.{view}')
   target_h=132
   if (b[3]-b[1])<target_h:raise RuntimeError(f'plan too short {oid}.{view}: {b}')
   y0=(b[1]+b[3]-target_h)//2;cropbox=(0,y0,im.width,y0+target_h)
   candidate=im.crop(cropbox)
   staged[view]=candidate;descriptions[view]={'method':'central-repeated-course-trim','guide_object_id':oid,'guide_view':view,'guide_path':item['current_views'][view]['path'],'guide_sha256':item['current_views'][view]['sha256'],'source_bbox_xyxy':list(b),'crop_bounds_xyxy':list(cropbox),'binding':'target NE canonical source retained; preserve original brick pixels, remove excess repeated length only'}
 elif oid=='surface-entry-urban-brick-wall-northeast':
  for view in ('top','bottom'):
   im,rec=nwimg(view);im=rotate90(im);b=box(im)
   target_w=53
   if (b[2]-b[0])<target_w:raise RuntimeError(f'plan too narrow {oid}.{view}: {b}')
   x0=(b[0]+b[2]-target_w)//2;cropbox=(x0,0,x0+target_w,im.height);staged[view]=im.crop(cropbox)
   descriptions[view]={'method':'rigid-axis-remap-and-center-thickness-crop','guide_object_id':guide_id,'guide_view':view,'guide_path':rec['path'],'guide_sha256':rec['sha256'],'transform':'cw90 then center crop wall-thickness X to source-supported 53px','crop_bounds_xyxy':list(cropbox),'binding':'target NE canonical source retained; NW guide supplies same-kit brick material/geometry'}
  # Known source+six hold has broad side elevations too short in Z; do not fabricate a distortion.
  descriptions['_unresolved_right_left']={'status':'needs-art-candidate','reason':'current side wall elevations are 115-119px high against 158-161px front/rear; no valid rigid transform preserves both Y width and common Z. Staging does not approve or alter these siblings.'}
 else:raise RuntimeError(f'unhandled NE wall {oid}')
 # All staged outputs remain under core-staging/candidates only.
 out_views={}
 for v,im in staged.items():
  path=OUT/f'{oid}.{v}.candidate.png';im.save(path,format='PNG',optimize=False)
  out_views[v]={'candidate_path':str(path.relative_to(HERE)),'candidate_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'candidate_rgba_sha256':hashlib.sha256(im.width.to_bytes(4,'big')+im.height.to_bytes(4,'big')+im.convert('RGBA').tobytes()).hexdigest(),'size':[im.width,im.height],'alpha_bbox_xyxy':list(box(im)) if box(im) else None,'derivation':descriptions[v]}
 records.append({'object_id':oid,'source':item['source'],'source_actual_sha256':sha(src),'current_views':{v:{'path':item['current_views'][v]['path'],'sha256':sha(p)} for v,p in cur.items()},'nw_guide_id':guide_id,'nw_guide_status':(guide or {}).get('status'),'candidates':out_views,'unresolved':descriptions.get('_unresolved_right_left')})
# Contact per group-of-three: canonical source, current six, candidate six (candidate dir marks staged only).
for start in range(0,len(records),3):
 batch=records[start:start+3]; cw,ch=170,340; out=Image.new('RGBA',(13*cw,len(batch)*ch),(44,44,48,255)); d=ImageDraw.Draw(out)
 for row,r in enumerate(batch):
  oid=r['object_id']; item=next(x for x in HANDOFF['sets'] if x['object_id']==oid); source=PACK/item['source']['path'];
  panels=[('SOURCE',source)]
  panels += [('OLD-'+v.upper(),PACK/item['current_views'][v]['path']) for v in VIEWS]
  panels += [('CAND-'+v.upper(),HERE/r['candidates'][v]['candidate_path']) if v in r['candidates'] else ('KEEP-'+v.upper(),PACK/item['current_views'][v]['path']) for v in VIEWS]
  d.text((2,row*ch+2),oid[:70],fill='white')
  for col,(label,path) in enumerate(panels):
   im=Image.open(path).convert('RGBA');im.thumbnail((136,280),Image.Resampling.NEAREST);out.alpha_composite(im,(col*cw+17+(136-im.width)//2,row*ch+38+(280-im.height)//2));d.text((col*cw+3,row*ch+20),label,fill='white')
 path=HERE/f'ne-wall-candidate-review-{start+1:02d}-{start+len(batch):02d}.png';out.save(path)
 for r in batch:r['contact_path']=str(path.relative_to(HERE));r['contact_sha256']=sha(path)
report={'handoff_path':'/workspace/scratch/inkbook-core-ne-wall-staging-handoff.json','policy':'staging only; no live PNG/index/sidecar edits; Ink artist sole installer after root visual acceptance','axis_convention':'NE wall extends long world-Y; thin front/rear ends, broad right/left faces at common wall Z, long-Y vertical-image top/bottom plans','map_convention':'approved NW long-X family remapped to NE long-Y: NE front<-NW right; NE rear<-NW left; NE right<-NW front; NE left<-NW rear; NE top/bottom<-NW top/bottom rigid clockwise90','sets':records}
report_path=HERE/'staged-wall-candidates.json';report_path.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'staged_sets':len(records),'candidate_counts':{r['object_id']:list(r['candidates']) for r in records},'report':str(report_path),'contacts':{r['object_id']:r['contact_path'] for r in records}},indent=2))
