#!/usr/bin/env python3
"""Replace only the two repeated-front staircase rears with closed support faces."""
from pathlib import Path
import json,hashlib,struct
import numpy as np
from PIL import Image
from scipy import ndimage
PACK=Path(__file__).resolve().parents[4];VD=PACK/'reusable/views-additional';RAW=VD/'raw';atlas_path=RAW/'atlases/iron-trains-stairs-rear-v1.png';atlas=Image.open(atlas_path).convert('RGBA');a=np.asarray(atlas.getchannel('A'));labels,n=ndimage.label(a>=245,structure=np.ones((3,3),dtype=np.uint8));ids=['iron-trains-railcar-metal-stairs-up','iron-trains-railcar-metal-stairs-down'];ledger=json.loads(Path('/workspace/scratch/view-qa-root.json').read_text())['reviewed'];idxp=VD/'set-index.json';idx=json.loads(idxp.read_text());corpath=VD/'corrections.json';spec=json.loads(corpath.read_text());ops=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rsha(im):return hashlib.sha256(struct.pack('>II',*im.size)+im.convert('RGBA').tobytes()).hexdigest()
for row,oid in enumerate(ids):
 r=ledger['book-tiles/pocket-dungeon::'+oid]
 if r['status']!='needs-correction' or r.get('affected_views')!=['rear']:raise SystemExit(f'root QA scope changed: {oid}')
 if sha(r['source'])!=r['source_sha256']:raise SystemExit('source changed')
 for v,p in r['view_paths'].items():
  if sha(p)!=r['image_hashes'][v]:raise SystemExit(f'current source+six mismatch {oid}.{v}')
 cx=atlas.width/2;cy=(row+.5)*atlas.height/2;candidates=[]
 for lab,sl in enumerate(ndimage.find_objects(labels),1):
  if sl is None:continue
  area=int((labels[sl]==lab).sum())
  if area<1000:continue
  yy,xx=ndimage.center_of_mass(labels==lab);dist=((xx-cx)**2+(yy-cy)**2)**.5;candidates.append((dist,lab,area,sl))
 dist,lab,area,sl=min(candidates)
 if dist>200:raise SystemExit(f'no rear component for row {row}: {oid}')
 bbox=[sl[1].start,sl[0].start,sl[1].stop,sl[0].stop];crop=atlas.crop(tuple(bbox));ref=Image.open(VD/f'{oid}.front.png').convert('RGBA');rb=ref.getchannel('A').getbbox();targetw=rb[2]-rb[0];scale=targetw/crop.width;size=(targetw,max(1,round(crop.height*scale)));crop=crop.resize(size,Image.Resampling.NEAREST);frame=Image.new('RGBA',(256,256),(0,0,0,0));frame.alpha_composite(crop,((256-size[0])//2,248-size[1]));dst=VD/f'{oid}.rear.png';mp=VD/f'{oid}.rear.json';md=json.loads(mp.read_text());before=r['image_hashes']['rear'];frame.save(dst,optimize=True);after=sha(dst);src_rel=str(Path(r['source']).relative_to(PACK));md.setdefault('provenance_history',[]).append(md.get('provenance',{}));md['image']={'path':f'reusable/views-additional/{oid}.rear.png','width':256,'height':256,'sha256':after,'rgba_sha256':rsha(frame)};md['geometry_qa']='pending-review';md['provenance']={'method':'generated','source_image':src_rel,'source_sha256':r['source_sha256'],'generated_atlas':str(atlas_path.relative_to(PACK)),'generated_atlas_sha256':sha(atlas_path),'generation_request':'reusable/views-additional/raw/requests/iron-trains-stairs-rear-v1.json','normalization':{'alpha_threshold':245,'component_policy':'whole-atlas CC selected by row centroid; full bounds retained','component':[lab,area,bbox],'reference_view':'front','reference_sha256':sha(VD/f'{oid}.front.png'),'uniform_scale':scale,'render_size':list(size),'resampling':'NEAREST','anchor_px':[128,248]},'notes':'Inferred closed reverse retaining/support face of the source staircase; no forward treads shown.'};mp.write_text(json.dumps(md,indent=2)+'\n')
 for q in idx['assets']:
  if q['id']==md['id']:q.clear();q.update(md);break
 g=next(x for x in idx['view_sets'] if x['object_id']==oid);g['complete']=False;g['geometry_qa']='pending-review';g['notes']='Rear replaced with source-matched closed support elevation; pending independent source+six review.'
 ops.append({'type':'replace-generated-view','object_id':oid,'view':'rear','before_sha256':before,'after_sha256':after,'atlas_path':'raw/atlases/iron-trains-stairs-rear-v1.png','atlas_sha256':sha(atlas_path),'crop_bbox':bbox,'reference_view':'front','reference_sha256':sha(VD/f'{oid}.front.png'),'scale':scale,'render_size':list(size),'reason':'Replace the repeated forward-tread image with the coherent closed reverse support face, preserving source identity, common Z and footprint.'})
spec['operations'].extend(ops);corpath.write_text(json.dumps(spec,indent=2)+'\n');idxp.write_text(json.dumps(idx,indent=2)+'\n');print(json.dumps(ops,indent=2))
