#!/usr/bin/env python3
"""Alias held square cap elevations from the accepted tall-post projections."""
from pathlib import Path
import hashlib,json,struct,shutil
from PIL import Image
PACK=Path(__file__).resolve().parents[4];VD=PACK/'reusable/views-additional'
EXPECTED={
'clubs-guilds-dark-polished-club-panel-endcap-northwest':{'front': '2e8c62b2f128bf10ff4c7d1531913e3647da99c558068305d272478c2d99d04e', 'top': '6a372d7e0a450590bb4bf54fc13b0ae0de53b2e8219962987f1bfe47f957409f', 'right': '8122ab1b3693c451b7af99421d1b88293323cbd3b52d1dcb18421a9ec1ab4cae', 'left': 'c65bd3609f4d278e702b2160cd52162461a837cde6e0c1954a049c9dae09da11', 'bottom': '9e78f7ec725b5cee842352ff0778249cc18b0a8d17e66623a7d0ad2af5d9b4fb', 'rear': '3e88477a01071896504db52a0ed51e50c9b09bd049022854f4025e20e39cb66b'},
'clubs-guilds-dark-polished-club-panel-endcap-northeast':{'front': 'd78d4810cbff50e3d97d325e74817cda4b1595c285364655be088248cb56b268', 'top': 'b7f1f2298c1d9d886be5784c77b08993dcf974b44eafd1cb84e35e4e05588e16', 'right': '6bcca11810aa342d8a6281f9e6fe3006a9c29a43fef1e67cf931106da42d245c', 'left': 'ace63c865a8ea7d090dd08be0b634cd191ac296017f617d70f563eec0fc19fa1', 'bottom': 'ce1d8768ce6dbd0c2fb52ce19f5fa38749ebdb1722bdb7a0d139988cb4ef8e3c', 'rear': 'd886e1dbd6a144d01e7606c8e14a2775d78bfe1ffc8a70284b99c91db69bc0e6'}}
PLAN_FINAL={
'clubs-guilds-dark-polished-club-panel-endcap-northwest':{'top':'cb0ef65bdbadca3304b5b7d56901086d38a7759683860735e882c356a83cd863','bottom':'36a026601f54845d979fa7517de50833dcd73a10bd4453751db39d991011cf34'},
'clubs-guilds-dark-polished-club-panel-endcap-northeast':{'top':'008fab86108dd3b0a666c4b387d27bd13d02a9480cdb76f5dff69a4fd8e013c8','bottom':'eef6ee8786015582b815b4b71bb3a157e43412c0c5b251d087e6cb44d64af4e3'}}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rgba_sha(im):return hashlib.sha256(struct.pack('>II',*im.size)+im.convert('RGBA').tobytes()).hexdigest()
idxp=VD/'set-index.json';idx=json.loads(idxp.read_text());raw=VD/'raw/targeted-repairs';raw.mkdir(parents=True,exist_ok=True)
for obj,hs in EXPECTED.items():
 for v,h in hs.items():
  p=VD/f'{obj}.{v}.png'
  if not h: continue
  if v in ('front','rear'):
   donor='right' if v=='front' else 'left'; donor_sha=sha(VD/f'{obj}.{donor}.png')
   if sha(p) not in (h,donor_sha): raise SystemExit(f'current-hash guard failed: {obj}.{v}')
  elif sha(p)!=h and sha(p)!=PLAN_FINAL.get(obj,{}).get(v): raise SystemExit(f'current-hash guard failed: {obj}.{v}')
 for target,donor in [('front','right'),('rear','left')]:
  src=VD/f'{obj}.{donor}.png';dst=VD/f'{obj}.{target}.png'
  if sha(dst)==sha(src): continue
  shutil.copy2(dst,raw/f'{obj}.{target}.before-post-alias.png');shutil.copyfile(src,dst)
  mp=VD/f'{obj}.{target}.json';md=json.loads(mp.read_text());im=Image.open(dst).convert('RGBA');md['image']={'path':f'reusable/views-additional/{obj}.{target}.png','width':256,'height':256,'sha256':sha(dst),'rgba_sha256':rgba_sha(im)};md['geometry_qa']='pending-review';md['provenance'].setdefault('repair_steps',[]).append({'operation':'same-object orthogonal post-view alias','donor_view':donor,'donor_path':f'reusable/views-additional/{obj}.{donor}.png','donor_sha256':sha(src),'reason':'Source has a square cap plan with symmetric end posts; front/rear are the same physical post projections as the already accepted right/left views.'});md['provenance']['notes']='Inferred orthographic projection; front/rear use matching same-object accepted end-post views; canonical source retained.';mp.write_text(json.dumps(md,indent=2)+'\n')
  for a in idx['assets']:
   if a.get('id')==md['id']:a.clear();a.update(md);break
 # Plans are uniformly scaled to the measured width of the accepted end-post cap cross-section.
 front=Image.open(VD/f'{obj}.front.png').convert('RGBA'); fb=front.getchannel('A').point(lambda x:255 if x>=245 else 0).getbbox(); target_w=fb[2]-fb[0]
 for view in ('top','bottom'):
  dst=VD/f'{obj}.{view}.png'; before=sha(dst)
  if PLAN_FINAL[obj][view] and before==PLAN_FINAL[obj][view]: continue
  if before!=hs[view]: raise SystemExit(f'plan-scale hash guard failed: {obj}.{view}')
  shutil.copy2(dst,raw/f'{obj}.{view}.before-plan-scale.png'); im=Image.open(dst).convert('RGBA'); mask=im.getchannel('A').point(lambda x:255 if x>=245 else 0); bb=mask.getbbox()
  if not bb: raise SystemExit(f'empty cap plan {obj}.{view}')
  crop=im.crop(bb); scale=target_w/crop.width; size=(target_w,round(crop.height*scale)); crop=crop.resize(size,Image.Resampling.NEAREST); canvas=Image.new('RGBA',(256,256),(0,0,0,0)); canvas.alpha_composite(crop,(128-size[0]//2,248-size[1])); canvas.save(dst,optimize=True)
  mp=VD/f'{obj}.{view}.json';md=json.loads(mp.read_text());md['image']={'path':f'reusable/views-additional/{obj}.{view}.png','width':256,'height':256,'sha256':sha(dst),'rgba_sha256':rgba_sha(canvas)};md['geometry_qa']='pending-review';md['provenance'].setdefault('repair_steps',[]).append({'operation':'uniform nearest-neighbor scale cap plan to accepted end-post width','reference_view':'front','reference_bbox_xyxy':list(fb),'source_bbox_xyxy':list(bb),'target_width_px':target_w,'scale':scale,'render_size':list(size),'anchor_px':[128,248]});mp.write_text(json.dumps(md,indent=2)+'\n')
  for a in idx['assets']:
   if a.get('id')==md['id']:a.clear();a.update(md);break
 g=next(x for x in idx['view_sets'] if x['object_id']==obj);g['complete']=False;g['geometry_qa']='pending-review';g['notes']='FRONT/REAR alias accepted end-post projections; TOP/BOTTOM uniformly scaled to the same cap footprint width. Awaiting independent review.'
proofs=json.loads((raw/'reviewed-pass-proofs-pocket-scenery.json').read_text())
for obj in EXPECTED:
 proof=proofs.get(obj,{});sourcep=PACK/proof.get('source_path','');ok=proof.get('status')=='pass' and sourcep.is_file() and sha(sourcep)==proof.get('source_sha256')
 if ok:
  for view,h in proof.get('image_hashes',{}).items():
   if sha(VD/f'{obj}.{view}.png')!=h:ok=False;break
 status='pass' if ok else 'pending-review'
 for view in ('front','top','right','left','bottom','rear'):
  mp=VD/f'{obj}.{view}.json';md=json.loads(mp.read_text());md['geometry_qa']=status;mp.write_text(json.dumps(md,indent=2)+'\n')
  for a in idx['assets']:
   if a.get('id')==md['id']:a.clear();a.update(md);break
 g=next(x for x in idx['view_sets'] if x['object_id']==obj);g['complete']=ok;g['geometry_qa']=status;g['notes']='Whole source+six root PASS restored from pinned current-hash proof.' if ok else 'Awaiting independent current-hash review.'
idxp.write_text(json.dumps(idx,indent=2)+'\n')
print(json.dumps({obj:{v:sha(VD/f'{obj}.{v}.png') for v in ['front','top','right','left','bottom','rear']} for obj in EXPECTED},indent=2))
