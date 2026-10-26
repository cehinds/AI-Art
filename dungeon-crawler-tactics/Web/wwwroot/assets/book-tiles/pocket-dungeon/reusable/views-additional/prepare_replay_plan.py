#!/usr/bin/env python3
"""Verify frozen live outputs before base replay destroys their index, then snapshot active final provenance."""
from pathlib import Path
import hashlib,json,sys
OUT=Path(__file__).resolve().parent;PACK=OUT.parents[1];BASE=OUT/'replay-baseline.json';PLAN=OUT/'replay-plan.json'
if not BASE.is_file():raise SystemExit('missing replay-baseline.json; freeze art and capture a baseline first')
b=json.loads(BASE.read_text());idxp=PACK/b['set_index_path']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
errors=[]
if not idxp.is_file() or sha(idxp)!=b['set_index_sha256']:errors.append('set-index hash differs from frozen baseline')
for rel,h in b['replay_inputs'].items():
 p=PACK/rel
 if not p.is_file() or sha(p)!=h:errors.append(f'replay input changed: {rel}')
for rel,h in b['sources'].items():
 p=PACK/rel
 if not p.is_file() or sha(p)!=h:errors.append(f'canonical source changed: {rel}')
for group in b['sets']:
 for view,v in group['views'].items():
  for rel,key in ((v['image_path'],'image_sha256'),(v['metadata_path'],'metadata_sha256')):
   p=PACK/rel
   if not p.is_file() or sha(p)!=v[key]:errors.append(f'current output changed before replay: {rel}')
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
retained_manifest=json.loads((OUT/'raw/replay-retained/replay-retained-manifest.json').read_text())
retained_leaves={(x['object_id'],x['view']):x for x in retained_manifest['leaves']}
missing_field_report=[]
for operation_index,op in enumerate(corrections):
 typ=op.get('type')
 if typ not in supported:
  errors.append(f'unsupported correction operation {operation_index}: {typ}');continue
 if op.get('replay_policy')!='skip-incomplete-historical-op-restore-exact-final-output':
  for field in ('atlas_path','candidate_path','snapshot_path','metadata_snapshot_path','donor_image_path','before_snapshot'):
   rel=op.get(field)
   if not rel:continue
   candidate=Path(rel)
   candidate=candidate if candidate.is_absolute() else ((PACK/candidate) if rel.startswith('reusable/views-additional/') else (OUT/candidate))
   if not candidate.is_file():errors.append(f'correction operation {operation_index} missing referenced file {field}: {rel}')
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
plan={'schema_version':1,'baseline_sha256':sha(BASE),'baseline_set_index_sha256':b['set_index_sha256'],'source_top_reuse_active_ids':active,'source_top_reuse_decisions':decisions,'corrections_sha256':sha(OUT/'corrections.json'),'correction_preflight':{'operation_count':len(corrections),'supported_types':sorted(supported),'missing_required_fields':missing_field_report,'unknown_operations':0,'explicitly_superseded_incomplete_operations':sum(1 for row in superseded if row.get('policy')=='skip-incomplete-historical-op-restore-exact-final-output')},'superseded_corrections':superseded,'stage_order':['freeze active provenance, supersession sources, and output hashes','base split','chronological repair-history atlases and cleanups','stray component cleanup','only source TOP reuse explicitly active in frozen baseline','deterministic corrections with explicitly hash-bound supersession snapshots','hash-gated QA overrides','restore exact reviewed leaves only where regenerated hashes diverge; restore release set-index last','compare all 4,464 PNG/RGBA and sidecar hashes']}
PLAN.write_text(json.dumps(plan,indent=2)+'\n');print(json.dumps({'baseline_verified':True,'source_top_candidates':len(candidates),'active_source_top_reuse':len(active),'plan':str(PLAN)},indent=2))
