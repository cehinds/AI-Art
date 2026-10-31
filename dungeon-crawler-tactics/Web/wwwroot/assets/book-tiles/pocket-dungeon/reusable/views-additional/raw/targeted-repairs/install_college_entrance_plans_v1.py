#!/usr/bin/env python3
import hashlib,importlib.util,json
from pathlib import Path
from PIL import Image,ImageDraw
import struct
ROOT=Path(__file__).resolve().parents[4];OUT=ROOT/'reusable/views-additional';C=OUT/'raw/candidates';B=C/'college-magic-entrance-plans-v1';OID='faction-larracos-larracos-college-of-magic-entrance';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();rgba=lambda im:hashlib.sha256(struct.pack('>II',*im.size)+im.convert('RGBA').tobytes()).hexdigest()
topreqp=C/'college-magic-entrance-plans-v1-request.json';botreqp=C/'college-magic-entrance-bottom-v2-request.json';topreq=json.loads(topreqp.read_text());botreq=json.loads(botreqp.read_text());topproof=json.loads((B/'top-candidate-proof.json').read_text());proof=json.loads((B/'candidate-plans-proof.json').read_text());src=ROOT/topreq['source_path']
if sha(src)!=topproof['source_sha256']:raise RuntimeError('canonical source changed')
# Guard every current view from the full staged proof; only top and bottom are replaced.
for v,h in topproof['current_live_hashes'].items():
 if sha(OUT/f'{OID}.{v}.png')!=h:raise RuntimeError(f'{OID}.{v} changed since candidate staging')
if sha(OUT/botreq['geometry_guide_path'].split('reusable/views-additional/',1)[1]) if False else False:pass
idxp=OUT/'set-index.json';idx=json.loads(idxp.read_text());corrp=OUT/'corrections.json';corr=json.loads(corrp.read_text());ops=[]
for v,cand_rel,raw_rel,req,reqp,recipe_path,recipe_sha,normalization in [
 ('top',topproof['candidate_path'],'raw/candidates/college-magic-entrance-plans-v1-raw-atlas.png',topreq,topreqp,str((B/'top-candidate-proof.json').relative_to(OUT)),sha(B/'top-candidate-proof.json'),topproof['normalization']),
 ('bottom',proof['bottom_candidate_path'],'raw/candidates/college-magic-entrance-bottom-v2-raw.png',botreq,botreqp,str((B/'candidate-plans-proof.json').relative_to(OUT)),sha(B/'candidate-plans-proof.json'),proof['bottom_normalization'])]:
 cand=OUT/cand_rel; raw=OUT/raw_rel; target=OUT/f'{OID}.{v}.png'; before=topproof['current_live_hashes'][v]
 if sha(cand)!=(topproof['candidate_sha256'] if v=='top' else proof['bottom_candidate_sha256']):raise RuntimeError(f'{v} candidate changed')
 prov={'method':'generated','source_image':req['source_path'],'source_sha256':req['source_sha256'],'generated_atlas':raw_rel,'generated_atlas_sha256':sha(raw),'generation_request':str(reqp.relative_to(OUT)),'generation_request_sha256':sha(reqp),'prompt':req['prompt'],'output_binding':{'path':req['output_path'],'sha256':req['output_sha256']},'candidate_recipe':recipe_path,'candidate_recipe_sha256':recipe_sha,'normalization':normalization,'reference_inputs':[{'path':req.get('reference_contact',req.get('reference_sheet','')),'sha256':req.get('reference_contact_sha256',req.get('reference_sheet_sha256','')),'role':'native target identity, accepted elevations and plan geometry; canonical source is authoritative'}],'anchor_px':[128,248],'notes':'Root-scoped-accepted College of Magic entrance plan; target facade identity and open passage preserved; pending whole-set review.'}
 ops.append({'type':'install-view-candidate','object_id':OID,'view':v,'before_sha256':before,'candidate_path':cand_rel,'candidate_sha256':sha(cand),'canonical_source_image':req['source_path'],'canonical_source_sha256':req['source_sha256'],'donor_object_id':OID,'donor_view':'front','donor_image_path':raw_rel,'donor_image_sha256':sha(raw),'transform':{'method':'generated shallow orthographic plan; uniform fit to target facade width','normalization':normalization,'resampling':'NEAREST'},'reason':f'Install root-scoped-accepted College entrance {v.upper()} plan candidate.','provenance':prov})
backup=OUT/'raw/targeted-repairs/college-entrance-plans-v1-backup';backup.mkdir(parents=True,exist_ok=True);spec=importlib.util.spec_from_file_location('vf',OUT/'apply_deterministic_view_fixes.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
for op in ops:print(mod.apply(op,idx,backup))
for op in ops:
 if not any(x.get('type')==op['type'] and x.get('object_id')==OID and x.get('view')==op['view'] and x.get('candidate_sha256')==op['candidate_sha256'] for x in corr['operations']):corr['operations'].append(op)
s=next(x for x in idx['view_sets'] if x['object_id']==OID);s['complete']=False;s['geometry_qa']='pending-review';s['qa_replay_gate']={'status':'pending-review','reason':'Two scoped-accepted plan views installed; fresh whole-set current-hash review pending.','proof_reviewed_at':None}
tmp=idxp.with_suffix('.json.tmp');tmp.write_text(json.dumps(idx,indent=2)+'\n');tmp.replace(idxp);corrp.write_text(json.dumps(corr,indent=2)+'\n')
canvas=Image.new('RGBA',(7*256,256),(235,235,235,255));d=ImageDraw.Draw(canvas);si=Image.open(src).convert('RGBA');si.thumbnail((220,220),Image.Resampling.NEAREST);canvas.alpha_composite(si,((256-si.width)//2,(256-si.height)//2));d.text((5,4),'source',fill='black');views=[]
for col,v in enumerate(['front','top','right','left','bottom','rear'],1):
 p=OUT/f'{OID}.{v}.png';im=Image.open(p).convert('RGBA');canvas.alpha_composite(im,(col*256,0));d.text((col*256+4,4),v,fill='black');views.append({'view':v,'path':str(p.relative_to(ROOT)),'sha256':sha(p),'rgba_sha256':rgba(im),'alpha_bbox':list(im.getchannel('A').getbbox()) if im.getchannel('A').getbbox() else None})
contact=B/'postinstall-source-plus-six.png';canvas.convert('RGB').save(contact);current={'schema_version':1,'object_id':OID,'source_path':topreq['source_path'],'source_sha256':sha(src),'contact_path':str(contact.relative_to(OUT)),'contact_sha256':sha(contact),'views':views,'status':'pending-independent-whole-set-review'};(B/'postinstall-source-plus-six.json').write_text(json.dumps(current,indent=2)+'\n');print(json.dumps(current,indent=2))
