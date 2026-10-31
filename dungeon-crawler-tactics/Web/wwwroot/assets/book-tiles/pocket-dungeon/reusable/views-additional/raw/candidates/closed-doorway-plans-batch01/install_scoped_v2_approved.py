import hashlib,json,shutil,importlib.util
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/pocket-dungeon'); OUT=ROOT/'reusable/views-additional'; B=OUT/'raw/candidates/closed-doorway-plans-batch01'; V2=B/'v2'; req=json.loads((B/'request-v2.json').read_text()); idxp=OUT/'set-index.json'; idx=json.loads(idxp.read_text()); corrp=OUT/'corrections.json'; corr=json.loads(corrp.read_text()); sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest(); backup=OUT/'raw/targeted-repairs/closed-doorway-plans-batch01-v2-backup';backup.mkdir(parents=True,exist_ok=True);spec=importlib.util.spec_from_file_location('fixes',OUT/'apply_deterministic_view_fixes.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
# Root explicitly scoped-approved only these three objects' TOP/BOTTOM candidates. Check source and target hashes.
approved={'early-arenas-heavy-dungeon-stone-closed-doorway','hunting-jungle-vine-covered-ruin-stone-closed-doorway','iron-tracks-tunnel-stone-closed-doorway'}
rootqa=json.loads(Path('/workspace/scratch/view-qa-root.json').read_text())['reviewed']; results=[]
recipe=json.loads((V2/'normalization-recipe.json').read_text()); by={(r['object_id'],r['view']):r for r in recipe['candidates']}
idxc=json.loads((V2/'candidate-index.json').read_text()); idxby={r['object_id']:r for r in idxc['candidates']}
for o in req['objects']:
 oid=o['object_id']
 if oid not in approved: continue
 q=rootqa.get('book-tiles/pocket-dungeon::'+oid,{}); assert q.get('status')=='needs-correction' and q.get('source_sha256')==o['source_sha256'],f'root current state changed: {oid}'
 src=ROOT/o['source_path']; assert sha(src)==o['source_sha256']
 ci=idxby[oid]
 for view in ('top','bottom'):
  target=OUT/f'{oid}.{view}.png'; assert sha(target)==o['current_hashes'][view],f'target changed: {oid}.{view}'
  candidate=ROOT/ci['views'][view]['path']; expected=ci['views'][view]['sha256']; assert sha(candidate)==expected
  snaprel=f'raw/targeted-repairs/reviewed-snapshots/{oid}.{view}.closed-doorway-batch01-v2.png'; snap=OUT/snaprel; snap.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(candidate,snap)
  normal=by[(oid,view)]
  prov={'method':'generated','source_image':o['source_path'],'source_sha256':o['source_sha256'],'generated_atlas':'reusable/views-additional/raw/candidates/closed-doorway-plans-batch01/raw-atlas-v2.png','generated_atlas_sha256':req['raw_atlas_sha256'],'generation_request':'reusable/views-additional/raw/candidates/closed-doorway-plans-batch01/request-v2.json','candidate_contact':ci['contact_path'],'candidate_contact_sha256':ci['contact_sha256'],'normalization':normal,'output_binding':req['output_binding'],'geometry_reference':req['reference_contacts'],'notes':'Installed exact root-scoped-accepted v2 plan candidate. Inferred orthographic cap/underside and thin closed-door edge; no source pixels recovered. Whole-set review remains pending.'}
  op={'type':'restore-reviewed-png','object_id':oid,'view':view,'before_sha256':sha(target),'snapshot_path':snaprel,'snapshot_sha256':sha(snap),'reviewer':'root-scoped-candidate-approval','reviewed_at':'2026-10-26','review_source_sha256':sha(src),'reason':'Install exact scoped-approved TOP/BOTTOM candidate from closed-doorway batch01 v2; current hash-gated, preserve other four views, request fresh whole-set review.','provenance_override':prov}
  results.append(mod.apply(op,idx,backup)); corr['operations'].append(op)
 s=next(s for s in idx['view_sets'] if s['object_id']==oid); s.update({'complete':False,'geometry_qa':'pending-review','notes':'Scoped-approved v2 plan leaves installed; fresh current source-plus-six independent review pending.'})
idxp.write_text(json.dumps(idx,indent=2)+'\n'); corrp.write_text(json.dumps(corr,indent=2)+'\n')
# Make indexed labeled contacts for each changed object.
for oid in sorted(approved):
 o=next(o for o in req['objects'] if o['object_id']==oid); src=ROOT/o['source_path']; contact=Image.new('RGBA',(8*256,256),(238,238,238,255)); draw=ImageDraw.Draw(contact)
 for i,(name,p) in enumerate([('source',src)]+[(v,OUT/f'{oid}.{v}.png') for v in ['front','top','right','left','bottom','rear']]):
  pane=Image.new('RGBA',(256,256),'white'); pane.alpha_composite(Image.open(p).convert('RGBA')); contact.alpha_composite(pane,(i*256,0)); draw.text((i*256+4,4),name,fill='black')
 cp=V2/f'{oid}.postinstall-source-plus-six.png'; contact.convert('RGB').save(cp)
print(json.dumps({'installed':results,'postinstall_contacts':{oid:{'path':str((V2/f'{oid}.postinstall-source-plus-six.png').relative_to(ROOT)),'sha256':sha(V2/f'{oid}.postinstall-source-plus-six.png')} for oid in sorted(approved)}},indent=2))
