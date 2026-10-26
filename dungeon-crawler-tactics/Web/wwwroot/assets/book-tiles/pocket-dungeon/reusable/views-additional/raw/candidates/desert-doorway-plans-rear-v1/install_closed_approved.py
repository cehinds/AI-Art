from pathlib import Path
import json,hashlib,shutil,importlib.util
from PIL import Image,ImageDraw
ROOT=Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/pocket-dungeon');OUT=ROOT/'reusable/views-additional';STAGE=OUT/'raw/candidates/desert-doorway-plans-rear-v1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
manifest=json.loads((STAGE/'candidate-manifest.json').read_text());root=json.loads(Path('/workspace/scratch/view-qa-root.json').read_text())['reviewed'];idx=json.loads((OUT/'set-index.json').read_text());corr=json.loads((OUT/'corrections.json').read_text());reviewed_at='2026-10-26T14:00:16Z';backup=OUT/'raw/targeted-repairs/desert-closed-door-v1-backup';backup.mkdir(parents=True,exist_ok=True);snapdir=OUT/'raw/targeted-repairs/reviewed-snapshots';snapdir.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('fixes',OUT/'apply_deterministic_view_fixes.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);ops=[];results=[]
for obj in manifest['objects']:
 oid=obj['object_id']
 if oid!='bubble-desert-adobe-desert-plaster-closed-doorway':continue
 proof=root[f'book-tiles/pocket-dungeon::{oid}'];source=ROOT/obj['source_path'];assert sha(source)==obj['source_sha256']==proof['source_sha256'];assert proof['status']=='needs-correction'
 for view,h in proof['image_hashes'].items():assert sha(OUT/f'{oid}.{view}.png')==h,f'{oid}.{view} changed since root capture'
 for rec in obj['candidates']:
  v=rec['view'];target=OUT/f'{oid}.{v}.png';assert sha(target)==rec['target_sha256_before']==proof['image_hashes'][v];candidate=ROOT/rec['candidate_path'];assert sha(candidate)==rec['candidate_sha256']
  snaprel=f'raw/targeted-repairs/reviewed-snapshots/{oid}.{v}.desert-door-v1.png';snap=OUT/snaprel;shutil.copyfile(candidate,snap)
  norm={k:rec[k] for k in ['raw_component','scale','render_size','resampling','anchor_px']}
  prov={'method':'generated','source_image':obj['source_path'],'source_sha256':obj['source_sha256'],'generated_atlas':manifest['raw_atlas']['path'],'generated_atlas_sha256':manifest['raw_atlas']['sha256'],'prompt_file':manifest['prompt_file'],'prompt_sha256':manifest['prompt_sha256'],'candidate_contact':obj['contact_path'],'candidate_contact_sha256':obj['contact_sha256'],'normalization':norm,'notes':'Root-approved inferred desert doorway projection. The closed state remains source-faithful; hidden surfaces are inferred, not recovered.'}
  op={'type':'restore-reviewed-png','object_id':oid,'view':v,'before_sha256':sha(target),'snapshot_path':snaprel,'snapshot_sha256':sha(snap),'reviewer':'root','reviewed_at':reviewed_at,'review_source_sha256':sha(source),'reason':'Install exact root-approved closed desert doorway TOP/BOTTOM/REAR candidate; await fresh whole-set review.','provenance_override':prov};ops.append(op)
res=[mod.apply(op,idx,backup) for op in ops]
for s in idx['view_sets']:
 if s['object_id']=='bubble-desert-adobe-desert-plaster-closed-doorway':s.update({'complete':False,'geometry_qa':'pending-review','notes':'Root-approved TOP/BOTTOM/REAR candidate installed; awaiting fresh whole-set current hash review.'})
corr['operations'].extend(ops);(OUT/'set-index.json').write_text(json.dumps(idx,indent=2)+'\n');(OUT/'corrections.json').write_text(json.dumps(corr,indent=2)+'\n')
# post-install source+six contact
obj=next(o for o in manifest['objects'] if o['object_id']=='bubble-desert-adobe-desert-plaster-closed-doorway');oid=obj['object_id'];src=ROOT/obj['source_path'];contact=Image.new('RGBA',(7*256,256),(235,235,235,255));draw=ImageDraw.Draw(contact);bg=Image.new('RGBA',(256,256),'white');bg.alpha_composite(Image.open(src).convert('RGBA'));contact.alpha_composite(bg,(0,0));draw.text((4,4),'source',fill='black');views=[]
for c,v in enumerate(['front','top','right','left','bottom','rear'],1):
 p=OUT/f'{oid}.{v}.png';contact.alpha_composite(Image.open(p).convert('RGBA'),(c*256,0));draw.text((c*256+4,4),v,fill='black');views.append({'view':v,'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)})
cp=STAGE/f'{oid}.postinstall-source-plus-six.png';contact.convert('RGB').save(cp);record={'object_id':oid,'source_path':src.relative_to(ROOT).as_posix(),'source_sha256':sha(src),'contact_path':cp.relative_to(ROOT).as_posix(),'contact_sha256':sha(cp),'views':views};cp.with_suffix('.json').write_text(json.dumps(record,indent=2)+'\n');(STAGE/'closed-install-result.json').write_text(json.dumps({'reviewer':'root','reviewed_at':reviewed_at,'ops':ops,'results':res,'postinstall':record},indent=2)+'\n');print(json.dumps(record,indent=2))
