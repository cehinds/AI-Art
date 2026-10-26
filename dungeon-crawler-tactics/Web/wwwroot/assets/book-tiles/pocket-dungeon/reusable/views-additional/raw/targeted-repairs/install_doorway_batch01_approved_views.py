#!/usr/bin/env python3
"""Install only the four root-approved directions from doorway-gate-plans-batch01."""
import hashlib,importlib.util,json
from pathlib import Path
ROOT=Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/pocket-dungeon');OUT=ROOT/'reusable/views-additional';B=OUT/'raw/candidates';stage=B/'doorway-gate-plans-batch01'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
req=json.loads((B/'doorway-gate-plans-batch01-request.json').read_text());manifest=json.loads((B/'doorway-gate-plans-batch01-manifest.json').read_text());raw=OUT/manifest['raw_atlas_path'];rh=sha(raw);idxp=OUT/'set-index.json';corrp=OUT/'corrections.json';idx=json.loads(idxp.read_text());corr=json.loads(corrp.read_text())
targets=[('iron-tracks-tunnel-stone-open-doorway','top'),('hunting-jungle-vine-covered-ruin-stone-open-doorway','rear'),('industry-menagerie-soot-stained-brick-open-doorway','rear'),('faction-battlefield-fortified-camp-gate','top')]
plans=[]
for oid,view in targets:
 ref=req['source_current_refs'][oid]; src=ROOT/ref['source_path']
 if not src.is_file() or sha(src)!=ref['source_sha256']:raise RuntimeError(f'{oid}: source hash changed')
 target=OUT/f'{oid}.{view}.png';before=ref['current_view_hashes'][view]
 if sha(target)!=before:raise RuntimeError(f'{oid}.{view}: current view hash changed')
 recipe_path=stage/f'{oid}.recipe.json';recipe=json.loads(recipe_path.read_text());cand_info=recipe['views'][view];candidate=OUT/cand_info['candidate_path'];ch=sha(candidate)
 if ch!=cand_info['candidate_sha256']:raise RuntimeError(f'{oid}.{view}: candidate hash changed')
 if recipe['canonical_source_sha256']!=ref['source_sha256']:raise RuntimeError(f'{oid}: recipe source mismatch')
 prov={'method':'generated','source_image':ref['source_path'],'source_sha256':ref['source_sha256'],'generated_atlas':manifest['raw_atlas_path'],'generated_atlas_sha256':rh,'generation_request':'reusable/views-additional/raw/candidates/doorway-gate-plans-batch01-request.json','generation_request_sha256':sha(B/'doorway-gate-plans-batch01-request.json'),'prompt':req['prompt'],'output_binding':req.get('output_path'),'candidate_recipe':str(recipe_path.relative_to(OUT)),'candidate_recipe_sha256':sha(recipe_path),'normalization':cand_info,'anchor_px':[128,248],'root_scoped_review':'accepted direction; complete-set independent review pending','notes':'Install only this root-scoped-accepted direction. Preserve all other current directions unchanged.'}
 op={'type':'install-view-candidate','object_id':oid,'view':view,'before_sha256':before,'candidate_path':str(candidate.relative_to(OUT)),'candidate_sha256':ch,'canonical_source_image':ref['source_path'],'canonical_source_sha256':ref['source_sha256'],'donor_object_id':oid,'donor_view':view,'donor_image_path':str(raw.relative_to(OUT)),'donor_image_sha256':rh,'transform':{'method':'global-connected-component-centroid-assignment','resampling':'NEAREST','anchor_px':[128,248]},'reason':'Install exact root-scoped-accepted view from the six-object doorway/gate atlas.','provenance':prov}
 plans.append((oid,view,op,candidate,ch))
# All guards are checked before any target changes.
backup=OUT/'raw/targeted-repairs/reviewed-snapshots/20261026';backup.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('pocket_view_fixes',OUT/'apply_deterministic_view_fixes.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);results=[]
for oid,view,op,candidate,ch in plans:
 snap=backup/f'{oid}.{view}.approved-candidate.png'
 if not snap.exists():snap.write_bytes(candidate.read_bytes())
 if sha(snap)!=ch:raise RuntimeError(f'{oid}.{view}: retained candidate mismatch')
 results.append(mod.apply(op,idx,backup))
 if not any(x.get('type')==op['type'] and x.get('object_id')==oid and x.get('view')==view and x.get('candidate_sha256')==ch for x in corr['operations']):corr['operations'].append(op)
for oid,_ in targets:
 if any(s['object_id']==oid for s in [next(z for z in idx['view_sets'] if z['object_id']==oid)]):
  s=next(z for z in idx['view_sets'] if z['object_id']==oid);s['complete']=False;s['geometry_qa']='pending-review';s['qa_replay_gate']={'status':'pending-review','reason':'Scoped direction installed; whole-set current-hash review pending.','proof_reviewed_at':None}
tmp=idxp.with_suffix('.json.tmp');tmp.write_text(json.dumps(idx,indent=2)+'\n');tmp.replace(idxp);corrp.write_text(json.dumps(corr,indent=2)+'\n')
print(json.dumps({'installed':results,'pending_whole_set_review':sorted({x[0] for x in targets})},indent=2))
