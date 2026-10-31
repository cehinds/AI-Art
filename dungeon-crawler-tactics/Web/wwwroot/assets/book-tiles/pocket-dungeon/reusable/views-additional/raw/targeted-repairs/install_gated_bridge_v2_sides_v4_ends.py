#!/usr/bin/env python3
import hashlib,importlib.util,json,struct
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];OUT=ROOT/'reusable/views-additional';C=OUT/'raw/candidates';oid='early-arenas-gated-stone-bridge';srcpath='early-arenas/components/early-arenas-gated-stone-bridge.png';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();rh=lambda im:hashlib.sha256(struct.pack('>II',*im.size)+im.convert('RGBA').tobytes()).hexdigest()
versions={'front':'gated-stone-bridge-elevations-v4','rear':'gated-stone-bridge-elevations-v4','right':'gated-stone-bridge-elevations-v2','left':'gated-stone-bridge-elevations-v2'}
source=ROOT/srcpath; expected='b22a8ee27dbbe1da2d10d21adc63c31584099991103c8e34bbcb2192b4002efd'
if sha(source)!=expected:raise RuntimeError('canonical source changed')
manifests={name:json.loads((C/name/'candidate-manifest.json').read_text()) for name in set(versions.values())}
for m in manifests.values():
 if m['source_sha256']!=expected:raise RuntimeError('staged source mismatch')
 for v,h in m['current_live_hashes'].items():
  if sha(OUT/f'{oid}.{v}.png')!=h:raise RuntimeError(f'live {v} changed before install')
idxp=OUT/'set-index.json';idx=json.loads(idxp.read_text());corrp=OUT/'corrections.json';corr=json.loads(corrp.read_text());ops=[];back=OUT/'raw/targeted-repairs/gated-bridge-install-backup';back.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('vf',OUT/'apply_deterministic_view_fixes.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
for v,name in versions.items():
 m=manifests[name];record=next(x for x in m['candidates'] if x['view']==v); candrel=record['path'];cand=OUT/candrel;reqkey='prompt_path' if 'prompt_path' in m else 'request_path';reqrel=m[reqkey];reqp=OUT/reqrel;req=json.loads(reqp.read_text());rawrel=m['raw_atlas_path'];raw=OUT/rawrel
 if sha(cand)!=record['sha256']:raise RuntimeError(f'{v} candidate mismatch')
 if sha(raw)!=m['raw_atlas_sha256']:raise RuntimeError(f'{v} raw atlas mismatch')
 prov={'method':'generated','source_image':srcpath,'source_sha256':expected,'generated_atlas':rawrel,'generated_atlas_sha256':sha(raw),'generation_request':reqrel,'generation_request_sha256':sha(reqp),'prompt':req['prompt'],'output_binding':{'path':req.get('output_binding',{}).get('path',req.get('output_path')),'sha256':req.get('output_binding',{}).get('sha256',req.get('output_sha256'))},'candidate_manifest':str((C/name/'candidate-manifest.json').relative_to(OUT)),'candidate_manifest_sha256':sha(C/name/'candidate-manifest.json'),'candidate_normalization':{k:record.get(k) for k in ('raw_bbox','render_size','target_width_from_top','resampling','anchor_px','uniform_scale','source_dimensions','threshold_alpha')},'reference_contact':m.get('contact_path'),'reference_contact_sha256':m.get('contact_sha256'),'notes':'Root-scoped-accepted principal end elevation installed with current source and all-six hash guards. FRONT/REAR use v4 low gate end profiles (173x56); RIGHT/LEFT use v2 accepted long parapet profiles. TOP/BOTTOM retained.'}
 op={'type':'install-view-candidate','object_id':oid,'view':v,'before_sha256':m['current_live_hashes'][v],'candidate_path':candrel,'candidate_sha256':record['sha256'],'canonical_source_image':srcpath,'canonical_source_sha256':expected,'donor_object_id':oid,'donor_view':v,'donor_image_path':rawrel,'donor_image_sha256':sha(raw),'transform':{'method':'source-bound generated orthographic elevation','normalization':prov['candidate_normalization'],'resampling':'NEAREST'},'reason':'Install root-approved bridge end/side elevations; preserve accepted TOP/BOTTOM.','provenance':prov}
 ops.append(op)
for op in ops:print(mod.apply(op,idx,back))
for op in ops:
 if not any(x.get('object_id')==oid and x.get('view')==op['view'] and x.get('candidate_sha256')==op['candidate_sha256'] for x in corr['operations']):corr['operations'].append(op)
s=next(x for x in idx['view_sets'] if x['object_id']==oid);s['complete']=False;s['geometry_qa']='pending-review';s['qa_replay_gate']={'status':'pending-review','reason':'Four scoped-accepted end/side views installed; awaiting fresh current-source whole-set review.','proof_reviewed_at':None}
t=idxp.with_suffix('.json.tmp');t.write_text(json.dumps(idx,indent=2)+'\n');t.replace(idxp);corrp.write_text(json.dumps(corr,indent=2)+'\n')
can=Image.new('RGBA',(7*256,256),(235,235,235,255));d=ImageDraw.Draw(can);im=Image.open(source).convert('RGBA');im.thumbnail((220,220),Image.Resampling.NEAREST);can.alpha_composite(im,((256-im.width)//2,(256-im.height)//2));d.text((4,4),'source',fill='black');views=[]
for col,v in enumerate(('front','top','right','left','bottom','rear'),1):
 p=OUT/f'{oid}.{v}.png';im=Image.open(p).convert('RGBA');can.alpha_composite(im,(col*256,0));d.text((col*256+4,4),v,fill='black');box=im.getchannel('A').getbbox();views.append({'view':v,'path':str(p.relative_to(ROOT)),'sha256':sha(p),'rgba_sha256':rh(im),'alpha_bbox':list(box) if box else None})
P=C/'gated-stone-bridge-install-v1';P.mkdir(parents=True,exist_ok=True);contact=P/'postinstall-source-plus-six.png';can.convert('RGB').save(contact);proof={'schema_version':1,'object_id':oid,'source_path':srcpath,'source_sha256':sha(source),'contact_path':str(contact.relative_to(OUT)),'contact_sha256':sha(contact),'views':views,'status':'pending-independent-whole-set-review'};(P/'postinstall-source-plus-six.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2))
