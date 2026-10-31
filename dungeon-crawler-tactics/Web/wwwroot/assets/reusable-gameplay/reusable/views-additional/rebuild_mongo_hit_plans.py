#!/usr/bin/env python3
"""Rebuild the accepted Mongo HIT TOP/BOTTOM PNGs from retained raw atlases.

Usage: python rebuild_mongo_hit_plans.py [output-directory]
This helper is offline and writes only to the selected output directory.
"""
from pathlib import Path
import hashlib, json
import numpy as np
from PIL import Image
from scipy import ndimage

PACK=Path(__file__).resolve().parents[2]
VIEWS=PACK/"reusable/views-additional"
RAW=VIEWS/"raw"
OUT=Path(__import__("sys").argv[1]).resolve() if len(__import__("sys").argv)>1 else RAW/"mongo-hit-plan-rebuild"
OUT.mkdir(parents=True,exist_ok=True)
SPECS={
    "top": {"atlas":"mongo-hit-top-dorsal-refinement.png","cell_xywh":[0,0,1536,1024],"alpha_threshold":200,"crop_xywh":[480,101,576,830],"scale":0.2253012048192771,"offset":[63,35]},
    "bottom": {"atlas":"ally-mongo-hit-plans-v1.png","cell_xywh":[887,0,887,887],"alpha_threshold":16,"crop_xywh":[973,60,594,784],"scale":0.21717171717171718,"offset":[64,43]},
}
def sha(b): return hashlib.sha256(b).hexdigest()
report={"object_id":"revamp--mongo--mongo--hit","views":{}}
for view,spec in SPECS.items():
    raw=RAW/spec["atlas"]; source=Image.open(raw).convert("RGBA")
    x,y,w,h=spec["cell_xywh"]; cell=source.crop((x,y,x+w,y+h))
    alpha=np.asarray(cell.getchannel("A")); labels,count=ndimage.label(alpha>=spec["alpha_threshold"])
    sizes=np.bincount(labels.ravel());sizes[0]=0;component=int(np.argmax(sizes))
    cx,cy,cw,ch=spec["crop_xywh"]
    crop=cell.crop((cx-x,cy-y,cx-x+cw,cy-y+ch))
    rgba=np.asarray(crop).copy(); sublabels=labels[cy-y:cy-y+ch,cx-x:cx-x+cw]
    rgba[:,:,3]=np.where(sublabels==component,rgba[:,:,3],0).astype(np.uint8)
    crop=Image.fromarray(rgba,"RGBA")
    out_size=(round(cw*spec["scale"]),round(ch*spec["scale"]))
    resized=crop.resize(out_size,Image.Resampling.LANCZOS)
    canvas=Image.new("RGBA",(256,256),(0,0,0,0));canvas.alpha_composite(resized,tuple(spec["offset"]))
    dest=OUT/f"{view}.png";canvas.save(dest,format="PNG",optimize=False)
    report["views"][view]={"atlas":spec["atlas"],"atlas_sha256":sha(raw.read_bytes()),"alpha_threshold":spec["alpha_threshold"],"selected_component":component,"crop_bounds_xywh":spec["crop_xywh"],"scale":spec["scale"],"output_offset":spec["offset"],"output_png":str(dest),"output_sha256":sha(dest.read_bytes())}
(OUT/"build-report.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report,indent=2))
