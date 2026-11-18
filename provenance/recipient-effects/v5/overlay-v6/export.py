from pathlib import Path
import hashlib, importlib.util, json, sys
from PIL import Image
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('helpers',ROOT.parent/'front-on-v4/exporter.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
source=ROOT/'heal-bleed-raw.png';im=Image.open(source).convert('RGBA')
assert im.getchannel('A').getextrema()[0]==0
grid=h.rects(im,2)
scale=.6010362694300518*362/(im.width/3)
frames={};entries={}
for folder in ('frames','strips'): (ROOT/folder).mkdir(exist_ok=True)
for row,name in enumerate(('heal-plus','bleed-drops')):
    crops=[im.crop(rect) for rect in grid[row]];b=h.union_bounds(crops)
    offset=(round(128-(b[0]+b[2])/2*scale),round(128-(b[1]+b[3])/2*scale))
    frames[name]=[]
    for i,crop in enumerate(crops):
        frame=Image.new('RGBA',(256,256));crop=crop.resize((round(crop.width*scale),round(crop.height*scale)),Image.Resampling.NEAREST)
        frame.alpha_composite(crop,offset);frame.save(ROOT/'frames'/f'{name}-{i+1:02}.png');frames[name].append(frame)
    strip=Image.new('RGBA',(768,256))
    for i,f in enumerate(frames[name]):strip.alpha_composite(f,(256*i,0))
    path=ROOT/'strips'/f'{name}.png';strip.save(path)
    entries[name]={'sourceRects':grid[row],'scale':scale,'sharedOffset':offset,'strip':f'strips/{name}.png','sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
h.contact_sheet(ROOT/'heal-bleed-contact.png','HEALING / BLOOD SECONDARY OVERLAYS',['heal-plus','bleed-drops'],frames,1)
(ROOT/'manifest.json').write_text(json.dumps({'source':source.name,'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'frameCount':3,'frameSize':[256,256],'effects':entries},indent=2)+'\n')
print('Extracted 2 transparent strips, fixed scale and shared row registration.')
