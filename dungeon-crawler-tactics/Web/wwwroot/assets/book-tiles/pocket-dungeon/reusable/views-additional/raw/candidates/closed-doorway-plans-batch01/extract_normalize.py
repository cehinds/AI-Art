import json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
ROOT=Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/pocket-dungeon');OUT=ROOT/'reusable/views-additional';D=OUT/'raw/candidates/closed-doorway-plans-batch01';REQ=json.loads((D/'request.json').read_text());RAW=D/'raw-atlas.png';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
raw=Image.open(RAW).convert('RGBA');a=np.array(raw.getchannel('A'))>16;lab,n=label(a,np.ones((3,3),dtype=np.uint8));comps=[]
for i in range(1,n+1):
 y,x=np.where(lab==i);area=len(x);bbox=(int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1));cent=(float(x.mean()),float(y.mean()))
 if area>=4: comps.append({'area':area,'bbox':bbox,'centroid':cent,'mask':lab==i})
cols=6;rows=2;cw=raw.width/cols;ch=raw.height/rows
assert abs(cw-round(cw))<1e-6 and abs(ch-round(ch))<1e-6,(raw.size,cw,ch)
# Every sizeable component belongs to one cell by nearest logical cell center; retain all cell components.
groups={(r,c):[] for r in range(rows) for c in range(cols)}
for comp in comps:
 x,y=comp['centroid']; c=min(range(cols),key=lambda j:abs(x-(j+.5)*cw)); r=min(range(rows),key=lambda j:abs(y-(j+.5)*ch));groups[(r,c)].append(comp)
assert all(len(groups[(r,c)])>=1 for r in range(rows) for c in range(cols)),{k:[(x['area'],x['bbox']) for x in v] for k,v in groups.items()}
# No cell may include stray outside components from another row/column; report each entire grouped bbox.
files=[]; contacts=[]
for c,obj in enumerate(REQ['objects']):
 oid=obj['object_id'];src=ROOT/obj['source_path'];assert sha(src)==obj['source_sha256']
 for r,view in enumerate(['top','bottom']):
  group=groups[(r,c)];
  # Keep all meaningful components assigned by logical cell; compute whole group bounds.
  x0=min(g['bbox'][0] for g in group);y0=min(g['bbox'][1] for g in group);x1=max(g['bbox'][2] for g in group);y1=max(g['bbox'][3] for g in group)
  assert x0>=c*cw-24 and x1<=(c+1)*cw+24 and y0>=r*ch-24 and y1<=(r+1)*ch+24,(oid,view,(x0,y0,x1,y1))
  arr=np.array(raw); keep=np.zeros((raw.height,raw.width),bool)
  for g in group: keep|=g['mask']
  arr[~keep]=0;crop=Image.fromarray(arr,'RGBA').crop((x0,y0,x1,y1))
  front=Image.open(OUT/f'{oid}.front.png').convert('RGBA').getchannel('A').getbbox();rear=Image.open(OUT/f'{oid}.rear.png').convert('RGBA').getchannel('A').getbbox();target_width=min(front[2]-front[0],rear[2]-rear[0])
  scale=target_width/crop.width;size=(target_width,max(1,round(crop.height*scale)));render=crop.resize(size,Image.Resampling.NEAREST)
  out=Image.new('RGBA',(256,256),(0,0,0,0)); out.alpha_composite(render,((256-size[0])//2,248-size[1])); path=D/f'{oid}.{view}.candidate.png';out.save(path)
  files.append({'object_id':oid,'view':view,'candidate_path':path.relative_to(ROOT).as_posix(),'candidate_sha256':sha(path),'cell_index':[r,c],'components':[{'area':g['area'],'bbox':list(g['bbox']),'centroid':list(g['centroid'])} for g in group],'group_bbox':[x0,y0,x1,y1],'crop_size':[crop.width,crop.height],'reference_front_width':front[2]-front[0],'reference_rear_width':rear[2]-rear[0],'target_plan_width':target_width,'uniform_scale':scale,'render_size':list(size),'resampling':'NEAREST','anchor_px':[128,248]})
 # One source-plus-six contact per object with only approved batch candidate leaves substituted.
 canvas=Image.new('RGBA',(7*256,256),(235,235,235,255));draw=ImageDraw.Draw(canvas);simg=Image.open(src).convert('RGBA');simg.thumbnail((220,220),Image.Resampling.NEAREST);canvas.alpha_composite(simg,((256-simg.width)//2,(256-simg.height)//2));draw.text((4,4),'source',fill='black')
 for col,v in enumerate(['front','top','right','left','bottom','rear'],1):
  cp=D/f'{oid}.{v}.candidate.png' if v in ['top','bottom'] else OUT/f'{oid}.{v}.png';im=Image.open(cp).convert('RGBA');canvas.alpha_composite(im,(col*256,0));draw.text((col*256+4,4),v,fill='black')
 contact=D/f'{oid}.source-plus-six-candidate.png';canvas.convert('RGB').save(contact)
 contacts.append({'object_id':oid,'source_path':obj['source_path'],'source_sha256':obj['source_sha256'],'contact_path':contact.relative_to(ROOT).as_posix(),'contact_sha256':sha(contact),'review_status':'pending-root-candidate-review','views':{v:{'path':(D/f'{oid}.{v}.candidate.png').relative_to(ROOT).as_posix(),'sha256':sha(D/f'{oid}.{v}.candidate.png')} if v in ['top','bottom'] else {'path':(OUT/f'{oid}.{v}.png').relative_to(ROOT).as_posix(),'sha256':sha(OUT/f'{oid}.{v}.png')} for v in ['front','top','right','left','bottom','rear']}})
recipe={'schema_version':1,'batch_id':REQ['batch_id'],'object_order':REQ['object_ids'],'raw_atlas_path':REQ['raw_atlas_path'],'raw_atlas_sha256':REQ['raw_atlas_sha256'],'generation_request':'reusable/views-additional/raw/candidates/closed-doorway-plans-batch01/request.json','output_binding':REQ['output_binding'],'cell_layout':{'columns':REQ['cell_layout']['columns'],'rows':REQ['cell_layout']['rows'],'atlas_size':list(raw.size),'logical_cell_size':[int(cw),int(ch)],'extraction_policy':'Full-atlas alpha connected components; map each component centroid to nearest logical cell center; retain every component >=4px in each cell; take full group bbox; verify groups do not cross cell boundaries beyond 24px.'},'candidates':files,'contacts':contacts,'notes':'Both views use uniform NEAREST scale matching the source front/rear width; four existing elevations remain untouched. Candidate plans staged for root review only.'}
(D/'normalization-recipe.json').write_text(json.dumps(recipe,indent=2)+'\n');(D/'candidate-index.json').write_text(json.dumps({'schema_version':1,'status':'staged-awaiting-root-review','candidates':contacts,'recipe_path':(D/'normalization-recipe.json').relative_to(ROOT).as_posix(),'recipe_sha256':sha(D/'normalization-recipe.json')},indent=2)+'\n');print(json.dumps({'candidate_count':len(files),'contacts':contacts,'recipe_sha256':sha(D/'normalization-recipe.json')},indent=2))
