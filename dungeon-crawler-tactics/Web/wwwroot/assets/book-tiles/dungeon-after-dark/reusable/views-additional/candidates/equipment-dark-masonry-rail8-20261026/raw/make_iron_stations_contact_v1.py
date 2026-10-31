from pathlib import Path
import hashlib, json
from PIL import Image, ImageDraw

ASSETS=Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets')
PACK=ASSETS/'book-tiles/dungeon-after-dark'
CAND=PACK/'reusable/views-additional/candidates/equipment-dark-masonry-rail8-20261026'
HAND=json.loads(Path('/workspace/scratch/equipment-dark-masonry-rail8-handoff-20261026.json').read_text())
manifest_path=CAND/'iron-stations-candidate-manifest-v1.json';manifest=json.loads(manifest_path.read_text())
sets={(s['object_id'],s['view']):s for s in manifest['sets']}
ids=[o['object_id'] for o in HAND['objects'][2:6]];views=['front','top','right','left','bottom','rear']
tw,th=170,160;cols=13
canvas=Image.new('RGB',(cols*tw,len(ids)*(th+25)+28),'white');draw=ImageDraw.Draw(canvas)
labels=['SOURCE']+[f'BASE {v.upper()}'for v in views]+[f'CAND {v.upper()}'for v in views]
for c,l in enumerate(labels):draw.text((c*tw+3,3),l,fill='black')
proof={'candidate_id':manifest['candidate_id'],'manifest_path':str(manifest_path),'manifest_sha256':hashlib.sha256(manifest_path.read_bytes()).hexdigest(),'objects':[]}
for row,oid in enumerate(ids):
 o=next(x for x in HAND['objects']if x['object_id']==oid);source=Path(o['source']['path'])
 rp={'object_id':oid,'source':{'path':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest()},'base':{},'candidate':{}}
 proof['objects'].append(rp)
 paths=[source]+[PACK/'reusable/views-additional/images'/f'{oid}.{v}.png'for v in views]+[CAND/'images'/f'{oid}.{v}.stage1.png'for v in views]
 for c,p in enumerate(paths):
  im=Image.open(p).convert('RGBA');im.thumbnail((tw-10,th-10),Image.Resampling.NEAREST)
  bg=Image.new('RGBA',(tw-6,th-6),(238,238,238,255));d=ImageDraw.Draw(bg)
  for y in range(0,th-6,8):
   for x in range(0,tw-6,8):
    if (x//8+y//8)%2:d.rectangle((x,y,x+7,y+7),fill=(216,216,216,255))
  bg.alpha_composite(im,((bg.width-im.width)//2,(bg.height-im.height)//2));canvas.paste(bg.convert('RGB'),(c*tw+3,row*(th+25)+25))
  entry={'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
  if c==0:continue
  key=views[(c-1)%6]
  (rp['base']if c<=6 else rp['candidate'])[key]=entry
 draw.text((3,row*(th+25)+th+25),oid,fill='black')
contact=CAND/'iron-stations-source-base-candidate-contact-v1.png';canvas.save(contact)
proof['contact']={'path':str(contact),'sha256':hashlib.sha256(contact.read_bytes()).hexdigest()}
proofpath=CAND/'iron-stations-contact-proof-v1.json';proofpath.write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps({'contact':str(contact),'contact_sha256':hashlib.sha256(contact.read_bytes()).hexdigest(),'proof':str(proofpath),'proof_sha256':hashlib.sha256(proofpath.read_bytes()).hexdigest(),'manifest_sha256':proof['manifest_sha256']},indent=2))
