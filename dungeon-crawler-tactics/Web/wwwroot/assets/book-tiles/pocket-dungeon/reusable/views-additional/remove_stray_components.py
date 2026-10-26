#!/usr/bin/env python3
"""Drop tiny disconnected atlas spill islands for explicitly reviewed floor views."""
from pathlib import Path
from PIL import Image
import hashlib,json,struct,sys
import numpy as np
from scipy import ndimage
BOOK=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
spec=json.loads((OUT/'stray-component-fixes.json').read_text());idxp=OUT/'set-index.json';idx=json.loads(idxp.read_text())
for entry in spec['assets']:
 aid=entry['asset_id'];a=next(x for x in idx['assets'] if x['id']==aid);p=BOOK/a['image']['path'];im=Image.open(p).convert('RGBA');rgba=np.array(im);alpha=rgba[:,:,3];lab,n=ndimage.label(alpha>=245,structure=np.ones((3,3),dtype=np.uint8));counts=np.bincount(lab.ravel());removed=[]
 for ident,area in enumerate(counts[1:],1):
  if area<spec.get('minimum_component_area',100):
   m=lab==ident;removed.append({'area':int(area),'bbox':list(ndimage.find_objects(m.astype(np.uint8))[0][1:]) if False else None});alpha[m]=0
 if not removed:continue
 rgba[:,:,3]=alpha;im=Image.fromarray(rgba,'RGBA');im.save(p);a['image']['sha256']=hashlib.sha256(p.read_bytes()).hexdigest();a['image']['rgba_sha256']=hashlib.sha256(struct.pack('>II',*im.size)+im.tobytes()).hexdigest();a['provenance']['component_cleanup']={'minimum_component_area':spec.get('minimum_component_area',100),'removed_areas':[x['area'] for x in removed],'reason':'isolated border spill confirmed by geometry QA'};a['geometry_qa']='pending-review'
 side=BOOK/a['metadata_path'];side.write_text(json.dumps(a,indent=2)+'\n')
idxp.write_text(json.dumps(idx,indent=2)+'\n');print('cleaned',len(spec['assets']),'target assets')
