from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw
import numpy as np
from scipy.ndimage import label,find_objects,binary_dilation
b=Path(__file__).resolve().parent;root=b.parents[3];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();guard=json.loads((b/'inputs-current-v2/source-current-guards.json').read_text());objects={o['object_id']:o for o in guard['objects']};rows=[];immutable=[]
def components(name,mode):
 raw=b/'raw'/f'{name}-v1.png';im=Image.open(raw).convert('RGBA');arr=np.array(im);lab,n=label(arr[:,:,3]>=64,np.ones((3,3)));cc=[]
 for idx,sl in enumerate(find_objects(lab),1):
  if sl and (lab[sl]==idx).sum()>1000:
   box=[sl[1].start,sl[0].start,sl[1].stop,sl[0].stop];cc.append({'idx':idx,'box':box,'area':int((lab[sl]==idx).sum())})
 if mode=='rows':
  cc.sort(key=lambda c:(c['box'][1],c['box'][0]));cc=[z for start in range(0,len(cc),2) for z in sorted(cc[start:start+2],key=lambda c:c['box'][0])]
 else:cc.sort(key=lambda c:(c['box'][0],c['box'][1]))
 return raw,im,arr,lab,cc
jobs=[('circus','rows','over-city-venues-circus-striped-platform',['front','rear','right','left','top','bottom'],180,'circus-four-post-principal-geometry-guide-v1.png'),('trap','columns','hunting-shrines-hunter-trap-mechanism',['front','top','rear'],226,'trap-three-spike-principal-guide-v1.png'),('roofbed','columns',None,['top','front'],None,'roof-top-bed-front-guide-v1.png')]
for name,mode,oid,views,width,guide in jobs:
 raw,im,arr,lab,cc=components(name,mode);assert len(cc)==len(views),(name,len(cc));prepared=[]
 for c in cc:
  mask=binary_dilation(lab==c['idx'],structure=np.ones((3,3)));a=arr.copy();a[:,:,3]=np.where(mask,a[:,:,3],0);box=[max(0,c['box'][0]-1),max(0,c['box'][1]-1),min(im.width,c['box'][2]+1),min(im.height,c['box'][3]+1)];crop=Image.fromarray(a).crop(box);prepared.append((c,box,crop))
 common=width/max(crop.width for _,_,crop in prepared) if width else None
 for index,(view,(c,box,crop)) in enumerate(zip(views,prepared)):
  targetoid=oid or ['faction-larracos-drained-slum-house','starter-dungeon-simple-bed'][index];targetwidth=width or [204,172][index];scale=common or targetwidth/crop.width;size=[round(crop.width*scale),round(crop.height*scale)];xy=[(256-size[0])//2,(256-size[1])//2];assert max(size)<=256;crop=crop.resize(size,Image.Resampling.NEAREST);out=Image.new('RGBA',(256,256));out.alpha_composite(crop,xy);dest=b/'images'/f'{targetoid}.{view}.candidate-generated-v1.png';out.save(dest)
  source=objects[targetoid];row={'object_id':targetoid,'view':view,'source':source['source'],'base_views':source['views'],'candidate':{'path':str(dest.relative_to(root)),'sha256':sha(dest)},'raw':{'path':str(raw.relative_to(root)),'sha256':sha(raw)},'prompt':{'path':str((b/'raw'/f'{name}-v1.prompt.txt').relative_to(root)),'sha256':sha(b/'raw'/f'{name}-v1.prompt.txt')},'response':{'path':str((b/'raw'/f'{name}-v1-response.json').relative_to(root)),'sha256':sha(b/'raw'/f'{name}-v1-response.json')},'geometry_guide':{'path':str((b/'inputs'/guide).relative_to(root)),'sha256':sha(b/'inputs'/guide)},'recipe':{'threshold':64,'connectivity':8,'selection':'measured global connected component, no nominal-cell clipping','component_bbox_xyxy':c['box'],'component_area':c['area'],'mask_dilation_footprint':[3,3],'mask_dilation_iterations':1,'crop_bbox_xyxy':box,'uniform_scale':scale,'shared_object_raw_scale':common,'resized_wh':size,'offset_xy':xy,'resampler':'NEAREST','canvas':[256,256]},'inference':'Generated principal projection and hidden construction inferred; source material/count/layout authoritative, no recovered hidden pixels.'};rows.append(row)
for oid,o in objects.items():
 for v,a in [('source',o['source']),*o['views'].items()]:
  p=b/'inputs-current-v2'/f'{oid}.{v}.png';assert sha(p)==a['sha256'];immutable.append({'path':str(p.relative_to(root)),'sha256':sha(p)})
c=Image.new('RGB',(1400,220*len(objects)*2),'#ddd');dr=ImageDraw.Draw(c);lookup={(x['object_id'],x['view']):x for x in rows}
for n,(oid,o) in enumerate(objects.items()):
 for proposed in [False,True]:
  y=(n*2+proposed)*220;dr.text((0,y),oid+(' PROPOSED' if proposed else ' CURRENT'),fill='black')
  for col,v in enumerate(['source','front','top','right','left','bottom','rear']):
   row=lookup.get((oid,v));p=root/row['candidate']['path'] if proposed and row else b/'inputs-current-v2'/f'{oid}.{v}.png';a=Image.open(p).convert('RGBA');a.thumbnail((190,190),Image.Resampling.NEAREST);c.paste(a,(col*200+(200-a.width)//2,y+20),a);dr.text((col*200+3,y+205),v,fill='black')
p=b/'generated-source-current-candidate-v1.png';c.save(p);m={'scope':guard['pack'],'candidate_only':True,'candidate_owner':'page_inventory','reviewer':'root','installer':'views_ink_books','sets':rows,'immutable_inputs':immutable,'input_guard':{'path':str((b/'inputs-current-v2/source-current-guards.json').relative_to(root)),'sha256':sha(b/'inputs-current-v2/source-current-guards.json')},'script':{'path':str(Path(__file__).relative_to(root)),'sha256':sha(Path(__file__))},'contact':{'path':str(p.relative_to(root)),'sha256':sha(p)},'source_count_adjudication':{'reviewer':'root','trap':'THREEspikes; FRONT/REAR expanded as companions toTOP','circus':'FOURposts,2tallrear withbunting+2shortnearfront, circles inT/B; source intact'},'requirements':['No live output/index/sidecar changes; candidate only. Fresh source/current-six guards before install.','Preserve all unspecified directions and exact native sources. Source count expansions explicit; hidden views inferred.','Use retained raw/prompt/guide/current inputs, exact component masks and common object raw scale. No active-leaf replay dependency.']};(b/'generated-candidate-manifest-v1.json').write_text(json.dumps(m,indent=2)+'\n');print('11 candidates',sha(p));print([(x['object_id'],x['view'],x['recipe']['resized_wh'])for x in rows])
