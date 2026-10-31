import json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/pocket-dungeon');OUT=ROOT/'reusable/views-additional';D=OUT/'raw/targeted-repairs/postinstall-contacts-20261026';D.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
ids=['race-circuits-vehicle-upgrade-workbench','early-arenas-round-arena-stairwell','bubble-desert-adobe-town-gate','masquerade-masquerade-mask-sculpture']
rows=[]
for oid in ids:
 entry=next(x for x in json.loads((OUT/'set-index.json').read_text())['view_sets'] if x['object_id']==oid)
 src=ROOT/'race-circuits/components'/f'{oid}.png' if oid.startswith('race-circuits-') else ROOT/next(a['provenance']['source_image'] for a in json.loads((OUT/'set-index.json').read_text())['assets'] if a['id']==entry['views']['front'])
 canvas=Image.new('RGBA',(7*256,256),(235,235,235,255));draw=ImageDraw.Draw(canvas);source=Image.open(src).convert('RGBA');source.thumbnail((220,220),Image.Resampling.NEAREST);canvas.alpha_composite(source,((256-source.width)//2,(256-source.height)//2));draw.text((5,4),'source',fill='black');vh=[]
 for col,v in enumerate(['front','top','right','left','bottom','rear'],1):
  aid=entry['views'][v]; asset=next(a for a in json.loads((OUT/'set-index.json').read_text())['assets'] if a['id']==aid); p=ROOT/asset['image']['path']; im=Image.open(p).convert('RGBA');canvas.alpha_composite(im,(col*256,0));draw.text((col*256+5,4),v,fill='black');vh.append({'view':v,'path':asset['image']['path'],'sha256':sha(p),'width':im.width,'height':im.height,'bbox':list(im.getchannel('A').getbbox()) if im.getchannel('A').getbbox() else None})
 contact=D/f'{oid}.source-plus-six.png';canvas.convert('RGB').save(contact)
 rows.append({'object_id':oid,'source_path':src.relative_to(ROOT).as_posix(),'source_sha256':sha(src),'contact_path':contact.relative_to(ROOT).as_posix(),'contact_sha256':sha(contact),'views':vh,'set_complete':False,'review_status':'pending-root-whole-set-review'})
proof={'schema_version':1,'generated_at':'2026-10-26','scope':'root-approved staged view installs; current canonical bytes','sets':rows};(D/'contact-index.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2))
