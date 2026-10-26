import json,hashlib,shutil,importlib.util
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/pocket-dungeon');OUT=ROOT/'reusable/views-additional';STAGE=OUT/'raw/candidates/faction-bunker-bottom-v4';OID='faction-battlefield-battlefield-descent-bunker'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
man=json.loads((STAGE/'candidate-manifest.json').read_text());proof=json.loads(Path('/workspace/scratch/view-qa-root.json').read_text())['reviewed'][f'book-tiles/pocket-dungeon::{OID}'];source=ROOT/man['source_path'];target=OUT/f'{OID}.bottom.png';candidate=ROOT/man['candidate_path']
assert proof['status']=='needs-correction'
assert sha(source)==man['source_sha256']==proof['source_sha256']
assert sha(target)==man['target_sha256_before']==proof['image_hashes']['bottom']
assert sha(candidate)==man['candidate_sha256']
idx=json.loads((OUT/'set-index.json').read_text());corr=json.loads((OUT/'corrections.json').read_text());asset=next(a for a in idx['assets'] if a['id']==f'{OID}.bottom');
reviewed_at='2026-10-26T13:54:32Z';snaprel=f'raw/targeted-repairs/reviewed-snapshots/{OID}.bottom.bunker-v4.png';snap=OUT/snaprel;snap.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(candidate,snap)
prov={'method':'generated','source_image':man['source_path'],'source_sha256':man['source_sha256'],'generated_atlas':man['raw_atlas'],'generated_atlas_sha256':man['raw_atlas_sha256'],'prompt_file':man['prompt_file'],'prompt_sha256':man['prompt_sha256'],'candidate_contact':man['contact_path'],'candidate_contact_sha256':man['contact_sha256'],'normalization':man['normalization'],'output_binding':man['output_binding'],'notes':'Root-approved inferred underside of the same earth-and-stone mound; hidden surface is generated, not recovered source pixels.'}
op={'type':'restore-reviewed-png','object_id':OID,'view':'bottom','before_sha256':sha(target),'snapshot_path':snaprel,'snapshot_sha256':sha(snap),'reviewer':'root','reviewed_at':reviewed_at,'review_source_sha256':sha(source),'reason':'Install exact root-approved bunker earth/stone underside candidate; awaiting fresh current whole-set review.','provenance_override':prov}
backup=OUT/'raw/targeted-repairs/faction-bunker-bottom-v4-backup';backup.mkdir(parents=True,exist_ok=True);spec=importlib.util.spec_from_file_location('fixes',OUT/'apply_deterministic_view_fixes.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);result=mod.apply(op,idx,backup)
s=next(s for s in idx['view_sets'] if s['object_id']==OID);s.update({'complete':False,'geometry_qa':'pending-review','notes':'Root-approved underside candidate installed; awaiting fresh whole-set review.'});corr['operations'].append(op);(OUT/'set-index.json').write_text(json.dumps(idx,indent=2)+'\n');(OUT/'corrections.json').write_text(json.dumps(corr,indent=2)+'\n')
# Capture canonical source+six with current accepted five views.
contact=Image.new('RGBA',(7*256,256),(235,235,235,255));draw=ImageDraw.Draw(contact);bg=Image.new('RGBA',(256,256),'white');bg.alpha_composite(Image.open(source).convert('RGBA'));contact.alpha_composite(bg,(0,0));draw.text((4,4),'source',fill='black');hashes=[]
for c,v in enumerate(['front','top','right','left','bottom','rear'],1):
 p=OUT/f'{OID}.{v}.png';contact.alpha_composite(Image.open(p).convert('RGBA'),(c*256,0));draw.text((c*256+4,4),v,fill='black');hashes.append({'view':v,'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)})
cp=STAGE/'postinstall-source-plus-six.png';contact.convert('RGB').save(cp);proofout={'object_id':OID,'source_path':source.relative_to(ROOT).as_posix(),'source_sha256':sha(source),'contact_path':cp.relative_to(ROOT).as_posix(),'contact_sha256':sha(cp),'views':hashes,'install_result':result};(STAGE/'postinstall-source-plus-six.json').write_text(json.dumps(proofout,indent=2)+'\n');print(json.dumps(proofout,indent=2))
