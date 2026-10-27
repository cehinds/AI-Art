from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib
b=Path(__file__).resolve().parent;root=b.parents[3];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();guard=json.loads((b/'inputs/source-current-guards.json').read_text());objects={o['object_id']:o for o in guard['objects']};rows=[]
jobs=[('great-race-transition-fractured-maze-slab','front','right',0,None,False),('great-race-transition-fractured-maze-slab','rear','left',0,None,False),('starter-dungeon-simple-bed','bottom','bottom',90,200,False),('industry-menagerie-soot-stained-brick-wall-northwest','top','rear',0,None,False),('industry-menagerie-soot-stained-brick-wall-northwest','rear','front',0,None,True)]
for oid,v,donor,rotate,target,mirror in jobs:
 o=objects[oid];p=b/'inputs'/f'{oid}.{donor}.png';assert sha(p)==o['views'][donor]['sha256'];im=Image.open(p).convert('RGBA');box=im.getbbox();crop=im.crop(box)
 if rotate:crop=crop.transpose(Image.Transpose.ROTATE_90)
 if mirror:crop=crop.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
 scale=target/max(crop.size) if target else 1.0;size=[round(crop.width*scale),round(crop.height*scale)];crop=crop.resize(size,Image.Resampling.NEAREST);xy=[(256-size[0])//2,(256-size[1])//2]
 if not rotate and not mirror and not target:out=im;xy=[box[0],box[1]]
 else:out=Image.new('RGBA',(256,256));out.alpha_composite(crop,xy)
 dest=b/'images'/f'{oid}.{v}.candidate-v1.png';out.save(dest);rows.append({'object_id':oid,'view':v,'source':o['source'],'base_views':o['views'],'candidate':{'path':str(dest.relative_to(root)),'sha256':sha(dest)},'recipe':{'input_path':str(p.relative_to(root)),'input_sha256':sha(p),'alpha_bbox_xyxy':list(box),'rigid_rotation_ccw_degrees':rotate,'horizontal_reflection':mirror,'uniform_scale':scale,'resized_wh':size,'offset_xy':xy,'full_canvas_alias':not rotate and not mirror and not target,'resampler':'NEAREST','canvas':[256,256]},'inference':'Declared same-object illustrative symmetry/re-key; no recovered hidden pixels.'})
inputs=[]
for oid in dict.fromkeys(x[0] for x in jobs):
 o=objects[oid]
 for v,a in [('source',o['source']),*o['views'].items()]:
  p=b/'inputs'/f'{oid}.{v}.png';assert sha(p)==a['sha256'];inputs.append({'path':str(p.relative_to(root)),'sha256':sha(p)})
c=Image.new('RGB',(1600,230*len(rows)),'#ddd');dr=ImageDraw.Draw(c)
for row,x in enumerate(rows):
 oid=x['object_id'];dr.text((0,row*230),oid+' '+x['view'].upper(),fill='black')
 for col,v in enumerate(['source','front','top','right','left','bottom','rear','candidate']):
  p=root/x['candidate']['path'] if col==7 else b/'inputs'/f'{oid}.{v}.png';a=Image.open(p).convert('RGBA');a.thumbnail((190,190),Image.Resampling.NEAREST);c.paste(a,(col*200+(200-a.width)//2,row*230+20),a);dr.text((col*200+3,row*230+210),v,fill='black')
p=b/'deterministic-source-current-candidate-v1.png';c.save(p);m={'scope':guard['scope'],'candidate_only':True,'candidate_owner':'page_inventory','reviewer':'root','installer':'views_ink_books','sets':rows,'immutable_inputs':inputs,'input_guard':{'path':str((b/'inputs/source-current-guards.json').relative_to(root)),'sha256':sha(b/'inputs/source-current-guards.json')},'script':{'path':str(Path(__file__).relative_to(root)),'sha256':sha(Path(__file__))},'contact':{'path':str(p.relative_to(root)),'sha256':sha(p)},'required_view_set_symmetry':[{'object_id':'great-race-transition-fractured-maze-slab','views':['front','right'],'reason':'Inferred square slab rotational symmetry, same retained lowedge/hanging-shard projection across principal horizontal cameras.'},{'object_id':'great-race-transition-fractured-maze-slab','views':['rear','left'],'reason':'Inferred opposite square slab edge/shard symmetry from same-target retained projection.'}],'requirements':['Fresh exact source/all-six current guards before install; preserve all other valid views. BedFRONT remains pending separate candidate, no wholebed approval.','Canonical source unchanged; raw inputs immutable retainedcopies. All hidden same-object symmetry explicitly inferred.']};(b/'deterministic-candidate-manifest-v1.json').write_text(json.dumps(m,indent=2)+'\n');print(sha(p))
