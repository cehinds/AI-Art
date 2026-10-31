from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib
BASE=Path(__file__).resolve().parents[4];OUT=Path(__file__).resolve().parent
M=json.loads(Path('/workspace/scratch/view-review-merged.json').read_text());l=next(x for x in M['libraries'] if x['scope']=='book-tiles/ink-and-lanterns');sets={s['object_id']:s for s in l['sets']};idx=json.loads((BASE/'reusable/index.json').read_text());assets={a['id']:a for a in idx['assets']}
ids=['bubble-necropolis-ancient-tomb-masonry-inner-corner','bubble-necropolis-ancient-tomb-masonry-outer-corner','bubble-airship-riveted-scrap-hull-inner-corner','bubble-airship-riveted-scrap-hull-outer-corner']
views=['front','top','right','left','bottom','rear'];cw=164;ch=190;im=Image.new('RGBA',(7*cw,len(ids)*ch),(42,42,46,255));d=ImageDraw.Draw(im)
for row,oid in enumerate(ids):
 s=sets[oid];src=assets[oid]['image']['path'];d.text((2,row*ch+2),oid,fill='white');arr=[('SOURCE',BASE/src)]+[(v.upper(),BASE/s['views'][v]['path']) for v in views]
 for col,(label,p) in enumerate(arr):
  x=Image.open(p).convert('RGBA');x.thumbnail((128,128),Image.Resampling.NEAREST);px=col*cw+18+(128-x.width)//2;py=row*ch+32+(128-x.height)//2;im.alpha_composite(x,(px,py));d.text((col*cw+3,row*ch+17),label,fill='white')
out=OUT/'approved-corner-geometry-references.png';im.save(out,optimize=False);print(out,hashlib.sha256(out.read_bytes()).hexdigest())
