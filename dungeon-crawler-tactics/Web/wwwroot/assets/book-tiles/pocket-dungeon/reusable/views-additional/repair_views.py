#!/usr/bin/env python3
"""Apply retained view-cell repairs offline, preserving full connected-component bounds."""
from pathlib import Path
from PIL import Image
import numpy as np
from scipy import ndimage
import hashlib,json,struct,sys,shutil
BOOK=Path(__file__).resolve().parents[2]
ATLAS=Path(sys.argv[1]);OUT=Path(__file__).resolve().parent;RELP=Path(sys.argv[2]);ROWS=json.loads(Path(sys.argv[3]).read_text())
raw=OUT/'raw'/'atlases'/RELP.name;raw.parent.mkdir(parents=True,exist_ok=True)
if ATLAS.resolve()!=raw.resolve():shutil.copy2(ATLAS,raw)
rawsha=hashlib.sha256(raw.read_bytes()).hexdigest();im=Image.open(raw).convert('RGBA');idxp=OUT/'set-index.json';idx=json.loads(idxp.read_text())
NROWS=max(max(r['row'] for r in ROWS)+1,max((r.get('atlas_rows',0) for r in ROWS),default=0));cols=max(r.get('columns',6) for r in ROWS);cellw=im.width/cols;cellh=im.height/NROWS
mask=np.asarray(im.getchannel('A'))>=245;labels,n=ndimage.label(mask,structure=np.ones((3,3),dtype=np.uint8));counts=np.bincount(labels.ravel());centers=ndimage.center_of_mass(mask,labels,range(1,n+1));boxes=ndimage.find_objects(labels)
groups=[[[] for _ in range(cols)] for _ in range(NROWS)]
for lab,area in enumerate(counts[1:],1):
 if area<4:continue
 cy,cx=centers[lab-1];ri=int(np.argmin(np.abs((np.arange(NROWS)+.5)*cellh-cy)));ci=int(np.argmin(np.abs((np.arange(cols)+.5)*cellw-cx)));sl=boxes[lab-1]
 if sl is None:continue
 groups[ri][ci].append((lab,(sl[1].start,sl[0].start,sl[1].stop,sl[0].stop)))
for row in ROWS:
 oid=row['object_id'];ri=row['row'];ci=row.get('column',4);view=row.get('view','bottom');members=groups[ri][ci]
 if not members:raise SystemExit(f'empty repair cell {oid} {view}')
 if row.get('largest_component_only'):
  members=[max(members,key=lambda item: next((counts[lab] for lab,_ in members if lab==item[0]),0))]
 x0=min(b[0] for _,b in members);y0=min(b[1] for _,b in members);x1=max(b[2] for _,b in members);y1=max(b[3] for _,b in members)
 crop=im.crop((x0,y0,x1,y1));local=labels[y0:y1,x0:x1];keep=np.isin(local,[lab for lab,_ in members]);crop.putalpha(Image.fromarray((keep*255).astype(np.uint8)))
 meta_path=OUT/f'{oid}.{view}.json';meta=json.loads(meta_path.read_text());norm=meta['provenance']['normalization'];shared_scale=norm['shared_scale']
 calibration_view=row.get('calibrate_to_view','top' if row.get('calibrate_to_top') else None)
 if row.get('target_max_px'):
  scale=row['target_max_px']/max(crop.size)
 elif calibration_view:
  calibration=json.loads((OUT/f'{oid}.{calibration_view}.json').read_text());target=max(calibration['provenance']['normalization']['render_size']);scale=target/max(crop.size)
 else:scale=shared_scale
 size=[max(1,round(v*scale)) for v in crop.size]
 if max(size)>256:raise SystemExit(f'repair would clip {oid}.{view}: size {size}; adjust calibration')
 frame=Image.new('RGBA',(256,256),(0,0,0,0));frame.alpha_composite(crop.resize(size,Image.Resampling.NEAREST),((256-size[0])//2,248-size[1]))
 png=OUT/f'{oid}.{view}.png';frame.save(png)
 meta['image']['sha256']=hashlib.sha256(png.read_bytes()).hexdigest();meta['image']['rgba_sha256']=hashlib.sha256(struct.pack('>II',*frame.size)+frame.tobytes()).hexdigest()
 meta['provenance']['repair_atlas']=raw.relative_to(BOOK).as_posix();meta['provenance']['repair_atlas_sha256']=rawsha
 if len(sys.argv)>4:meta['provenance']['repair_prompt_file']=Path(sys.argv[4]).relative_to(BOOK).as_posix()
 if len(sys.argv)>5:meta['provenance']['repair_reference_sheet']=Path(sys.argv[5]).relative_to(BOOK).as_posix()
 meta['provenance']['repair_cell']={'row':ri,'column':ci,'bbox':[x0,y0,x1,y1],'resampling':'NEAREST','repair_scale':scale,'calibrated_to_view':calibration_view,'source_crop_size':list(crop.size),'render_size':size};norm['source_crop_size']=list(crop.size);norm['render_size']=size
 meta['provenance']['notes']=meta['provenance'].get('notes','')+' Corrected view inferred from retained repair atlas.';meta['geometry_qa']='pending-review';meta_path.write_text(json.dumps(meta,indent=2)+'\n')
 asset=next((a for a in idx['assets'] if a['id']==meta['id']),None)
 if asset is None:idx['assets'].append(meta)
 else:asset.clear();asset.update(meta)
 s=next(s for s in idx['view_sets'] if s['object_id']==oid);s.setdefault('views',{})[view]=meta['id'];s['geometry_qa']='pending-review';s['complete']=False;s['notes']=s.get('notes','')+' Corrected atlas applied; awaiting independent geometry QA before marking complete.'
idxp.write_text(json.dumps(idx,indent=2)+'\n');print('repaired',len(ROWS),'views; atlas',raw.relative_to(BOOK),rawsha)
