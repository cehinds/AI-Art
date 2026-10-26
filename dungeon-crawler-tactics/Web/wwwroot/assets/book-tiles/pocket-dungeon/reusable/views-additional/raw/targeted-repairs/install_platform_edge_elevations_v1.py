#!/usr/bin/env python3
import hashlib,importlib.util,json
from pathlib import Path
from PIL import Image,ImageDraw
import struct
ROOT=Path(__file__).resolve().parents[4];OUT=ROOT/'reusable/views-additional';C=OUT/'raw/candidates';OID='iron-stations-platform-edge-segment';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();rgba=lambda im:hashlib.sha256(struct.pack('>II',*im.size)+im.convert('RGBA').tobytes()).hexdigest()
B1=C/'iron-stations-platform-edge-orthographic-v1';m1=json.loads((B1/'candidate-manifest.json').read_text());r1=m1['objects'][0];req1p=C/'iron-stations-platform-edge-orthographic-v1-request.json';req1=json.loads(req1p.read_text())
B3=C/'platform-edge-end-profiles-v3';m3=json.loads((B3/'candidate-manifest.json').read_text());req3p=C/'platform-edge-end-profiles-v3-request.json';req3=json.loads(req3p.read_text());row3=m3
source=ROOT/r1['source_path'];
if sha(source)!=r1['source_sha256']:raise RuntimeError('source hash changed')
# Current-view guard from both staged batches.
for v,h in r1['source_view_hashes'].items():
 if sha(OUT/f'{OID}.{v}.png')!=h:raise RuntimeError(f'current {v} changed after staging')
idxp=OUT/'set-index.json';idx=json.loads(idxp.read_text());corrp=OUT/'corrections.json';corr=json.loads(corrp.read_text());ops=[]
def add(v,rec,batch,request,reqpath,rawrel,manifestpath):
 cand=OUT/rec['path'];raw=OUT/rawrel;before=r1['source_view_hashes'][v]
 if sha(cand)!=rec['sha256'] or sha(raw)!=(m1['raw_atlas_sha256'] if batch=='v1' else m3['raw_atlas_sha256']):raise RuntimeError(f'{v} candidate/raw hash mismatch')
 prov={'method':'generated','source_image':r1['source_path'],'source_sha256':r1['source_sha256'],'generated_atlas':rawrel,'generated_atlas_sha256':sha(raw),'generation_request':str(reqpath.relative_to(OUT)),'generation_request_sha256':sha(reqpath),'prompt':request['prompt'],'output_binding':{'path':request['output_path'],'sha256':sha(raw)},'candidate_recipe':str(manifestpath.relative_to(OUT)),'candidate_recipe_sha256':sha(manifestpath),'normalization':rec,'reference_inputs':[{'path':request.get('reference_contact',''),'sha256':request.get('reference_contact_sha256',''),'role':'canonical source and accepted plan/profile context; target source identity preserved'}],'anchor_px':[128,248],'notes':'Root-scoped-accepted orthographic platform edge profile; candidate pending whole-set review.'}
 ops.append({'type':'install-view-candidate','object_id':OID,'view':v,'before_sha256':before,'candidate_path':rec['path'],'candidate_sha256':sha(cand),'canonical_source_image':r1['source_path'],'canonical_source_sha256':r1['source_sha256'],'donor_object_id':OID,'donor_view':'top','donor_image_path':rawrel,'donor_image_sha256':sha(raw),'transform':{'method':'source-cell component crop and uniform plan-axis width calibration','scale':rec['scale'],'render_size':rec['render_size'],'resampling':'NEAREST'},'reason':f'Install root-scoped-accepted platform edge {v.upper()} profile.','provenance':prov})
for v in ('front','rear'): add(v,r1['candidates'][v],'v1',req1,req1p,m1['raw_atlas_path'],B1/'candidate-manifest.json')
for rec in row3['candidates']:add(rec['view'],rec,'v3',req3,req3p,m3['raw_atlas_path'],B3/'candidate-manifest.json')
backup=OUT/'raw/targeted-repairs/platform-edge-elevations-v1-backup';backup.mkdir(parents=True,exist_ok=True);spec=importlib.util.spec_from_file_location('vf',OUT/'apply_deterministic_view_fixes.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
for op in ops:print(mod.apply(op,idx,backup))
for op in ops:
 if not any(x.get('type')==op['type'] and x.get('object_id')==OID and x.get('view')==op['view'] and x.get('candidate_sha256')==op['candidate_sha256'] for x in corr['operations']):corr['operations'].append(op)
s=next(x for x in idx['view_sets'] if x['object_id']==OID);s['complete']=False;s['geometry_qa']='pending-review';s['qa_replay_gate']={'status':'pending-review','reason':'Four scoped-accepted edge profiles installed; fresh whole-set review pending.','proof_reviewed_at':None}
tmp=idxp.with_suffix('.json.tmp');tmp.write_text(json.dumps(idx,indent=2)+'\n');tmp.replace(idxp);corrp.write_text(json.dumps(corr,indent=2)+'\n')
canvas=Image.new('RGBA',(7*256,256),(235,235,235,255));d=ImageDraw.Draw(canvas);si=Image.open(source).convert('RGBA');si.thumbnail((220,220),Image.Resampling.NEAREST);canvas.alpha_composite(si,((256-si.width)//2,(256-si.height)//2));d.text((5,4),'source',fill='black');views=[]
for col,v in enumerate(['front','top','right','left','bottom','rear'],1):
 p=OUT/f'{OID}.{v}.png';im=Image.open(p).convert('RGBA');canvas.alpha_composite(im,(col*256,0));d.text((col*256+4,4),v,fill='black');views.append({'view':v,'path':str(p.relative_to(ROOT)),'sha256':sha(p),'rgba_sha256':rgba(im),'alpha_bbox':list(im.getchannel('A').getbbox()) if im.getchannel('A').getbbox() else None})
contact=B3/'postinstall-source-plus-six.png';canvas.convert('RGB').save(contact);proof={'schema_version':1,'object_id':OID,'source_path':r1['source_path'],'source_sha256':sha(source),'contact_path':str(contact.relative_to(OUT)),'contact_sha256':sha(contact),'views':views,'status':'pending-independent-whole-set-review'};(B3/'postinstall-source-plus-six.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2))
