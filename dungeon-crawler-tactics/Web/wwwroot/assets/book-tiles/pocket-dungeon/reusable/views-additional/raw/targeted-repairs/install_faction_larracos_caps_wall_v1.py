#!/usr/bin/env python3
"""Install root-scoped-approved Larracos masonry candidates under source/current byte guards."""
import hashlib, importlib.util, json
from pathlib import Path
ROOT=Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/pocket-dungeon')
OUT=ROOT/'reusable/views-additional'; STAGE=OUT/'raw/candidates/faction-larracos-caps-wall-v1'
BACKUP=OUT/'raw/targeted-repairs/reviewed-snapshots/20261026'; BACKUP.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
manifest=json.loads((STAGE/'candidate-manifest.json').read_text())
request_path=STAGE/'request.json'; request=json.loads(request_path.read_text())
raw_atlas=STAGE/'raw-atlas.png'; raw_sha=sha(raw_atlas)
if raw_sha != json.loads((STAGE/'generation-result.json').read_text().replace('\\n',''))['raw_atlas_sha256']:
    raise RuntimeError('raw atlas hash does not match generation result')
idxp=OUT/'set-index.json'; corrp=OUT/'corrections.json'
idx=json.loads(idxp.read_text()); corr=json.loads(corrp.read_text())
assets={a['id']:a for a in idx['assets']}
updates=[]
for obj in manifest['objects']:
    oid=obj['object_id']; recipe_path=OUT/obj['recipe_path']; recipe=json.loads(recipe_path.read_text())
    src=ROOT/recipe['canonical_source_path']
    if not src.is_file() or sha(src)!=recipe['canonical_source_sha256']:
        raise RuntimeError(f'{oid}: canonical source changed')
    for view in ('front','top','right','left','bottom','rear'):
        target=OUT/f'{oid}.{view}.png'; expected=recipe['current_view_hashes'][view]
        if sha(target)!=expected: raise RuntimeError(f'{oid}.{view}: current view hash no longer matches staged review base')
        cand_info=next(v for v in recipe['candidate_views'] if v['view']==view)
        candidate=OUT/cand_info['path']; cand_sha=sha(candidate)
        if cand_sha != obj['candidate_hashes'][view] or cand_sha != cand_info['sha256']:
            raise RuntimeError(f'{oid}.{view}: candidate hash mismatch')
        side=json.loads((OUT/f'{oid}.{view}.json').read_text())
        provenance={
            'method':'generated', 'source_image':recipe['canonical_source_path'],
            'source_sha256':recipe['canonical_source_sha256'],
            'generated_atlas':raw_atlas.relative_to(ROOT).as_posix(), 'generated_atlas_sha256':raw_sha,
            'generation_request':request_path.relative_to(ROOT).as_posix(),
            'generation_request_sha256':sha(request_path), 'prompt':request['prompt'],
            'output_hint':json.loads((STAGE/'generation-result.json').read_text().replace('\\n',''))['output_hint'],
            'candidate_recipe':recipe_path.relative_to(ROOT).as_posix(), 'candidate_recipe_sha256':sha(recipe_path),
            'normalization':cand_info, 'anchor_px':[128,248],
            'notes':'Root-scoped candidate accepted; whole-set current-source-plus-six review pending.'
        }
        op={
            'type':'install-view-candidate','object_id':oid,'view':view,
            'before_sha256':expected,'candidate_path':cand_info['path'],'candidate_sha256':cand_sha,
            'canonical_source_image':recipe['canonical_source_path'],
            'canonical_source_sha256':recipe['canonical_source_sha256'],
            'donor_object_id':oid,'donor_view':view,
            'donor_image_path':raw_atlas.relative_to(OUT).as_posix(),'donor_image_sha256':raw_sha,
            'transform':{'method':'global-alpha-component-centroid-row-column-assignment','resampling':'NEAREST','anchor_px':[128,248]},
            'reason':'Install root-scoped-approved source-faithful Larracos orthographic view candidate.',
            'provenance':provenance
        }
        updates.append((oid,view,op,candidate,cand_sha))
# All source/current/candidate guards are checked before any write.
spec=importlib.util.spec_from_file_location('pocket_view_fixes',OUT/'apply_deterministic_view_fixes.py')
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
results=[]
for oid,view,op,candidate,cand_sha in updates:
    snap=BACKUP/f'{oid}.{view}.accepted-candidate.png'
    if not snap.exists(): snap.write_bytes(candidate.read_bytes())
    if sha(snap)!=cand_sha: raise RuntimeError(f'{oid}.{view}: retained candidate snapshot mismatch')
    result=mod.apply(op,idx,BACKUP); results.append(result)
    if not any(x.get('type')=='install-view-candidate' and x.get('object_id')==oid and x.get('view')==view and x.get('candidate_sha256')==cand_sha for x in corr['operations']): corr['operations'].append(op)
for obj in manifest['objects']:
    s=next(x for x in idx['view_sets'] if x['object_id']==obj['object_id'])
    s['complete']=False; s['geometry_qa']='pending-review'
    s['qa_replay_gate']={'status':'pending-review','reason':'Scoped candidates installed; current-hash whole-set independent review pending.','proof_reviewed_at':None}
    s['notes']=(s.get('notes','')+' Root-scoped candidate directions installed; whole-set review pending.').strip()
tmp=idxp.with_suffix('.json.tmp'); tmp.write_text(json.dumps(idx,indent=2)+'\n'); tmp.replace(idxp)
corrp.write_text(json.dumps(corr,indent=2)+'\n')
print(json.dumps({'installed':results,'sets_pending':[o['object_id'] for o in manifest['objects']]},indent=2))
