from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,math
HERE=Path(__file__).resolve().parent;PACK=HERE.parents[3]
h=json.load(open('/workspace/scratch/inkbook-core-ne-wall-staging-handoff.json'))
merged=json.load(open('/workspace/scratch/view-review-merged.json'));lib=next(x for x in merged['libraries'] if x['scope']=='book-tiles/ink-and-lanterns'); by={x['object_id']:x for x in lib['sets']}
views=['front','top','right','left','bottom','rear']
for start in range(0,len(h['sets']),3):
 group=h['sets'][start:start+3]; cells=13; cw=164; ch=184
 out=Image.new('RGBA',(cells*cw,len(group)*ch),(44,44,48,255));d=ImageDraw.Draw(out)
 for row,item in enumerate(group):
  oid=item['object_id']; nwid=item['suggested_same_kit_nw_object']; nw=by.get(nwid); source=PACK/item['source']['path']
  entries=[('SRC',source)]
  entries.extend(('NE-'+v.upper(),PACK/item['current_views'][v]['path']) for v in views)
  if nw and nw.get('status')=='passed':
   entries.extend(('NW-'+v.upper(),PACK/nw['views'][v]['path']) for v in views)
  else:
   entries.extend(('NW-'+v.upper()+'-NO-GUIDE',PACK/nw['views'][v]['path']) for v in views) if nw else None
  d.text((2,row*ch+3),oid[:80],fill='white')
  for col,(label,path) in enumerate(entries):
   im=Image.open(path).convert('RGBA'); im.thumbnail((128,128),Image.Resampling.NEAREST)
   x=col*cw+18+(128-im.width)//2; y=row*ch+32+(128-im.height)//2
   out.alpha_composite(im,(x,y));d.text((col*cw+3,row*ch+18),label,fill='white')
 name=f'ne-wall-contact-{start+1:02d}-{start+len(group):02d}.png';path=HERE/name;out.save(path)
 print(name,hashlib.sha256(path.read_bytes()).hexdigest(),[x['object_id'] for x in group])
