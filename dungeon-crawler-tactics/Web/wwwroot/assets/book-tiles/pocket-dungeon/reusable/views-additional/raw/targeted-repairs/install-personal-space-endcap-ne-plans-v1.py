#!/usr/bin/env python3
"""Install only the two source-faithful rectangular plans for the Personal Space NE endcap."""
from pathlib import Path
import hashlib,json,struct,shutil
import numpy as np
from PIL import Image
from scipy import ndimage
PACK=Path(__file__).resolve().parents[4];VD=PACK/'reusable/views-additional';OBJ='personal-space-plaster-and-timber-endcap-northeast';ATLAS='reusable/views-additional/raw/atlases/personal-space-endcap-ne-plans-v1.png';REQ='reusable/views-additional/raw/requests/personal-space-endcap-ne-plans-v1.json'
EXPECTED={'front':'02060034e27575d46aac19774b1574246e35ba56f704901383b04f7c2dac000a','top':'a8fe74e4bbc9ca415c1027a583a7a55c0ff76a241d4c05532d427c452d1cfc49','right':'1369f503e0ae38e97e66e893275c8d9113065ee086a56f827be104c6f617135d','left':'728cd7e98dae9deee242c5769519800cb9a3f356e611fea51ee07763d9c59b36','bottom':'4e9febf35f63f5bb010e9b11e34766cde12191179c1b39ca5e5a08a9b87bd2aa','rear':'4ed6b8677b41840d3b112ec0472bd39d1dd7291cffe9b21c40cef252a66a6726'}
COL={'top':1,'bottom':4};SCALE=0.5
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rgba_sha(im):return hashlib.sha256(struct.pack('>II',*im.size)+im.convert('RGBA').tobytes()).hexdigest()
atlas_path=PACK/ATLAS;atlas=Image.open(atlas_path).convert('RGBA');
if atlas.size!=(2170,725):raise SystemExit(f'unexpected atlas dimensions {atlas.size}')
idxp=VD/'set-index.json';idx=json.loads(idxp.read_text());source=PACK/'personal-space/components'/f'{OBJ}.png';source_hash=sha(source);atlas_hash=sha(atlas_path)
for v,h in EXPECTED.items():
 f=VD/f'{OBJ}.{v}.png';md=json.loads((VD/f'{OBJ}.{v}.json').read_text())
 if v in COL and md.get('provenance',{}).get('generated_atlas_sha256')==atlas_hash:
  if sha(f)!=md['image']['sha256']:raise SystemExit(f'installed bytes changed: {v}')
 elif sha(f)!=h:raise SystemExit(f'current root hash guard failed: {v}')
# Find components globally and group by centroid, retaining their entire bounds across cell borders.
a=np.asarray(atlas);labels,n=ndimage.label(a[:,:,3]>=245,structure=np.ones((3,3),dtype=np.uint8));comps=[]
for lab,sl in enumerate(ndimage.find_objects(labels),1):
 if sl is None:continue
 area=int((labels[sl]==lab).sum())
 if area<4:continue
 cy,cx=ndimage.center_of_mass(labels==lab);comps.append({'label':lab,'area':area,'centroid':[float(cx),float(cy)],'bbox':[sl[1].start,sl[0].start,sl[1].stop,sl[0].stop]})
assigned={}
for v,col in COL.items():
 center=180.8333333333+362*col;c=min(comps,key=lambda x:abs(x['centroid'][0]-center))
 if abs(c['centroid'][0]-center)>100:raise SystemExit(f'no component for {v}: {c}')
 assigned[v]=c
for v,c in assigned.items():
 x0,y0,x1,y1=c['bbox']
 if x0==0 or y0==0 or x1>=atlas.width or y1>=atlas.height:raise SystemExit(f'component touches atlas outer boundary: {v} {c}')
 body=atlas.crop((x0,y0,x1,y1));ba=np.asarray(body).copy();ba[:,:,3]=np.where(labels[y0:y1,x0:x1]==c['label'],255,0).astype(np.uint8);body=Image.fromarray(ba,'RGBA');size=(round(body.width*SCALE),round(body.height*SCALE));body=body.resize(size,Image.Resampling.NEAREST);canvas=Image.new('RGBA',(256,256),(0,0,0,0));canvas.alpha_composite(body,(128-size[0]//2,248-size[1]));dst=VD/f'{OBJ}.{v}.png';snap=VD/'raw/targeted-repairs'/f'{OBJ}.{v}.before-plans-v1.png';snap.parent.mkdir(parents=True,exist_ok=True)
 if not snap.exists():shutil.copy2(dst,snap)
 canvas.save(dst,optimize=True);mp=VD/f'{OBJ}.{v}.json';md=json.loads(mp.read_text());md['image']={'path':f'reusable/views-additional/{OBJ}.{v}.png','width':256,'height':256,'sha256':sha(dst),'rgba_sha256':rgba_sha(canvas)};md['geometry_qa']='pending-review';md['provenance']['generated_atlas']=ATLAS;md['provenance']['generated_atlas_sha256']=atlas_hash;md['provenance']['generation_request']=REQ;md['provenance']['source_sha256']=source_hash;md['provenance']['normalization']={'alpha_threshold':245,'minimum_component_area':4,'component_policy':'whole-atlas connected components assigned by nearest column centroid; full object bounds retained; no fixed-cell clipping','component_group':[c],'shared_scale':SCALE,'render_size':list(size),'canvas':[256,256],'resampling':'NEAREST','anchor_px':[128,248]};md['provenance']['notes']='Inferred axis-aligned orthographic compact 1-by-2 Y footprint cap plan; source-specific cream plaster and timber retained. Not recovered pixels.';mp.write_text(json.dumps(md,indent=2)+'\n')
 for asset in idx['assets']:
  if asset.get('id')==md['id']:asset.clear();asset.update(md);break
g=next(x for x in idx['view_sets'] if x['object_id']==OBJ);g['complete']=False;g['geometry_qa']='pending-review';g['notes']='TOP/BOTTOM regenerated as compact rectangular 1-by-2 Y cap/underside footprints; four accepted elevations preserved pending review.';idxp.write_text(json.dumps(idx,indent=2)+'\n')
print(json.dumps({'atlas_sha256':atlas_hash,'source_sha256':source_hash,'scale':SCALE,'assigned':assigned,'view_hashes':{v:sha(VD/f'{OBJ}.{v}.png') for v in ['front','top','right','left','bottom','rear']}},indent=2))
