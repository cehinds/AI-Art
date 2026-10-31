"""Asset-only shop/temple room composition. Writes only this isolated staging kit."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageChops
import json,hashlib,math,argparse

BASE=Path(__file__).resolve().parents[2]
GAME=BASE.parents[1]
CFG=Path(__file__).with_name('kit.json')
PROD=BASE/'Assets/Art/Production/ShopInteriorsV1'
REVIEW=BASE/'Review/shop-interiors-v1'
RAW=BASE/'ArtSource/ShopInteriorsV1'
TILE=32;CANVAS=(448,416)
REQUIRED=['weapon-display','armor-display','item-display','magic-display','temple-altar','temple-wall','item-clerk','armorer','temple-cleric']

def sha(data):return hashlib.sha256(data).hexdigest()
def load(path,default=None):return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default
def write_json(path,data):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
def png(im):
 import io
 stream=io.BytesIO();im.save(stream,format='PNG');return stream.getvalue()
def save(path,data):
 path.parent.mkdir(parents=True,exist_ok=True)
 if path.exists() and path.read_bytes()!=data:
  if path.is_relative_to(PROD/'rooms'):
   previous=path.read_bytes();backup=RAW/'proof-iterations'/(path.parent.name+'-'+path.stem+'-'+sha(previous)[:12]+'.png');backup.parent.mkdir(parents=True,exist_ok=True)
   if not backup.exists():backup.write_bytes(previous)
   path.write_bytes(data);return
  raise ValueError('Preserve differing output; version the asset: '+str(path))
 if not path.exists():path.write_bytes(data)
def asset_record(path):
 data=path.read_bytes();im=Image.open(path);return {'file':path.relative_to(BASE).as_posix(),'sha256':sha(data),'width':im.width,'height':im.height}

def normalize(source,c):
 im=source.convert('RGBA');x,y,w,h=c.get('crop',[0,0,im.width,im.height])
 if min(x,y)<0 or min(w,h)<=0 or x+w>im.width or y+h>im.height:raise ValueError('Invalid crop '+c['id'])
 im=im.crop((x,y,x+w,y+h));bounds=[0,0,w,h]
 if c['alpha']=='binary':
  a=im.getchannel('A').point(lambda v:255 if v>=128 else 0);bounds=a.getbbox()
  if bounds is None:raise ValueError('Empty cutout '+c['id'])
  if a.getextrema()[0]!=0:raise ValueError('Cutout lacks actual transparent background '+c['id'])
  im.putalpha(a);im=im.crop(bounds)
  factor=min((c['size'][0]-4)/im.width,(c['size'][1]-4)/im.height)
  size=(max(1,round(im.width*factor)),max(1,round(im.height*factor)));im=im.resize(size,Image.Resampling.NEAREST)
  out=Image.new('RGBA',c['size'],(0,0,0,0));offset=((out.width-im.width)//2,out.height-2-im.height);out.alpha_composite(im,offset)
 else:
  if im.getchannel('A').getextrema()!=(255,255):raise ValueError('Opaque wall has transparency '+c['id'])
  out=im.resize(c['size'],Image.Resampling.NEAREST);offset=(0,0)
 return out,{'sourceCrop':[x,y,w,h],'alphaBounds':list(bounds),'nativePlacement':list(offset),'anchor':[c['size'][0]//2,c['size'][1]-2 if c['alpha']=='binary' else c['size'][1]],'normalization':'alpha128 bbox, nearest aspect fit with2px transparent padding' if c['alpha']=='binary' else 'opaque nearest full canvas'}

def export_components(cfg):
 records={c['id']:dict(c) for c in cfg['reused']}
 for c in cfg['generated']:
  source=BASE/c['source'];data=source.read_bytes();assert sha(data)==c['rawSha256'],'Generated source drift';im,details=normalize(Image.open(source),c);path=PROD/'components'/(c['id']+'.png');save(path,png(im))
  records[c['id']]={**c,**asset_record(path),**details,'sourceSha256':sha(data),'operation':'normalized generated component; source preserved','logicalSizePx':[im.width*32/c['ppu'],im.height*32/c['ppu']]}
 for c in cfg.get('sharedDependencies',[]):
  source=BASE/c['file'];data=source.read_bytes();assert sha(data)==c['sha256'],'Shared terrain drift'
  records[c['id']]={**c,'operation':'unchanged sibling dependency; not copied or authored in shop kit'}
 return records

def logical_image(c):
 path=BASE/c['file'];data=path.read_bytes();assert sha(data)==c['sha256'],'Component source drift: '+c['id']
 im=Image.open(path).convert('RGBA');size=(round(im.width*32/c['ppu']),round(im.height*32/c['ppu']))
 return im if im.size==size else im.resize(size,Image.Resampling.NEAREST)

def make_room(kind,components):
 temple=kind=='temple';layers={name:Image.new('RGBA',CANVAS,(0,0,0,0)) for name in ['floor','wall','furniture','npc']};placements=[];blocked=set()
 def place(cid,layer,left,top,role,tiles=None):
  im=logical_image(components[cid]);layers[layer].alpha_composite(im,(left,top));cells=tiles or []
  for cell in cells:blocked.add(tuple(cell))
  placements.append({'component':cid,'layer':layer,'rectPx':[left,top,im.width,im.height],'role':role,'bottomCenterPx':[left+im.width/2,top+im.height],'proposedCollisionCells':cells,'occlusionBaseY':top+im.height})
 def floor_region(cid,rect,role):
  im=logical_image(components[cid]);x,y,w,h=rect
  for yy in range(y,y+h,im.height):
   for xx in range(x,x+w,im.width):layers['floor'].alpha_composite(im.crop((0,0,min(im.width,x+w-xx),min(im.height,y+h-yy))),(xx,yy))
  placements.append({'component':cid,'layer':'floor','rectPx':list(rect),'role':role,'proposedCollisionCells':[],'operation':'regular repeat proof; no new edge repair'})
 floor_region('cool-floor' if temple else 'red-floor',(32,64,384,320),'main interior ground')
 floor_region('shop-flagstone' if not temple else 'cool-floor',(192,352,64,64),'clear two-cell entrance threshold')
 wall='temple-wall' if temple else 'shop-wall';face=logical_image(components[wall]);northY=64-face.height
 for x in range(32,416,face.width):
  cropped=face.crop((0,0,min(face.width,416-x),face.height));layers['wall'].alpha_composite(cropped,(x,northY))
 placements.append({'component':wall,'layer':'wall','rectPx':[32,northY,384,face.height],'role':'north wall face, bottom aligned to floor boundary','proposedCollisionCells':[[x,y] for x in range(1,13) for y in range(2)],'operation':'whole authored components repeated in proof; no seamlessness claim'})
 blocked.update((x,y) for x in range(14) for y in range(2))
 for y in range(2,13):
  place('wall-cap-w','wall',0,y*32,'cutaway side boundary',[[0,y]]);place('wall-cap-e','wall',416,y*32,'cutaway side boundary',[[13,y]])
 for x in range(1,13):
  if x not in [6,7]:place('wall-cap-s','wall',x*32,384,'south wall with entrance gap',[[x,12]])
 if temple:
  place('temple-rug','floor',192,160,'blue/cream central aisle rug')
  place('temple-altar','furniture',192,96,'temple altar with integral candles',[[6,4],[7,4],[8,4]])
  for x in [3,10]:place('stone-pillar','furniture',x*32,96,'sanctuary-side stone support',[[x,3]])
  for x in [3,10]:
   for y in [7,9]:place('red-chair','furniture',x*32,y*32-48,'side seating',[[x,y-1]])
  npc='temple-cleric';anchor=[240,96];service=[[7,5],[6,5],[8,5]]
 else:
  place('shop-rug','floor',144,192,'shared cream/lilac customer rug')
  display={'weapon':'weapon-display','armor':'armor-display','item':'item-display','magic':'magic-display'}[kind]
  place(display,'furniture',96,64,kind+' stock display',[[3,3],[4,3]])
  place(display,'furniture',352,64,kind+' stock display',[[11,3],[12,3]])
  place('gold-counter','furniture',64,128,'shared golden counter front',[[x,4] for x in range(2,6)])
  place('gold-counter-corner','furniture',174,96,'shared golden L counter; source alpha edges overlap straight segment',[[x,4] for x in range(5,10)]+[[8,3],[9,3]])
  npc={'weapon':'shopkeeper','armor':'armorer','item':'item-clerk','magic':'magic-clerk'}[kind];anchor=[240,128];service=[[7,5],[6,5],[8,5]]
 actor=logical_image(components[npc]);place(npc,'npc',anchor[0]-actor.width//2,anchor[1]-actor.height,'static down-idle attendant',[[7,2 if temple else 3]])
 composite=Image.new('RGBA',CANVAS,(0,0,0,0))
 for name in ['floor','wall','npc','furniture']:composite.alpha_composite(layers[name])
 # All attendants stand completely above counter/altar front art: faces remain visible.
 npcPlacement=placements[-1];actorRect=npcPlacement['rectPx'];faceBox=(actorRect[0],actorRect[1],actorRect[0]+actorRect[2],actorRect[1]+max(1,actorRect[3]//3))
 assert layers['furniture'].getchannel('A').crop(faceBox).getbbox() is None,'Furniture hides attendant face: '+kind
 overlap=ImageChops.multiply(layers['npc'].getchannel('A'),layers['furniture'].getchannel('A')).getbbox()
 assert overlap is None or overlap[1]>=actorRect[1]+actorRect[3]-2,'Furniture hides more than attendant feet: '+kind
 metadata={'id':kind,'shopType':kind,'status':'asset-only assembled room candidate','referenceBasis':'confirmed Tobul shop materials; starter layout inferred' if kind=='weapon' else 'shared starter-shop art direction; individual retail layout not verified' if not temple else 'proposed distinct temple candidate; no verified retail temple reference','canvasPx':list(CANVAS),'tilePixels':32,'pixelsPerUnit':32,'layerOrder':['floor','wall','npc','furniture'],'placements':placements,'entryCells':[[6,12],[7,12]],'serviceApproachCells':service,'proposedBlockedCells':[list(c) for c in sorted(blocked)],'collisionScope':'proposed placement metadata only; not a runtime collision implementation','notes':['No sprites or layers from retail screenshots.','Static attendants only; no animation, dialogue, shop stock, event or runtime claim.','Floor and walls shared across ordinary shops; fixture and attendant vary.']}
 return layers,composite,metadata

def check_routes(room):
 blocked={tuple(c) for c in room['proposedBlockedCells']};starts=[tuple(c) for c in room['entryCells']]
 assert all(c not in blocked for c in starts),'Entrance blocked'
 visited=set(starts);queue=list(starts)
 for x,y in queue:
  for nx,ny in [(x+1,y),(x-1,y),(x,y+1),(x,y-1)]:
   if 0<=nx<14 and 0<=ny<13 and (nx,ny) not in blocked and (nx,ny) not in visited:visited.add((nx,ny));queue.append((nx,ny))
 assert all(tuple(c) in visited for c in room['serviceApproachCells']),'Service lane disconnected'
 return len(visited)

def build():
 cfg=load(CFG);components=export_components(cfg);missing=[name for name in REQUIRED+['shop-flagstone'] if name not in components]
 if missing:raise ValueError('Required generated/shared inputs pending: '+', '.join(missing))
 manifest={'schemaVersion':1,'kit':'shop-interiors-v1','status':'asset-only starter candidates; not integrated','ownedComponentCount':len(cfg['reused'])+len(cfg['generated']),'generatedComponentCount':len(cfg['generated']),'reusedComponentCount':len(cfg['reused']),'sharedDependencyCount':len(cfg.get('sharedDependencies',[])),'components':[c for c in components.values() if c['file'].startswith('Assets/Art/Production/ShopInteriorsV1/')],'sharedDependencies':[c for c in components.values() if not c['file'].startswith('Assets/Art/Production/ShopInteriorsV1/')],'rooms':[],'limits':['Temple is an art-direction proposal, not a verified retail match.','No new repeat/seamlessness contract is assigned to approved whole walls/rugs/counters.','No game code, scene, build, NPC behavior or Art-repository changes.']}
 for kind in ['weapon','armor','item','magic','temple']:
  layers,composite,room=make_room(kind,components);room['reachableProposalCells']=check_routes(room);outputs={}
  for layer,im in [*layers.items(),('composite',composite)]:
   path=PROD/'rooms'/kind/(layer+'.png');save(path,png(im));outputs[layer]=asset_record(path)
  room['outputs']=outputs;path=PROD/'rooms'/kind/'placement.json';write_json(path,room);manifest['rooms'].append(room)
  review=REVIEW/'rooms'/(kind+'-3x.png');review.parent.mkdir(parents=True,exist_ok=True);review.write_bytes(png(composite.resize((CANVAS[0]*3,CANVAS[1]*3),Image.Resampling.NEAREST)))
 manifest['sourceRecords']=[{'file':path.relative_to(BASE).as_posix(),'sha256':sha(path.read_bytes())} for path in sorted(RAW.rglob('*')) if path.is_file() and 'proof-iterations' not in path.parts]
 write_json(PROD/'manifest.json',manifest);make_gallery(manifest);print('Built',manifest['ownedComponentCount'],'owned components +',manifest['sharedDependencyCount'],'unchanged shared floor dependency and5room layer sets; no integration.')

def make_gallery(manifest):
 font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',17);small=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',12);cols=3;cw=480;ch=510;sheet=Image.new('RGBA',(cols*cw,70+2*ch),(22,29,40,255));draw=ImageDraw.Draw(sheet);draw.text((18,16),'ShopInteriorsV1 / five asset-only starter room candidates',font=font,fill='#f6dfae')
 for i,room in enumerate(manifest['rooms']):
  x=(i%cols)*cw;y=70+(i//cols)*ch;im=Image.open(BASE/room['outputs']['composite']['file']).convert('RGBA')
  sheet.alpha_composite(im,(x+16,y));draw.text((x+18,y+430),room['id'].upper(),font=font,fill='#f6dfae');draw.text((x+18,y+461),'PROPOSED TEMPLE' if room['id']=='temple' else 'Shared floor/wall/counter; distinct stock + clerk',font=small,fill='#c8d6e5')
 REVIEW.mkdir(parents=True,exist_ok=True);(REVIEW/'contact-sheet.png').write_bytes(png(sheet))
 cards=''
 for room in manifest['rooms']:
  links=' | '.join(f'<a href="../../{row["file"]}">{name}</a>' for name,row in room['outputs'].items())
  cards+=f'<article><h2>{room["id"]}</h2><img src="../../{room["outputs"]["composite"]["file"]}"><p>{room["referenceBasis"]}</p><p>{links}</p><p><a href="../../Assets/Art/Production/ShopInteriorsV1/rooms/{room["id"]}/placement.json">Placement/collision proposal</a></p></article>'
 html='<!doctype html><meta charset="utf-8"><title>ShopInteriorsV1</title><style>body{font:17px system-ui;background:#161d28;color:#d8e4ee;margin:28px}a{color:#8cceff}main{display:grid;grid-template-columns:repeat(2,minmax(400px,1fr));gap:20px}article{border:1px solid #586e82;padding:16px}img{width:100%;image-rendering:pixelated;background:#0b1018}</style><h1>ShopInteriorsV1</h1><p>Five layered asset candidates. No game integration or runtime claims. Temple is proposed art direction.</p><p><a href="../../Docs/ShopInteriorsV1/README.md">Source scope and contracts</a></p><main>'+cards+'</main>'
 extra='<section><h2>Components and layers</h2><p><a href="component-sheet.png">Individual component sheet</a> | <a href="alpha-edge-proof.png">NPC/altar alpha proof</a></p><ul>'
 for room in manifest['rooms']:extra+=f'<li><a href="layers/{room["id"]}-layers.png">{room["id"]} ordered layers</a></li>'
 (REVIEW/'index.html').write_text(html+extra+'</ul></section>',encoding='utf-8')

def verify():
 m=load(PROD/'manifest.json');assert m and len(m['rooms'])==5
 prompts=load(RAW/'generation-prompts.json');assert len(prompts['generations'])==10,'Expected nine selected generations plus one preserved altar iteration'
 for generation in prompts['generations']:assert (RAW/generation['savedAs']).is_file(),'Missing generation source registration'
 for record in m['sourceRecords']:assert sha((BASE/record['file']).read_bytes())==record['sha256'],'Source/provenance record drift'
 for c in m['components']+m.get('sharedDependencies',[]):
  p=BASE/c['file'];assert sha(p.read_bytes())==c['sha256'],'Component drift: '+c['id']
  if c.get('source'):
   source=BASE/c['source'];assert sha(source.read_bytes())==c.get('sourceSha256',c['sha256']),'Preserved source drift'
 for room in m['rooms']:
  composed=Image.new('RGBA',CANVAS,(0,0,0,0))
  for layer in room['layerOrder']:
   data=room['outputs'][layer];p=BASE/data['file'];assert sha(p.read_bytes())==data['sha256'];im=Image.open(p).convert('RGBA');assert im.size==CANVAS;composed.alpha_composite(im)
  assert composed.tobytes()==Image.open(BASE/room['outputs']['composite']['file']).convert('RGBA').tobytes(),'Room layers do not reconstruct'
  npc=Image.open(BASE/room['outputs']['npc']['file']).getchannel('A');furniture=Image.open(BASE/room['outputs']['furniture']['file']).getchannel('A');overlap=ImageChops.multiply(npc,furniture).getbbox();actor=next(p for p in room['placements'] if p['layer']=='npc')['rectPx'];assert overlap is None or overlap[1]>=actor[1]+actor[3]-2,'Clerk torso/face occlusion'
  check_routes(room)
 for c in m['components']:
  if c.get('operation','').startswith('normalized'):
   im=Image.open(BASE/c['file']).convert('RGBA');assert set(im.getchannel('A').get_flattened_data())<={0,255},'Generated nonbinary alpha'
   assert all(pixel[:3]==(0,0,0) for pixel in im.get_flattened_data() if pixel[3]==0),'Invisible RGB uncleared'
 expected={c['file'] for c in m['components'] if c['file'].startswith('Assets/Art/Production/ShopInteriorsV1/')}
 expected.update(v['file'] for room in m['rooms'] for v in room['outputs'].values())
 actual={path.relative_to(BASE).as_posix() for path in PROD.rglob('*.png')};assert expected==actual,'Missing/unlisted shop PNGs'
 print('ProductionPNGcount',len(actual))
 print('PASS source/output hashes; five layer reconstructions; clear entrance + service lanes; no runtime claim.')

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['build','verify','inventory']);args=parser.parse_args()
 if args.action=='build':build()
 elif args.action=='verify':verify()
 else:print(json.dumps(export_components(load(CFG)),indent=2))
