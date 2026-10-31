from pathlib import Path
import json
from PIL import Image
p=Path(__file__).resolve().parent
m=json.loads((p/'manifest.json').read_text()); cs={c['id']:c for c in m['components']}
r=json.loads((p/'room-recipe.json').read_text()); out=Image.new('RGBA',tuple(r['canvas']),r['background'])
s=r['surface']; im=Image.open(p/cs[s['componentId']]['path']).convert('RGBA'); x,y,w,h=s['tileRect']
for yy in range(y,y+h,im.height):
 for xx in range(x,x+w,im.width):out.alpha_composite(im,(xx,yy))
for item in r.get('surfaceOverlays',[]):
 im=Image.open(p/cs[item['componentId']]['path']).convert('RGBA').resize(tuple(item['size']),Image.Resampling.NEAREST);out.alpha_composite(im,tuple(item['position']))
for item in sorted(r['placements'],key=lambda i:i['layer']):
 im=Image.open(p/cs[item['componentId']]['path']).convert('RGBA');im.thumbnail(tuple(item['maxSize']));out.alpha_composite(im,tuple(item['position']))
out.save(p/'previews/reassembled-room.png')
