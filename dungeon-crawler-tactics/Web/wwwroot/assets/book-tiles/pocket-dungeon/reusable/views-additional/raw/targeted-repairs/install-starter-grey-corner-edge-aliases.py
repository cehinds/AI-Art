#!/usr/bin/env python3
"""Use accepted same-material orthographic edge views for the Starter Dungeon notched floor corner."""
from pathlib import Path
import hashlib,json,struct,shutil
from PIL import Image,ImageOps
PACK=Path(__file__).resolve().parents[4]; VD=PACK/'reusable/views-additional'
TARGET='starter-dungeon-grey-flagstone-corner-transition'; DONOR='starter-dungeon-grey-flagstone-edge-transition'
EXPECTED_TARGET={'front':'3d9be664b7622c0359a7bf6273812355ac423157b02f4f35a5aff37fbbbd3dee','top':'857761aded848ac839245756e3734717feb6e5ebb55e047eaefd0383ce826e9d','right':'4c7657c7fac3dd16a45d280925723190f180d2be99fb963dce3f3a6c13fb9fa8','left':'1fcd708bb9856122f2b2b5b492c72d8e1617c5980ea469d0d1fcab03d7a5f40e','bottom':'a3edf6ef67b8b6ab6a5d883995efdc6140beb82c9cce776596e9df395bef93ae','rear':'0db7a5fb0c73366a9c74b31dfc18073296df452c60a6235ea2d5332b43b62d2d'}
FINAL_TARGET={'front':'5f5e7933ec1a1ca21b197dd0005aa02ab09e97ee823857e4f5c289b28cf59914','top':'857761aded848ac839245756e3734717feb6e5ebb55e047eaefd0383ce826e9d','right':'582eb765a2df7b1fa533406b5cb9e768baf25ae6052df9476eb7f979e0e57166','left':'0698bd377bc84298d5e14ed0fc8020533a3c7e9512f826d6a1f2a45e1cc29890','bottom':'2d3c9452fa42d4a020d1fd7be731a305a649ef5b45525f779b80bd15f11f466a','rear':'43504a6d904e680e221840429c1da6b220c909c6358863ba623eda9e8ca52842'}
EXPECTED_DONOR={'front':'5f5e7933ec1a1ca21b197dd0005aa02ab09e97ee823857e4f5c289b28cf59914','top':'5f36274497228f55f26af6bcd4311430f4d47e6439e862f4788d0032d2e3758c','right':'582eb765a2df7b1fa533406b5cb9e768baf25ae6052df9476eb7f979e0e57166','left':'0698bd377bc84298d5e14ed0fc8020533a3c7e9512f826d6a1f2a45e1cc29890','bottom':'f2c11179fef9e4bfbb70bdfc3461d32521645e6e4e3c3d1b7f236e0177b3fdb8','rear':'43504a6d904e680e221840429c1da6b220c909c6358863ba623eda9e8ca52842'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rgba_sha(im):return hashlib.sha256(struct.pack('>II',*im.size)+im.convert('RGBA').tobytes()).hexdigest()
idxp=VD/'set-index.json';idx=json.loads(idxp.read_text());
for o,hs in [(TARGET,EXPECTED_TARGET),(DONOR,EXPECTED_DONOR)]:
 for v,h in hs.items():
  actual=sha(VD/f'{o}.{v}.png')
  if o==DONOR and actual!=h:raise SystemExit(f'hash guard {o}.{v}')
  if o==TARGET and actual not in (h,FINAL_TARGET[v]):raise SystemExit(f'hash guard {o}.{v}')
raw=VD/'raw/targeted-repairs';raw.mkdir(parents=True,exist_ok=True)
for v in ['front','right','left','bottom','rear']:
 if sha(VD/f'{TARGET}.{v}.png')==EXPECTED_TARGET[v] and not (raw/f'{TARGET}.{v}.before-projection-alias.png').exists():shutil.copy2(VD/f'{TARGET}.{v}.png',raw/f'{TARGET}.{v}.before-projection-alias.png')
ops={'front':('edge-front','copy'), 'right':('edge-right','copy'), 'left':('edge-left','copy'), 'rear':('edge-rear','copy')}
for view,(donor_view,_) in ops.items():
 src=VD/f'{DONOR}.{donor_view.split("-")[1]}.png';dst=VD/f'{TARGET}.{view}.png'
 if sha(dst)!=sha(src):shutil.copyfile(src,dst)
 else:continue
# underside inferred from the same complete L footprint, viewed from below (vertical mirror reverses front/back basis).
top=Image.open(VD/f'{TARGET}.top.png').convert('RGBA');bottom=ImageOps.flip(top);dst=VD/f'{TARGET}.bottom.png'
if sha(dst)!=FINAL_TARGET['bottom']:bottom.save(dst,optimize=True)
for view in ['front','right','left','rear','bottom']:
 p=VD/f'{TARGET}.{view}.png';mp=VD/f'{TARGET}.{view}.json';md=json.loads(mp.read_text());im=Image.open(p).convert('RGBA');md['image']={'path':f'reusable/views-additional/{TARGET}.{view}.png','width':256,'height':256,'sha256':sha(p),'rgba_sha256':rgba_sha(im)};md['geometry_qa']='pending-review'
 if view=='bottom': step={'operation':'mirror same-object complete L plan for underside view','donor_view':'top','donor_sha256':sha(VD/f'{TARGET}.top.png'),'basis':'looking upward reverses front/back direction; footprint preserved'}
 else:
  dv=view;step={'operation':'cross-object same-material floor-edge alias','donor_object_id':DONOR,'donor_view':dv,'donor_path':f'reusable/views-additional/{DONOR}.{dv}.png','donor_sha256':sha(VD/f'{DONOR}.{dv}.png'),'reason':'Both objects are flat grey flagstone tiles in the same kit; target only needs low slab edge elevations, while its notched L footprint remains in TOP/BOTTOM.'}
 steps=md['provenance'].setdefault('repair_steps',[]);key=step['operation']+':'+step.get('donor_view','')
 if key not in [z.get('operation','')+':'+z.get('donor_view','') for z in steps]:steps.append(step)
 md['provenance']['notes']='Canonical target source identity retained. Edge geometry is borrowed from accepted same-material tile projections; underside uses the target L footprint mirrored for below-view.';mp.write_text(json.dumps(md,indent=2)+'\n')
 for a in idx['assets']:
  if a.get('id')==md['id']:a.clear();a.update(md);break
proofs=json.loads((raw/'reviewed-pass-proofs-pocket-scenery.json').read_text());proof=proofs.get(TARGET,{});source=PACK/proof.get('source_path','');ok=proof.get('status')=='pass' and source.is_file() and sha(source)==proof.get('source_sha256')
if ok:
 for v,h in proof.get('image_hashes',{}).items():
  if sha(VD/f'{TARGET}.{v}.png')!=h:ok=False;break
status='pass' if ok else 'pending-review'
for v in ['front','top','right','left','bottom','rear']:
 mp=VD/f'{TARGET}.{v}.json';md=json.loads(mp.read_text());md['geometry_qa']=status;mp.write_text(json.dumps(md,indent=2)+'\n')
 for a in idx['assets']:
  if a.get('id')==md['id']:a.clear();a.update(md);break
g=next(x for x in idx['view_sets'] if x['object_id']==TARGET);g['complete']=ok;g['geometry_qa']=status;g['notes']='Whole source+six root PASS restored from pinned current-hash proof.' if ok else 'Awaiting independent current-hash review.'
idxp.write_text(json.dumps(idx,indent=2)+'\n')
recipe={'target':TARGET,'donor':DONOR,'precondition_hashes':{'target':EXPECTED_TARGET,'donor':EXPECTED_DONOR},'operations':{'front':'copy donor front','right':'copy donor right','left':'copy donor left','rear':'copy donor rear','bottom':'vertical mirror of target top'},'preserved_views':['top'],'status':'installed-current-hash-reviewed' if status=='pass' else 'installed-pending-review'};(raw/f'{TARGET}-projection-aliases.json').write_text(json.dumps(recipe,indent=2)+'\n')
print(json.dumps({v:sha(VD/f'{TARGET}.{v}.png') for v in ['front','top','right','left','bottom','rear']},indent=2))
