from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw
ASSETS=Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets');PACK=ASSETS/'book-tiles/dungeon-after-dark';CAND=PACK/'reusable/views-additional/candidates/equipment-dark-masonry-rail8-20261026'
HAND=json.loads(Path('/workspace/scratch/equipment-dark-masonry-rail8-handoff-20261026.json').read_text());M=CAND/'iron-trains-candidate-manifest-v2.json';man=json.loads(M.read_text());S={(x['object_id'],x['view']):x for x in man['sets']};views=['front','top','right','left','bottom','rear'];ids=['iron-trains-riveted-carriage-metal-inner-corner','iron-trains-riveted-carriage-metal-endcap-northwest']
tw,th=172,160;canvas=Image.new('RGB',(13*tw,2*(th+26)+30),'white');d=ImageDraw.Draw(canvas)
for c,l in enumerate(['SOURCE']+[f'BASE {v.upper()}'for v in views]+[f'CAND {v.upper()}'for v in views]):d.text((c*tw+2,2),l,fill='black')
proof={'candidate_id':man['candidate_id'],'manifest_path':str(M),'manifest_sha256':hashlib.sha256(M.read_bytes()).hexdigest(),'objects':[]}
for r,oid in enumerate(ids):
 o=next(x for x in HAND['objects']if x['object_id']==oid);src=Path(o['source']['path']);row={'object_id':oid,'source':{'path':str(src),'sha256':hashlib.sha256(src.read_bytes()).hexdigest()},'base':{},'candidate':{}};proof['objects'].append(row)
 paths=[src]+[PACK/'reusable/views-additional/images'/f'{oid}.{v}.png'for v in views]+[CAND/'images'/f'{oid}.{v}.stage2.png'for v in views]
 for c,p in enumerate(paths):
  im=Image.open(p).convert('RGBA');im.thumbnail((tw-10,th-10),Image.Resampling.NEAREST);bg=Image.new('RGBA',(tw-6,th-6),(238,238,238,255));bd=ImageDraw.Draw(bg)
  for y in range(0,th-6,8):
   for x in range(0,tw-6,8):
    if(x//8+y//8)%2:bd.rectangle((x,y,x+7,y+7),fill=(214,214,214,255))
  bg.alpha_composite(im,((bg.width-im.width)//2,(bg.height-im.height)//2));canvas.paste(bg.convert('RGB'),(c*tw+3,r*(th+26)+24))
  entry={'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
  if c: (row['base']if c<=6 else row['candidate'])[views[(c-1)%6]]=entry
 d.text((2,r*(th+26)+th+25),oid,fill='black')
cp=CAND/'iron-trains-source-base-candidate-contact-v2.png';canvas.save(cp);proof['contact']={'path':str(cp),'sha256':hashlib.sha256(cp.read_bytes()).hexdigest()}
pp=CAND/'iron-trains-contact-proof-v2.json';pp.write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps({'contact':str(cp),'contact_sha256':hashlib.sha256(cp.read_bytes()).hexdigest(),'proof':str(pp),'proof_sha256':hashlib.sha256(pp.read_bytes()).hexdigest(),'manifest_sha256':proof['manifest_sha256']},indent=2))
