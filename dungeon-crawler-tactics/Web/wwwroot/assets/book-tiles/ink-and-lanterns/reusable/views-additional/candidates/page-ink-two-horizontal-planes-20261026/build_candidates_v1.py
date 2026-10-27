from pathlib import Path
import json,hashlib,shutil
from PIL import Image,ImageDraw
root=Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/ink-and-lanterns')
b=root/'reusable/views-additional/candidates/page-ink-two-horizontal-planes-20261026';(b/'inputs').mkdir(exist_ok=True);(b/'images').mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
h=Path('/workspace/scratch/scenery-ink-six-orientation-caps-handoff-20261026.json');s=json.loads(h.read_text());objects=[o for o in s['objects'] if o['object_id'] in ['thresholds-red-carpet-runner','thresholds-nebula-ceiling-panel']]
for o in objects:
 for label,r in [('source',o['source']),*o['views'].items()]:
  p=Path(r['path']);assert sha(p)==r['sha256'],p
  out=b/'inputs'/f"{o['object_id']}.{label}.png"
  if out.exists():assert sha(out)==r['sha256']
  else:shutil.copyfile(p,out)

def fit(oid,donor,rotation,width):
 p=b/'inputs'/f'{oid}.{donor}.png';im=Image.open(p).convert('RGBA');box=im.getbbox();c=im.crop(box)
 if rotation:c=c.transpose(Image.Transpose.ROTATE_90 if rotation==90 else Image.Transpose.ROTATE_180)
 factor=width/c.width;size=(round(c.width*factor),max(1,round(c.height*factor)));c=c.resize(size,Image.Resampling.NEAREST);out=Image.new('RGBA',(256,256));xy=((256-c.width)//2,(256-c.height)//2);out.paste(c,xy)
 return out,{'input_path':str(p.relative_to(root)),'input_sha256':sha(p),'alpha_bbox_xyxy':list(box),'rotation_ccw_degrees':rotation,'uniform_scale':factor,'resized_dimensions':list(size),'offset_px':list(xy),'resampler':'NEAREST','canvas':[256,256]}
rows=[]
for o in objects:
 oid=o['object_id'];carpet='red-carpet' in oid
 mapping={'top':('front',0,120),'front':('top',0,120),'rear':('top',0,120),'right':('right',90,172),'left':('left',90,172)} if carpet else {'bottom':('front',0,157),'top':('bottom',0,157),'front':('top',0,157),'rear':('top',0,157),'right':('right',90,142),'left':('left',90,142)}
 candidates={}
 for view,(donor,rot,w) in mapping.items():
  im,recipe=fit(oid,donor,rot,w);p=b/'images'/f'{oid}.{view}.candidate-v1.png';im.save(p);candidates[view]={'path':str(p.relative_to(root)),'sha256':sha(p),'recipe':recipe}
 rows.append({'object_id':oid,'source':{'path':str(Path(o['source']['path']).relative_to(root)),'sha256':o['source']['sha256']},'base_views':{v:{'path':str(Path(r['path']).relative_to(root)),'sha256':r['sha256']} for v,r in o['views'].items()},'candidates':candidates,'preserved_views':['bottom'] if carpet else [],'inference':'Horizontal floor rug, decorated face above; retained backing below.' if carpet else 'Horizontal ceiling panel, decorated face below; plain backing above. Opposite unmarked thin edges inferred symmetric.','required_symmetry':[{'views':['front','rear'],'reason':'Inferred identical opposite unmarked thin edge projection from same retained edge input.'}]})
# Compare current row followed by candidate row; source repeated for explicit native identity.
cell=180;head=24;rowh=212;contact=Image.new('RGB',(cell*7,rowh*4),(244,244,244));draw=ImageDraw.Draw(contact)
for n,(o,row) in enumerate(zip(objects,rows)):
 for proposed in [False,True]:
  y=(n*2+proposed)*rowh;draw.text((4,y+2),o['object_id']+(' PROPOSED' if proposed else ' CURRENT'),fill='black')
  for col,v in enumerate(['source','front','top','right','left','bottom','rear']):
   p=b/'inputs'/f"{o['object_id']}.{v}.png"
   if proposed and v in row['candidates']:p=root/row['candidates'][v]['path']
   im=Image.open(p).convert('RGBA');im.thumbnail((172,172),Image.Resampling.NEAREST);x=col*cell+(cell-im.width)//2;contact.paste(im,(x,y+head),im);draw.text((col*cell+4,y+192),v,fill='black')
p=b/'source-current-candidate-contact-v1.png';contact.save(p)
script=b/'build_candidates_v1.py';shutil.copyfile(__file__,script) if Path(__file__)!=script else None
manifest={'scope':'book-tiles/ink-and-lanterns','candidate_only':True,'candidate_owner':'page_inventory','reviewer':'root','installer':'views_ink_books','handoff_archival':str(h),'handoff_sha256':sha(h),'script':{'path':str(script.relative_to(root)),'sha256':sha(script)},'objects':rows,'contact':{'path':str(p.relative_to(root)),'sha256':sha(p)},'rules':['No production outputs/index/sidecars modified. Every current source/six rechecked before snapshot.','All output geometry is retained source-bound pixel re-key/rigid rotation/uniform nearest-neighbor scale; no new paint.','Inputs are immutable retained byte copies, no live-leaf replay dependency.','Whole-set approval remains independent Root current-source/six review after Ink installation.']}
(b/'candidate-manifest-v1.json').write_text(json.dumps(manifest,indent=2)+'\n');print(str(b/'candidate-manifest-v1.json'));print(sha(p))
