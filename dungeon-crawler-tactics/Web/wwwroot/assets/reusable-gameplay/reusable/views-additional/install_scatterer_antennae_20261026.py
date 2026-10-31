#!/usr/bin/env python3
"""Install a source-bound six-view Scatterer atlas with the native antenna pair."""
from __future__ import annotations
import hashlib, json, os, struct
from pathlib import Path
from PIL import Image

PACK=Path(__file__).resolve().parents[2]
VIEWS=PACK/"reusable/views-additional";RAW=VIEWS/"raw"
OID="scenario-props--scatterer"
ATLAS=RAW/"scatterer-six-view-v1-20261026.png"
REQUEST="exec-dbd24b5f-70e5-4c03-bdc8-140f102761f8"
PROMPT=RAW/"scatterer-six-view-v1-20261026.prompt.txt"
ORDER=["front","top","right","left","bottom","rear"]

def sha(b):return hashlib.sha256(b).hexdigest()
def rgba_hash(im):return sha(struct.pack(">II",*im.size)+im.convert("RGBA").tobytes())

index_path=VIEWS/"set-index.json";index=json.loads(index_path.read_text());records={a["id"]:a for a in index["assets"]}
atlas_bytes=ATLAS.read_bytes();atlas=Image.open(ATLAS).convert("RGBA");cellw=atlas.width/6
source_path=PACK/"reusable/native"/f"{OID}.png";source_sha=sha(source_path.read_bytes())
staged=[]
# One isotropic scale is calibrated from accepted elevation heights, then shared
# by all six cells so views remain one object in a common physical scale.
old_heights=[]
for view in ("front","right","left","rear"):
    b=Image.open(VIEWS/f"{OID}.{view}.png").convert("RGBA").getchannel("A").getbbox();old_heights.append(b[3]-b[1])
target_z=sum(old_heights)/len(old_heights)
new_heights=[]
cells=[]
for i,view in enumerate(ORDER):
    x0,x1=round(i*cellw),round((i+1)*cellw)
    cell=atlas.crop((x0,0,x1,atlas.height))
    box=cell.getchannel("A").point(lambda x:255 if x>=16 else 0).getbbox()
    if not box:raise ValueError(f"Empty atlas cell {i} {view}")
    crop=cell.crop(box);cells.append((view,x0,x1-x0,box,crop));
    if view in ("front","right","left","rear"):new_heights.append(crop.height)
scale=target_z/(sum(new_heights)/len(new_heights))
for view,x0,cw,box,crop in cells:
    nw,nh=max(1,round(crop.width*scale)),max(1,round(crop.height*scale))
    resized=crop.resize((nw,nh),Image.Resampling.LANCZOS)
    canvas=Image.new("RGBA",(256,256),(0,0,0,0));offset=(128-nw//2,128-nh//2);canvas.alpha_composite(resized,offset)
    aid=f"{OID}.{view}";out=VIEWS/f"{aid}.png";side=VIEWS/f"{aid}.json";meta=json.loads(side.read_text())
    if meta["provenance"]["source_image"]!=f"reusable/native/{OID}.png":raise ValueError(f"{aid} noncanonical source")
    staged.append((aid,view,out,side,meta,canvas,x0,cw,atlas.height,box,(nw,nh),offset,sha(out.read_bytes())))

for aid,view,out,side,meta,canvas,x0,cw,ch,box,resized,offset,old_sha in staged:
    tmp=out.with_suffix(".png.tmp");canvas.save(tmp,format="PNG",optimize=False);os.replace(tmp,out);new=out.read_bytes()
    meta["image"]["sha256"]=sha(new);meta["image"]["rgba_sha256"]=rgba_hash(canvas)
    meta["provenance"].update({
        "source_image":f"reusable/native/{OID}.png","source_image_sha256":source_sha,
        "source_atlas":f"reusable/views-additional/raw/{ATLAS.name}","source_atlas_sha256":sha(atlas_bytes),
        "generation_request_id":REQUEST,"generation_prompt":f"reusable/views-additional/raw/{PROMPT.name}",
        "generation_recipe":"reusable/views-additional/install_scatterer_antennae_20261026.py",
        "notes":"Generated inferred orthographic view; native's two long curved antennae are preserved as separate structural feelers in all principal views. Hidden undersides and rear occlusion are inferred, not recovered pixels.",
        "crop_bounds_px":{"coordinate_format":"xywh","nominal_cell":{"bounds":[x0,0,cw,ch]},"alpha_threshold":16,"alpha_bounds_global":[x0+box[0],box[1],box[2]-box[0],box[3]-box[1]],"resized_bounds_px":list(resized),"canvas_offset_px":list(offset),"shared_anchor_px":[128,128],"uniform_scale":scale,"normalization":"shared isotropic scale calibrated to accepted elevation Z extents; common anchor"}
    })
    side.write_text(json.dumps(meta,indent=2)+"\n");records[aid].clear();records[aid].update(meta)
    (RAW/f"{aid}.antennae-repair-20261026.json").write_text(json.dumps({"asset_id":aid,"source_image":f"reusable/native/{OID}.png","source_image_sha256":source_sha,"source_atlas":ATLAS.name,"source_atlas_sha256":sha(atlas_bytes),"generation_request_id":REQUEST,"view":view,"cell_crop_bounds_xywh":[x0+box[0],box[1],box[2]-box[0],box[3]-box[1]],"normalized_bbox_xywh":list(canvas.getchannel("A").getbbox()),"uniform_scale":scale,"old_png_sha256":old_sha,"new_png_sha256":sha(new)},indent=2)+"\n")
index["assets"]=[records[a["id"]] for a in index["assets"]];index_path.write_text(json.dumps(index,indent=2)+"\n")
print(json.dumps({a[0]:{"bbox":list(a[5].getchannel("A").getbbox()),"sha256":records[a[0]]["image"]["sha256"]} for a in staged},indent=2))
