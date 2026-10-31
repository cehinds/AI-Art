import hashlib,json,shutil,importlib.util
from pathlib import Path
from PIL import Image
ROOT=Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/pocket-dungeon');OUT=ROOT/'reusable/views-additional';ST=OUT/'raw/candidates/desert-doorway-open-v6';OID='bubble-desert-adobe-desert-plaster-open-doorway'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();man=json.loads((ST/'candidate-manifest.json').read_text());proof=json.loads(Path('/workspace/scratch/view-qa-root.json').read_text())['reviewed'][f'book-tiles/pocket-dungeon::{OID}'];source=ROOT/man['target_source_path']
assert proof['status']=='needs-correction',proof['status']
assert sha(source)==man['target_source_sha256']==proof['source_sha256']
idxp=OUT/'set-index.json';idx=json.loads(idxp.read_text());corrp=OUT/'corrections.json';corr=json.loads(corrp.read_text());backup=OUT/'raw/targeted-repairs/desert-open-v6-backup';backup.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('fixes',OUT/'apply_deterministic_view_fixes.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);results=[]
for view in ('top','bottom'):
 target=OUT/f'{OID}.{view}.png';candidate=ROOT/man['candidates'][view]['path'];expected=proof['image_hashes'][view]
 assert sha(target)==expected, f'{view} changed since authoritative root review'
 assert sha(target)==proof['image_hashes'][view]
 assert sha(candidate)==man['candidates'][view]['sha256']
 snaprel=f'raw/targeted-repairs/reviewed-snapshots/{OID}.{view}.desert-open-v6.png';snap=OUT/snaprel;snap.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(candidate,snap)
 prov={'method':'generated','source_image':man['target_source_path'],'source_sha256':man['target_source_sha256'],'generated_atlas':man['generated_atlas'],'generated_atlas_sha256':man['generated_atlas_sha256'],'generation_request':man['generation_request'],'candidate_contact':man['contact_path'],'candidate_contact_sha256':man['contact_sha256'],'normalization':man['prop_extractions'],'output_binding':man['output_binding'],'geometry_frame_donors':man['geometry_frame_donors'],'composition_ops':man['composition_ops'],'notes':'Root scoped-accepted this inferred orthographic view candidate. Pot mouth/base is a source-attached separate footprint at the front-left of the post; the red curtain edge is retained. The full set awaits independent current source-plus-six review.'}
 op={'type':'restore-reviewed-png','object_id':OID,'view':view,'before_sha256':sha(target),'snapshot_path':snaprel,'snapshot_sha256':sha(snap),'reviewer':'root-scoped-candidate-approval','reviewed_at':'2026-10-26','review_source_sha256':sha(source),'reason':'Install exact root-scoped-accepted desert open doorway plan candidate; full set remains pending independent current-hash review.','provenance_override':prov}
 results.append(mod.apply(op,idx,backup));corr['operations'].append(op)
setrec=next(s for s in idx['view_sets'] if s['object_id']==OID);setrec.update({'complete':False,'geometry_qa':'pending-review','notes':'TOP/BOTTOM scoped candidates installed; REAR opposite-side curtain candidate remains pending, then request independent current source-plus-six review.'})
idxp.write_text(json.dumps(idx,indent=2)+'\n');corrp.write_text(json.dumps(corr,indent=2)+'\n')
# Fresh source+six with installed T/B and unchanged current other views.
contact=Image.new('RGBA',(8*256,256),(238,238,238,255));from PIL import ImageDraw
d=ImageDraw.Draw(contact)
for i,(name,p) in enumerate([('source',source),('front',OUT/f'{OID}.front.png'),('top',OUT/f'{OID}.top.png'),('right',OUT/f'{OID}.right.png'),('left',OUT/f'{OID}.left.png'),('bottom',OUT/f'{OID}.bottom.png'),('rear',OUT/f'{OID}.rear.png')]):
 panel=Image.new('RGBA',(256,256),'white');panel.alpha_composite(Image.open(p).convert('RGBA'));contact.alpha_composite(panel,(i*256,0));d.text((i*256+4,4),name,fill='black')
cp=ST/'postinstall-top-bottom-source-plus-six.png';contact.convert('RGB').save(cp);out={'object_id':OID,'source_sha256':sha(source),'contact_path':cp.relative_to(ROOT).as_posix(),'contact_sha256':sha(cp),'current_view_hashes':{v:sha(OUT/f'{OID}.{v}.png') for v in ('front','top','right','left','bottom','rear')},'ops':results,'set_status':'pending-independent-whole-set-review'};(ST/'install-result.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
