"""Calibrate and extract selected isolated west-wall direction atlases."""
import json, os, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from build_batch import process_view_column
OUT=Path(__file__).resolve().parent
specs=json.loads((OUT/'west-wall-repair-specs.json').read_text())
index=json.loads((OUT/'set-index.json').read_text())
wanted=set(sys.argv[1:])
if not wanted: raise SystemExit('pass one or more west-wall batch ids')
added=[]
for spec in specs:
    if spec['batch_id'] not in wanted: continue
    raw=OUT/spec['raw']; pixels=np.asarray(Image.open(raw).convert('RGBA'))
    h,w=pixels.shape[:2]; labels,_=ndimage.label(pixels[:,:,3]>32); calibration={}
    for row,obj in enumerate(spec['objects']):
        y0,y1=round(row*h/len(spec['objects'])),round((row+1)*h/len(spec['objects']))
        boxes=[]
        for label,sl in enumerate(ndimage.find_objects(labels),1):
            if sl is None: continue
            yy,xx=sl; area=int(np.count_nonzero(labels[sl]==label))
            if area>=24 and y0 <= (yy.start+yy.stop)/2 < y1:
                boxes.append((xx.start,yy.start,xx.stop,yy.stop))
        if not boxes: raise ValueError(f"{spec['batch_id']}: no assigned component for {obj['id']}")
        x0=min(b[0] for b in boxes); yb=min(b[1] for b in boxes)
        x1=max(b[2] for b in boxes); ye=max(b[3] for b in boxes)
        asset=next(a for a in index['assets'] if a['object_id']==obj['id'])
        scale=asset['provenance']['normalization']['scale']
        tw,th=spec['target_size_by_object'][obj['id']]
        calibration[obj['id']]=[tw/((x1-x0)*scale),th/((ye-yb)*scale)]
    correction={**spec,'object_cell_calibration':calibration}
    process_view_column(correction,spec['view'],0,column_count=1)
    added.append(correction)
if wanted != {x['batch_id'] for x in added}:
    raise ValueError(f"missing batch ids: {sorted(wanted-{x['batch_id'] for x in added})}")
path=OUT/'corrections.json';text=path.read_text();corrections=json.loads(text.removesuffix('\\n'))
known={x.get('batch_id') for x in corrections}
corrections += [x for x in added if x['batch_id'] not in known]
tmp=path.with_suffix('.json.tmp');tmp.write_text(json.dumps(corrections,indent=2)+'\n');os.replace(tmp,path)
print('processed',len(added),sorted(wanted))
