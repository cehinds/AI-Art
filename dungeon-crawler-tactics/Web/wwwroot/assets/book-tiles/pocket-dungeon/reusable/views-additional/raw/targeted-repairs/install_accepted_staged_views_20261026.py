#!/usr/bin/env python3
"""Install only root-scoped-approved view candidates under current queue hash guards."""
import hashlib,json,shutil,importlib.util
from pathlib import Path
ROOT=Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/pocket-dungeon')
OUT=ROOT/'reusable/views-additional'; ST=OUT/'raw/candidates'; BACKUP=OUT/'raw/targeted-repairs/reviewed-snapshots'; BACKUP.mkdir(parents=True,exist_ok=True)
QUEUE=Path('/tmp/pocket-queue-scenery-current.json')
idxp=OUT/'set-index.json'; corrp=OUT/'corrections.json'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
queue=json.loads(QUEUE.read_text()); idx=json.loads(idxp.read_text()); corr=json.loads(corrp.read_text()); known={s['object_id']:s for s in queue['sets']}
# Candidate files are staged and approved for these exact directions. Do not modify any other view.
updates={
 'race-circuits-vehicle-upgrade-workbench':{
  'stage':'race-workbench-left-alias-v1','files':{
   'front':'front.clean.candidate.png','right':'right.clean.candidate.png','left':'left.calibrated.candidate.png','bottom':'bottom.clean.candidate.png','rear':'rear.clean.candidate.png'},
  'recipe':'race-workbench-left-alias-v1/cleanup-calibration-recipe.json','kind':'mixed-cleanup-calibration',
  'reason':'Install root-accepted calibrated workbench LEFT and remove only proven detached guide components from FRONT/RIGHT/REAR/BOTTOM; retain remaining views and source identity.'},
 'early-arenas-round-arena-stairwell':{
  'stage':'early-arena-round-stairwell-top-v3','files':{'top':'top.candidate.png'},
  'recipe':'early-arena-round-stairwell-top-v3/recipe.json','kind':'generated',
  'reason':'Install root-accepted flat orthographic spiral-stair TOP plan, matching the accepted circular BOTTOM footprint.'},
 'bubble-desert-adobe-town-gate':{
  'stage':'desert-town-gate-planes-rear-v1','files':{'top':'bubble-desert-adobe-town-gate.top.candidate.png','bottom':'bubble-desert-adobe-town-gate.bottom.candidate.png'},
  'recipe':'desert-town-gate-planes-rear-v1/candidate-manifest.json','kind':'generated',
  'reason':'Install root-accepted tower/arch TOP and BOTTOM plans; REAR remains pending correction.'},
 'masquerade-masquerade-mask-sculpture':{
  'stage':'masquerade-mask-bottom-v1','files':{'bottom':'bottom.candidate.png'},
  'recipe':'masquerade-mask-bottom-v1/candidate-manifest.json','kind':'generated',
  'reason':'Install root-accepted full-footprint mask-and-feather underside; preserve other five views.'}
}
# Preflight every target against the latest current-hash root queue before writing any image.
plans=[]
for oid,cfg in updates.items():
 s=known[oid]
 if s['status']!='needs-correction': raise RuntimeError(f'{oid} is not currently needs-correction; got {s["status"]}')
 src=ROOT/s['source']['path']
 if sha(src)!=s['source']['sha256']: raise RuntimeError(f'{oid} source hash changed')
 for view,name in cfg['files'].items():
  target=OUT/f'{oid}.{view}.png'; expected=s['views'][view]['sha256']
  candidate=ST/cfg['stage']/name
  if not candidate.is_file(): raise RuntimeError(f'missing candidate {candidate}')
  actual=sha(target); staged_sha=sha(candidate)
  backup=BACKUP/f'{oid}.{view}.before-reviewed-snapshot.png'
  if actual!=expected and not (actual==staged_sha and backup.is_file() and sha(backup)==expected):
   raise RuntimeError(f'{oid}.{view} target is neither captured base nor guarded installed candidate (actual={actual})')
  plans.append((oid,view,cfg,s,target,candidate,src))
# Apply snapshots through the pack's deterministic correction function, which updates both leaf JSON and index.
spec=importlib.util.spec_from_file_location('pocket_view_fixes',OUT/'apply_deterministic_view_fixes.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
results=[]
for oid,view,cfg,s,target,candidate,src in plans:
 stage=ST/cfg['stage']; recipe=OUT/'raw/candidates'/cfg['recipe']; recipe_sha=sha(recipe)
 snaprel=f'raw/targeted-repairs/reviewed-snapshots/20261026/{oid}.{view}.png'; snap=OUT/snaprel; snap.parent.mkdir(parents=True,exist_ok=True)
 if not snap.exists(): shutil.copyfile(candidate,snap)
 if sha(snap)!=sha(candidate): raise RuntimeError(f'{oid}.{view} retained candidate snapshot differs from staged candidate')
 candidate_sha=sha(snap); source_rel=s['source']['path']; source_sha=s['source']['sha256']
 if cfg['kind']=='generated':
  if cfg['stage']=='early-arena-round-stairwell-top-v3':
   req=OUT/'raw/candidates/early-arena-round-stairwell-top-v3-request.json'; rq=json.loads(req.read_text()); atlas=OUT/'raw/candidates/early-arena-round-stairwell-top-v3-raw.png'; normalization=json.loads(recipe.read_text())['normalization']; prompt=rq['prompt']; prompt_sha=sha(req)
  elif cfg['stage']=='desert-town-gate-planes-rear-v1':
   m=json.loads(recipe.read_text()); req=ROOT/m['generation_request']; atlas=ROOT/m['raw_atlas']; normalization=next(z for z in m['normalization'] if z['view']==view); prompt=m['prompt']; prompt_sha=sha(req)
  else:
   m=json.loads(recipe.read_text()); req=ROOT/m['generation_request']; atlas=ROOT/m['raw_atlas']; normalization=m['normalization']; prompt=m['prompt']; prompt_sha=sha(req)
  provenance={'method':'generated','source_image':source_rel,'source_sha256':source_sha,'generated_atlas':atlas.relative_to(ROOT).as_posix(),'generated_atlas_sha256':sha(atlas),'generation_request':req.relative_to(ROOT).as_posix(),'generation_request_sha256':sha(req),'prompt':prompt,'output_binding':(rq.get('output_binding') if cfg['stage'].startswith('early-arena') else m.get('output_binding')),'candidate_recipe':recipe.relative_to(ROOT).as_posix(),'candidate_recipe_sha256':recipe_sha,'normalization':normalization,'root_candidate_review':'scoped view candidate accepted; whole-set independent review pending','notes':cfg['reason']}
 else:
  recipe_data=json.loads(recipe.read_text())
  source_image_ref=source_rel
  provenance={'method':'inferred-orthographic-cleanup' if view!='left' else 'generated','source_image':source_image_ref,'source_sha256':source_sha,'candidate_recipe':recipe.relative_to(ROOT).as_posix(),'candidate_recipe_sha256':recipe_sha,'root_candidate_review':'scoped view candidate accepted; whole-set independent review pending','notes':cfg['reason']}
  if view=='left':
   m=json.loads((OUT/'raw/candidates/race-workbench-left-alias-v1/candidate-manifest.json').read_text())
   provenance.update({'generated_atlas':m['raw_atlas'],'generated_atlas_sha256':m['raw_atlas_sha256'],'generation_request':m['generation_request'],'output_binding':m['output_binding'],'normalization':recipe_data['body_bounds_after_cleanup']['left']})
  else: provenance['cleanup_operation']=next((o for o in recipe_data['operations'] if o.get('view')==view and o.get('operation')=='remove-disconnected-guide-component'),None)
 op={'type':'restore-reviewed-png','object_id':oid,'view':view,'before_sha256':sha(target),'snapshot_path':snaprel,'snapshot_sha256':candidate_sha,'reviewer':'root','reviewed_at':'2026-10-26','review_source_sha256':source_sha,'reason':cfg['reason'],'provenance_override':provenance}
 result=mod.apply(op,idx,BACKUP)
 # Synchronize the index from the current leaf JSON even when this operation had already been applied before a prior process interruption.
 leaf=json.loads((OUT/f'{oid}.{view}.json').read_text()); asset=next(a for a in idx['assets'] if a['id']==leaf['id']); asset.clear(); asset.update(leaf)
 if not any(x.get('type')=='restore-reviewed-png' and x.get('object_id')==oid and x.get('view')==view and x.get('snapshot_sha256')==candidate_sha for x in corr['operations']): corr['operations'].append(op)
 results.append(result)
# Whole sets remain pending until root reviews the current source+six bytes.
for oid in updates:
 sidx=next(s for s in idx['view_sets'] if s['object_id']==oid);sidx.update({'complete':False,'geometry_qa':'pending-review','qa_replay_gate':{'status':'pending-review','reason':'Scoped candidates installed; awaiting current-hash whole-set independent review.','proof_reviewed_at':None}})
 note='Root-scoped view candidates installed; whole-set review pending.'
 sidx['notes']=(sidx.get('notes','')+' '+note).strip()
# Write index and replay operations only after all target preflights and installs succeed.
tmp=idxp.with_suffix('.json.tmp');tmp.write_text(json.dumps(idx,indent=2)+'\n');tmp.replace(idxp);corrp.write_text(json.dumps(corr,indent=2)+'\n')
print(json.dumps({'installed':results,'sets_pending':list(updates)},indent=2))
