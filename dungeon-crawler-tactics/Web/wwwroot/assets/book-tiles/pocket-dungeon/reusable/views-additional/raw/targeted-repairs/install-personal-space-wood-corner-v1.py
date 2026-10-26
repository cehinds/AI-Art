#!/usr/bin/env python3
"""Install source-faithful orthographic projections from the retained wood-corner atlas."""
from pathlib import Path
import hashlib,json,struct
import numpy as np
from PIL import Image
from scipy import ndimage
PACK=Path(__file__).resolve().parents[4];VD=PACK/'reusable/views-additional';OBJ='personal-space-warm-wood-plank-corner-transition';ATLAS='reusable/views-additional/raw/atlases/personal-space-wood-corner-edge-v1.png';REQ='reusable/views-additional/raw/requests/personal-space-wood-corner-edge-v1.json'
EXPECTED={'front':'46bcb1ceb97b30cf4748b96d607d2083c4e6538e8a6bb5174db69c32a21aa25e','top':'64e2708ab8d29478c38b4ed8a26bf4c761185ad3a94fc09258a325b039a17dfe','right':'202c55dc8de3bebfde6e939af37f4fb9ccc1a1a3839611af51929ebbc2645f24','left':'b3ca67bbe7590b688db97ebebcd5047f382d109c9b290b211f82fd7ca4eb97c5','bottom':'92eb06affb2518f7e67db2d14b967a6779c45ae9c74f6d31b8fa4e27c1a81619','rear':'00b4aff70387dd66bf340a374d8de58af7ab6d1e3489d7fe5763fc56618a9877'}
COLS={'front':0,'top':1,'right':2,'left':3,'bottom':4,'rear':5};INSTALL=['front','top','bottom','rear']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rgba_sha(im):return hashlib.sha256(struct.pack('>II',*im.size)+im.convert('RGBA').tobytes()).hexdigest()
source=PACK/'personal-space/components'/f'{OBJ}.png'; source_hash=sha(source); atlas_path=PACK/ATLAS; atlas=Image.open(atlas_path).convert('RGBA')
if atlas.size!=(2172,724):raise SystemExit(f'unexpected atlas size {atlas.size}')
idxp=VD/'set-index.json';idx=json.loads(idxp.read_text());atlas_hash=sha(atlas_path)
# Accept either the original reviewed bytes or this exact already-installed atlas result for replay.
for v,h in EXPECTED.items():
 p=VD/f'{OBJ}.{v}.png';md=json.loads((VD/f'{OBJ}.{v}.json').read_text());
 if v in INSTALL and md.get('provenance',{}).get('generated_atlas_sha256')==atlas_hash:
  if sha(p)!=md['image']['sha256']:raise SystemExit(f'installed byte mismatch {v}')
 elif sha(p)!=h:raise SystemExit(f'root current-hash guard failed: {v}')
# Whole-atlas connected components; assign the full body by its centroid to six logical view columns.
arr=np.asarray(atlas); labels,n=ndimage.label(arr[:,:,3]>=245,structure=np.ones((3,3),dtype=np.uint8)); comps=[]
for lab,sl in enumerate(ndimage.find_objects(labels),1):
 if sl is None:continue
 area=int((labels[sl]==lab).sum())
 if area<4:continue
 cy,cx=ndimage.center_of_mass(labels==lab);bbox=[sl[1].start,sl[0].start,sl[1].stop,sl[0].stop]
 comps.append({'label':lab,'area':area,'centroid':[float(cx),float(cy)],'bbox':bbox})
centers=[181+i*362 for i in range(6)];assigned={}
for v,col in COLS.items():
 candidates=sorted(comps,key=lambda c:abs(c['centroid'][0]-centers[col]))
 c=candidates[0]
 if abs(c['centroid'][0]-centers[col])>100:raise SystemExit(f'no confident component for {v}: {c}')
 if c['label'] in assigned.values():raise SystemExit('same component assigned to multiple views')
 assigned[v]=c['label']
# Shared isotropic scale is calibrated to accepted 210px edge width. No atlas cell clipping.
max_w=max(assigned[v] and next(c['bbox'][2]-c['bbox'][0] for c in comps if c['label']==assigned[v]) for v in INSTALL);scale=210/max_w
for v in INSTALL:
 c=next(c for c in comps if c['label']==assigned[v]);x0,y0,x1,y1=c['bbox']
 if x0<=0 or y0<=0 or x1>=atlas.width or y1>=atlas.height:raise SystemExit(f'global object touches atlas boundary: {v} {c}')
 crop=atlas.crop((x0,y0,x1,y1));ca=np.asarray(crop).copy();ca[:,:,3]=np.where(labels[y0:y1,x0:x1]==c['label'],255,0).astype(np.uint8);crop=Image.fromarray(ca,'RGBA')
 size=(round(crop.width*scale),round(crop.height*scale));crop=crop.resize(size,Image.Resampling.NEAREST);canvas=Image.new('RGBA',(256,256),(0,0,0,0));canvas.alpha_composite(crop,(128-size[0]//2,248-size[1]));dst=VD/f'{OBJ}.{v}.png';canvas.save(dst,optimize=True);mp=VD/f'{OBJ}.{v}.json';md=json.loads(mp.read_text());md['image']={'path':f'reusable/views-additional/{OBJ}.{v}.png','width':256,'height':256,'sha256':sha(dst),'rgba_sha256':rgba_sha(canvas)};md['geometry_qa']='pending-review';md['provenance']['generated_atlas']=ATLAS;md['provenance']['generated_atlas_sha256']=atlas_hash;md['provenance']['generation_request']=REQ;md['provenance']['source_sha256']=source_hash;md['provenance']['normalization']={'alpha_threshold':245,'minimum_component_area':4,'component_policy':'whole-atlas connected components assigned by centroid to six view columns; preserve entire bounds; no fixed-cell clipping','component_group':[c],'shared_scale':scale,'render_size':list(size),'canvas':[256,256],'resampling':'NEAREST','anchor_px':[128,248]};md['provenance']['notes']='Generated axis-aligned orthographic projection from source-faithful six-view atlas; 210px common scale matched to accepted side profiles. Hidden underside inferred, not recovered pixels.';mp.write_text(json.dumps(md,indent=2)+'\n')
 for a in idx['assets']:
  if a.get('id')==md['id']:a.clear();a.update(md);break
idxp.write_text(json.dumps(idx,indent=2)+'\n');g=next(x for x in idx['view_sets'] if x['object_id']==OBJ);g['complete']=False;g['geometry_qa']='pending-review';g['notes']='FRONT/TOP/BOTTOM/REAR regenerated from source-faithful atlas; accepted RIGHT/LEFT preserved. Awaiting independent review.';idxp.write_text(json.dumps(idx,indent=2)+'\n')
print(json.dumps({'atlas_sha256':atlas_hash,'source_sha256':source_hash,'scale':scale,'assigned_components':{v:next(c for c in comps if c['label']==assigned[v]) for v in INSTALL},'view_hashes':{v:sha(VD/f'{OBJ}.{v}.png') for v in ['front','top','right','left','bottom','rear']}},indent=2))
