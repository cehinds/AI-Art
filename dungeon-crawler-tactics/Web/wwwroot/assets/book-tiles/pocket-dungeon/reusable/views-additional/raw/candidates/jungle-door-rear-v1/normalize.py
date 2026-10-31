import hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np
from scipy import ndimage
ROOT=Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/pocket-dungeon'); OUT=ROOT/'reusable/views-additional'; ST=OUT/'raw/candidates/jungle-door-rear-v1'; oid='hunting-jungle-vine-covered-ruin-stone-closed-doorway'; sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
raw=Image.open(ST/'raw-atlas.png').convert('RGBA'); arr=np.array(raw); alpha=arr[:,:,3]; lab,n=ndimage.label(alpha>=245); objs=ndimage.find_objects(lab); comps=[]
for i,sl in enumerate(objs,1):
 if sl:
  ar=int((lab[sl]==i).sum())
  if ar>=4: comps.append((ar,(sl[1].start,sl[0].start,sl[1].stop,sl[0].stop)))
comps.sort(reverse=True); area,bbox=comps[0]; crop=raw.crop(bbox)
front=Image.open(OUT/f'{oid}.front.png').convert('RGBA'); fa=np.array(front.getchannel('A')); ys,xs=np.where(fa>=245); fb=(int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)); targetw=fb[2]-fb[0]; sc=targetw/crop.width; new=(targetw,max(1,round(crop.height*sc))); resized=crop.resize(new,Image.Resampling.NEAREST)
canvas=Image.new('RGBA',(256,256),(0,0,0,0)); x=128-new[0]//2; y=248-new[1]; canvas.alpha_composite(resized,(x,y)); cand=ST/f'{oid}.rear.candidate.png'; canvas.save(cand)
# contact includes source plus six with candidate rear
src=ROOT/'hunting-jungle/components'/f'{oid}.png'; names=['source','front','top','right','left','bottom','rear-candidate']; paths=[src]+[OUT/f'{oid}.{v}.png' for v in ['front','top','right','left','bottom']]+[cand]
contact=Image.new('RGBA',(len(paths)*256,256),(238,238,238,255)); draw=ImageDraw.Draw(contact)
for i,(nm,p) in enumerate(zip(names,paths)):
 pane=Image.new('RGBA',(256,256),'white'); pane.alpha_composite(Image.open(p).convert('RGBA')); contact.alpha_composite(pane,(i*256,0)); draw.text((i*256+4,4),nm,fill='black')
cp=ST/'source-plus-six-candidate.png'; contact.convert('RGB').save(cp)
manifest={'schema_version':1,'object_id':oid,'view':'rear','status':'staged-awaiting-root-review','source_path':'hunting-jungle/components/'+oid+'.png','source_sha256':sha(src),'target_before_sha256':sha(OUT/f'{oid}.rear.png'),'raw_atlas_path':'reusable/views-additional/raw/candidates/jungle-door-rear-v1/raw-atlas.png','raw_atlas_sha256':sha(ST/'raw-atlas.png'),'request_path':'reusable/views-additional/raw/candidates/jungle-door-rear-v1/request.json','request_sha256':sha(ST/'request.json'),'output_binding':json.loads((ST/'request.json').read_text())['output_binding'],'candidate_path':'reusable/views-additional/raw/candidates/jungle-door-rear-v1/'+cand.name,'candidate_sha256':sha(cand),'contact_path':'reusable/views-additional/raw/candidates/jungle-door-rear-v1/source-plus-six-candidate.png','contact_sha256':sha(cp),'alpha_components':comps,'selected_component_bbox':bbox,'front_alpha_bbox':fb,'scale':sc,'crop_size':list(crop.size),'render_size':list(new),'anchor_px':[128,248],'resampling':'NEAREST','notes':'Reverse orthographic elevation for existing closed timber gate. Candidate is generated from exact saved imagegen output; full natural alpha connected-component crop and isotropic nearest-neighbor normalization. Rear identity/proportions require independent review.'}
(ST/'candidate-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest,indent=2))
