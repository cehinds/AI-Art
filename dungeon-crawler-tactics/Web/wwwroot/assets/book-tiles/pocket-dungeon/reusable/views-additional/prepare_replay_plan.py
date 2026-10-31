#!/usr/bin/env python3
"""Verify frozen live outputs before base replay destroys their index, then snapshot active final provenance."""
from pathlib import Path
import argparse,hashlib,json,sys
OUT=Path(__file__).resolve().parent;PACK=OUT.parents[1];BASE=OUT/'replay-baseline.json';PLAN=OUT/'replay-plan.json'
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--allow-missing-active-outputs',action='store_true',help='isolated-copy mode: accept active outputs only when all are absent and the copy marker/baseline/retained index are hash-valid')
args=ap.parse_args()
if not BASE.is_file():raise SystemExit('missing replay-baseline.json; freeze art and capture a baseline first')
b=json.loads(BASE.read_text());idxp=PACK/b['set_index_path']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def confined(relative,root):
 path=Path(relative)
 if path.is_absolute() or '..' in path.parts:raise ValueError(f'unsafe replay reference path: {relative}')
 resolved=(root/path).resolve();resolved.relative_to(root.resolve());return resolved
errors=[]
def require_isolated_marker():
 marker=OUT/'isolated-replay-marker.json'
 if not marker.is_file():errors.append('empty-output mode requires isolated-replay-marker.json; refusing to delete live outputs');return None
 try:m=json.loads(marker.read_text())
 except Exception as e:errors.append(f'invalid isolated replay marker: {e}');return None
 canonical=Path(m.get('canonical_pack_root','')).resolve() if m.get('canonical_pack_root') else None
 if m.get('schema')!='pocket-isolated-replay-v1' or Path(m.get('isolated_pack_root','')).resolve()!=PACK.resolve():errors.append('isolated replay marker is not bound to this pack copy')
 if canonical is None or not canonical.is_dir():errors.append('isolated replay marker is missing a valid canonical pack root')
 elif canonical==PACK.resolve():errors.append('refusing empty-output replay against the canonical pack root')
 if m.get('baseline_sha256')!=sha(BASE) or m.get('set_index_sha256')!=b.get('set_index_sha256'):errors.append('isolated replay marker is bound to another baseline/index')
 if m.get('active_sets')!=len(b.get('sets',[])) or m.get('active_views')!=sum(len(g.get('views',{})) for g in b.get('sets',[])):errors.append('isolated replay marker counts differ from baseline')
 return m
marker=require_isolated_marker() if args.allow_missing_active_outputs else None
if idxp.is_file():
 if sha(idxp)!=b['set_index_sha256']:errors.append('set-index hash differs from frozen baseline')
elif not args.allow_missing_active_outputs:errors.append('set-index is missing; strict mode requires the frozen active index')
elif not marker:errors.append('cannot accept missing set-index without a valid isolated-copy marker')
for rel,h in b['replay_inputs'].items():
 p=PACK/rel
 if not p.is_file() or sha(p)!=h:errors.append(f'replay input changed: {rel}')
for rel,h in b['sources'].items():
 p=PACK/rel
 if not p.is_file() or sha(p)!=h:errors.append(f'canonical source changed: {rel}')
missing_outputs=[];present_output_count=0
for group in b['sets']:
 for view,v in group['views'].items():
  for rel,key in ((v['image_path'],'image_sha256'),(v['metadata_path'],'metadata_sha256')):
   p=PACK/rel
   if p.is_file():
    present_output_count+=1
    if sha(p)!=v[key]:errors.append(f'current output changed before replay: {rel}')
   else:missing_outputs.append(rel)
if args.allow_missing_active_outputs and present_output_count:
 errors.append(f'empty-output mode requires every active PNG and sidecar to be absent; found {present_output_count} still present')
if args.allow_missing_active_outputs and missing_outputs and not marker:
 errors.append('missing active outputs are allowed only in a marker-bound isolated copy')
if args.allow_missing_active_outputs and marker and len(missing_outputs)!=2*sum(len(g['views']) for g in b['sets']):
 errors.append(f'empty-output mode requires all active PNG+sidecar outputs absent; found {len(missing_outputs)} missing')
retained_manifest_path=OUT/'raw/replay-retained/replay-retained-manifest.json'
retained_manifest=json.loads(retained_manifest_path.read_text()) if retained_manifest_path.is_file() else {}
if args.allow_missing_active_outputs:
 retained_index=OUT/retained_manifest.get('release_index_snapshot_path','')
 if not retained_index.is_file() or sha(retained_index)!=b.get('set_index_sha256') or retained_manifest.get('release_set_index_sha256')!=b.get('set_index_sha256'):
  errors.append('empty-output mode requires the exact frozen release set-index snapshot in raw/replay-retained')
if errors:raise SystemExit('\n'.join(errors[:80])+f'\n{len(errors)} preflight mismatch(es); refusing to overwrite live/unfrozen outputs')
# The baseline metadata, not regenerated base metadata, decides whether source TOP reuse is active.
candidates=json.loads((OUT/'raw/prompts/source-top-reuse-ids.json').read_text());byid={s['object_id']:s for s in b['sets']};active=[];decisions=[]
correction_targets={o.get('object_id') for o in json.loads((OUT/'corrections.json').read_text()).get('operations',[]) if o.get('view')=='top'}
corrections=json.loads((OUT/'corrections.json').read_text()).get('operations',[])
baseline_leaves={(g['object_id'],v):row for g in b['sets'] for v,row in g['views'].items()}
snapshot_ops={(o.get('object_id'),o.get('view')):o for o in corrections if o.get('type')=='restore-replay-snapshot'}
superseded=[]
supported={'swap','remove-component-bbox','remove-components-bbox','alias','rotate','uniform-scale-to-view','uniform-scale-to-view-width','source-lineage','mirror-view','rotate-view','replace-generated-view','restore-reviewed-png','install-view-candidate','restore-replay-snapshot','clear-alpha-pixels'}
required={
 'swap':['object_id','views','before_sha256','after_sha256','reason'],
 'remove-component-bbox':['object_id','view','bbox','before_sha256','after_sha256','reason'],
 'remove-components-bbox':['object_id','view','bboxes','before_sha256','after_sha256','reason'],
 'alias':['object_id','target','source','before_sha256','after_sha256','source_sha256','reason'],
 'rotate':['object_id','view','calibrate_to_view','degrees_ccw','before_sha256','calibrate_to_sha256','reason'],
 'uniform-scale-to-view':['object_id','view','reference_view','before_sha256','reason'],
 'uniform-scale-to-view-width':['object_id','view','reference_view','before_sha256','reason'],
 'source-lineage':['object_id','view','image_sha256','source_image','source_sha256','reason'],
 'mirror-view':['object_id','view','source_view','before_sha256','after_sha256','source_sha256','reason'],
 'rotate-view':['object_id','view','degrees','before_sha256','after_sha256','reason'],
 'replace-generated-view':['object_id','view','before_sha256','after_sha256','atlas_path','atlas_sha256','crop_bbox','render_size','reference_view','reference_sha256','reason'],
 'restore-reviewed-png':['object_id','view','before_sha256','snapshot_path','snapshot_sha256','reviewer','reviewed_at','review_source_sha256','reason'],
 'install-view-candidate':['object_id','view','before_sha256','candidate_path','candidate_sha256','canonical_source_image','canonical_source_sha256','donor_image_path','donor_image_sha256','donor_object_id','donor_view','reason'],
 'restore-replay-snapshot':['object_id','view','before_sha256','snapshot_path','snapshot_sha256','metadata_snapshot_path','metadata_snapshot_sha256','metadata_path','image_path','reason'],
 'clear-alpha-pixels':['object_id','view','before_sha256','after_sha256','pixels','reason']}
retained_leaves={(x['object_id'],x['view']):x for x in retained_manifest['leaves']}
active_image_paths={row['image_path']:(oid,view,row) for (oid,view),row in baseline_leaves.items()}
donor_snapshot_path=OUT/'raw/replay-retained/donor-snapshots/manifest.json'
try:donor_snapshot_manifest=json.loads(donor_snapshot_path.read_text()) if donor_snapshot_path.is_file() else {}
except Exception as e:
 donor_snapshot_manifest={};errors.append(f'invalid active donor snapshot manifest: {e}')
missing_field_report=[]
for operation_index,op in enumerate(corrections):
 typ=op.get('type')
 if typ not in supported:
  errors.append(f'unsupported correction operation {operation_index}: {typ}');continue
 if op.get('replay_policy')!='skip-incomplete-historical-op-restore-exact-final-output':
  for field in ('atlas_path','candidate_path','snapshot_path','metadata_snapshot_path','before_snapshot'):
   rel=op.get(field)
   if not rel:continue
   try:candidate=confined(rel,PACK if rel.startswith('reusable/views-additional/') else OUT)
   except Exception as e:errors.append(f'correction operation {operation_index} unsafe {field}: {e}');continue
   if not candidate.is_file():errors.append(f'correction operation {operation_index} missing referenced file {field}: {rel}')
 if typ=='install-view-candidate':
  donor_rel=op['donor_image_path'];donor_path=(OUT/donor_rel).resolve()
  try:
   donor_path.relative_to(OUT.resolve());donor_pack_rel=donor_path.relative_to(PACK.resolve()).as_posix()
  except ValueError:errors.append(f'correction operation {operation_index} donor path escapes views directory: {donor_rel}');donor_pack_rel=None
  donor_leaf=baseline_leaves.get((op.get('donor_object_id'),op.get('donor_view')))
  active_entry=active_image_paths.get(donor_pack_rel) if donor_pack_rel else None
  if active_entry:
   if active_entry[0:2]!=(op.get('donor_object_id'),op.get('donor_view')):
    errors.append(f'correction operation {operation_index} donor path belongs to another indexed leaf: {donor_rel}')
   elif active_entry[2].get('image_sha256')==op.get('donor_image_sha256'):
    if donor_path.is_file():
     if sha(donor_path)!=op.get('donor_image_sha256'):errors.append(f'correction operation {operation_index} donor image hash mismatch: {donor_rel}')
    elif args.allow_missing_active_outputs:
     rec=next((x for x in donor_snapshot_manifest.get('donors',[]) if x.get('donor_image_path')==donor_rel and x.get('object_id')==op.get('donor_object_id') and x.get('view')==op.get('donor_view') and x.get('sha256')==op.get('donor_image_sha256')),None)
     try:snap=confined(rec['snapshot_path'],OUT) if rec else None
     except Exception as e:errors.append(f'correction operation {operation_index} unsafe donor snapshot path: {e}');snap=None
     if (donor_snapshot_manifest.get('baseline_sha256')!=sha(BASE) or donor_snapshot_manifest.get('set_index_sha256')!=b.get('set_index_sha256') or not snap or not snap.is_file() or sha(snap)!=op.get('donor_image_sha256')):
      errors.append(f'correction operation {operation_index} lacks valid baseline-bound donor snapshot: {donor_rel}')
    else:errors.append(f'correction operation {operation_index} missing donor image before replay: {donor_rel}')
   else:
    # Historical operations may point at a donor leaf which was later
    # corrected. They are safe to supersede only when the final target is
    # already the candidate or the frozen retained overlay fully covers it.
    target_leaf=baseline_leaves.get((op.get('object_id'),op.get('view')));ret=retained_leaves.get((op.get('object_id'),op.get('view')))
    image_covered=(target_leaf and ret and (target_leaf.get('image_sha256')==op.get('candidate_sha256') or ret.get('image_snapshot_sha256')==target_leaf.get('image_sha256') or target_leaf.get('image_sha256')==ret.get('replay_before_overlay_image_sha256')))
    metadata_covered=(target_leaf and ret and (ret.get('metadata_snapshot_sha256')==target_leaf.get('metadata_sha256') or target_leaf.get('metadata_sha256')==ret.get('replay_before_overlay_metadata_sha256')))
    if not image_covered or not metadata_covered:errors.append(f'correction operation {operation_index} has stale donor without exact final output coverage: {donor_rel}')
  else:
   input_sha=b['replay_inputs'].get(donor_pack_rel) if donor_pack_rel else None
   if input_sha!=op.get('donor_image_sha256'):
    errors.append(f'correction operation {operation_index} donor is neither an indexed leaf nor a hash-pinned replay input: {donor_rel}')
   elif not donor_path.is_file() or sha(donor_path)!=op.get('donor_image_sha256'):
    errors.append(f'correction operation {operation_index} retained donor input is missing or changed: {donor_rel}')
 missing=[field for field in required[typ] if field not in op]
 if not missing:continue
 missing_field_report.append({'operation_index':operation_index,'object_id':op.get('object_id'),'view':op.get('view'),'type':typ,'missing_fields':missing})
 if op.get('replay_policy')!='skip-incomplete-historical-op-restore-exact-final-output':
  errors.append(f'correction operation {operation_index} missing required fields without explicit supersession policy: {missing}');continue
 leaf=retained_leaves.get((op.get('object_id'),op.get('view')))
 if not leaf:
  errors.append(f'correction operation {operation_index} has no retained leaf coverage');continue
 image_snap=leaf.get('image_snapshot_path');meta_snap=leaf.get('metadata_snapshot_path')
 image_covered=bool(image_snap and leaf.get('image_snapshot_sha256')==leaf.get('release_image_sha256')) or leaf.get('release_image_sha256')==leaf.get('replay_before_overlay_image_sha256')
 meta_covered=bool(meta_snap and leaf.get('metadata_snapshot_sha256')==leaf.get('release_metadata_sha256'))
 for path_key,hash_key in (('image_snapshot_path','image_snapshot_sha256'),('metadata_snapshot_path','metadata_snapshot_sha256')):
  if leaf.get(path_key):
   target=OUT/leaf[path_key]
   if not target.is_file() or sha(target)!=leaf.get(hash_key):errors.append(f'correction operation {operation_index} retained snapshot hash mismatch: {path_key}')
 if not image_covered or not meta_covered:errors.append(f'correction operation {operation_index} lacks complete retained PNG+sidecar coverage')
 superseded.append({'operation_index':operation_index,'object_id':op['object_id'],'view':op['view'],'type':typ,'policy':op['replay_policy'],'missing_fields':missing,'reason':op.get('supersession_reason'),'release_image_sha256':leaf['release_image_sha256'],'release_metadata_sha256':leaf['release_metadata_sha256'],'image_snapshot_path':image_snap,'image_snapshot_sha256':leaf.get('image_snapshot_sha256'),'metadata_snapshot_path':meta_snap,'metadata_snapshot_sha256':leaf.get('metadata_snapshot_sha256')})
if len(corrections)!=975:errors.append(f'expected 975 correction operations, found {len(corrections)}')
for operation_index,op in enumerate(corrections):
 if op.get('replay_policy')!='skip-superseded-swap-and-restore-exact-final-leaves':continue
 outputs=[]
 for view in op.get('superseded_output_snapshot_views',[]):
  snap=snapshot_ops.get((op.get('object_id'),view));leaf=baseline_leaves.get((op.get('object_id'),view))
  if not snap or not leaf:errors.append(f"missing explicit replay supersession snapshot for {op.get('object_id')}.{view}");continue
  png=OUT/snap['snapshot_path'];meta=OUT/snap['metadata_snapshot_path']
  if not png.is_file() or sha(png)!=snap.get('snapshot_sha256'):errors.append(f"supersession PNG snapshot hash mismatch: {op.get('object_id')}.{view}")
  if not meta.is_file() or sha(meta)!=snap.get('metadata_snapshot_sha256'):errors.append(f"supersession metadata snapshot hash mismatch: {op.get('object_id')}.{view}")
  if leaf.get('image_sha256')!=snap.get('snapshot_sha256') or leaf.get('metadata_sha256')!=snap.get('metadata_snapshot_sha256'):errors.append(f"supersession snapshot differs from frozen release output: {op.get('object_id')}.{view}")
  outputs.append({'view':view,'snapshot_path':snap.get('snapshot_path'),'snapshot_sha256':snap.get('snapshot_sha256'),'metadata_snapshot_path':snap.get('metadata_snapshot_path'),'metadata_snapshot_sha256':snap.get('metadata_snapshot_sha256')})
 superseded.append({'operation_index':operation_index,'object_id':op.get('object_id'),'type':op.get('type'),'policy':op.get('replay_policy'),'reason':op.get('supersession_reason'),'outputs':outputs})
if errors:raise SystemExit('\n'.join(errors[:80])+f'\n{len(errors)} replay supersession preflight error(s)')
for oid in candidates:
 top=byid.get(oid,{}).get('views',{}).get('top',{});prov=top.get('provenance',{});reuse=prov.get('source_top_reuse')
 source_path=prov.get('source_image');expected_source=b['sources'].get(source_path) if source_path else None
 enabled=bool(prov.get('method')=='source-art-reused' and reuse and expected_source and reuse.get('source_sha256')==expected_source and oid not in correction_targets)
 (active if enabled else []).append(oid)
 reason='frozen canonical top provenance declares source-top reuse' if enabled else (f"retained TOP correction supersedes source reuse ({prov.get('method','missing')})" if oid in correction_targets else f"frozen current TOP provenance supersedes candidate reuse ({prov.get('method','missing')})")
 decisions.append({'object_id':oid,'active':enabled,'reason':reason})
donor_manifest=OUT/'raw/replay-retained/donor-snapshots/manifest.json'
donor_manifest_info=None
if args.allow_missing_active_outputs:
 dm=json.loads(donor_manifest.read_text());donor_manifest_info={'path':donor_manifest.relative_to(OUT).as_posix(),'sha256':sha(donor_manifest),'count':len(dm.get('donors',[])),'policy':'active donor images copied before deletion from baseline-hash-pinned indexed leaves'}
plan={'schema_version':1,'baseline_sha256':sha(BASE),'baseline_set_index_sha256':b['set_index_sha256'],'empty_output_replay':bool(args.allow_missing_active_outputs),'missing_active_output_count':len(missing_outputs),'isolated_marker_sha256':sha(OUT/'isolated-replay-marker.json') if args.allow_missing_active_outputs else None,'donor_snapshot_manifest':donor_manifest_info,'source_top_reuse_active_ids':active,'source_top_reuse_decisions':decisions,'corrections_sha256':sha(OUT/'corrections.json'),'correction_preflight':{'operation_count':len(corrections),'supported_types':sorted(supported),'missing_required_fields':missing_field_report,'unknown_operations':0,'explicitly_superseded_incomplete_operations':sum(1 for row in superseded if row.get('policy')=='skip-incomplete-historical-op-restore-exact-final-output')},'superseded_corrections':superseded,'stage_order':['verify frozen baseline and complete source/recipe closure and active donor leaf identities/hashes','validate isolated marker and all active outputs before deletion','snapshot every active donor image referenced by install-view-candidate operations into raw/replay-retained/donor-snapshots','if empty-output mode, remove only indexed active PNGs, sidecars, and frozen set-index from a marker-bound isolated copy','base split','chronological repair-history atlases and cleanups','stray component cleanup','only source TOP reuse explicitly active in frozen baseline','deterministic corrections resolved against exact baseline-bound donor snapshots','hash-gated QA overrides','restore exact reviewed leaves only from immutable retained snapshots where replay output diverges; restore release set-index last','compare all 4,464 PNG/RGBA and sidecar hashes']}
PLAN.write_text(json.dumps(plan,indent=2)+'\n');print(json.dumps({'baseline_verified':True,'source_top_candidates':len(candidates),'active_source_top_reuse':len(active),'plan':str(PLAN)},indent=2))
