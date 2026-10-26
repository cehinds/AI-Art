#!/usr/bin/env python3
import hashlib,importlib.util,json,struct
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];OUT=ROOT/'reusable/views-additional';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();rh=lambda im:hashlib.sha256(struct.pack('>II',*im.size)+im.convert('RGBA').tobytes()).hexdigest();idxp=OUT/'set-index.json';idx=json.loads(idxp.read_text());corrp=OUT/'corrections.json';corr=json.loads(corrp.read_text());back=OUT/'raw/targeted-repairs/console-float-install-backup';back.mkdir(parents=True,exist_ok=True);spec=importlib.util.spec_from_file_location('vf',OUT/'apply_deterministic_view_fixes.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
sets=[('iron-trains-train-control-console','control-console-top-v1',['top']),('parade-horribles-unoccupied-parade-float-base','parade-float-end-elevations-v1',['front','rear'])]; loaded=[]
for oid,folder,views in sets:
 P=OUT/'raw/candidates'/folder;proof=json.loads((P/'candidate-proof.json').read_text());reqp=OUT/proof['request_path'];req=json.loads(reqp.read_text());src=ROOT/req['source_path'];
 if sha(src)!=req['source_sha256']:raise RuntimeError(f'{oid} source changed')
 for v,h in proof['current_live_hashes'].items():
  if sha(OUT/f'{oid}.{v}.png')!=h:raise RuntimeError(f'{oid}.{v} changed before install')
 if sha(OUT/proof['generated_atlas'])!=proof['generated_atlas_sha256']:raise RuntimeError(f'{oid} atlas changed')
 for v in views:
  rec=next(x for x in proof['normalization'] if x['view']==v) if isinstance(proof['normalization'],list) else proof
  rel=rec.get('candidate_path',proof.get('candidate_path'));h=rec.get('candidate_sha256',proof.get('candidate_sha256'));cand=OUT/rel
  if sha(cand)!=h:raise RuntimeError(f'{oid}.{v} candidate hash mismatch')
 loaded.append((oid,folder,views,proof,req,reqp,src))
ops=[]
for oid,folder,views,proof,req,reqp,src in loaded:
 rawrel=proof['generated_atlas'];raw=OUT/rawrel;P=OUT/'raw/candidates'/folder
 for v in views:
  rec=next(x for x in proof['normalization'] if x['view']==v) if isinstance(proof['normalization'],list) else proof;rel=rec.get('candidate_path',proof.get('candidate_path'));h=rec.get('candidate_sha256',proof.get('candidate_sha256')); normalization=rec.get('normalization',proof.get('normalization'))
  prov={'method':'generated','source_image':str(src.relative_to(ROOT)),'source_sha256':sha(src),'generated_atlas':rawrel,'generated_atlas_sha256':sha(raw),'generation_request':proof['request_path'],'generation_request_sha256':sha(OUT/proof['request_path']),'prompt':req['prompt'],'output_binding':req['output_binding'],'candidate_recipe':str((P/'candidate-proof.json').relative_to(OUT)),'candidate_recipe_sha256':sha(P/'candidate-proof.json'),'normalization':normalization,'reference_inputs':req['geometry_material_inputs'],'notes':'Root-scoped-accepted source-bound principal-view candidate installed; fresh whole-set review pending.'}
  ops.append({'type':'install-view-candidate','object_id':oid,'view':v,'before_sha256':proof['current_live_hashes'][v],'candidate_path':rel,'candidate_sha256':h,'canonical_source_image':str(src.relative_to(ROOT)),'canonical_source_sha256':sha(src),'donor_object_id':oid,'donor_view':v,'donor_image_path':rawrel,'donor_image_sha256':sha(raw),'transform':{'method':'generated orthographic principal view','normalization':normalization,'resampling':'NEAREST'},'reason':f'Install root-scoped-accepted {v.upper()} candidate.','provenance':prov})
for op in ops: print(mod.apply(op,idx,back))
for op in ops:
 if not any(x.get('object_id')==op['object_id'] and x.get('view')==op['view'] and x.get('candidate_sha256')==op['candidate_sha256'] for x in corr['operations']):corr['operations'].append(op)
for oid,folder,views,proof,*_ in loaded:
 s=next(x for x in idx['view_sets'] if x['object_id']==oid);s['complete']=False;s['geometry_qa']='pending-review';s['qa_replay_gate']={'status':'pending-review','reason':'Scoped-accepted candidate view(s) installed; fresh whole-set current-hash review pending.','proof_reviewed_at':None}
t=idxp.with_suffix('.json.tmp');t.write_text(json.dumps(idx,indent=2)+'\n');t.replace(idxp);corrp.write_text(json.dumps(corr,indent=2)+'\n')
for oid,folder,views,proof,req,reqp,src in loaded:
 P=OUT/'raw/candidates'/folder;can=Image.new('RGBA',(7*256,256),(235,235,235,255));d=ImageDraw.Draw(can);im=Image.open(src).convert('RGBA');im.thumbnail((220,220),Image.Resampling.NEAREST);can.alpha_composite(im,((256-im.width)//2,(256-im.height)//2));d.text((4,4),'source',fill='black');result=[]
 for col,v in enumerate(('front','top','right','left','bottom','rear'),1):
  p=OUT/f'{oid}.{v}.png';im=Image.open(p).convert('RGBA');can.alpha_composite(im,(col*256,0));d.text((col*256+4,4),v,fill='black');box=im.getchannel('A').getbbox();result.append({'view':v,'path':str(p.relative_to(ROOT)),'sha256':sha(p),'rgba_sha256':rh(im),'alpha_bbox':list(box) if box else None})
 contact=P/'postinstall-source-plus-six.png';can.convert('RGB').save(contact);res={'schema_version':1,'object_id':oid,'source_path':req['source_path'],'source_sha256':sha(src),'contact_path':str(contact.relative_to(OUT)),'contact_sha256':sha(contact),'views':result,'status':'pending-independent-whole-set-review'};(P/'postinstall-source-plus-six.json').write_text(json.dumps(res,indent=2)+'\n');print(contact)
