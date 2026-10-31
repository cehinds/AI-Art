#!/usr/bin/env python3
"""Rebuild accepted full-tail WALK3 profile candidates from the retained atlas."""
from pathlib import Path
import hashlib,json
from PIL import Image

PACK=Path(__file__).resolve().parents[2]
VIEWS=PACK/"reusable/views-additional";RAW=VIEWS/"raw"
OUT=Path(__import__("sys").argv[1]).resolve() if len(__import__("sys").argv)>1 else RAW/"mongo-walk3-tail-rebuild"
OUT.mkdir(parents=True,exist_ok=True)
ATLAS=RAW/"ally-mongo-walk3-sides-v2.png"
SPECS={
  "right":{"cell":0,"crop_xywh":[245,166,685,400]},
  "left":{"cell":1,"crop_xywh":[154,165,684,401]},
}
SCALE=0.3425
def sha(b):return hashlib.sha256(b).hexdigest()
atlas_bytes=ATLAS.read_bytes();atlas=Image.open(ATLAS).convert("RGBA");cellw=atlas.width//2
report={"object_id":"revamp--mongo--mongo--walk3","atlas_sha256":sha(atlas_bytes),"uniform_scale":SCALE,"views":{}}
for view,spec in SPECS.items():
  x0=spec["cell"]*cellw;cell=atlas.crop((x0,0,x0+cellw,atlas.height));cx,cy,cw,ch=spec["crop_xywh"]
  crop=cell.crop((cx,cy,cx+cw,cy+ch));size=(round(cw*SCALE),round(ch*SCALE));resized=crop.resize(size,Image.Resampling.LANCZOS)
  offset=(128-size[0]//2,128-size[1]//2);canvas=Image.new("RGBA",(256,256),(0,0,0,0));canvas.alpha_composite(resized,offset)
  dest=OUT/f"{view}.png";canvas.save(dest,format="PNG",optimize=False)
  report["views"][view]={"atlas":ATLAS.name,"cell_bounds_xywh":[x0,0,cellw,atlas.height],"crop_bounds_xywh":[x0+cx,cy,cw,ch],"resized_bounds_px":list(size),"offset_px":list(offset),"output":str(dest),"output_sha256":sha(dest.read_bytes())}
(OUT/"build-report.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report,indent=2))
