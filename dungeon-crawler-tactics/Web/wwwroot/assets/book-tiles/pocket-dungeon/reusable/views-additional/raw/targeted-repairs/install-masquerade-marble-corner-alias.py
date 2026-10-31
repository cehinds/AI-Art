#!/usr/bin/env python3
"""Replay symmetric edge aliases and preserve current-hash approval."""
from pathlib import Path
import hashlib,json,struct,shutil
from PIL import Image
PACK=Path(__file__).resolve().parents[4];VD=PACK/'reusable/views-additional';OBJ='masquerade-white-marble-corner-transition'
PRE={'front':'cef09319dbd95f26f9e0d9358875899ddc570964b8d35ae680714d5c56a34fd8','top':'20262670b4b779c114aefa36dda862eba214f3ec591c31d0e32826f26d345aac','right':'1edb41e8cd334a561c7ea5af5a08a759e9c5fe62b1085d0954567cb8c8015c24','left':'208a1a14ca1a27f161a44d414e3727475ff149620bb8a6eb561d229480ec90d7','bottom':'e73e3dedd2d7bd5e71e4900b82cbf3afc2762155146e112db6fe09806276efb9','rear':'863689aaa9ab03f06148140a4154eb3d5be3e0db57a201faaac2793239c90ad3'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rgba_sha(im):return hashlib.sha256(struct.pack('>II',*im.size)+im.convert('RGBA').tobytes()).hexdigest()
idxp=VD/'set-index.json';idx=json.loads(idxp.read_text());raw=VD/'raw/targeted-repairs';proofs=json.loads((raw/'reviewed-pass-proofs-pocket-scenery.json').read_text());
for v,h in PRE.items():
 p=VD/f'{OBJ}.{v}.png'; donor='right' if v=='front' else 'left' if v=='rear' else None
 if donor:
  if sha(p) not in (h,sha(VD/f'{OBJ}.{donor}.png')):raise SystemExit(f'hash guard {v}')
 elif sha(p)!=h:raise SystemExit(f'hash guard {v}')
for target,donor in [('front','right'),('rear','left')]:
 dst=VD/f'{OBJ}.{target}.png';src=VD/f'{OBJ}.{donor}.png'
 if sha(dst)==sha(src):continue
 shutil.copy2(dst,raw/f'{OBJ}.{target}.before-edge-alias.png');shutil.copyfile(src,dst);mp=VD/f'{OBJ}.{target}.json';md=json.loads(mp.read_text());im=Image.open(dst).convert('RGBA');md['image']={'path':f'reusable/views-additional/{OBJ}.{target}.png','width':256,'height':256,'sha256':sha(dst),'rgba_sha256':rgba_sha(im)};md['provenance'].setdefault('repair_steps',[]).append({'operation':'same-object symmetric horizontal floor-edge alias','donor_view':donor,'donor_path':f'reusable/views-additional/{OBJ}.{donor}.png','donor_sha256':sha(src),'reason':'Uniform thin marble slab boundary profile is symmetric under axis rotation.'});md['provenance']['notes']='Front/rear edge profiles are symmetry-derived from accepted same-object right/left profiles; canonical source retained.';mp.write_text(json.dumps(md,indent=2)+'\n')
proof=proofs[OBJ];source=PACK/proof['source_path'];ok=proof['status']=='pass' and sha(source)==proof['source_sha256']
if ok:
 for v,h in proof['image_hashes'].items():
  if sha(VD/f'{OBJ}.{v}.png')!=h:ok=False;break
status='pass' if ok else 'pending-review'
for v in ['front','top','right','left','bottom','rear']:
 mp=VD/f'{OBJ}.{v}.json';md=json.loads(mp.read_text());md['geometry_qa']=status;mp.write_text(json.dumps(md,indent=2)+'\n')
 for a in idx['assets']:
  if a.get('id')==md['id']:a.clear();a.update(md);break
g=next(x for x in idx['view_sets'] if x['object_id']==OBJ);g['complete']=ok;g['geometry_qa']=status;g['notes']='Whole source+six root PASS restored from pinned current-hash proof.' if ok else 'Awaiting independent current-hash review.';idxp.write_text(json.dumps(idx,indent=2)+'\n')
