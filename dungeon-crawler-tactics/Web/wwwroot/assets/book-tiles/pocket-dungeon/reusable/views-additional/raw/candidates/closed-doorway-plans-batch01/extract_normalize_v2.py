import json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
ROOT=Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/pocket-dungeon');OUT=ROOT/'reusable/views-additional';D=OUT/'raw/candidates/closed-doorway-plans-batch01';V=D/'v2';V.mkdir(exist_ok=True)
REQ=json.loads((D/'request-v2.json').read_text());RAW=D/'raw-atlas-v2.png';Q=json.loads(Path('/tmp/pocket-queue-scenery-current4.json').read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
raw=Image.open(RAW).convert('RGBA');a=np.array(raw.getchannel('A'))>16;lab,n=label(a,np.ones((3,3),dtype=np.uint8));cw=raw.width/6;ch=raw.height/2;groups={(r,c):[] for r in range(2) for c in range(6)}
for i in range(1,n+1):
 y,x=np.where(lab==i);area=len(x)
 if area<4:continue
 cx,cy=float(x.mean()),float(y.mean());c=min(range(6),key=lambda k:abs(cx-(k+.5)*cw));r=min(range(2),key=lambda k:abs(cy-(k+.5)*ch));groups[(r,c)].append({'area':area,'bbox':(int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)),'centroid':[cx,cy],'mask':lab==i})
assert all(len(groups[(r,c)])==1 for r in range(2) for c in range(6)),{k:[(g['area'],g['bbox']) for g in v] for k,v in groups.items()}
objs=REQ['objects'];allfiles=[];contacts=[]
for c,o in enumerate(objs):
 oid=o['object_id']; s=next(x for x in Q['sets'] if x['object_id']==oid); assert s['status']=='needs-correction' and s['source']['sha256']==o['source_sha256']
 source=ROOT/o['source_path']; assert sha(source)==o['source_sha256']
 src_im=Image.open(source).convert('RGBA')
 for r,view in enumerate(['top','bottom']):
  g=groups[(r,c)][0];x0,y0,x1,y1=g['bbox'];arr=np.array(raw);arr[~g['mask']]=0;crop=Image.fromarray(arr,'RGBA').crop((x0,y0,x1,y1))
  fb=Image.open(OUT/f'{oid}.front.png').convert('RGBA').getchannel('A').getbbox();rb=Image.open(OUT/f'{oid}.rear.png').convert('RGBA').getchannel('A').getbbox();front_w=fb[2]-fb[0];rear_w=rb[2]-rb[0];target_w=min(front_w,rear_w)
  side_w=min(Image.open(OUT/f'{oid}.right.png').convert('RGBA').getchannel('A').getbbox()[2]-Image.open(OUT/f'{oid}.right.png').convert('RGBA').getchannel('A').getbbox()[0],Image.open(OUT/f'{oid}.left.png').convert('RGBA').getchannel('A').getbbox()[2]-Image.open(OUT/f'{oid}.left.png').convert('RGBA').getchannel('A').getbbox()[0])
  scale=target_w/crop.width;size=(target_w,max(1,round(crop.height*scale)));render=crop.resize(size,Image.Resampling.NEAREST);out=Image.new('RGBA',(256,256),(0,0,0,0));out.alpha_composite(render,((256-size[0])//2,248-size[1]));cp=V/f'{oid}.{view}.candidate.png';out.save(cp)
  allfiles.append({'object_id':oid,'view':view,'candidate_path':cp.relative_to(ROOT).as_posix(),'candidate_sha256':sha(cp),'cell':[r,c],'component_area':g['area'],'component_bbox':list(g['bbox']),'cell_size':[int(cw),int(ch)],'crop_size':[crop.width,crop.height],'target_width_from_front_rear':target_w,'reference_front_width':front_w,'reference_rear_width':rear_w,'side_depth_width':side_w,'render_size':list(size),'plan_depth_ratio_to_side_profile':round(size[1]/side_w,3),'scale':scale,'resampling':'NEAREST','anchor_px':[128,248]})
 canvas=Image.new('RGBA',(7*256,256),(235,235,235,255));draw=ImageDraw.Draw(canvas);sourceim=Image.open(source).convert('RGBA');sourceim.thumbnail((220,220),Image.Resampling.NEAREST);canvas.alpha_composite(sourceim,((256-sourceim.width)//2,(256-sourceim.height)//2));draw.text((4,4),'source',fill='black')
 viewhash={}
 for col,v in enumerate(['front','top','right','left','bottom','rear'],1):
  path=V/f'{oid}.{v}.candidate.png' if v in ['top','bottom'] else OUT/f'{oid}.{v}.png';im=Image.open(path).convert('RGBA');canvas.alpha_composite(im,(col*256,0));draw.text((col*256+4,4),v,fill='black');viewhash[v]={'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path)}
 contact=V/f'{oid}.source-plus-six-candidate.png';canvas.convert('RGB').save(contact);contacts.append({'object_id':oid,'source_path':o['source_path'],'source_sha256':o['source_sha256'],'contact_path':contact.relative_to(ROOT).as_posix(),'contact_sha256':sha(contact),'views':viewhash})
recipe={'schema_version':1,'batch_id':REQ['batch_id'],'status':'staged-awaiting-root-review','request_path':'reusable/views-additional/raw/candidates/closed-doorway-plans-batch01/request-v2.json','request_sha256':sha(D/'request-v2.json'),'raw_atlas_path':REQ['raw_atlas_path'],'raw_atlas_sha256':REQ['raw_atlas_sha256'],'output_binding':REQ['output_binding'],'layout':{'columns':REQ['cell_layout']['columns'],'rows':REQ['cell_layout']['rows'],'atlas_size':list(raw.size),'logical_cell_size':[int(cw),int(ch)],'component_grouping':'full-atlas alpha connected components; map centroid to nearest 6x2 cell center; retain >=4px components; take full group bbox'},'candidates':allfiles,'contacts':contacts,'notes':'Top/bottom directions normalized uniformly to target source front/rear width with NEAREST. Four elevations remain unchanged. Candidates not installed; v1 held candidates retained.'}
(V/'normalization-recipe.json').write_text(json.dumps(recipe,indent=2)+'\n');(V/'candidate-index.json').write_text(json.dumps({'schema_version':1,'status':'staged-awaiting-root-review','candidates':contacts,'recipe_path':(V/'normalization-recipe.json').relative_to(ROOT).as_posix(),'recipe_sha256':sha(V/'normalization-recipe.json')},indent=2)+'\n');print(json.dumps({'candidates':len(allfiles),'recipe_sha256':sha(V/'normalization-recipe.json'),'contacts':[{x['object_id']:x['contact_path']} for x in contacts]},indent=2))
