"""Create source-plus-six QA contacts for a west-wall repair group."""
import json,sys
from pathlib import Path
from PIL import Image,ImageDraw
OUT=Path(__file__).resolve().parent; BOOK=OUT.parent.parent
group=sys.argv[1]; specs=[s for s in json.loads((OUT/'west-wall-repair-specs.json').read_text()) if s['batch_id'].startswith(f'west-wall-{group}-')]
if not specs: raise SystemExit(f'no specs for {group}')
objects=specs[0]['objects'];views=['front','top','right','left','bottom','rear'];labels=['SOURCE']+views
cw,ch=220,260;out=Image.new('RGBA',(len(labels)*cw,len(objects)*ch),(35,31,29,255));draw=ImageDraw.Draw(out)
for row,obj in enumerate(objects):
    for col,key in enumerate(labels):
        file=BOOK/obj['source_image'] if key=='SOURCE' else OUT/'images'/f"{obj['id']}.{key}.png"
        im=Image.open(file).convert('RGBA');im.thumbnail((212,228),Image.Resampling.NEAREST)
        out.alpha_composite(im,(col*cw+(cw-im.width)//2,row*ch+2+(228-im.height)//2))
        draw.text((col*cw+4,row*ch+232),key,fill='white')
    draw.text((0,row*ch+246),obj['id'],fill=(205,195,175))
path=OUT/'qa'/f'west-wall-repair-group-{group}-review.png';out.save(path);print(path)
