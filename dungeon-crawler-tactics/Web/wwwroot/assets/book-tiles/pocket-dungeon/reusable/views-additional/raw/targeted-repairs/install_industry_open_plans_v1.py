#!/usr/bin/env python3
import hashlib,importlib.util,json,struct
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4]; OUT=ROOT/'reusable/views-additional'; C=OUT/'raw/candidates'; B=C/'industry-open-doorway-plans-v1'; oid='industry-menagerie-soot-stained-brick-open-doorway'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
rh=lambda im:hashlib.sha256(struct.pack('>II',*im.size)+im.convert('RGBA').tobytes()).hexdigest()
m=json.loads((B/'candidate-manifest.json').read_text()); reqp=C/'industry-open-doorway-plans-v1-request.json'; req=json.loads(reqp.read_text()); src=ROOT/m['source_path']
if sha(src)!=m['source_sha256']: raise RuntimeError('canonical source changed')
for v,h in m['current_live_hashes'].items():
 if sha(OUT/f'{oid}.{v}.png')!=h: raise RuntimeError(f'{v} changed since staging')
idxp=OUT/'set-index.json'; idx=json.loads(idxp.read_text()); corrp=OUT/'corrections.json'; corr=json.loads(corrp.read_text()); backup=OUT/'raw/targeted-repairs/industry-open-plans-v1-backup';backup.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('vf',OUT/'apply_deterministic_view_fixes.py'); mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod); ops=[]
for v in ('top','bottom'):
 rec=next(x for x in m['candidates'] if x['view']==v); cand=OUT/rec['path']; raw=OUT/m['raw_atlas_path']
 if sha(cand)!=rec['sha256']: raise RuntimeError('candidate changed')
 prov={'method':'generated','source_image':m['source_path'],'source_sha256':m['source_sha256'],'generated_atlas':m['raw_atlas_path'],'generated_atlas_sha256':m['raw_atlas_sha256'],'generation_request':str(reqp.relative_to(OUT)),'generation_request_sha256':m['prompt_sha256'],'prompt':req['prompt'],'output_binding':{'path':req['output_path'],'sha256':req['output_sha256']},'candidate_manifest':str((B/'candidate-manifest.json').relative_to(OUT)),'candidate_manifest_sha256':sha(B/'candidate-manifest.json'),'normalization':{'bbox':rec['bbox'],'scale':rec['scale'],'render_size':rec['render_size'],'resampling':rec['resampling'],'anchor_px':rec['anchor_px']},'reference_inputs':[{'path':req['reference_contact'],'sha256':req['reference_contact_sha256'],'role':'current source plus accepted elevations; target identity authoritative'}]+[{'path':p,'role':'shallow doorway geometry only'} for p in req['geometry_only_guides']],'notes':'Root-scoped-accepted shallow plan for the open soot-stained brick doorway; source identity and open passage preserved. Pending fresh whole-set review.'}
 ops.append({'type':'install-view-candidate','object_id':oid,'view':v,'before_sha256':m['current_live_hashes'][v],'candidate_path':rec['path'],'candidate_sha256':rec['sha256'],'canonical_source_image':m['source_path'],'canonical_source_sha256':m['source_sha256'],'donor_object_id':oid,'donor_view':'front','donor_image_path':m['raw_atlas_path'],'donor_image_sha256':m['raw_atlas_sha256'],'transform':{'method':'generated shallow orthographic plan; uniform fit','normalization':prov['normalization'],'resampling':'NEAREST'},'reason':f'Install root-scoped-accepted open doorway {v.upper()} projection.','provenance':prov})
for op in ops: print(mod.apply(op,idx,backup))
for op in ops:
 if not any(x.get('candidate_sha256')==op['candidate_sha256'] and x.get('object_id')==oid and x.get('view')==op['view'] for x in corr['operations']): corr['operations'].append(op)
s=next(x for x in idx['view_sets'] if x['object_id']==oid); s['complete']=False; s['geometry_qa']='pending-review'; s['qa_replay_gate']={'status':'pending-review','reason':'Scoped-accepted TOP/BOTTOM plans installed; fresh whole-set review pending.','proof_reviewed_at':None}
t=idxp.with_suffix('.json.tmp');t.write_text(json.dumps(idx,indent=2)+'\n');t.replace(idxp);corrp.write_text(json.dumps(corr,indent=2)+'\n')
canvas=Image.new('RGBA',(7*256,256),(235,235,235,255));d=ImageDraw.Draw(canvas); im=Image.open(src).convert('RGBA'); im.thumbnail((220,220),Image.Resampling.NEAREST);canvas.alpha_composite(im,((256-im.width)//2,(256-im.height)//2)); d.text((4,4),'source',fill='black'); views=[]
for col,v in enumerate(('front','top','right','left','bottom','rear'),1):
 p=OUT/f'{oid}.{v}.png'; im=Image.open(p).convert('RGBA');canvas.alpha_composite(im,(col*256,0));d.text((col*256+4,4),v,fill='black');box=im.getchannel('A').getbbox();views.append({'view':v,'path':str(p.relative_to(ROOT)),'sha256':sha(p),'rgba_sha256':rh(im),'alpha_bbox':list(box) if box else None})
contact=B/'postinstall-source-plus-six.png'; canvas.convert('RGB').save(contact); proof={'schema_version':1,'object_id':oid,'source_path':m['source_path'],'source_sha256':sha(src),'contact_path':str(contact.relative_to(OUT)),'contact_sha256':sha(contact),'views':views,'status':'pending-independent-whole-set-review'};(B/'postinstall-source-plus-six.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2))
