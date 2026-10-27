#!/usr/bin/env python3
"""Build labeled contact sheets from indexed normalized view sets."""
import argparse,json,pathlib
from PIL import Image,ImageDraw
OUT=pathlib.Path(__file__).resolve().parent
PACK=OUT.parents[1]
DIRECTIONS=('front','top','right','left','bottom','rear')
p=argparse.ArgumentParser();p.add_argument('--start',type=int,required=True);p.add_argument('--count',type=int,default=6);a=p.parse_args()
index=json.loads((OUT/'set-index.json').read_text());assets={x['id']:x for x in index['assets']};sets_by_source={s.get('source_id',s['object_id']):s for s in index['view_sets']}
source_ids=[x['id'] for x in json.loads((PACK/'manifest.json').read_text())['assets'][a.start:a.start+a.count]]
sets=[sets_by_source.get(sid) for sid in source_ids]
canvas=Image.new('RGBA',(6*170,a.count*212),(235,231,220,255));draw=ImageDraw.Draw(canvas);missing=[]
for r,(source_id,s) in enumerate(zip(source_ids,sets)):
 y=r*212;draw.text((8,y+3),source_id,fill=(15,15,15,255))
 if s is None:
  missing.append(source_id);draw.text((780,y+5),'MISSING SET',fill=(200,0,0,255));continue
 for c,direction in enumerate(DIRECTIONS):
  aid=s.get('views',{}).get(direction)
  if not aid: continue
  item=assets.get(aid)
  if not item: continue
  image_path=PACK/item['image']['path'];im=Image.open(image_path).convert('RGBA');im.thumbnail((145,145),Image.Resampling.LANCZOS)
  x=c*170+12; yy=y+24;canvas.alpha_composite(im,(x+(145-im.width)//2,yy+(145-im.height)//2));draw.text((x,yy+148),direction,fill=(15,15,15,255))
start=a.start+1;end=a.start+a.count;path=OUT/f'qa-contact-{start:04d}-{end:04d}.png';canvas.save(path)
index_path=OUT/'qa-contact-index.json';old=json.loads(index_path.read_text()) if index_path.exists() else {'contacts':[]};entries=[x for x in old['contacts'] if x['start']!=start]
entries.append({'start':start,'end':end,'path':path.name,'objects':source_ids,'missing_sets':missing})
index_path.write_text(json.dumps({'contacts':sorted(entries,key=lambda x:x['start'])},indent=2)+'\n')
print(path)
