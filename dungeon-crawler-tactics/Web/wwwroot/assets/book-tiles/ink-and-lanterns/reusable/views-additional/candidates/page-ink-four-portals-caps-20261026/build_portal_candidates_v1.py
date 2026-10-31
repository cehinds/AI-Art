from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw
import numpy as np
from scipy.ndimage import label,find_objects
b=Path(__file__).resolve().parent;root=b.parents[3];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();guards=json.loads((b/'inputs/source-current-guards.json').read_text())['objects'];raw=b/'raw/portals-rear-v1.png';im=Image.open(raw).convert('RGBA');lab,n=label(np.array(im.getchannel('A'))>=64,np.ones((3,3)));components=[]
for idx,sl in enumerate(find_objects(lab),1):
 if sl and (lab[sl]==idx).sum()>500:components.append((sl[1].start,idx,[sl[1].start,sl[0].start,sl[1].stop,sl[0].stop]))
components.sort();assert len(components)==2;rows=[]
input_closure=[]
for obj in guards[:2]:
 for name,ref in [('source',obj['source']),*obj['views'].items()]:
  inp=b/'inputs'/f"{obj['object_id']}.{name}.png";assert sha(inp)==ref['sha256'];input_closure.append({'path':str(inp.relative_to(root)),'sha256':sha(inp)})
for src,(_,idx,box) in zip(guards[:2],components):
 oid=src['object_id'];front=Image.open(b/'inputs'/f'{oid}.front.png').getbbox();height=front[3]-front[1];crop=im.crop(box);alpha=np.array(crop.getchannel('A'));crop.putalpha(Image.fromarray(np.where(lab[box[1]:box[3],box[0]:box[2]]==idx,alpha,0).astype('uint8')));scale=height/crop.height;size=[round(crop.width*scale),height];crop=crop.resize(size,Image.Resampling.NEAREST);offset=[(256-size[0])//2,(256-size[1])//2];out=Image.new('RGBA',(256,256));out.alpha_composite(crop,offset);dest=b/'images'/f'{oid}.rear.candidate-v1.png';out.save(dest)
 rows.append({'object_id':oid,'view':'rear','source':{'path':src['source']['path'],'sha256':src['source']['sha256']},'base_views':{v:{'path':a['path'],'sha256':a['sha256']} for v,a in src['views'].items()},'candidate':{'path':str(dest.relative_to(root)),'sha256':sha(dest)},'raw':{'path':str(raw.relative_to(root)),'sha256':sha(raw)},'prompt':{'path':str((b/'raw/portals-rear-v1.prompt.txt').relative_to(root)),'sha256':sha(b/'raw/portals-rear-v1.prompt.txt')},'response':{'path':str((b/'raw/portals-rear-v1-response.json').relative_to(root)),'sha256':sha(b/'raw/portals-rear-v1-response.json')},'recipe':{'component_bbox_xyxy':box,'alpha_threshold':64,'connectivity':8,'component_area':int((lab==idx).sum()),'alpha_mask':'retain original alpha only inside selected component, no dilation','uniform_scale':scale,'resized_wh':size,'offset_xy':offset,'canvas':[256,256],'resampler':'NEAREST'},'inference':'Plain reverse metal door face and reverse handle/hinges inferred from closed FRONT; source cream/red jambs preserved. No recovered hidden pixels.'})
c=Image.new('RGB',(1600,230*2),'#ddd');dr=ImageDraw.Draw(c)
for row,x in enumerate(rows):
 oid=x['object_id'];dr.text((0,row*230),oid,fill='black')
 for col,v in enumerate(['source','front','top','right','left','bottom','rear','candidate-rear']):
  p=root/x['candidate']['path'] if col==7 else b/'inputs'/f'{oid}.{v}.png';a=Image.open(p).convert('RGBA');a.thumbnail((190,190),Image.Resampling.NEAREST);c.paste(a,(col*200+(200-a.width)//2,row*230+22),a);dr.text((col*200+4,row*230+210),v,fill='black')
p=b/'portal-source-current-candidate-v1.png';c.save(p);m={'scope':'book-tiles/ink-and-lanterns','candidate_only':True,'candidate_owner':'page_inventory','reviewer':'root','installer':'views_ink_books','sets':rows,'immutable_inputs':input_closure,'input_guard':{'path':str((b/'inputs/source-current-guards.json').relative_to(root)),'sha256':sha(b/'inputs/source-current-guards.json')},'script':{'path':str(Path(__file__).relative_to(root)),'sha256':sha(Path(__file__))},'contact':{'path':str(p.relative_to(root)),'sha256':sha(p)},'requirements':['Keep other five views unchanged; recheck current source/six before installation.','Canonical source unchanged; retained raw/prompt/input lineage pack-local. Inputs under inputs/ are immutable copies; no live sibling replay dependency.']};(b/'portal-candidate-manifest-v1.json').write_text(json.dumps(m,indent=2)+'\n');print('portal candidates',sha(p))
