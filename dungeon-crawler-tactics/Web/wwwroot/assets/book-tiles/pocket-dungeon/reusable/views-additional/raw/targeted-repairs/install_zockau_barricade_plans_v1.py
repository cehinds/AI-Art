#!/usr/bin/env python3
import hashlib,importlib.util,json,struct
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];OUT=ROOT/'reusable/views-additional';oid='hunting-zockau-narrow-alley-barricade';P=OUT/'raw/candidates/zockau-barricade-plans-v1';proof=json.loads((P/'candidate-proof.json').read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();rh=lambda im:hashlib.sha256(struct.pack('>II',*im.size)+im.convert('RGBA').tobytes()).hexdigest();reqp=OUT/proof['request_path'];req=json.loads(reqp.read_text());src=ROOT/proof['source_path']
if sha(src)!=proof['source_sha256']:raise RuntimeError('source changed')
for v,h in proof['current_live_hashes'].items():
 if sha(OUT/f'{oid}.{v}.png')!=h:raise RuntimeError(f'{v} changed')
raw=OUT/proof['generated_atlas'];
if sha(raw)!=proof['generated_atlas_sha256']:raise RuntimeError('raw changed')
idxp=OUT/'set-index.json';idx=json.loads(idxp.read_text());corrp=OUT/'corrections.json';corr=json.loads(corrp.read_text());back=OUT/'raw/targeted-repairs/zockau-plans-v1-backup';back.mkdir(parents=True,exist_ok=True);spec=importlib.util.spec_from_file_location('vf',OUT/'apply_deterministic_view_fixes.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);ops=[]
for r in proof['normalization']:
 v=r['view'];cand=OUT/r['candidate_path']
 if sha(cand)!=r['candidate_sha256']:raise RuntimeError(f'{v} candidate changed')
 prov={'method':'generated','source_image':proof['source_path'],'source_sha256':proof['source_sha256'],'generated_atlas':proof['generated_atlas'],'generated_atlas_sha256':proof['generated_atlas_sha256'],'generation_request':proof['request_path'],'generation_request_sha256':sha(reqp),'prompt':req['prompt'],'output_binding':req['output_binding'],'candidate_recipe':str((P/'candidate-proof.json').relative_to(OUT)),'candidate_recipe_sha256':sha(P/'candidate-proof.json'),'normalization':r,'reference_inputs':req['geometry_material_inputs'],'notes':'Root-scoped-accepted barricade principal plan preserving offset barrel/cone and posts; pending fresh whole-set review.'}
 ops.append({'type':'install-view-candidate','object_id':oid,'view':v,'before_sha256':proof['current_live_hashes'][v],'candidate_path':r['candidate_path'],'candidate_sha256':r['candidate_sha256'],'canonical_source_image':proof['source_path'],'canonical_source_sha256':proof['source_sha256'],'donor_object_id':oid,'donor_view':v,'donor_image_path':proof['generated_atlas'],'donor_image_sha256':proof['generated_atlas_sha256'],'transform':{'method':'source-bound generated orthographic plan','normalization':r,'resampling':'NEAREST'},'reason':f'Install root-scoped-accepted barricade {v.upper()} plan.','provenance':prov})
for op in ops:print(mod.apply(op,idx,back))
for op in ops:
 if not any(x.get('object_id')==oid and x.get('view')==op['view'] and x.get('candidate_sha256')==op['candidate_sha256'] for x in corr['operations']):corr['operations'].append(op)
s=next(x for x in idx['view_sets'] if x['object_id']==oid);s['complete']=False;s['geometry_qa']='pending-review';s['qa_replay_gate']={'status':'pending-review','reason':'Scoped-accepted TOP/BOTTOM installed; fresh current-source review pending.','proof_reviewed_at':None};t=idxp.with_suffix('.json.tmp');t.write_text(json.dumps(idx,indent=2)+'\n');t.replace(idxp);corrp.write_text(json.dumps(corr,indent=2)+'\n')
can=Image.new('RGBA',(7*256,256),(235,235,235,255));d=ImageDraw.Draw(can);im=Image.open(src).convert('RGBA');im.thumbnail((220,220),Image.Resampling.NEAREST);can.alpha_composite(im,((256-im.width)//2,(256-im.height)//2));d.text((4,4),'source',fill='black');views=[]
for col,v in enumerate(('front','top','right','left','bottom','rear'),1):
 p=OUT/f'{oid}.{v}.png';im=Image.open(p).convert('RGBA');can.alpha_composite(im,(col*256,0));d.text((col*256+4,4),v,fill='black');box=im.getchannel('A').getbbox();views.append({'view':v,'path':str(p.relative_to(ROOT)),'sha256':sha(p),'rgba_sha256':rh(im),'alpha_bbox':list(box) if box else None})
contact=P/'postinstall-source-plus-six.png';can.convert('RGB').save(contact);res={'schema_version':1,'object_id':oid,'source_path':proof['source_path'],'source_sha256':sha(src),'contact_path':str(contact.relative_to(OUT)),'contact_sha256':sha(contact),'views':views,'status':'pending-independent-whole-set-review'};(P/'postinstall-source-plus-six.json').write_text(json.dumps(res,indent=2)+'\n');print(contact)
