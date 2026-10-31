#!/usr/bin/env python3
"""Offline full-atlas extraction for generated six-view Pocket book assets."""
from pathlib import Path
import argparse,hashlib,json,struct
import numpy as np
from PIL import Image
from scipy import ndimage
OUT=Path(__file__).resolve().parent; BOOK=OUT.parents[1]; RAW=OUT/'raw'
VIEWS=['front','top','right','left','bottom','rear']; ALPHA=245; MIN_AREA=4
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rgba_sha(im):return hashlib.sha256(struct.pack('>II',*im.size)+im.convert('RGBA').tobytes()).hexdigest()
def dump(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def snapshot_active_donors(baseline):
 corrections=json.loads((OUT/'corrections.json').read_text())['operations'];leaves={(g['object_id'],v):row for g in baseline['sets'] for v,row in g['views'].items()};active_paths={row['image_path']:(oid,view,row) for (oid,view),row in leaves.items()};retained=json.loads((OUT/'raw/replay-retained/replay-retained-manifest.json').read_text());retained_leaves={(x['object_id'],x['view']):x for x in retained['leaves']};rows=[];seen={}
 for i,op in enumerate(corrections):
  if op.get('type')!='install-view-candidate':continue
  key=(op['donor_object_id'],op['donor_view']);donor_path=(OUT/op['donor_image_path']).resolve()
  if (not key[0] or key[0] in {'.','..'} or '/' in key[0] or '\\' in key[0]
      or key[1] not in VIEWS or len(op.get('donor_image_sha256',''))!=64
      or any(c not in '0123456789abcdef' for c in op['donor_image_sha256'])):
   raise SystemExit(f'candidate operation {i} has an unsafe donor identity or hash: {key}')
  try:pack_rel=donor_path.relative_to(BOOK.resolve()).as_posix()
  except ValueError:raise SystemExit(f'candidate operation {i} donor path escapes book root: {op["donor_image_path"]}')
  active=active_paths.get(pack_rel)
  if active:
   if active[0:2]!=key:raise SystemExit(f'candidate operation {i} donor path/id mismatch: {op["donor_image_path"]}')
   leaf=active[2]
   if leaf['image_sha256']!=op['donor_image_sha256']:
    target=leaves.get((op['object_id'],op['view']));ret=retained_leaves.get((op['object_id'],op['view'])) or {}
    image_covered=target and (target['image_sha256']==op['candidate_sha256'] or ret.get('image_snapshot_sha256')==target['image_sha256'] or target['image_sha256']==ret.get('replay_before_overlay_image_sha256'))
    meta_covered=target and (ret.get('metadata_snapshot_sha256')==target['metadata_sha256'] or target['metadata_sha256']==ret.get('replay_before_overlay_metadata_sha256'))
    if not image_covered or not meta_covered:raise SystemExit(f'candidate operation {i} stale donor lacks exact target output coverage: {key}')
    continue
   source=(BOOK/leaf['image_path']).resolve()
   if source!=donor_path or not source.is_file() or sha(source)!=op['donor_image_sha256']:
    raise SystemExit(f'candidate operation {i} donor image path/hash mismatch before deletion: {op["donor_image_path"]}')
  else:
   if baseline['replay_inputs'].get(pack_rel)!=op['donor_image_sha256'] or not donor_path.is_file() or sha(donor_path)!=op['donor_image_sha256']:
    raise SystemExit(f'candidate operation {i} donor is not an exact hash-pinned replay input: {op["donor_image_path"]}')
   continue
  if key in seen:continue
  rel=f"raw/replay-retained/donor-snapshots/{key[0]}.{key[1]}.{op['donor_image_sha256']}.png";target=(OUT/rel).resolve()
  target.relative_to(OUT.resolve())
  target.parent.mkdir(parents=True,exist_ok=True)
  tmp=target.with_suffix(target.suffix+'.tmp');tmp.write_bytes(source.read_bytes());tmp.replace(target)
  if sha(target)!=op['donor_image_sha256']:raise SystemExit(f'candidate donor snapshot hash mismatch: {rel}')
  row={'object_id':key[0],'view':key[1],'donor_image_path':op['donor_image_path'],'source_active_image_path':leaf['image_path'],'sha256':op['donor_image_sha256'],'snapshot_path':rel}
  rows.append(row);seen[key]=row
 manifest={'schema':'pocket-replay-donor-snapshots-v1','baseline_sha256':sha(OUT/'replay-baseline.json'),'set_index_sha256':baseline['set_index_sha256'],'donors':rows}
 dump(OUT/'raw/replay-retained/donor-snapshots/manifest.json',manifest)
 return len(rows)

# Default is strict and checks every active output before overwriting it. The
# destructive mode is explicitly limited to a marker-bound isolated copy.
import subprocess,sys
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--empty-output-replay',action='store_true',help='rebuild only inside a marker-bound isolated copy after deleting all indexed active PNGs, sidecars, and set-index')
args=parser.parse_args()
preflight=[sys.executable,str(OUT/'prepare_replay_plan.py')]
subprocess.run(preflight,check=True)

if args.empty_output_replay:
 baseline=json.loads((OUT/'replay-baseline.json').read_text())
 marker_path=OUT/'isolated-replay-marker.json'
 try: marker=json.loads(marker_path.read_text())
 except Exception as e: raise SystemExit(f'invalid isolated replay marker: {e}')
 if marker.get('schema')!='pocket-isolated-replay-v1':
  raise SystemExit('isolated marker has an unsupported schema')
 if marker.get('isolated_pack_root')!=str(BOOK.resolve()) or marker.get('baseline_sha256')!=sha(OUT/'replay-baseline.json'):
  raise SystemExit('isolated marker does not match this pack copy and frozen baseline')
 canonical_root=Path(marker.get('canonical_pack_root','')).resolve() if marker.get('canonical_pack_root') else None
 if canonical_root is None or not canonical_root.is_dir():
  raise SystemExit('isolated marker is missing a valid canonical pack root')
 if canonical_root==BOOK.resolve():
  raise SystemExit('refusing empty-output replay against the canonical pack root')
 if marker.get('set_index_sha256')!=baseline.get('set_index_sha256'):
  raise SystemExit('isolated marker is not bound to the frozen set-index hash')
 if marker.get('active_sets')!=len(baseline.get('sets',[])) or marker.get('active_views')!=sum(len(g.get('views',{})) for g in baseline.get('sets',[])):
  raise SystemExit('isolated marker counts do not match the frozen baseline')
 # Validate the retained release index before any destructive action. The
 # later planner repeats this check; this early copy prevents malformed marker
 # or snapshot state from deleting otherwise intact active outputs.
 retained_manifest_path=OUT/'raw/replay-retained/replay-retained-manifest.json'
 if not retained_manifest_path.is_file():raise SystemExit('missing retained replay manifest')
 retained_manifest=json.loads(retained_manifest_path.read_text())
 retained_index=OUT/retained_manifest.get('release_index_snapshot_path','')
 if (not retained_index.is_file() or sha(retained_index)!=baseline.get('set_index_sha256')
     or retained_manifest.get('release_set_index_sha256')!=baseline.get('set_index_sha256')):
  raise SystemExit('retained release index snapshot does not match frozen baseline')
 outputs=[]
 for group in baseline['sets']:
  for row in group['views'].values():
   outputs.extend((row['image_path'],row['metadata_path']))
 expected_count=2*sum(len(group['views']) for group in baseline['sets'])
 if len(outputs)!=expected_count or len(set(outputs))!=expected_count:
  raise SystemExit('frozen baseline has duplicate or incomplete active output paths')
 resolved_outputs=[];row_by_path={}
 for group in baseline['sets']:
  for row in group['views'].values():
   row_by_path[row['image_path']]=(row,'image_sha256')
   row_by_path[row['metadata_path']]=(row,'metadata_sha256')
 for rel in outputs:
  p=(BOOK/rel).resolve();p.relative_to(BOOK.resolve())
  row,key=row_by_path[rel]
  expected=row[key]
  if not p.is_file() or sha(p)!=expected:raise SystemExit(f'active output changed since strict preflight: {rel}')
  resolved_outputs.append((rel,p))
 # The index is an active rebuild output too. Its immutable copy lives under
 # raw/replay-retained and was checked by prepare_replay_plan.py.
 index_path=BOOK/baseline['set_index_path']
 index_path=index_path.resolve();index_path.relative_to(BOOK.resolve())
 if not index_path.is_file() or sha(index_path)!=baseline['set_index_sha256']:
  raise SystemExit('set-index changed since strict preflight')
 donor_count=snapshot_active_donors(baseline)
 # All paths, bindings, and bytes have now passed before the first unlink.
 for rel,p in resolved_outputs:p.unlink()
 index_path.unlink()
 subprocess.run([sys.executable,str(OUT/'prepare_replay_plan.py'),'--allow-missing-active-outputs'],check=True)
 plan=json.loads((OUT/'replay-plan.json').read_text())
 if not plan.get('empty_output_replay') or plan.get('baseline_sha256')!=sha(OUT/'replay-baseline.json'):
  raise SystemExit('empty-output replay plan is absent or not bound to the current frozen baseline')
 print(f'snapshotted {donor_count} hash-pinned active donor images before deletion')

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
