#!/usr/bin/env python3
"""Apply a documented, reversible orthographic orientation correction."""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from PIL import Image

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent.parent

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--object-id', required=True)
    ap.add_argument('--view', required=True, choices=('front','top','right','left','bottom','rear'))
    ap.add_argument('--degrees', required=True, type=int, choices=(90,180,270))
    ap.add_argument('--notes', required=True)
    a = ap.parse_args()
    aid=f'{a.object_id}.{a.view}'; path=OUT/'images'/f'{aid}.png'; side=path.with_suffix('.json')
    rawdir=OUT/'raw'/'targeted-repairs';rawdir.mkdir(parents=True,exist_ok=True)
    raw=rawdir/f'{aid}.before-rotation.png'
    raw.write_bytes(path.read_bytes())
    recipe=rawdir/f'{aid}.json'
    recipe.write_text(json.dumps({'object_id':a.object_id,'view':a.view,
                                  'input_image':raw.relative_to(ROOT).as_posix(),
                                  'input_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),
                                  'transformation':{'rotation_degrees_ccw':a.degrees},
                                  'notes':a.notes},indent=2)+'\n')
    im=Image.open(raw).convert('RGBA');bbox=im.getchannel('A').getbbox()
    if not bbox: raise ValueError('No visible alpha')
    crop=im.crop(bbox).rotate(a.degrees,expand=True,resample=Image.Resampling.NEAREST)
    scale=min(204/crop.width,204/crop.height);size=(max(1,round(crop.width*scale)),max(1,round(crop.height*scale)))
    crop=crop.resize(size,Image.Resampling.NEAREST);canvas=Image.new('RGBA',(256,256),(0,0,0,0));offset=((256-size[0])//2,(256-size[1])//2);canvas.alpha_composite(crop,offset);canvas.save(path,optimize=True)
    m=json.loads(side.read_text());idxp=OUT/'set-index.json';idx=json.loads(idxp.read_text());
    digest=hashlib.sha256(path.read_bytes()).hexdigest();rgba=hashlib.sha256(struct.pack('>II',256,256)+canvas.tobytes()).hexdigest()
    m['image'].update({'sha256':digest,'rgba_sha256':rgba,'width':256,'height':256})
    m['provenance'].update({'method':'derived-transformation','repair_source':raw.relative_to(ROOT).as_posix(),'repair_source_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'transformation':{'rotation_degrees_ccw':a.degrees,'resampling':'nearest','offset_px':list(offset)},'repair_recipe':recipe.relative_to(ROOT).as_posix(),'notes':a.notes})
    side.write_text(json.dumps(m,indent=2,ensure_ascii=False)+'\n')
    for leaf in idx['assets']:
        if leaf.get('id')==aid: leaf.clear();leaf.update(m);break
    else: raise ValueError(f'{aid} missing from index')
    for group in idx['view_sets']:
        if group.get('object_id')==a.object_id:
            group['complete']=False;group['geometry_qa']={'status':'pending-review','reason':'Targeted orthographic orientation correction; awaiting independent current-hash QA.'};break
    idxp.write_text(json.dumps(idx,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'id':aid,'sha256':digest,'raw':raw.relative_to(ROOT).as_posix()}))
if __name__=='__main__': main()
