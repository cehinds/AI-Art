#!/usr/bin/env python3
"""Extract reviewed native concept rectangles and build a seeded connected tile example.
Run: python tools/build_pocket_scene_assets.py --seed 23
Crops preserve source pixels. Rectangular scene patches are never isolated sprites.
"""
from pathlib import Path
import argparse,hashlib,json,random,struct
from PIL import Image
import numpy as np
from scipy import ndimage
ROOT=Path(__file__).resolve().parents[1]/'dungeon-crawler-tactics/Web/wwwroot/assets/style-packs/pocket-dungeon'
OUT=ROOT/'reusable/scene-assets'
def savejson(p,d): p.write_text(json.dumps(d,indent=2)+'\n')
def build(seed):
 OUT.mkdir(parents=True,exist_ok=True); assets=[]; placements={}; sources={s:Image.open(ROOT/f'concepts/{s}.png').convert('RGBA') for s in ['original','new','combat']}
 def crop(scene,name,rect,kind='ui_region',reusable=True,role='semantic',mask=None):
  x,y,w,h=rect; im=sources[scene].crop((x,y,x+w,y+h)); aid=f'{scene}-{name}'; p=OUT/f'{aid}.png'
  if mask:
   pixels=np.array(im)
   if mask['type']=='border-insets':
    inset=mask['inset_px'];pixels[inset:h-inset,inset:w-inset,3]=0
   elif mask['type']=='border-connected-cream':
    rgb=pixels[:,:,:3].astype(np.int16);cream=(rgb[:,:,0]>195)&(rgb[:,:,1]>175)&(rgb[:,:,2]>110)&((rgb[:,:,0]-rgb[:,:,2])>15)
    labels,_=ndimage.label(cream,np.ones((3,3)));edge=np.unique(np.concatenate([labels[0],labels[-1],labels[:,0],labels[:,-1]]));edge=edge[edge!=0];pixels[np.isin(labels,edge),3]=0
   else:raise ValueError('Unknown extraction mask')
   im=Image.fromarray(pixels)
  im.save(p)
  rel=p.relative_to(ROOT).as_posix(); meta=p.with_suffix('.json'); d={'id':aid,'name':name.replace('-',' ').title(),'kind':kind,'tags':[scene,'native-pixels','screen-space' if kind=='ui_region' else 'concept-extraction'],'image':{'path':rel,'width':w,'height':h,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'rgba_sha256':hashlib.sha256(struct.pack('>II',w,h)+im.tobytes()).hexdigest()},'metadata_path':meta.relative_to(ROOT).as_posix(),'provenance':{'method':'extracted','source_image':f'concepts/{scene}.png','source_rect':rect},'anchor_px':[0,0],'views':{'applicable':False,'complete':True,'reason':'screen-space UI element' if kind=='ui_region' else 'flat terrain sample' if kind=='terrain_tile' else 'screen-space reconstruction patch; hidden surfaces unavailable'},'reusable':reusable}
  if mask:d['provenance']['mask']=mask;d['tags'].append('transparent-extraction');d['limitations']='Only retained source pixels are copied; removed background is transparent. No hidden pixels are invented.'
  if kind=='reconstruction_patch': d['limitations']='Flattened scene crop includes baked ground, lighting and/or neighboring pixels. Not an isolated sprite; cannot reveal occluded art.'
  if kind=='terrain_tile': d['procedural']={'cell_size_px':w,'walkable':True,'connections':['north','east','south','west'],'rotation_degrees':[0,90,180,270],'edge_policy':'interior texture sample; repeat seams may be visible, no edge compatibility claim'}
  savejson(meta,d);assets.append(d); placements.setdefault('source-'+scene,[]).append({'asset_id':aid,'path':rel,'x':x,'y':y,'z':len(assets),'rotation_deg':0,'scale':1,'blend':'replace','role':role});return d
 # Whole HUD is an exact reconstruction patch; all semantic elements below exported individually.
 for s,y,h in [('original',764,160),('new',787,134),('combat',766,156)]:
  crop(s,'hotbar-composite',[0,y,1672,h],'reconstruction_patch',False)
  crop(s,'hotbar-backing-swatch',[155,y+5,17,10])
  crop(s,'hotbar-outline',[0,y,1672,h],mask={'type':'border-insets','inset_px':7})
 for s,r in [('original',[18,20,453,72]),('new',[18,18,586,59]),('combat',[19,18,495,70])]:
  crop(s,'objective-banner',r);crop(s,'objective-alert-icon',[39,29 if s=='new' else 32,43,43]);crop(s,'objective-label',[101,29,486 if s=='new' else 341 if s=='original' else 396,40 if s!='combat' else 48])
 for s in ['original','combat']: crop(s,'party-turn-badge',[1350,19,311,66]);crop(s,'party-turn-hourglass',[1370,31,38,40]);crop(s,'party-turn-label',[1424,32,224,36])
 crop('original','move-selected-indicator',[872,769,36,23],mask={'type':'border-connected-cream'})
 crop('new','minimap',[1374,17,287,170]);crop('new','inspect-machine-prompt',[536,523,151,68]);crop('new','prompt-gamepad-a',[549,541,33,33]);crop('new','prompt-inspect-label',[587,536,84,42])
 # Character panels, portrait frames with visible portraits, and bars retain their native context.
 for s,boxes in {'original':[(29,776,126,139),(411,782,91,91),(527,782,91,91),(642,782,92,91)],'new':[(26,799,100,109),(289,802,80,92),(501,802,81,92),(721,802,84,92)],'combat':[(24,775,120,135),(392,778,94,90),(507,778,93,90),(622,778,93,90)]}.items():
  for i,(x,y,w,h) in enumerate(boxes):
   n=['carl','donut','katia','mongo'][i];crop(s,n+'-portrait-frame',[x,y,w,h]);crop(s,n+'-portrait',[x+5,y+5,w-10,h-10]);
   if i==0:
    bx,by,bw=(175,853,208) if s=='original' else (136,855,134) if s=='new' else (162,836,201)
   else: bx,by,bw=(x,879,w) if s=='original' else (x+92,y+53,106) if s=='new' else (x,874,w)
   crop(s,n+'-hp-bar',[bx,by,bw,13]);crop(s,n+'-mana-bar',[bx,by+20 if s!='new' else by+41,bw,13])
   if s=='new':crop(s,n+'-party-card',[x,798,244 if i==0 else 204,112])
 for s,buttons in {'original':[('move',818,790,140,112),('kick',976,790,126,112),('bomb',1116,790,131,112),('items',1263,790,134,112)],'new':[('inspect',979,801,132,105),('interact',1129,802,133,102),('party',1274,803,127,102)],'combat':[('move',1084,789,106,94),('bomb',1204,789,108,95),('items',1325,789,111,95)]}.items():
  for n,x,y,w,h in buttons:
   crop(s,n+'-button',[x,y,w,h]);crop(s,n+'-icon',[x+24,y+12,w-48,51]);crop(s,n+'-label',[x+8,y+69,w-16,26]);crop(s,n+'-frame-top',[x+10,y,w-20,7])
   crop(s,n+'-frame-outline',[x,y,w,h],mask={'type':'border-insets','inset_px':8})
   crop(s,n+'-icon-transparent',[x+24,y+12,w-48,51],mask={'type':'border-connected-cream'})
 crop('combat','selected-kick-command',[764,787,306,78]);crop('combat','kick-icon',[789,799,52,49]);crop('combat','kick-command-label',[853,811,197,30]);crop('combat','confirm-prompt',[793,872,128,40]);crop('combat','cancel-prompt',[937,872,117,40]);crop('combat','end-turn-button',[1478,791,176,77]);crop('combat','end-turn-icon',[1497,815,25,29]);crop('combat','end-turn-label',[1525,815,115,29]);crop('combat','move-pips',[279,895,85,23]);crop('combat','charge-bubble',[1375,363,120,66]);crop('combat','danger-tile',[919,229,82,72],'reconstruction_patch',False)
 # Exact local scene patches, deliberately labelled non-reusable rather than claiming alpha separation.
 patches={'original':[('carl',171,275,115,140),('donut',342,384,109,90),('katia',235,490,119,153),('mongo',366,493,201,155),('rat-sword',923,126,152,117),('rat-charge',1120,382,149,116),('rat-club',1156,547,175,127),('rescued-crawler',1325,458,129,119),('rescue-alert',1380,401,49,58),('exit-portal',1482,235,151,247)],'new':[('merchant',397,204,96,104),('frog-vendor',750,153,96,107),('donut-counter',478,222,110,82),('guard',1353,290,97,173),('carl',365,568,116,164),('katia',726,571,112,145),('mongo',108,352,166,119),('turnstile',1040,217,308,213),('machine',411,411,231,307),('house-entry',1527,237,144,279),('merchant-stall',347,86,308,309),('frog-stall',669,63,253,328)],'combat':[('carl',361,241,110,150),('donut',190,435,121,101),('katia',408,478,138,157),('mongo',605,482,211,145),('merchant-cart',686,304,211,151),('bomb-rat',943,151,179,125),('charge-rat',1290,394,178,148),('house-portal',1470,94,153,266),('produce-cart',186,130,164,157)]}
 for s,ps in patches.items():
  for n,x,y,w,h in ps:crop(s,n+'-scene-patch',[x,y,w,h],'reconstruction_patch',False)
 tiles=[crop('original','floor-interior-a',[458,369,32,32],'terrain_tile'),crop('original','floor-interior-b',[460,438,32,32],'terrain_tile'),crop('new','floor-interior-c',[285,687,32,32],'terrain_tile'),crop('combat','floor-interior-d',[824,178,32,32],'terrain_tile')]
 savejson(OUT/'index.json',{'schema_version':1,'description':'Native semantic crops; overlapping exact placement layers. Composite patches retain baked surroundings. No hidden pixels invented.','assets':assets,'placements':placements})
 procedural(seed,tiles)
def procedural(seed,tiles):
 out=ROOT/'reusable/procedural';out.mkdir(exist_ok=True,parents=True);rng=random.Random(seed);w,h=24,18;walk={(2,2)};x,y=2,2
 # Carve a deterministic random walk and guaranteed route to the exit.
 for _ in range(700):
  dx,dy=rng.choice([(1,0),(-1,0),(0,1),(0,-1)]);x=max(1,min(w-2,x+dx));y=max(1,min(h-2,y+dy));walk.add((x,y))
 for x in range(2,w-1):walk.add((x,2))
 for y in range(2,h-1):walk.add((w-2,y))
 reached={(2,2)};todo=[(2,2)]
 while todo:
  a,b=todo.pop()
  for p in [(a+1,b),(a-1,b),(a,b+1),(a,b-1)]:
   if p in walk and p not in reached:reached.add(p);todo.append(p)
 assert reached==walk and (w-2,h-2) in reached
 im=Image.new('RGBA',(w*32,h*32),(20,18,35,255));cells=[]
 for y in range(h):
  for x in range(w):
   yes=(x,y) in walk;c={'x':x,'y':y,'walkable':yes,'connections':[]}
   if yes:
    t=rng.choice(tiles);rot=rng.choice([0,90,180,270]);im.alpha_composite(Image.open(ROOT/t['image']['path']).convert('RGBA').rotate(rot),(x*32,y*32));c.update(asset_id=t['id'],path=t['image']['path'],rotation_deg=rot,position_px=[x*32,y*32],anchor_px=[0,0]);c['connections']=[n for n,dx,dy in [('north',0,-1),('east',1,0),('south',0,1),('west',-1,0)] if (x+dx,y+dy) in walk]
   cells.append(c)
 objects=[]
 for aid,pos in [('rat',(w-2,h-2)),('crate',(2,2))]:
  source=ROOT/f'components/{aid}.png'
  sprite=Image.open(source).convert('RGBA'); scale=32/max(sprite.size); size=(max(1,round(sprite.width*scale)),max(1,round(sprite.height*scale))); preview=sprite.resize(size,Image.Resampling.NEAREST);px=pos[0]*32+(32-size[0])//2;py=pos[1]*32+32-size[1];im.alpha_composite(preview,(px,py));objects.append({'asset_id':aid,'path':f'components/{aid}.png','cell':list(pos),'position_px':[px,py],'rotation_deg':0,'scale':scale,'render_size_px':list(size),'resampling':'nearest','blocks_movement':False})
 im.save(out/'sample.png');savejson(out/'sample.json',{'schema_version':1,'seed':seed,'rotation_convention':'counterclockwise','grid':{'width':w,'height':h,'cell_size_px':32},'entry':[2,2],'exit':[w-2,h-2],'validation':{'all_walkable_cells_connected':True,'reachable_walkable_cells':len(reached)},'cells':cells,'objects':objects,'limitations':'Interior texture samples may show repeat seams. Dark cells are uncarved void, not wall artwork. No invented scene sprites.','generator':'tools/build_pocket_scene_assets.py --seed '+str(seed)})
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--seed',type=int,default=23);build(ap.parse_args().seed)
