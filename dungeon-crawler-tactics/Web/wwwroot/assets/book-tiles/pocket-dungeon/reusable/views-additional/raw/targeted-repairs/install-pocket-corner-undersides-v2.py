#!/usr/bin/env python3
"""Install three full-footprint, source-specific corner-tile undersides."""
from pathlib import Path
import json, hashlib, struct, shutil
import numpy as np
from PIL import Image
from scipy import ndimage
PACK=Path(__file__).resolve().parents[4]
VD=PACK/'reusable/views-additional'; RAW=VD/'raw'
ATLAS=RAW/'atlases/pocket-corner-undersides-v2.png'
ATLAS_SHA=''
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def rgba_sha(im): return hashlib.sha256(struct.pack('>II',*im.size)+im.convert('RGBA').tobytes()).hexdigest()
root=Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/pocket-dungeon')
ledger=json.loads(Path('/workspace/scratch/view-qa-root.json').read_text())['reviewed']
idxp=VD/'set-index.json'; idx=json.loads(idxp.read_text())
atlas=Image.open(ATLAS).convert('RGBA'); arr=np.asarray(atlas)
labels,n=ndimage.label(arr[:,:,3]>=245,structure=np.ones((3,3),dtype=np.uint8))
rows=[
 ('faction-larracos-drained-city-cobblestone-corner-transition',0),
 ('iron-trains-railcar-metal-corner-transition',1),
 ('hunting-zockau-mid-century-street-pavement-corner-transition',2),
]
for oid,row in rows:
 key='book-tiles/pocket-dungeon::'+oid; review=ledger.get(key)
 if not review or review.get('status')!='needs-correction' or review.get('affected_views')!=['BOTTOM']:
  raise SystemExit(f'root QA no longer authorizes BOTTOM-only edit: {oid}')
 g=next(x for x in idx['view_sets'] if x['object_id']==oid)
 asset=next(x for x in idx['assets'] if x['id']==g['views']['bottom'])
 bottom=VD/f'{oid}.bottom.png'; mdp=VD/f'{oid}.bottom.json'; md=json.loads(mdp.read_text())
 # Guard all six live PNGs and canonical source against the latest captured hashes.
 for view,path in review['view_paths'].items():
  if sha(Path(path))!=review['image_hashes'][view]: raise SystemExit(f'changed current {oid}.{view}')
 src=Path(review['source'])
 if sha(src)!=review['source_sha256']: raise SystemExit(f'changed source {oid}')
 # Recover the full row component by its expected row center; never cell-crop.
 candidates=[]
 for lab,sl in enumerate(ndimage.find_objects(labels),1):
  if sl is None: continue
  area=int((labels[sl]==lab).sum())
  if area<1000: continue
  yy,xx=ndimage.center_of_mass(labels==lab)
  candidates.append((abs(yy-(row*724+362)),lab,area,sl))
 dist,lab,area,sl=min(candidates)
 if dist>150: raise SystemExit(f'no centered component in atlas row {row}: {oid}')
 x0,y0,x1,y1=sl[1].start,sl[0].start,sl[1].stop,sl[0].stop
 mask=(labels[y0:y1,x0:x1]==lab)
 body=np.asarray(atlas.crop((x0,y0,x1,y1))).copy(); body[:,:,3]=np.where(mask,255,0).astype(np.uint8); body=Image.fromarray(body,'RGBA')
 # Match the accepted TOP footprint's native alpha bounds using uniform scale.
 top=Image.open(VD/f'{oid}.top.png').convert('RGBA'); top_a=np.asarray(top.getchannel('A')); ys,xs=np.where(top_a>=128)
 target_w=int(xs.max()+1-xs.min()); target_h=int(ys.max()+1-ys.min())
 scale=min(target_w/body.width,target_h/body.height)
 size=(round(body.width*scale),round(body.height*scale)); body=body.resize(size,Image.Resampling.NEAREST)
 canvas=Image.new('RGBA',(256,256),(0,0,0,0)); canvas.alpha_composite(body,(128-size[0]//2,248-size[1]))
 snap=RAW/'targeted-repairs'/f'{oid}.bottom.before-corner-underside-v2.png'
 if not snap.exists(): shutil.copy2(bottom,snap)
 canvas.save(bottom,optimize=True)
 md['image']={'path':f'reusable/views-additional/{oid}.bottom.png','width':256,'height':256,'sha256':sha(bottom),'rgba_sha256':rgba_sha(canvas)}
 md['geometry_qa']='pending-review'
 md['provenance']['generated_atlas']='reusable/views-additional/raw/atlases/pocket-corner-undersides-v2.png'
 md['provenance']['generated_atlas_sha256']=sha(ATLAS)
 md['provenance']['generation_request']='reusable/views-additional/raw/requests/pocket-corner-undersides-v1.json'
 md['provenance']['source_sha256']=review['source_sha256']
 md['provenance']['normalization']={'alpha_threshold':245,'component_policy':'whole-atlas connected component selected by row centroid; full component bounds retained; no fixed-cell clipping','component':[lab,area,[x0,y0,x1,y1]],'matched_reference':'accepted TOP footprint','uniform_scale':scale,'render_size':list(size),'canvas':[256,256],'resampling':'NEAREST','anchor_px':[128,248]}
 md['provenance']['notes']='Inferred full-footprint orthographic underside plane, guided by accepted natural stone-floor underside; source-specific material retained, no top-only vegetation or surface markings.'
 mdp.write_text(json.dumps(md,indent=2)+'\n')
 for a in idx['assets']:
  if a.get('id')==md['id']: a.clear(); a.update(md); break
 g['complete']=False; g['geometry_qa']='pending-review'; g['notes']='BOTTOM-only full-square undersides installed; other five current views preserved pending independent source+six review.'
idxp.write_text(json.dumps(idx,indent=2)+'\n')
print(json.dumps([{'object_id':oid,'bottom_sha256':sha(VD/f'{oid}.bottom.png')} for oid,_ in rows],indent=2))
