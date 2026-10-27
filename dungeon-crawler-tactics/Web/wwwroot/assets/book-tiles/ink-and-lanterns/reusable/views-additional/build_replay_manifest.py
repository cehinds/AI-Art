#!/usr/bin/env python3
"""Collect an external, hash-pinned replay manifest without changing the pack."""
import argparse, hashlib, json, pathlib, tempfile, os, shutil
import numpy as np
from PIL import Image
from scipy import ndimage
R=pathlib.Path(__file__).resolve().parent; P=R.parents[1]; IP=R/'set-index.json'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--manifest-output',required=True,type=pathlib.Path,help='write the manifest outside the live pack')
parser.add_argument('--retained-input-dir',required=True,type=pathlib.Path,help='external directory for immutable current-PNG inputs')
args=parser.parse_args()
manifest_output=args.manifest_output.resolve(); retained_dir=args.retained_input_dir.resolve()
if P==manifest_output or P in manifest_output.parents:parser.error('manifest output must be outside the pack')
if P==retained_dir or P in retained_dir.parents:parser.error('retained input directory must be outside the pack')
manifest_output.parent.mkdir(parents=True,exist_ok=True); retained_dir.mkdir(parents=True,exist_ok=True)
idx=json.loads(IP.read_text()); idx_hash=hashlib.sha256(IP.read_bytes()).hexdigest(); assets={a['id']:a for a in idx['assets']};sets={s['object_id']:s for s in idx['view_sets']};
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def pack_file(rel):
 path=pathlib.PurePosixPath(rel)
 if path.is_absolute() or '..' in path.parts or not str(rel):raise ValueError(f'unsafe pack-relative input: {rel}')
 resolved=(P/pathlib.Path(*path.parts)).resolve()
 if resolved!=P and P not in resolved.parents:raise ValueError(f'input escapes pack root: {rel}')
 return resolved
by_obj_view={}
for o,s in sets.items():
 for v,aid in s['views'].items():by_obj_view[(o,v)]=aid
records={}; skipped=[]
immutable_inputs={}
for aid,a in assets.items():
 mpath=P/a['metadata_path']
 if not mpath.is_file():continue
 m=json.loads(mpath.read_text());der=m.get('provenance',{}).get('derivation') or {}
 current_path=P/a['image']['path']; current_bytes=current_path.read_bytes(); current_hash=hashlib.sha256(current_bytes).hexdigest()
 if current_hash!=a['image']['sha256']:raise SystemExit(f"current PNG hash mismatch during read-only collection: {aid}")
 current_rgba=hashlib.sha256(__import__('struct').pack('>II',int(a['image']['width']),int(a['image']['height']))+Image.open(current_path).convert('RGBA').tobytes()).hexdigest()
 if current_rgba!=a['image'].get('rgba_sha256'):raise SystemExit(f"current RGBA hash mismatch during read-only collection: {aid}")
 retained=retained_dir/'fallback'/f"{aid}.{current_hash[:16]}.png"; retained.parent.mkdir(parents=True,exist_ok=True)
 if not retained.exists():shutil.copy2(current_path,retained)
 if sha(retained)!=current_hash:raise SystemExit(f"immutable fallback copy hash mismatch: {aid}")
 portable_ref=f"reusable/views-additional/raw/replay-retained/fallback/{aid}.{current_hash[:16]}.png"
 immutable_inputs[aid]={'path':str(retained),'sha256':current_hash,'rgba_sha256':current_rgba,'portable_ref':portable_ref}
 method=der.get('method',''); task=None
 oid=a.get('object_id');view=a.get('view')
 prov=m.get('provenance',{})
 if method in {'full-square-earth-under-overhead-L-palisade-corner'}:
  task={'op':'composite_over','base_asset_id':der['base_asset_id'],'base_view':der['base_view'],'base_sha256':der['base_image_sha256'],'overlay_source_path':der['overlay_source_path'],'overlay_sha256':der['overlay_source_sha256']}
 elif method=='composite-over-full-square-earth-edge-cap-overlay':
  task={'op':'composite_over','base_asset_id':der['base_asset_id'],'base_view':der['base_view'],'base_sha256':der['base_image_sha256'],'overlay_source_path':der['overlay_source_path'],'overlay_sha256':der['overlay_sha256'],'png_optimize':True}
 elif method in {'solid-earth-underside-matched-to-top-footprint','opaque-door-underside-masked-to-accepted-overhead-footprint'}:
  guide=der.get('guide_asset_id'); task={'op':'mask_fill','mask_asset_id':guide if guide else der['guide_object_id'],'mask_view':der.get('guide_view','top'),'mask_sha256':der['guide_image_sha256'],'fill_rgba':der['fill_rgba']}
 elif method=='manual-global-alpha-component-reextract':
  task={'op':'component_crop','source_path':der['source_atlas'],'source_sha256':der['source_atlas_sha256'],'labels':der['component_labels'],'bounds':der['alpha_bounds_global'],'mask_components':False,'scale':der['scale'],'alpha_threshold':245,'canvas':[256,256],'anchor':[128,128]}
 elif method.startswith('generated-') and der.get('raw_atlas') and der.get('raw_atlas_sha256') and der.get('alpha_bounds_global') and der.get('shared_scale') is not None:
  raw=der['alpha_bounds_global']; declared=der.get('coordinate_format') or der.get('alpha_bbox_global_coordinate_format')
  formats=[declared] if declared in ('xyxy','xywh') else ['xyxy','xywh']; bounds_candidates=[]
  for fmt in formats:
   x,y,c,d=[int(v) for v in raw]; box=[x,y,c,d] if fmt=='xyxy' else [x,y,x+c,y+d]
   if box not in bounds_candidates:bounds_candidates.append(box)
  task={'op':'atlas_crop','source_path':der['raw_atlas'],'source_sha256':der['raw_atlas_sha256'],'bounds':bounds_candidates[0],'bounds_candidates':bounds_candidates,'scale':der['shared_scale'],'canvas':[256,256],'anchor':[128,128],
        'resampling_candidates':['nearest','lanczos','bilinear','bicubic'],'png_optimize_candidates':[True,False]}
 elif der.get('recovered_input_path') and der.get('recovered_input_sha256'):
  task={'op':'copy_path','source_path':der['recovered_input_path'],'source_sha256':der['recovered_input_sha256']}
 elif prov.get('reused_source_top'):
  # Native source TOP reuse is directly replayable from its exact source alpha
  # crop and recorded isotropic frame normalization.
  top=prov['reused_source_top']
  task={'op':'component_crop','source_path':top['path'],'source_sha256':top['sha256'],
        'bounds':top.get('alpha_bounds_px',[0,0,256,256]),'mask_components':False,'scale':top['scale'],
        'resampling':top.get('resampling','nearest'),'png_optimize':True,
        'canvas':[256,256],'anchor':[128,128],'offset':top['offset_px']}
 elif ('alias' in method or 'remap' in method) and der.get('guide_object_id') and der.get('guide_view') and der.get('guide_image_sha256'):
  gobj=der['guide_object_id'];gv=der['guide_view'];gaid=der.get('guide_asset_id') or by_obj_view.get((gobj,gv))
  if not gaid or gaid not in assets:
   skipped.append({'asset_id':aid,'reason':'guide asset is not indexed'});continue
  guide_current=assets[gaid]['image']['sha256']
  # Old aliases whose original input was not retained are explicitly excluded.
  if guide_current != der['guide_image_sha256']:
   skipped.append({'asset_id':aid,'reason':'recorded guide hash is not the current indexed guide; source input unavailable'});continue
  transform=der.get('transform','')
  if '90-degree clockwise rotation' in transform:
   task={'op':'rotate','source_asset_id':gaid,'source_view':gv,'source_sha256':guide_current,'degrees_clockwise':90}
  elif 'exact' in transform or 'copy' in transform or 'no resampling' in transform:
   task={'op':'copy','source_asset_id':gaid,'source_view':gv,'source_sha256':guide_current}
  else:
   skipped.append({'asset_id':aid,'reason':f'unsupported alias transform: {transform}'});continue
 # Original generated leaves retain their exact atlas component labels, full
 # component bounds, scale, atlas hash, and recipe path in ordinary provenance.
 # Replay those instead of treating them as unchanged catalog pass-throughs.
 if task is None and not der and not prov.get('reused_source_top'):
  crop=prov.get('crop_bounds_px',{})
  norm=prov.get('normalization') or prov.get('normalization_adapter')
  atlas=prov.get('source_atlas'); atlas_sha=prov.get('source_atlas_sha256')
  labels=crop.get('component_labels'); bounds=crop.get('alpha_bounds_components_global_px')
  preserve_alpha=bounds is not None
  if bounds is None and crop.get('alpha_bounds_global') is not None:
   bounds=[crop['alpha_bounds_global']]
  scale=crop.get('shared_scale'); recipe=prov.get('generation_recipe')
  norm_input=(norm.get('original_png') or norm.get('archived_original_png') or norm.get('raw_snapshot')) if isinstance(norm,dict) else None
  norm_sha=(norm.get('original_png_sha256') or norm.get('archived_original_png_sha256') or norm.get('prior_image_sha256')) if isinstance(norm,dict) else None
  norm_bounds=(norm.get('original_alpha_bounds_px') or norm.get('original_alpha_bounds') or norm.get('old_alpha_bounds_px')) if isinstance(norm,dict) else None
  if not norm_input and isinstance(norm,dict) and norm.get('prior_image_sha256'):
   prior=next((q for q in prov.get('superseded_provenance',[]) if q.get('image_sha256')==norm['prior_image_sha256']),None)
   if prior:norm_input=prior.get('raw_snapshot')
  norm_scale=norm.get('ratio',norm.get('scale')) if isinstance(norm,dict) else None
  if norm_input and norm_input.startswith('raw/'):
   norm_input='reusable/views-additional/'+norm_input
  if norm_input and norm_sha and norm_bounds and norm_scale is not None:
   original=P/norm_input
   if original.is_file() and sha(original)==norm_sha:
    resampling='nearest' if 'nearest' in norm.get('method','') else 'lanczos'
    task={'op':'component_crop','source_path':norm_input,'source_sha256':norm_sha,'bounds':norm_bounds,'scale':norm_scale,'offset':norm.get('canvas_offset_px'),'mask_components':False,'resampling':resampling,'rotate_degrees_ccw':norm.get('rotation_degrees_ccw'),'png_optimize':True,'canvas':[256,256]}
   else:
    skipped.append({'asset_id':aid,'reason':'isotropic-normalization input missing/hash-mismatched','source_path':norm_input});continue
  elif isinstance(prov.get('generated_input'),dict) and recipe:
   # A narrowly supported single-view chain: image-generation output is an
   # immutable intermediate, then a JSON recipe records a deterministic crop,
   # alpha clip, uniform resize, and placement. The generated intermediate is
   # the renderer input; the canonical source and generation request remain
   # provenance, not substitute pixels. Candidate output hashes are only
   # accepted by replay_current_index after exact PNG and RGBA comparison.
   generated=prov['generated_input']; recipe_file=pack_file(recipe)
   try:
    recipe_data=json.loads(recipe_file.read_text())
   except Exception:
    skipped.append({'asset_id':aid,'reason':'generated-input normalization recipe missing or invalid JSON','generation_recipe':recipe});continue
   recipe_generated=recipe_data.get('generated_input',{})
   recipe_normalization=recipe_data.get('normalization',{})
   recipe_candidate=recipe_data.get('candidate',{})
   object_match=recipe_data.get('object_id') in (None,oid)
   view_match=recipe_data.get('view') in (None,view)
   canonical=recipe_data.get('canonical_source',{})
   request=recipe_data.get('generation_request',{})
   expected_crop=(generated.get('component_bbox_xyxy') or crop.get('component_bounds_xyxy_px'))
   canonical_file=pack_file(canonical.get('path',''))
   request_file=pack_file(request.get('path',''))
   canonical_sha=canonical.get('sha256')
   request_sha=request.get('sha256')
   if (not object_match or not view_match or not recipe_file.is_file()
       or recipe_generated.get('path')!=generated.get('path')
       or recipe_generated.get('sha256')!=generated.get('sha256')
       or canonical.get('path')!=prov.get('source_image')
       or (prov.get('source_sha256') or prov.get('source_image_sha256')) not in (None,canonical_sha)
       or not canonical_sha or not canonical_file.is_file() or sha(canonical_file)!=canonical_sha
       or request.get('path')!=prov.get('generation_request')
       or request_sha!=prov.get('generation_request_sha256') or not request_file.is_file()
       or sha(request_file)!=request_sha
       or expected_crop!=recipe_generated.get('component_bbox_xyxy')
       or expected_crop!=crop.get('component_bounds_xyxy_px')
       or recipe_normalization.get('uniform_scale')!=crop.get('uniform_scale')
       or recipe_normalization.get('resized_dimensions_px')!=crop.get('resized_dimensions_px')
       or recipe_normalization.get('canvas_offset_px')!=crop.get('canvas_offset_px')
       or recipe_normalization.get('canvas_size_px')!=crop.get('canvas_size_px')
       or not recipe_candidate.get('sha256') or recipe_candidate.get('sha256')!=a['image'].get('sha256')
       or recipe_candidate.get('rgba_sha256')!=a['image'].get('rgba_sha256')):
    skipped.append({'asset_id':aid,'reason':'generated-input normalization recipe does not exactly bind current provenance/output'});continue
   input_file=pack_file(generated['path'])
   if not input_file.is_file() or sha(input_file)!=generated['sha256']:
    skipped.append({'asset_id':aid,'reason':'generated-input normalization source missing/hash-mismatched','source_path':generated['path']});continue
   threshold=int(generated.get('alpha_threshold',32))
   task={'op':'component_crop','source_path':generated['path'],'source_sha256':generated['sha256'],
      'bounds':expected_crop,'scale':recipe_normalization['uniform_scale'],
      'resized_bounds_px':recipe_normalization['resized_dimensions_px'],
      'offset':recipe_normalization['canvas_offset_px'],'canvas':recipe_normalization['canvas_size_px'],
      'alpha_threshold':threshold,'clip_alpha_below':threshold,'mask_components':False,
      'resampling':'nearest','png_optimize':False,'png_optimize_candidates':[False,True],
      'generation_recipe':recipe,'generation_recipe_sha256':sha(recipe_file),
      'generation_request':request.get('path'),'generation_request_sha256':request_sha,
      'canonical_source':canonical.get('path'),'canonical_source_sha256':canonical.get('sha256'),
      'generated_input_path':generated['path'],'generated_input_sha256':generated['sha256'],
      'candidate_sha256':recipe_candidate['sha256'],'candidate_rgba_sha256':recipe_candidate['rgba_sha256']}
  elif crop.get('normalization_adjustment_scale') is not None:
   skipped.append({'asset_id':aid,'reason':'historical normalization has an additional scale adjustment not represented by retained crop recipe','generation_recipe':recipe,'source_atlas':atlas})
  elif atlas and atlas_sha and labels and bounds and scale is not None and recipe:
   ap=P/atlas; rp=P/recipe
   if ap.is_file() and rp.is_file() and sha(ap)==atlas_sha:
    recipe_data=json.loads(rp.read_text()) if rp.suffix.lower()=='.json' else {}
    single_view_recipe=isinstance(recipe_data.get('grid'),dict) and crop.get('alpha_bounds_global') is not None
    preserve_alpha=preserve_alpha or single_view_recipe
    default_alpha=16 if preserve_alpha else 245
    normalization=recipe_data.get('normalization',{})
    if not isinstance(normalization,dict):normalization={}
    alpha_threshold=recipe_data.get('alpha_threshold',normalization.get('alpha_threshold',default_alpha))
    candidates=list(dict.fromkeys([int(alpha_threshold),*([int(crop['alpha_threshold'])] if crop.get('alpha_threshold') is not None else []),16,32,64,128,200,245]))
    resampling=recipe_data.get('resampling','lanczos' if preserve_alpha else 'nearest')
    raw_bounds=crop.get('alpha_bounds_global')
    bounds_candidates=[]
    if crop.get('alpha_bounds_components_global_px'):
     comp=crop['alpha_bounds_components_global_px']
     bounds_candidates.append([min(b[0] for b in comp),min(b[1] for b in comp),max(b[2] for b in comp),max(b[3] for b in comp)])
    elif raw_bounds:
     declared=crop.get('coordinate_format') or crop.get('alpha_bbox_global_coordinate_format')
     formats=[declared] if declared in ('xyxy','xywh') else ['xyxy','xywh']
     for fmt in formats:
      x,y,c,d=[int(v) for v in raw_bounds]
      box=[x,y,c,d] if fmt=='xyxy' else [x,y,x+c,y+d]
      if box not in bounds_candidates:bounds_candidates.append(box)
    base_bounds=[min(b[0] for b in bounds),min(b[1] for b in bounds),max(b[2] for b in bounds),max(b[3] for b in bounds)]
    if base_bounds not in bounds_candidates:bounds_candidates.insert(0,base_bounds)
    resamples=list(dict.fromkeys([resampling,'nearest','lanczos','bilinear','bicubic']))
    preserve_candidates=list(dict.fromkeys(([bool(recipe_data['preserve_alpha'])] if 'preserve_alpha' in recipe_data else [])+[False,True]))
    task={'op':'component_crop','source_path':atlas,'source_sha256':atlas_sha,'labels':labels,
      'bounds':base_bounds,'bounds_candidates':bounds_candidates,'mask_components':True,
      'mask_components_candidates':[True,False],'preserve_alpha':preserve_alpha,
      'preserve_alpha_candidates':preserve_candidates,'connectivity':8,'connectivity_candidates':[8,4],
      'scale':scale,'resampling':resampling,'resampling_candidates':resamples,'png_optimize':True,
      'png_optimize_candidates':[True,False],'alpha_threshold':alpha_threshold,'alpha_threshold_candidates':candidates,
      'resized_bounds_px':crop.get('resized_bounds_px'),'canvas':[256,256],'anchor':[128,128],
      'offset':crop.get('canvas_offset_px'),'generation_recipe':recipe,'generation_recipe_sha256':sha(rp)}
    if recipe_data.get('ledger_hash_match') is False or ('ghost-havana-colonial-street-paving-stairs-' in recipe and '-bottom-underside-repair-v2.recipe.json' in recipe):
     reason='retained historical atlas recipe explicitly records that regenerated bytes do not match the approved current PNG' if recipe_data.get('ledger_hash_match') is False else 'retained crop metadata is insufficient to reproduce the installed PNG byte-for-byte; preserve current indexed input'
     skipped.append({'asset_id':aid,'reason':reason,'generation_recipe':recipe,'source_atlas':atlas})
     task=None
   else:
    skipped.append({'asset_id':aid,'reason':'base atlas or recipe missing/hash-mismatched','atlas':atlas,'recipe':recipe});continue
 if task is None:continue
 asset_path=R/pathlib.Path(a['image']['path']).name
 if not asset_path.is_file():
  skipped.append({'asset_id':aid,'reason':'target PNG missing'});continue
 task.update({'target_asset_id':aid,'target_object_id':oid,'target_view':view,'expected_output_sha256':a['image']['sha256'],'expected_output_rgba_sha256':a['image']['rgba_sha256'],'id':f'{oid}.{view}'})
 records[aid]=task
for task in records.values():
 for field,vfield in [('source_asset_id','source_view'),('mask_asset_id','mask_view'),('texture_asset_id','texture_view'),('base_asset_id','base_view'),('overlay_asset_id','overlay_view')]:
  if field in task and task[field] not in assets:
   resolved=by_obj_view.get((task[field],task.get(vfield)))
   if resolved: task[field]=resolved
# Component bounds/alpha settings are now candidate interpretations. The
# isolated renderer must select them only by exact PNG+RGBA hash agreement.
# Every remaining current leaf is explicitly catalog-validated and copied as
# an unchanged current PNG. This is not presented as a base-atlas rebuild; it
# identifies outputs whose historical base recipe is not yet replayed here.
for aid, asset in assets.items():
 if aid in records: continue
 records[aid]={'op':'preserve_current','target_asset_id':aid,'target_object_id':asset.get('object_id'),
               'target_view':asset.get('view'),'expected_output_sha256':asset['image']['sha256'],
               'expected_output_rgba_sha256':asset['image']['rgba_sha256'],'id':f"{asset.get('object_id')}.{asset.get('view')}",
               'catalog_status':'base-recipe-not-in-bounded-replay; current indexed PNG copied and exact-hash validated'}
# Respect dependencies such as a generated TOP followed by a masked BOTTOM.
tasks=[];pending=dict(records);written=set()
while pending:
 ready=[]
 for aid,t in pending.items():
  deps=[]
  for fld,vfld in [('source_asset_id','source_view'),('mask_asset_id','mask_view'),('texture_asset_id','texture_view'),('base_asset_id','base_view'),('overlay_asset_id','overlay_view')]:
   if fld in t:
    dep=t[fld] if t[fld] in assets else by_obj_view.get((t[fld],t[vfld]))
    if dep in records:deps.append(dep)
  if all(d in written for d in deps):ready.append(aid)
 if not ready:raise SystemExit(f'replay dependency cycle among {list(pending)}')
 for aid in ready:
  tasks.append(pending.pop(aid));written.add(aid)
catalog_only=[]
for t in tasks:
 if t['op']!='preserve_current':continue
 a=assets[t['target_asset_id']]; mpath=P/a['metadata_path']; meta=json.loads(mpath.read_text()) if mpath.is_file() else {}; prov=meta.get('provenance',{}); der=prov.get('derivation',{})
 reason='historical derivation is outside the bounded renderer; current indexed PNG is copied and exact-hash validated'
 if der and der.get('method'):
  reason=f"derivation method '{der['method']}' is not modeled by the bounded renderer; current PNG is copied and exact-hash validated"
 elif prov.get('crop_bounds_px',{}).get('normalization_adjustment_scale') is not None:
  reason='source-atlas crop has an extra normalization adjustment whose exact replay rule is not retained'
 elif not prov.get('source_atlas'):
  reason='raw source atlas was not retained in provenance; current PNG is copied and exact-hash validated'
 retained_name=f"{t['target_asset_id']}.{t['expected_output_sha256'][:16]}.png"
 live=P/a['image']['path']; retained=retained_dir/'fallback'/retained_name
 if sha(live)!=t['expected_output_sha256']:raise SystemExit(f"current PNG hash changed before immutable archive: {t['target_asset_id']}")
 if not retained.exists():shutil.copy2(live,retained)
 if sha(retained)!=t['expected_output_sha256']:raise SystemExit(f"retained current PNG archive hash mismatch: {t['target_asset_id']}")
 t.update({'op':'copy_path','external_source_path':str(retained),'source_portable_ref':immutable_inputs[t['target_asset_id']]['portable_ref'],'source_sha256':t['expected_output_sha256'],'catalog_status':'retained-current-index-png exact-hash copy; not regenerated from historical atlas'})
 catalog_only.append({'asset_id':t['target_asset_id'],'object_id':t['target_object_id'],'view':t['target_view'],'reason':reason,'source_atlas':prov.get('source_atlas'),'source_atlas_sha256':prov.get('source_atlas_sha256'),'generation_recipe':prov.get('generation_recipe'),'derivation_method':der.get('method'),'retained_input_path':str(retained),'retained_input_ref':immutable_inputs[t['target_asset_id']]['portable_ref'],'retained_input_sha256':t['expected_output_sha256'],'retained_input_rgba_sha256':immutable_inputs[t['target_asset_id']]['rgba_sha256']})
# Every generated candidate task also has an explicit immutable, SHA-pinned
# recovery input. The adapter uses it only if all declared reconstruction
# candidates fail both current PNG and RGBA hashes.
for aid,task in records.items():
 retained=immutable_inputs[aid]
 task.update({'fallback_external_source_path':retained['path'],'fallback_portable_ref':retained['portable_ref'],'fallback_sha256':retained['sha256'],
              'fallback_rgba_sha256':retained['rgba_sha256']})
manifest={'schema':'ink-current-index-replay-manifest-v1','index_sha256':idx_hash,'expected_view_set_count':len(sets),'expected_asset_count':len(assets),'scope':'All 4,464 current indexed PNG leaves are emitted into an isolated output tree. Supported retained aliases, rotations, raw-atlas component crops/isotropic scales, mask fills, and composites are hash-pinned and replayed. Catalog-only leaves are copied from the current index and exact-hash validated; they are not represented as regenerated from raw atlases. Each catalog-only reason and source-input availability is listed in catalog_only_outputs.','tasks':tasks,'skipped':skipped,'catalog_only_outputs':catalog_only}
out=manifest_output
fd,tmp=tempfile.mkstemp(dir=out.parent,prefix=out.name+'.',suffix='.tmp')
with os.fdopen(fd,'w') as f:json.dump(manifest,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
os.replace(tmp,out)
print(json.dumps({'manifest':out.name,'index_sha256':idx_hash,'tasks':len(tasks),'skipped':len(skipped),'operation_counts':{op:sum(t['op']==op for t in tasks) for op in sorted({t['op'] for t in tasks})}}))
