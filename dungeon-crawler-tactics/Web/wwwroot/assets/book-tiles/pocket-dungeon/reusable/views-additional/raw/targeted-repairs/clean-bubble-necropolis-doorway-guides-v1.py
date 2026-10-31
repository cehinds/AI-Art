#!/usr/bin/env python3
"""Remove only root-flagged detached guide fragments from three door elevations."""
from pathlib import Path
import json,hashlib,struct,shutil
import numpy as np
from PIL import Image
from scipy import ndimage
PACK=Path(__file__).resolve().parents[4];VD=PACK/'reusable/views-additional';OID='bubble-necropolis-ancient-tomb-masonry-closed-doorway'
ROOT=Path('/workspace/scratch/view-qa-root.json');review=json.loads(ROOT.read_text())['reviewed']['book-tiles/pocket-dungeon::'+OID]
if review['status']!='needs-correction' or set(review.get('affected_views',[]))!={'front','right','left'}:raise SystemExit('root review scope changed')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgba_sha(im):return hashlib.sha256(struct.pack('>II',*im.size)+im.convert('RGBA').tobytes()).hexdigest()
boxes={'front':[[26,203,72,204],[136,247,146,248]],'right':[[36,223,46,224]],'left':[[204,223,212,224],[227,223,234,224]]}
idxp=VD/'set-index.json';idx=json.loads(idxp.read_text());ops=[]
for view,bboxes in boxes.items():
 p=VD/f'{OID}.{view}.png';mp=VD/f'{OID}.{view}.json';md=json.loads(mp.read_text());proof_path=review['view_paths'][view]
 if sha(p)!=review['image_hashes'][view] or sha(proof_path)!=review['image_hashes'][view]:raise SystemExit(f'root/current hash mismatch {view}')
 im=Image.open(p).convert('RGBA');arr=np.asarray(im).copy();labels,n=ndimage.label(arr[:,:,3]>=245,structure=np.ones((3,3),dtype=np.uint8));
 for box in bboxes:
  x0,y0,x1,y1=box;hits=[]
  for lab,sl in enumerate(ndimage.find_objects(labels),1):
   if sl is not None and [sl[1].start,sl[0].start,sl[1].stop,sl[0].stop]==box:hits.append(lab)
  if len(hits)!=1:raise SystemExit(f'{view}: expected one detached component covering {box}, got {len(hits)}')
  arr[:,:,3][labels==hits[0]]=0
 out=Image.fromarray(arr,'RGBA');tmp=p.with_suffix('.tmp.png');out.save(tmp,optimize=True);before=sha(p);after=sha(tmp);tmp.replace(p)
 op={'type':'remove-components-bbox','object_id':OID,'view':view,'bboxes':bboxes,'before_sha256':before,'after_sha256':after,'reason':'Remove only the isolated detached gray guide fragments below/alongside the accepted doorway elevations, as root flagged; preserve the complete door and stonework.'};ops.append(op)
 md.setdefault('provenance_history',[]).append(md.get('provenance',{}));md.setdefault('provenance',{})['cleanup']={'method':'remove-components-bbox','bboxes':bboxes,'reason':op['reason']};md['provenance']['notes']=op['reason'];md['image']={'path':f'reusable/views-additional/{OID}.{view}.png','width':256,'height':256,'sha256':after,'rgba_sha256':rgba_sha(out)};md['geometry_qa']='pending-review';mp.write_text(json.dumps(md,indent=2)+'\n')
 for a in idx['assets']:
  if a['id']==md['id']:a.clear();a.update(md);break
# Append the exact before/after cleanup recipes for future base replay, without running other operations.
cp=VD/'corrections.json';spec=json.loads(cp.read_text());spec['operations'].extend(ops);cp.write_text(json.dumps(spec,indent=2)+'\n')
g=next(x for x in idx['view_sets'] if x['object_id']==OID);g['complete']=False;g['geometry_qa']='pending-review';g['notes']='Only detached guide fragments removed from front/right/left; awaiting independent current source+six review.';idxp.write_text(json.dumps(idx,indent=2)+'\n')
print(json.dumps(ops,indent=2))
