from pathlib import Path
from PIL import Image, ImageDraw
import json, hashlib
OUT=Path(__file__).resolve().parent
PACK=OUT.parents[1]

def make(ids, name):
 idx=json.loads((OUT/'set-index.json').read_text()); assets={a['id']:a for a in idx['assets']}; sets={s['object_id']:s for s in idx['view_sets']}
 W,H=7*256,len(ids)*286
 canvas=Image.new('RGBA',(W,H),(32,32,36,255)); draw=ImageDraw.Draw(canvas)
 records=[]
 for r,oid in enumerate(ids):
  s=sets[oid]; info={"object_id":oid,"pose":s.get('pose'),"character_id":s.get('character_id'),"complete":s.get('complete'),"geometry_qa":s.get('geometry_qa')}
  first=assets[s['views']['front']]; prov=first.get('provenance',{}); src_path=PACK/prov.get('source_image', first['image']['path']); native_path=PACK/prov['native_front'] if prov.get('native_front') else PACK/'reusable/native'/f'{oid}.png'
  if not native_path.is_file(): native_path=PACK/prov.get('source_image', first['image']['path'])
  
  if not native_path.is_file():
   pose_crop=PACK/'reusable/native'/f'{oid}.png'
   if pose_crop.is_file(): native_path=pose_crop
  native=Image.open(native_path).convert('RGBA')
  scale=first.get('native_front_atlas_scale',1.0)
  if scale!=1: native=native.resize((round(native.width*scale),round(native.height*scale)),Image.Resampling.NEAREST)
  source_cell=Image.new('RGBA',(256,256),(32,32,36,255)); native.thumbnail((220,220),Image.Resampling.NEAREST); source_cell.alpha_composite(native,((256-native.width)//2,(256-native.height)//2))
  items=[('SOURCE',source_cell)]
  for view in ['front','top','right','left','bottom','rear']:
   aid=s['views'][view]; a=assets[aid]; im=Image.open(PACK/a['image']['path']).convert('RGBA')
   info.setdefault('views',{})[view]={"asset_id":aid,"sha256":a['image']['sha256']}
   cell=Image.new('RGBA',(256,256),(32,32,36,255)); cell.alpha_composite(im)
   items.append((view.upper(),cell))
  info['source']=str(src_path); info['source_sha256']=hashlib.sha256(src_path.read_bytes()).hexdigest(); info['native_front']=str(native_path); info['native_front_sha256']=hashlib.sha256(native_path.read_bytes()).hexdigest(); info['native_front_atlas_scale']=scale
  records.append(info)
  y=r*286
  for c,(label,im) in enumerate(items):
   x=c*256; canvas.alpha_composite(im,(x,y+26)); draw.text((x+6,y+5),label,fill=(255,255,255,255))
 path=OUT/'review-contacts'/f'{name}-source-six.png'; path.parent.mkdir(exist_ok=True); canvas.convert('RGB').save(path)
 jpath=path.with_suffix('.json'); jpath.write_text(json.dumps({"contact":str(path),"objects":records},indent=2)+'\n'); print(path)
make(['revamp--characters--donut','revamp--characters--donut--idle2','revamp--characters--donut--walk1','revamp--characters--donut--walk2'],'revamp-donut-batch-001a')
make(['revamp--characters--donut--walk3','revamp--characters--donut--windup','revamp--characters--donut--attack','revamp--characters--donut--hit'],'revamp-donut-batch-001b')
make(['bosses--hoarder--frame-1','bosses--hoarder--frame-2','bosses--hoarder--frame-3'],'gameplay-bosses-batch-001')
make(['menu-concepts-safe-room-services--carl-bed','menu-concepts-safe-room-services--carl-left-bedside-cabinet','menu-concepts-safe-room-services--carl-right-bedside-cabinet','menu-concepts-safe-room-services--carl-wardrobe','menu-concepts-safe-room-services--carl-potted-plant','menu-concepts-safe-room-services--carl-boots'],'safe-room-carl-batch-001')
make(['menu-concepts-safe-room-services--carl-bed'],'safe-room-carl-bed-correction')
make(['menu-concepts-safe-room-services--donut-royal-bed','menu-concepts-safe-room-services--donut-bedside-table','menu-concepts-safe-room-services--donut-left-plant','menu-concepts-safe-room-services--donut-round-stool','menu-concepts-safe-room-services--donut-flower-rug','menu-concepts-safe-room-services--donut-bedside-candles'],'safe-room-donut-batch-001')
make(['menu-concepts-safe-room-services--donut-royal-bed'],'safe-room-donut-royal-bed-correction')
make(['revamp--characters--carl--windup','revamp--characters--carl--attack','revamp--characters--carl--hit'],'revamp-carl-pose-axis-pilot')
make(['menu-concepts-safe-room-services--training-front-dumbbell','menu-concepts-safe-room-services--training-blue-mat','menu-concepts-safe-room-services--training-red-mat','menu-concepts-safe-room-services--training-gray-crate','menu-concepts-safe-room-services--training-wood-crate','menu-concepts-safe-room-services--training-metal-chest'],'safe-room-training-batch-001')
make(['room-kit--props--barrel','room-kit--props--chest','room-kit--props--crate','room-kit--props--lever','room-kit--props--pillar','room-kit--props--rubble'],'room-kit-props-batch-001')
make(['room-kit--doors--door-closed-ne','room-kit--doors--door-open-ne','room-kit--doors--door-closed-nw','room-kit--doors--door-open-nw','room-kit--doors--exit','room-kit--concept--wall-ne'],'room-kit-doors-batch-001')
make(['dungeon-stone--stone-a','dungeon-stone--stone-b','dungeon-stone--stone-c','dungeon-stone--stone-d','room-kit--floors--oil-floor','room-kit--floors--water-floor'],'room-kit-ground-batch-001')
make(['room-kit--concept--wall-nw','room-kit--walls--wall-corner','room-kit--walls--wall-ne','room-kit--walls--wall-nw','room-kit--floors--stone-a','room-kit--floors--stone-b'],'room-kit-walls-ground-batch-001')
make(['room-kit--concept--wall-nw','room-kit--walls--wall-corner','room-kit--walls--wall-ne','room-kit--walls--wall-nw','room-kit--floors--stone-a','room-kit--floors--stone-b'],'room-kit-walls-ground-batch-001')
make(['room-kit--overlays--grate','room-kit--props--stairs','room-kit--props--torch'],'room-kit-grate-stairs-torch')
make(['concepts-boss-hoarder-concept-red-barrel','concepts-boss-hoarder-concept-washing-machine','concepts-boss-hoarder-concept-crate','concepts-boss-hoarder-concept-drain-grate','concepts-boss-hoarder-concept-garbage-bag','concepts-boss-hoarder-concept-entry-arch'],'hoarder-props-batch-001')
make(['concepts-boss-juicer-concept-flying-flaming-plate','concepts-boss-juicer-concept-bench-left','concepts-boss-juicer-concept-bench-middle','concepts-boss-juicer-concept-barbell-rack','concepts-boss-juicer-concept-crate','concepts-boss-juicer-concept-barrel'],'juicer-props-batch-001')
make(['menu-concepts-safe-room-services--katia-vanity-mirror','menu-concepts-safe-room-services--katia-vanity-desk','menu-concepts-safe-room-services--katia-vanity-stool','menu-concepts-safe-room-services--katia-wardrobe','menu-concepts-safe-room-services--katia-perfume-vessel','menu-concepts-safe-room-services--katia-laundry-hamper'],'katia-vanity-batch-001')
make(['menu-concepts-safe-room-services--social-screen-monitor','menu-concepts-safe-room-services--social-screen-desk','menu-concepts-safe-room-services--social-keyboard','menu-concepts-safe-room-services--social-left-speaker','menu-concepts-safe-room-services--social-stool','menu-concepts-safe-room-services--social-left-armchair'],'social-workstation-batch-001')
make(['menu-concepts-safe-room-services--crafting-workbench','menu-concepts-safe-room-services--crafting-tool-rack','menu-concepts-safe-room-services--crafting-anvil','menu-concepts-safe-room-services--crafting-stool','menu-concepts-safe-room-services--crafting-bookcase','menu-concepts-safe-room-services--crafting-small-left-cabinet'],'crafting-workshop-batch-001')
make(['menu-concepts-safe-room-services--social-coffee-table','menu-concepts-safe-room-services--social-table-tray','menu-concepts-safe-room-services--social-table-candle','menu-concepts-safe-room-services--social-rug','menu-concepts-safe-room-services--social-left-plant','menu-concepts-safe-room-services--social-right-plant'],'social-lounge-batch-001')
make(['menu-concepts-safe-room-services--training-dummy','menu-concepts-safe-room-services--training-wall-weapon-rack','menu-concepts-safe-room-services--training-short-dumbbell','menu-concepts-safe-room-services--training-bookcase','menu-concepts-safe-room-services--training-banner','menu-concepts-safe-room-services--training-plant'],'training-room-props-batch-001')
make(['menu-concepts-safe-room-services--crafting-blue-bottle','menu-concepts-safe-room-services--crafting-green-round-bottle','menu-concepts-safe-room-services--crafting-purple-flask','menu-concepts-safe-room-services--crafting-copper-pot','menu-concepts-safe-room-services--crafting-bench-vise','menu-concepts-safe-room-services--crafting-floor-crate'],'crafting-vessels-batch-001')
make(['menu-concepts-safe-room-services--carl-rug','menu-concepts-safe-room-services--donut-canopy-frame','menu-concepts-safe-room-services--donut-left-curtain','menu-concepts-safe-room-services--donut-crown-wall-emblem','menu-concepts-safe-room-services--donut-right-plant','menu-concepts-safe-room-services--katia-rug'],'donut-room-decor-batch-001')
make(['menu-concepts-safe-room-services--crafting-small-trunk','menu-concepts-safe-room-services--crafting-rug','menu-concepts-safe-room-services--crafting-front-candle','menu-concepts-safe-room-services--crafting-potted-plant','menu-concepts-safe-room-services--social-left-wall-bookshelf','menu-concepts-safe-room-services--social-small-potted-plant'],'crafting-final-decor-batch-001')
make(['menu-concepts-safe-room-services--crafting-small-trunk','menu-concepts-safe-room-services--crafting-rug','menu-concepts-safe-room-services--crafting-front-candle','menu-concepts-safe-room-services--crafting-potted-plant','menu-concepts-safe-room-services--social-left-wall-bookshelf','menu-concepts-safe-room-services--social-small-potted-plant'],'crafting-final-decor-batch-001')
make(['menu-concepts-safe-room-services--mongo-nest','menu-concepts-safe-room-services--mongo-eggs','menu-concepts-safe-room-services--mongo-left-plant','menu-concepts-safe-room-services--mongo-right-plant','menu-concepts-safe-room-services--mongo-rug','menu-concepts-safe-room-services--training-front-candle'],'mongo-room-decor-batch-001')
make(['revamp--characters--katia','revamp--characters--katia--idle2','revamp--characters--katia--walk1','revamp--characters--katia--walk2','revamp--characters--katia--walk3','revamp--characters--katia--windup'],'katia-poses-batch-001')
make(['revamp--characters--katia--attack','revamp--characters--katia--hit'],'katia-combat-batch-001')
make(['revamp--characters--mongo','revamp--characters--mongo--idle2','revamp--characters--mongo--walk1','revamp--characters--mongo--walk2','revamp--characters--mongo--walk3','revamp--characters--mongo--windup'],'mongo-poses-batch-001')
make(['menu-concepts-safe-room-services--carl-left-wall-torch','menu-concepts-safe-room-services--crafting-wooden-stool'],'safe-room-small-props-batch-001')
make(['revamp-terrain-stone-floor','revamp-terrain-worn-floor','revamp-terrain-water-floor','revamp-terrain-oil-floor','revamp-terrain-wall-corner','revamp-terrain-moss-wall'],'revamp-terrain-floorwall-batch-001')
make(['revamp-terrain-stone-floor','revamp-terrain-worn-floor','revamp-terrain-water-floor','revamp-terrain-oil-floor','revamp-terrain-wall-corner','revamp-terrain-moss-wall'],'revamp-terrain-floorwall-batch-001')
make(['revamp-terrain-torch-wall','revamp-terrain-broken-wall','revamp-terrain-crate','revamp-terrain-fire-barrel','revamp-terrain-treasure-chest','revamp-terrain-sun-door'],'revamp-terrain-props-batch-001')
make(['expedition-enemies--cinder','expedition-enemies--frost','expedition-enemies--mauler','expedition-enemies--sentry','expedition-enemies--sludge','expedition-enemies--spore'],'expedition-enemies-frame0-batch-001')
make(['revamp-terrain-torch-wall','revamp-terrain-broken-wall'],'revamp-terrain-corner-bases-bottom-correction')
make(['expedition-enemies--cinder','expedition-enemies--frost','expedition-enemies--mauler','expedition-enemies--sentry','expedition-enemies--sludge','expedition-enemies--spore'],'expedition-enemies-frame0-batch-001')
