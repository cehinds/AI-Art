import json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
ROOT=Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/pocket-dungeon'); V=ROOT/'reusable/views-additional'; ST=V/'raw/candidates'
OID='early-arenas-round-arena-stairwell'; C=ST/'early-arena-round-stairwell-top-v2-raw.png'; D=ST/'early-arena-round-stairwell-top-v2'
D.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
raw=Image.open(C).convert('RGBA'); a=np.array(raw.getchannel('A'))>16; lab,n=label(a,np.ones((3,3),dtype=np.uint8)); comps=[]
for i in range(1,n+1):
 y,x=np.where(lab==i); comps.append((len(x),(int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)),lab==i))
area,bbox,mask=max(comps,key=lambda x:x[0]); assert area==617139 and bbox==(184,196,1071,1092)
arr=np.array(raw); arr[~mask]=0; clean=Image.fromarray(arr,'RGBA').crop(bbox)
# Match the accepted round BOTTOM plan outer diameter with isotropic NEAREST sizing.
scale=181/max(clean.size); size=(round(clean.width*scale),round(clean.height*scale)); resized=clean.resize(size,Image.Resampling.NEAREST)
out=Image.new('RGBA',(256,256),(0,0,0,0)); x=37+(181-size[0])//2; y=67+(181-size[1])//2; out.alpha_composite(resized,(x,y)); dest=D/'top.candidate.png'; out.save(dest)
# Source + six capture, preserving the five currently retained directions.
contact=Image.new('RGBA',(7*256,256),(235,235,235,255)); draw=ImageDraw.Draw(contact)
src=Image.open(ROOT/'early-arenas/components'/f'{OID}.png').convert('RGBA'); src.thumbnail((220,220),Image.Resampling.NEAREST); contact.alpha_composite(src,((256-src.width)//2,(256-src.height)//2)); draw.text((5,4),'source',fill='black')
for c,v in enumerate(['front','right','left','top','bottom','rear'],1):
 im=out if v=='top' else Image.open(V/f'{OID}.{v}.png').convert('RGBA')
 contact.alpha_composite(im,(c*256,0)); draw.text((c*256+5,4),v,fill='black')
cp=D/'candidate-source-plus-six.png'; contact.convert('RGB').save(cp)
recipe={'schema_version':1,'object_id':OID,'status':'staged-awaiting-root-review','target_view':'top','raw_atlas_path':C.relative_to(ROOT).as_posix(),'raw_atlas_sha256':sha(C),'generation_request':'reusable/views-additional/raw/candidates/early-arena-round-stairwell-top-v2-request.json','output_binding':'/workspace/generated_images/exec-62145927-da0e-4d14-a0d9-8084ab13f0c1.png','main_component':{'area':area,'bbox':list(bbox),'source_size':list(clean.size)},'normalization':{'scale':scale,'render_size':list(size),'resampling':'NEAREST','output_canvas':[256,256],'output_anchor':[128,248],'matched_bottom_bbox':[37,67,218,248]},'candidate_path':dest.relative_to(ROOT).as_posix(),'candidate_sha256':sha(dest),'contact_path':cp.relative_to(ROOT).as_posix(),'contact_sha256':sha(cp),'current_live_unchanged':True,'notes':'Top-oriented circular stairwell candidate extracted from its bound generated output; root geometry review pending. Tiny disconnected alpha specks were discarded; all art pixels in the main connected silhouette are retained.'}
(D/'recipe.json').write_text(json.dumps(recipe,indent=2)+'\n'); print(json.dumps(recipe,indent=2))
