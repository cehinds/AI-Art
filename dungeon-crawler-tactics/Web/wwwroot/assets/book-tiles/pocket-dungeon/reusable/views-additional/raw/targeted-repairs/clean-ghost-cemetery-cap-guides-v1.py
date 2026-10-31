#!/usr/bin/env python3
"""Remove only isolated black/gray guide islands from the two mausoleum caps."""
from pathlib import Path
import json,hashlib,struct
import numpy as np
from PIL import Image
from scipy import ndimage
PACK=Path(__file__).resolve().parents[4];VD=PACK/'reusable/views-additional';IDX=VD/'set-index.json';COR=VD/'corrections.json'
spec={
 'ghost-cemetery-white-mausoleum-masonry-north-cap':{'front':[[51,81,202,84]],'top':[[20,57,23,94],[20,142,23,187]],'right':[[61,78,64,131]],'bottom':[[48,52,101,55],[176,52,197,55],[22,71,25,229]],'rear':[[52,78,200,81]]},
 'ghost-cemetery-white-mausoleum-masonry-west-cap':{'left':[[79,51,177,54],[192,210,194,222]],'bottom':[[27,87,30,215]],'rear':[[173,77,189,80]]}
}
ledger=json.loads(Path('/workspace/scratch/view-qa-root.json').read_text())['reviewed'];idx=json.loads(IDX.read_text());ops=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rsha(im):return hashlib.sha256(struct.pack('>II',*im.size)+im.convert('RGBA').tobytes()).hexdigest()
for oid,views in spec.items():
 r=ledger['book-tiles/pocket-dungeon::'+oid]
 if r['status']!='needs-correction' or set(r['affected_views'])!={'front','top','right','left','bottom','rear'}:raise SystemExit(f'root scope changed: {oid}')
 if sha(r['source'])!=r['source_sha256']:raise SystemExit(f'source changed: {oid}')
 for v,path in r['view_paths'].items():
  if sha(path)!=r['image_hashes'][v]:raise SystemExit(f'current six hash differs: {oid}.{v}')
 for view,bboxes in views.items():
  p=VD/f'{oid}.{view}.png';mp=VD/f'{oid}.{view}.json';md=json.loads(mp.read_text());im=Image.open(p).convert('RGBA');arr=np.asarray(im).copy();labels,n=ndimage.label(arr[:,:,3]>=245,structure=np.ones((3,3),dtype=np.uint8));
  for box in bboxes:
   hits=[]
   for i,sl in enumerate(ndimage.find_objects(labels),1):
    if sl is not None and [sl[1].start,sl[0].start,sl[1].stop,sl[0].stop]==box:hits.append(i)
   if len(hits)!=1:raise SystemExit(f'{oid}.{view}: guide component {box} match count={len(hits)}')
   arr[:,:,3][labels==hits[0]]=0
  before=r['image_hashes'][view];out=Image.fromarray(arr,'RGBA');out.save(p,optimize=True);after=sha(p)
  op={'type':'remove-components-bbox','object_id':oid,'view':view,'bboxes':bboxes,'before_sha256':before,'after_sha256':after,'reason':'Remove only detached black/gray horizontal or vertical atlas-guide fragments outside the cap silhouette, root-flagged; preserve the source-matched stone and moss.'};ops.append(op)
  md.setdefault('provenance_history',[]).append(md.get('provenance',{}));md['provenance']['cleanup']={'method':'remove-components-bbox','bboxes':bboxes,'reason':op['reason']};md['provenance']['notes']=op['reason'];md['geometry_qa']='pending-review';md['image'].update({'sha256':after,'rgba_sha256':rsha(out)});mp.write_text(json.dumps(md,indent=2)+'\n')
  for a in idx['assets']:
   if a['id']==md['id']:a.clear();a.update(md);break
 g=next(x for x in idx['view_sets'] if x['object_id']==oid);g['complete']=False;g['geometry_qa']='pending-review';g['notes']='Only detached guide islands outside the six silhouettes were removed; pending independent current-hash review.'
spc=json.loads(COR.read_text());spc['operations'].extend(ops);COR.write_text(json.dumps(spc,indent=2)+'\n');IDX.write_text(json.dumps(idx,indent=2)+'\n');print(json.dumps(ops,indent=2))
