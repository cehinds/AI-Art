import json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
ROOT=Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/pocket-dungeon'); V=ROOT/'reusable/views-additional'; D=V/'raw/candidates/early-arena-round-stairwell-top-v3'
OID='early-arenas-round-arena-stairwell'; rawp=V/'raw/candidates/early-arena-round-stairwell-top-v3-raw.png';D.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
raw=Image.open(rawp).convert('RGBA');a=np.array(raw.getchannel('A'))>16; lab,n=label(a,np.ones((3,3),dtype=np.uint8));comps=[]
for i in range(1,n+1):
 y,x=np.where(lab==i);comps.append((len(x),(int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)),lab==i))
area,bbox,mask=max(comps,key=lambda x:x[0]);assert bbox==(297,292,958,961) and area==351562
arr=np.array(raw);arr[~mask]=0;crop=Image.fromarray(arr,'RGBA').crop(bbox)
scale=181/max(crop.size); size=(round(crop.width*scale),round(crop.height*scale)); crop=crop.resize(size,Image.Resampling.NEAREST)
out=Image.new('RGBA',(256,256),(0,0,0,0)); x=37+(181-size[0])//2; y=67+(181-size[1])//2;out.alpha_composite(crop,(x,y));dest=D/'top.candidate.png';out.save(dest)
contact=Image.new('RGBA',(7*256,256),(235,235,235,255));draw=ImageDraw.Draw(contact)
src=Image.open(ROOT/'early-arenas/components'/f'{OID}.png').convert('RGBA');src.thumbnail((220,220),Image.Resampling.NEAREST);contact.alpha_composite(src,((256-src.width)//2,(256-src.height)//2));draw.text((5,4),'source',fill='black')
for c,v in enumerate(['front','right','left','top','bottom','rear'],1):
 im=out if v=='top' else Image.open(V/f'{OID}.{v}.png').convert('RGBA');contact.alpha_composite(im,(c*256,0));draw.text((c*256+5,4),v,fill='black')
cp=D/'candidate-source-plus-six.png';contact.convert('RGB').save(cp)
recipe={'schema_version':1,'object_id':OID,'status':'staged-awaiting-root-review','target_view':'top','raw_atlas_path':rawp.relative_to(ROOT).as_posix(),'raw_atlas_sha256':sha(rawp),'generation_request':'reusable/views-additional/raw/candidates/early-arena-round-stairwell-top-v3-request.json','output_binding':'/workspace/generated_images/exec-346537f9-e1cb-4bad-a164-004afb90f2f2.png','main_component':{'area':area,'bbox':list(bbox),'source_size':list(crop.size)},'normalization':{'scale':scale,'render_size':list(size),'resampling':'NEAREST','output_canvas':[256,256],'anchor_px':[128,248],'matched_bottom_bbox':[37,67,218,248]},'candidate_path':dest.relative_to(ROOT).as_posix(),'candidate_sha256':sha(dest),'contact_path':cp.relative_to(ROOT).as_posix(),'contact_sha256':sha(cp),'current_live_unchanged':True,'notes':'Flat orthographic top plan with sandstone annulus and radial tread top surfaces; generated from source plus accepted bottom footprint. Tiny disconnected alpha specks discarded; main art retained.'}
(D/'recipe.json').write_text(json.dumps(recipe,indent=2)+'\n');print(json.dumps(recipe,indent=2))
