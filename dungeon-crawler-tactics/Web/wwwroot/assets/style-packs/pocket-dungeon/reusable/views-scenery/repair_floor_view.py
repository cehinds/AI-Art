#!/usr/bin/env python3
"""Replayable single-view repair helper for Pocket physical ground tiles."""
import argparse, hashlib, json, shutil, struct
from pathlib import Path
from PIL import Image

PACK_ROOT=Path(__file__).resolve().parents[2]

p=argparse.ArgumentParser()
p.add_argument('--view-dir',required=True,help='Pack-relative reusable folder such as reusable/views-core')
p.add_argument('--object-id',required=True)
p.add_argument('--view',required=True,choices=('front','top','right','left','bottom','rear'))
p.add_argument('--input',required=True,type=Path)
p.add_argument('--atlas',required=True,type=Path)
p.add_argument('--cell',required=True)
p.add_argument('--target-width',type=int,default=204)
p.add_argument('--anchor-y',type=int,default=248)
p.add_argument('--alpha-threshold',type=int,default=32)
p.add_argument('--prompt',required=True)
p.add_argument('--notes',required=True)
a=p.parse_args()
OUT=(PACK_ROOT/a.view_dir).resolve(); aid=f'{a.object_id}.{a.view}'
png=OUT/f'{aid}.png'; meta_path=OUT/f'{aid}.json'; index_path=OUT/'set-index.json'
if not png.exists() or not meta_path.exists(): raise FileNotFoundError(aid)
meta=json.loads(meta_path.read_text()); index=json.loads(index_path.read_text())
if meta.get('id') not in (None,aid): raise ValueError(f'{aid}: sidecar id mismatch')
raw_dir=OUT/'raw'/'targeted-repairs';raw_dir.mkdir(parents=True,exist_ok=True)
raw=raw_dir/f'{aid}.png';atlas=raw_dir/f'{aid}.atlas.png';recipe=raw_dir/f'{aid}.json'
shutil.copy2(a.input,raw);shutil.copy2(a.atlas,atlas)
raw_sha=hashlib.sha256(raw.read_bytes()).hexdigest();atlas_sha=hashlib.sha256(atlas.read_bytes()).hexdigest()
recipe_data={'object_id':a.object_id,'view':a.view,'input_image':raw.relative_to(PACK_ROOT).as_posix(),'input_sha256':raw_sha,'generated_atlas':atlas.relative_to(PACK_ROOT).as_posix(),'generated_atlas_sha256':atlas_sha,'source_cell':a.cell,'target_width_px':a.target_width,'alpha_threshold':a.alpha_threshold,'anchor_px':[128,a.anchor_y],'prompt':a.prompt,'notes':a.notes}
recipe.write_text(json.dumps(recipe_data,indent=2)+'\n')
im=Image.open(raw).convert('RGBA'); alpha=im.getchannel('A'); mask=alpha.point(lambda v:255 if v>=a.alpha_threshold else 0); bbox=mask.getbbox()
if not bbox: raise ValueError(f'{aid}: empty alpha after threshold')
im.putalpha(mask); crop=im.crop(bbox); scale=a.target_width/crop.width; size=(a.target_width,max(1,round(crop.height*scale))); crop=crop.resize(size,Image.Resampling.NEAREST)
offset=(128-size[0]//2,a.anchor_y-size[1]); canvas=Image.new('RGBA',(256,256),(0,0,0,0)); canvas.alpha_composite(crop,offset); canvas.save(png,optimize=True)
sha=hashlib.sha256(png.read_bytes()).hexdigest();rgba_sha=hashlib.sha256(struct.pack('>II',256,256)+canvas.tobytes()).hexdigest()
meta.setdefault('image',{}).update({'path':meta.get('image',{}).get('path',png.relative_to(PACK_ROOT).as_posix()),'width':256,'height':256,'sha256':sha,'rgba_sha256':rgba_sha})
meta['id']=aid;meta['object_id']=a.object_id;meta['view']=a.view;meta['metadata_path']=meta_path.relative_to(PACK_ROOT).as_posix();meta['anchor_px']=[128,a.anchor_y]
meta.setdefault('provenance',{}).update({'method':'generated','generated_atlas':atlas.relative_to(PACK_ROOT).as_posix(),'generated_atlas_sha256':atlas_sha,'source_cell':a.cell,'repair_recipe':recipe.relative_to(PACK_ROOT).as_posix(),'normalization':{'source_alpha_bounds':list(bbox),'source_size':list(im.size),'alpha_threshold':a.alpha_threshold,'scale':scale,'render_size_px':list(size),'offset_px':list(offset),'canvas':[256,256],'resampling':'NEAREST','anchor_px':[128,a.anchor_y]},'notes':a.notes})
meta_path.write_text(json.dumps(meta,indent=2,ensure_ascii=False)+'\n')
assets=index['assets']; found=False
for item in assets:
 if item.get('id')==aid: item.clear();item.update(meta);found=True;break
if not found: raise ValueError(f'{aid}: missing from set-index')
for group in index['view_sets']:
 if group.get('object_id')==a.object_id:
  group['complete']=False;group['geometry_qa']={'status':'pending-review','reason':'Targeted floor geometry repaired; awaiting independent current-hash review.'};break
index_path.write_text(json.dumps(index,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({'asset_id':aid,'sha256':sha,'rgba_sha256':rgba_sha,'recipe':recipe.relative_to(PACK_ROOT).as_posix()}))
