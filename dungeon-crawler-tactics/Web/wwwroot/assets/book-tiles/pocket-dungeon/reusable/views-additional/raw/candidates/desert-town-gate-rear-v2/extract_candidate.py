import json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
ROOT=Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/pocket-dungeon');V=ROOT/'reusable/views-additional';D=V/'raw/candidates/desert-town-gate-rear-v2';OID='bubble-desert-adobe-town-gate';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
rawp=D/'raw-atlas.png';im=Image.open(rawp).convert('RGBA');a=np.array(im.getchannel('A'))>16;lab,n=label(a,np.ones((3,3),dtype=np.uint8));comps=[]
for i in range(1,n+1):
 y,x=np.where(lab==i);comps.append((len(x),(int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)),lab==i))
area,bbox,mask=max(comps,key=lambda x:x[0]);assert bbox==(154,334,1100,1110) and area==608719
arr=np.array(im);arr[~mask]=0;crop=Image.fromarray(arr,'RGBA').crop(bbox)
front=Image.open(V/f'{OID}.front.png').convert('RGBA');fb=front.getchannel('A').getbbox();fw,fh=fb[2]-fb[0],fb[3]-fb[1]
scale=fw/crop.width;size=(fw,round(crop.height*scale));crop=crop.resize(size,Image.Resampling.NEAREST);out=Image.new('RGBA',(256,256),(0,0,0,0));out.alpha_composite(crop,((256-fw)//2,248-size[1]));candidate=D/'rear.candidate.png';out.save(candidate)
contact=Image.new('RGBA',(7*256,256),(235,235,235,255));draw=ImageDraw.Draw(contact);src=Image.open(ROOT/'bubble-desert/components'/f'{OID}.png').convert('RGBA');src.thumbnail((220,220),Image.Resampling.NEAREST);contact.alpha_composite(src,((256-src.width)//2,(256-src.height)//2));draw.text((5,4),'source',fill='black')
for col,v in enumerate(['front','top','right','left','bottom','rear'],1):
 x=out if v=='rear' else Image.open(V/f'{OID}.{v}.png').convert('RGBA');contact.alpha_composite(x,(col*256,0));draw.text((col*256+5,4),v,fill='black')
cp=D/'candidate-source-plus-six.png';contact.convert('RGB').save(cp)
req=json.loads((D/'request.json').read_text());recipe={'schema_version':1,'object_id':OID,'status':'staged-awaiting-root-review','target_view':'rear','source_path':req['source_path'],'source_sha256':req['source_sha256'],'current_rear_sha256':req['current_rear_sha256'],'raw_atlas_path':rawp.relative_to(ROOT).as_posix(),'raw_atlas_sha256':sha(rawp),'generation_request':'reusable/views-additional/raw/candidates/desert-town-gate-rear-v2/request.json','output_binding':req['output_binding'],'main_component':{'area':area,'bbox':list(bbox),'source_size':[bbox[2]-bbox[0],bbox[3]-bbox[1]]},'normalization':{'reference_view':'front','reference_sha256':sha(V/f'{OID}.front.png'),'target_width':fw,'scale':scale,'render_size':list(size),'resampling':'NEAREST','canvas':[256,256],'anchor_px':[128,248]},'candidate_path':candidate.relative_to(ROOT).as_posix(),'candidate_sha256':sha(candidate),'contact_path':cp.relative_to(ROOT).as_posix(),'contact_sha256':sha(cp),'notes':'Generated reverse face of the same closed timber gate; preserve central gate state and matched adobe tower scale. Whole-set review pending.'}
(D/'recipe.json').write_text(json.dumps(recipe,indent=2)+'\n');print(json.dumps(recipe,indent=2))
