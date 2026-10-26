#!/usr/bin/env python3
"""Remove only the root-flagged top guide dashes from River Palace NE wall views."""
from pathlib import Path
import json,hashlib,struct
import numpy as np
from PIL import Image
from scipy import ndimage
PACK=Path(__file__).resolve().parents[4];VD=PACK/'reusable/views-additional';OID='hunting-river-river-palace-masonry-wall-northeast';views={'front':[103,28,153,29],'rear':[106,28,153,29]}
r=json.loads(Path('/workspace/scratch/view-qa-root.json').read_text())['reviewed']['book-tiles/pocket-dungeon::'+OID]
if r['status']!='needs-correction' or set(r['affected_views'])!={'front','rear'}:raise SystemExit('root QA scope changed')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rsha(im):return hashlib.sha256(struct.pack('>II',*im.size)+im.convert('RGBA').tobytes()).hexdigest()
idxp=VD/'set-index.json';idx=json.loads(idxp.read_text());ops=[]
for view,box in views.items():
 p=VD/f'{OID}.{view}.png';mp=VD/f'{OID}.{view}.json';md=json.loads(mp.read_text())
 if sha(p)!=r['image_hashes'][view]:raise SystemExit('current bytes differ from root capture')
 im=Image.open(p).convert('RGBA');arr=np.asarray(im).copy();labels,n=ndimage.label(arr[:,:,3]>=245,structure=np.ones((3,3),dtype=np.uint8));x0,y0,x1,y1=box
 hits=[]
 for i,sl in enumerate(ndimage.find_objects(labels),1):
  if sl is not None and [sl[1].start,sl[0].start,sl[1].stop,sl[0].stop]==box:hits.append(i)
 if len(hits)!=1:raise SystemExit(f'{view}: expected exact detached dash component {box}, got {len(hits)}')
 before=sha(p);arr[:,:,3][labels==hits[0]]=0;out=Image.fromarray(arr,'RGBA');out.save(p,optimize=True);after=sha(p)
 op={'type':'remove-component-bbox','object_id':OID,'view':view,'bbox':box,'before_sha256':before,'after_sha256':after,'reason':'Remove only the detached black horizontal guide dash above the accepted NE wall elevation, root-flagged; preserve all wall pixels and other isolated content.'};ops.append(op)
 md.setdefault('provenance_history',[]).append(md.get('provenance',{}));md.setdefault('provenance',{})['cleanup']={'method':'remove-component-bbox','bbox':box,'reason':op['reason']};md['provenance']['notes']=op['reason'];md['geometry_qa']='pending-review';md['image'].update({'sha256':after,'rgba_sha256':rsha(out)});mp.write_text(json.dumps(md,indent=2)+'\n')
 for a in idx['assets']:
  if a['id']==md['id']:a.clear();a.update(md);break
cp=VD/'corrections.json';spec=json.loads(cp.read_text());spec['operations'].extend(ops);cp.write_text(json.dumps(spec,indent=2)+'\n');g=next(x for x in idx['view_sets'] if x['object_id']==OID);g['complete']=False;g['geometry_qa']='pending-review';g['notes']='Only the detached top guide dashes in FRONT/REAR were removed; pending independent current-hash review.';idxp.write_text(json.dumps(idx,indent=2)+'\n');print(json.dumps(ops,indent=2))
