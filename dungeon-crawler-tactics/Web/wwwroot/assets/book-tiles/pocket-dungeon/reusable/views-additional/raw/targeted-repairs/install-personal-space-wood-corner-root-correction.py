#!/usr/bin/env python3
"""Apply the root-directed axis/bottom correction without regenerating accepted directions."""
from pathlib import Path
import hashlib,json,struct,shutil
from PIL import Image
PACK=Path(__file__).resolve().parents[4];VD=PACK/'reusable/views-additional';O='personal-space-warm-wood-plank-corner-transition';DONOR='personal-space-warm-wood-plank-floor'
PRE={'front':'c664ed39d505c517d68a4dbbda139b76a2bbced9e4e27a88c28f2836b3202672','top':'2b4b6e41440bef2ea9388fa9cd4d75480d9f4f7cd11904fae41e2fa90bfeb22e','right':'202c55dc8de3bebfde6e939af37f4fb9ccc1a1a3839611af51929ebbc2645f24','left':'b3ca67bbe7590b688db97ebebcd5047f382d109c9b290b211f82fd7ca4eb97c5','bottom':'7dfaf7276439cde855925c4a7c5a20b2d80a110c0ae21d1b6731eb79cd9582dc','rear':'aeacf9090be396759a23723b8593a012f6fac91060690adaf3cbe6ab4dbf2135'}
DONOR_SHA='6b60bcb6788502097fe561777b4ab66ae185d3642fe734276252b04f02a37bdf'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rgba_sha(im):return hashlib.sha256(struct.pack('>II',*im.size)+im.convert('RGBA').tobytes()).hexdigest()
# RIGHT and REAR remain accepted and are never written; TOP and LEFT are also preserved.
final_expected={}
for v,h in PRE.items():
 f=VD/f'{O}.{v}.png'; md=json.loads((VD/f'{O}.{v}.json').read_text()); installed=md.get('provenance',{}).get('root_correction','')=='2026-10-26 full-square wood corner correction'
 if installed:
  if sha(f)!=md['image']['sha256']:raise SystemExit(f'installed hash mismatch {v}')
 else:
  if sha(f)!=h:raise SystemExit(f'precondition changed; refusing {v}')
donor=VD/f'{DONOR}.bottom.png';if_hash=sha(donor)
if if_hash!=DONOR_SHA:raise SystemExit('approved donor bottom changed')
raw=VD/'raw/targeted-repairs';raw.mkdir(parents=True,exist_ok=True)
# Preserve the current generated attempt before the three source-directed corrections.
for v in ('front','right','bottom'):
 f=VD/f'{O}.{v}.png';snap=raw/f'{O}.{v}.before-root-correction.png'
 if not snap.exists():shutil.copy2(f,snap)
# FRONT/RIGHT source-plane border is on the rear and right edges: swap the current generated profiles.
front=VD/f'{O}.front.png';right=VD/f'{O}.right.png';temp=raw/f'{O}.front.before-root-correction.png'
if sha(front)==PRE['front']:
 current_right=Image.open(right).convert('RGBA'); current_front=Image.open(front).convert('RGBA'); current_right.save(raw/f'{O}.right.before-root-correction.png',optimize=True)
 current_front.save(raw/f'{O}.front.swap-temp.png',optimize=True);shutil.copyfile(front,right);shutil.copyfile(raw/f'{O}.right.before-root-correction.png',front)
# Full-square underside from the independently approved same-family warm wood floor, no L mask.
bottom=VD/f'{O}.bottom.png'
if sha(bottom)==PRE['bottom']:shutil.copyfile(donor,bottom)
idxp=VD/'set-index.json';idx=json.loads(idxp.read_text())
for v,donor_view,donor_obj in [('front','right',O),('right','front',O),('bottom','bottom',DONOR)]:
 f=VD/f'{O}.{v}.png';mp=VD/f'{O}.{v}.json';md=json.loads(mp.read_text());im=Image.open(f).convert('RGBA');md['image']={'path':f'reusable/views-additional/{O}.{v}.png','width':256,'height':256,'sha256':sha(f),'rgba_sha256':rgba_sha(im)};md['geometry_qa']='pending-review';source=VD/f'{donor_obj}.{donor_view}.png';step={'operation':'root-directed white-border axis correction' if v!='bottom' else 'same-family full-square underside alias','donor_object_id':donor_obj,'donor_view':donor_view,'donor_path':f'reusable/views-additional/{donor_obj}.{donor_view}.png','donor_sha256':sha(source),'reason':'The canonical top is a full square floor with white trim on two adjacent edges. FRONT/RIGHT are swapped so trim maps to RIGHT/REAR; underside is the approved full-square plain warm-wood bottom.'}; steps=md['provenance'].setdefault('repair_steps',[]);
 if step['operation'] not in [z.get('operation') for z in steps]:steps.append(step);md['provenance']['root_correction']='2026-10-26 full-square wood corner correction';md['provenance']['notes']='Target source identity retained; target is a full square wood floor with L-shaped white border, not an L-shaped footprint.';mp.write_text(json.dumps(md,indent=2)+'\n')
 for a in idx['assets']:
  if a.get('id')==md['id']:a.clear();a.update(md);break
g=next(x for x in idx['view_sets'] if x['object_id']==O);g['complete']=False;g['geometry_qa']='pending-review';g['notes']='Root-directed axis correction: FRONT/RIGHT swapped for adjacent white trim edges; BOTTOM aliases approved full-square same-family wood underside. Awaiting current-hash review.'
proofs=json.loads((raw/'reviewed-pass-proofs-pocket-scenery.json').read_text());proof=proofs.get(O,{});sourcep=PACK/proof.get('source_path','');ok=proof.get('status')=='pass' and sourcep.is_file() and sha(sourcep)==proof.get('source_sha256')
if ok:
 for view,h in proof.get('image_hashes',{}).items():
  if sha(VD/f'{O}.{view}.png')!=h:ok=False;break
status='pass' if ok else 'pending-review'
for view in ('front','top','right','left','bottom','rear'):
 mp=VD/f'{O}.{view}.json';md=json.loads(mp.read_text());md['geometry_qa']=status;mp.write_text(json.dumps(md,indent=2)+'\n')
 for a in idx['assets']:
  if a.get('id')==md['id']:a.clear();a.update(md);break
g['complete']=ok;g['geometry_qa']=status;g['notes']='Whole source+six root PASS restored from pinned current-hash proof.' if ok else 'Awaiting independent current-hash review.';idxp.write_text(json.dumps(idx,indent=2)+'\n')
recipe={'object_id':O,'status':'installed-pending-review','precondition_hashes':PRE,'donor_bottom':{'object_id':DONOR,'sha256':DONOR_SHA},'operations':{'front':'previous right profile','right':'previous front profile','bottom':'copy approved same-family full-square wood floor bottom'},'preserved':['top','left','rear'],'note':'No L footprint mask on square floor underside.'};(raw/f'{O}-root-correction.json').write_text(json.dumps(recipe,indent=2)+'\n')
print(json.dumps({v:sha(VD/f'{O}.{v}.png') for v in ['front','top','right','left','bottom','rear']},indent=2))
