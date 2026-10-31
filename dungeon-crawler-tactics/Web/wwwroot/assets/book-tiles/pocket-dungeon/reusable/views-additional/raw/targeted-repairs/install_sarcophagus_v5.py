#!/usr/bin/env python3
"""Install the six root-accepted Sarcophagus views with exact byte guards."""
import hashlib,importlib.util,json
from pathlib import Path
ROOT=Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/pocket-dungeon'); OUT=ROOT/'reusable/views-additional'; BASE=OUT/'raw/candidates'
OID='bubble-necropolis-sarcophagus'; src_rel='bubble-necropolis/components/bubble-necropolis-sarcophagus.png'; src=ROOT/src_rel
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
if sha(src)!='389c9143595c501a34630d2b3a725bd8dcc76995b39eb2d1ab37523b3d6713aa': raise RuntimeError('canonical source changed')
old_dir=BASE/'necropolis-doors-hatch-batch01'; old=json.loads((old_dir/f'{OID}.normalization-recipe.json').read_text())
axis_dir=BASE/'sarcophagus-plan-axis-v1'; axis=json.loads((axis_dir/'candidate-manifest.json').read_text())
v5=json.loads((axis_dir/'bottom-v5-recipe.json').read_text()); req_old=old_dir/'request.json'; req_v5=axis_dir/'bottom-v5-request.json'; raw_old=OUT/old['raw_atlas_path']; raw_v5=ROOT/v5['raw_atlas_path']
idxp=OUT/'set-index.json'; corrp=OUT/'corrections.json'; idx=json.loads(idxp.read_text());corr=json.loads(corrp.read_text())
plans=[]
for view in ('front','right','left','rear'):
 c=next(x for x in old['candidates'] if x['view']==view); before=old['current_view_hashes'][view]; candidate=OUT/c['candidate_path']
 if sha(OUT/f'{OID}.{view}.png')!=before: raise RuntimeError(f'{view}: live base hash changed')
 if sha(candidate)!=c['candidate_sha256']: raise RuntimeError(f'{view}: candidate hash changed')
 prov={'method':'generated','source_image':src_rel,'source_sha256':old['canonical_source_sha256'],'generated_atlas':old['raw_atlas_path'],'generated_atlas_sha256':old['raw_atlas_sha256'],'generation_request':old['prompt_path'],'generation_request_sha256':old['prompt_sha256'],'prompt':json.loads(req_old.read_text())['prompt'],'output_hint':json.loads((old_dir/'generation-result-attempt02.json').read_text())['output_hint'],'candidate_recipe':str((old_dir/f'{OID}.normalization-recipe.json').relative_to(OUT)),'candidate_recipe_sha256':sha(old_dir/f'{OID}.normalization-recipe.json'),'normalization':c,'anchor_px':[128,248],'notes':'Root-scoped candidate accepted; whole-set current-source-plus-six review pending.'}
 plans.append((view,before,candidate,raw_old,old['raw_atlas_sha256'],prov))
# Root-accepted rigidly rotated TOP from the same generation, with the axis correction bound to exact recipe.
topplan=axis['plans']['top']; cand=OUT/topplan['candidate_path']; before=topplan['before_sha256']
if sha(OUT/f'{OID}.top.png')!=before or sha(cand)!=topplan['candidate_sha256']: raise RuntimeError('TOP target/candidate hash mismatch')
prov={'method':'generated','source_image':src_rel,'source_sha256':axis['source_sha256'],'generated_atlas':axis['donor_atlas_path'],'generated_atlas_sha256':axis['donor_atlas_sha256'],'generation_request':old['prompt_path'],'generation_request_sha256':old['prompt_sha256'],'prompt':json.loads(req_old.read_text())['prompt'],'candidate_recipe':str((axis_dir/'candidate-manifest.json').relative_to(OUT)),'candidate_recipe_sha256':sha(axis_dir/'candidate-manifest.json'),'normalization':topplan,'anchor_px':[128,248],'notes':'Root-accepted horizontal TOP derived from the generated upright candidate by rigid 90-degree rotation and uniform scale; no anisotropic stretch.'}
plans.append(('top',before,cand,raw_old,old['raw_atlas_sha256'],prov))
# Root-accepted imagegen underside follows TOP footprint.
view='bottom'; cand=ROOT/v5['candidate_path']; before=axis['plans']['bottom']['before_sha256']
if sha(OUT/f'{OID}.bottom.png')!=before or sha(cand)!=v5['candidate_sha256']: raise RuntimeError('BOTTOM target/candidate hash mismatch')
prov={'method':'generated','source_image':src_rel,'source_sha256':v5['canonical_source_sha256'],'generated_atlas':v5['raw_atlas_path'],'generated_atlas_sha256':v5['raw_atlas_sha256'],'generation_request':str(req_v5.relative_to(OUT)),'generation_request_sha256':sha(req_v5),'prompt':json.loads(req_v5.read_text())['prompt'],'candidate_recipe':str((axis_dir/'bottom-v5-recipe.json').relative_to(OUT)),'candidate_recipe_sha256':sha(axis_dir/'bottom-v5-recipe.json'),'normalization':v5,'reference_inputs':[v5['geometry_reference']],'anchor_px':[128,248],'notes':'Root-accepted plain underside matched to the accepted horizontal TOP footprint; uniform scaling only, no anisotropic distortion.'}
plans.append((view,before,cand,raw_v5,v5['raw_atlas_sha256'],prov))
# Verify every target/source/raw atlas before writing any PNG.
for view,before,candidate,donor,donorsha,prov in plans:
 if sha(OUT/f'{OID}.{view}.png')!=before: raise RuntimeError(f'{view}: current target drifted')
 if sha(candidate)!=next((op.get('candidate_sha256') for op in []),sha(candidate)): raise RuntimeError('unreachable')
 if not donor.is_file() or sha(donor)!=donorsha: raise RuntimeError(f'{view}: raw atlas hash mismatch')
 if sha(src)!=prov['source_sha256']: raise RuntimeError(f'{view}: source provenance hash mismatch')
backup=OUT/'raw/targeted-repairs/reviewed-snapshots/20261026'; backup.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('pocket_view_fixes',OUT/'apply_deterministic_view_fixes.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
results=[]
for view,before,candidate,donor,donorsha,prov in plans:
 candidate_rel=str(candidate.relative_to(OUT));candsha=sha(candidate);donor_rel=str(donor.relative_to(OUT))
 op={'type':'install-view-candidate','object_id':OID,'view':view,'before_sha256':before,'candidate_path':candidate_rel,'candidate_sha256':candsha,'canonical_source_image':src_rel,'canonical_source_sha256':sha(src),'donor_object_id':OID,'donor_view':view,'donor_image_path':donor_rel,'donor_image_sha256':donorsha,'transform':{'method':'root-accepted-generated-principal-view','view':view},'reason':'Install root-accepted Sarcophagus principal view candidate under exact current/source/candidate hashes.','provenance':prov}
 snap=backup/f'{OID}.{view}.accepted-candidate.png'
 if not snap.exists(): snap.write_bytes(candidate.read_bytes())
 if sha(snap)!=candsha: raise RuntimeError(f'{view}: backup candidate mismatch')
 results.append(mod.apply(op,idx,backup))
 if not any(x.get('type')=='install-view-candidate' and x.get('object_id')==OID and x.get('view')==view and x.get('candidate_sha256')==candsha for x in corr['operations']): corr['operations'].append(op)
s=next(x for x in idx['view_sets'] if x['object_id']==OID);s['complete']=False;s['geometry_qa']='pending-review';s['qa_replay_gate']={'status':'pending-review','reason':'Accepted principal views installed; awaiting current-hash whole-set independent review.','proof_reviewed_at':None};s['notes']=(s.get('notes','')+' Root-accepted generated views installed; whole-set review pending.').strip()
tmp=idxp.with_suffix('.json.tmp');tmp.write_text(json.dumps(idx,indent=2)+'\n');tmp.replace(idxp);corrp.write_text(json.dumps(corr,indent=2)+'\n')
print(json.dumps({'installed':results,'status':'pending-current-whole-set-review'},indent=2))
