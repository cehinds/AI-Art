#!/usr/bin/env python3
"""Build labeled source-reference sheets only; does not create/modify game art."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,sys
BOOK=Path(__file__).resolve().parents[2]
kit,batch=sys.argv[1],int(sys.argv[2]);manifest=json.loads((BOOK/kit/'manifest.json').read_text());assets=manifest['assets'];ids=[x['id'] for x in assets[6*(batch-1):6*batch]]
if len(ids)!=6:raise SystemExit('batch must contain six source IDs')
out=Path(__file__).resolve().parent/'raw'/'source-refs';out.mkdir(parents=True,exist_ok=True);sheet=Image.new('RGBA',(1440,720),(39,36,47,255));draw=ImageDraw.Draw(sheet);font=ImageFont.load_default()
for i,oid in enumerate(ids):
 a=next(x for x in assets if x['id']==oid);im=Image.open(BOOK/kit/a['file']).convert('RGBA');im.thumbnail((430,300),Image.Resampling.NEAREST);col=i%3;row=i//3;x=col*480;y=row*360;sheet.alpha_composite(im,(x+(480-im.width)//2,y+5));draw.text((x+8,y+315),oid,fill='white',font=font);draw.text((x+8,y+333),a.get('label',oid),fill=(210,205,220,255),font=font)
p=out/f'{kit}-batch-{batch:02d}.png';sheet.convert('RGB').save(p);print(p);print('\n'.join(ids))
