#!/usr/bin/env python3
"""Offline full-atlas extraction for generated six-view Pocket book assets."""
from pathlib import Path
import hashlib,json,struct
import numpy as np
from PIL import Image
from scipy import ndimage
OUT=Path(__file__).resolve().parent; BOOK=OUT.parents[1]; RAW=OUT/'raw'
VIEWS=['front','top','right','left','bottom','rear']; ALPHA=245; MIN_AREA=4
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rgba_sha(im):return hashlib.sha256(struct.pack('>II',*im.size)+im.convert('RGBA').tobytes()).hexdigest()
def dump(p,d):p.write_text(json.dumps(d,indent=2)+'\n')

# Freeze and verify all current outputs before the base split overwrites its index.
import subprocess,sys
subprocess.run([sys.executable,str(OUT/'prepare_replay_plan.py')],check=True)

def run(entry, source):
 raw=BOOK/entry['raw']; im=Image.open(raw).convert('RGBA'); mask=np.asarray(im.getchannel('A'))>=ALPHA
 labels,n=ndimage.label(mask,structure=np.ones((3,3),dtype=np.uint8)); counts=np.bincount(labels.ravel()); centers=ndimage.center_of_mass(mask,labels,range(1,n+1)); boxes=ndimage.find_objects(labels)
 rows=len(entry['objects']); h,w=im.height/rows,im.width/6; groups=[[[] for _ in range(6)] for _ in range(rows)]
 for lab,area in enumerate(counts[1:],1):
  if area<MIN_AREA: continue
  cy,cx=centers[lab-1]
  row_centers=entry.get('row_centers')
  ri=int(np.argmin(np.abs(np.asarray(row_centers,dtype=float)-cy))) if row_centers and len(row_centers)==rows else int(np.argmin(np.abs((np.arange(rows)+.5)*h-cy)))
  ci=int(np.argmin(np.abs((np.arange(6)+.5)*w-cx)))
  sl=boxes[lab-1]
  if sl is None:continue
  y0,y1=sl[0].start,sl[0].stop;x0,x1=sl[1].start,sl[1].stop
  groups[ri][ci].append({'label':lab,'area':int(area),'centroid':[float(cx),float(cy)],'bbox':[x0,y0,x1,y1]})
 assets=[];sets=[]
 for ri,obj in enumerate(entry['objects']):
  oid=obj['object_id'];kit=entry['kit'];src=source[kit][oid]; crops=[];records=[];views={}
  for ci,view in enumerate(VIEWS):
   members=groups[ri][ci]
   if not members:crops.append(None);records.append([]);continue
   x0=min(m['bbox'][0] for m in members);y0=min(m['bbox'][1] for m in members);x1=max(m['bbox'][2] for m in members);y1=max(m['bbox'][3] for m in members)
   crop=im.crop((x0,y0,x1,y1)); local=labels[y0:y1,x0:x1]; keep=np.isin(local,[m['label'] for m in members]);crop.putalpha(Image.fromarray((keep*255).astype(np.uint8)));crops.append(crop);records.append(members)
  valid=[c for c in crops if c is not None];complete=len(valid)==6
  if valid:scale=220/max(max(c.size) for c in valid)
  else:scale=1
  for view,crop,members in zip(VIEWS,crops,records):
   if crop is None:continue
   size=[max(1,round(v*scale)) for v in crop.size];frame=Image.new('RGBA',(256,256),(0,0,0,0));frame.alpha_composite(crop.resize(size,Image.Resampling.NEAREST),((256-size[0])//2,248-size[1]))
   aid=oid+'.'+view; dst=OUT/(aid+'.png');frame.save(dst);meta=dst.with_suffix('.json')
   image={'path':dst.relative_to(BOOK).as_posix(),'width':256,'height':256,'sha256':sha(dst),'rgba_sha256':rgba_sha(frame)}
   source_image=f'{kit}/components/{src["file"].split("components/",1)[-1]}' if 'components/' in src['file'] else f'{kit}/{src["file"]}'
   kind='tile' if src.get('role')=='ground' or src.get('layer') in ('ground','floor') or src.get('squareLayout') in ('floor','tile','ground') else 'sprite'
   data={'id':aid,'name':src.get('label',oid)+' '+view,'kind':kind,'tags':list(dict.fromkeys(src.get('tags',[])+[view,'orthographic','inferred-view'])),'image':image,'object_id':oid,'view':view,'metadata_path':meta.relative_to(BOOK).as_posix(),'anchor_px':[128,248],'views':{'applicable':False,'complete':True,'reason':'individual principal-view image; grouped in this object view_set'},'provenance':{'method':'generated','source_image':source_image,'generated_atlas':entry['raw'],'generated_atlas_sha256':entry['sha256'],'reference_sheet':entry['reference_sheet'],'prompt_file':entry['prompt_file'],'normalization':{'alpha_threshold':ALPHA,'minimum_component_area':MIN_AREA,'component_policy':'group opaque connected components by nearest logical row/column center; preserve full bounds','component_group':members,'shared_scale':scale,'source_crop_size':list(crop.size),'render_size':size,'canvas':[256,256],'resampling':'NEAREST','anchor_px':[128,248]},'notes':'Inferred orthographic surfaces, not recovered pixels. Hidden faces and slab depth are conservative extrapolations.'}}
   dump(meta,data);assets.append(data);views[view]=aid
  sets.append({'object_id':oid,'views':views,'complete':complete and len(views)==6,'notes':'Six generated principal views; unseen surfaces are inferred.' if complete else 'One or more views could not be isolated from the raw atlas.'})
 recipe={'kit':entry['kit'],'batch':entry['batch'],'atlas_sha256':sha(raw),'grid':entry['grid'],'alpha_threshold':ALPHA,'minimum_component_area':MIN_AREA,'objects':[{'object_id':x['object_id'],'row':r,'cells':{VIEWS[c]:groups[r][c] for c in range(6)}} for r,x in enumerate(entry['objects'])]}
 dump(raw.with_suffix('.recipe.json'),recipe);print(entry['kit'],entry['batch'],len(assets),'view assets',sum(s['complete'] for s in sets),'sets')
 return assets,sets

manifest=json.loads((BOOK/'manifest.json').read_text()) if (BOOK/'manifest.json').exists() else None
source={}
for entry in json.loads((RAW/'generation.json').read_text()):
 kit=entry['kit']; md=json.loads((BOOK/kit/'manifest.json').read_text());source[kit]={a['id']:a for a in md['assets']}
all_assets=[];all_sets=[]
for entry in json.loads((RAW/'generation.json').read_text()):
 a,s=run(entry,source);all_assets.extend(a);all_sets.extend(s)
dump(OUT/'set-index.json',{'assets':all_assets,'view_sets':all_sets})
# Reapply retained correction atlases after source batches are rebuilt.
repairs_path=OUT/'repair-history.json'
if repairs_path.exists():
 import subprocess,sys,shlex
 for repair in json.loads(repairs_path.read_text()):
  # repair-history is an append-only audit log with several record kinds. Replay
  # only rows that contain a reproducible atlas/map recipe; older generated-art
  # notes and deterministic-fix notes are replayed by corrections.json below.
  if all(repair.get(k) for k in ('atlas','map','prompt')):
   args=[sys.executable,str(OUT/'repair_views.py'),str(BOOK/repair['atlas']),str(BOOK/repair['atlas']),str(BOOK/repair['map']),str(BOOK/repair['prompt'])]
   if repair.get('reference_sheet'):args.append(str(BOOK/repair['reference_sheet']))
   subprocess.run(args,check=True)
  elif repair.get('cleanup_script'):
   # Legacy guide cleanups are ordered with the atlas repairs. Deterministic
   # cleanup operations in corrections.json remain replayed in their own stage.
   cleaner=BOOK/repair['cleanup_script']
   if repair.get('command'):
    parts=shlex.split(repair['command'])
    while parts and parts[0] in ('python','python3'):parts.pop(0)
    if parts and parts[0].endswith('clean_detached_views.py'):parts.pop(0)
    subprocess.run([sys.executable,str(cleaner),*parts],check=True)
   else:
    targets=list(repair.get('targets',[]))
    if not targets and repair.get('object_ids'):
     targets=[f"{oid}.{repair.get('view','top')}" for oid in repair['object_ids']]
    if targets:
     args=[sys.executable,str(cleaner),*targets]
     if repair.get('view') and repair.get('object_ids'):args.extend(['--view',repair['view']])
     subprocess.run(args,check=True)
  # Rows with atlas-only or script/recipe fields document operations that are
  # replayed later from the hash-guarded deterministic correction journal.
subprocess.run([sys.executable,str(OUT/'remove_stray_components.py')],check=True)
# Replay source TOP reuse only for objects whose frozen pre-rebuild provenance explicitly
# declares that exact source-reuse operation active. Apply later retained corrections afterward,
# so an approved generated/calibrated TOP is never overwritten by an earlier source copy.
import subprocess,sys
for stage in ('reuse_source_floor_tops.py','apply_deterministic_view_fixes.py','apply_reviewed_qa_overrides.py','apply_retained_replay_outputs.py','validate_replay_baseline.py'):
 subprocess.run([sys.executable,str(OUT/stage)],check=True)
print('total',len(all_assets),'assets;',len(all_sets),'sets')
