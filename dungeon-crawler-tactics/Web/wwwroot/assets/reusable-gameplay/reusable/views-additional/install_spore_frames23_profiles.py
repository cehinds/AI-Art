#!/usr/bin/env python3
"""Install retained opposing Spore profile candidates after catalog materialization."""
import hashlib,json,struct,tempfile,os
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

PACK=Path(__file__).resolve().parents[2]; VIEWS=PACK/"reusable/views-additional"; RAW=VIEWS/"raw"
JOBS={
 "expedition-enemies--spore--frame-2":{
  "right":"exec-896921a2-c028-4c27-9836-dd3c4e146495",
  "left":"exec-b457fcc2-4ab8-45e9-866e-0dbcaecce3c4"},
 "expedition-enemies--spore--frame-3":{
  "right":"exec-d2d17664-9cad-4b80-8094-990ff27aa333",
  "left":"exec-e0ca64cc-39dc-42d1-b4e0-265f64e82b5e"}
}
def sha(b):return hashlib.sha256(b).hexdigest()
idxp=VIEWS/"set-index.json";idx=json.loads(idxp.read_text());assets={a["id"]:a for a in idx["assets"]}
staged={}
for oid,views in JOBS.items():
 for view,gen in views.items():
  atlas_path=RAW/f"{gen}.png"; atlas_bytes=atlas_path.read_bytes()
  atlas=Image.open(atlas_path).convert("RGBA"); alpha=np.asarray(atlas)[:,:,3]; labels,n=ndimage.label(alpha>=16)
  if not n: raise SystemExit(f"No foreground alpha in {atlas_path}")
  sizes=np.bincount(labels.ravel()); label=int(np.argmax(sizes[1:])+1); ys,xs=np.where(labels==label)
  box=(int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)); crop=atlas.crop(box)
  aid=f"{oid}.{view}"; meta=json.loads((VIEWS/f"{aid}.json").read_text()); path=VIEWS/f"{aid}.png"
  old=path.read_bytes(); target=Image.open(path).convert("RGBA"); tb=target.getchannel("A").getbbox(); tw,th=tb[2]-tb[0],tb[3]-tb[1]
  scale=min(tw/crop.width,th/crop.height); nw,nh=round(crop.width*scale),round(crop.height*scale)
  crop=crop.resize((nw,nh),Image.Resampling.LANCZOS); canvas=Image.new("RGBA",(256,256),(0,0,0,0)); anchor=(128,128)
  canvas.alpha_composite(crop,(anchor[0]-nw//2,anchor[1]-nh//2))
  (RAW/f"{gen}.previous-{view}.png").write_bytes(old)
  meta["image"]["rgba_sha256"]=sha(struct.pack(">II",256,256)+canvas.tobytes())
  meta["provenance"].update({
   "source_atlas":f"reusable/views-additional/raw/{gen}.png","source_atlas_sha256":sha(atlas_bytes),
   "generation_recipe":f"reusable/views-additional/raw/{gen}.prompt.txt",
   "notes":"inferred orthographic opposite side profile, not recovered pixels; pose, cap and any frame-specific reaching limb/effect are inferred from the canonical source; unseen surfaces inferred",
   "crop_bounds_px":{"alpha_threshold":16,"alpha_bounds_global":list(box),"component_labels":[label],
    "resized_bounds_px":[nw,nh],"canvas_offset_px":[anchor[0]-nw//2,anchor[1]-nh//2],
    "shared_scale":scale,"normalization":"uniform scale to prior accepted same-frame profile extent; centered at shared anchor"}})
  staged[aid]=(path,canvas,meta,old,box,scale)
for aid,(path,canvas,meta,old,box,scale) in staged.items():
 tmp=path.with_suffix(".png.tmp");canvas.save(tmp,format="PNG",optimize=False);os.replace(tmp,path)
 png=path.read_bytes();meta["image"]["sha256"]=sha(png)
 (VIEWS/f"{aid}.json").write_text(json.dumps(meta,indent=2)+"\n")
 assets[aid].clear();assets[aid].update(meta)
 (RAW/f"{aid}.install.json").write_text(json.dumps({"asset_id":aid,"old_png_sha256":sha(old),
  "new_png_sha256":sha(png),"source_image":meta["provenance"]["source_image"],
  "source_sha256":sha((PACK/meta["provenance"]["source_image"]).read_bytes()),
  "atlas":meta["provenance"]["source_atlas"],"atlas_sha256":meta["provenance"]["source_atlas_sha256"],
  "crop_bounds_xyxy":list(box),"installed_bbox":list(canvas.getchannel("A").getbbox()),
  "uniform_scale":scale,"alpha_threshold":16},indent=2)+"\n")
idx["assets"]=[assets[a["id"]] for a in idx["assets"]];idxp.write_text(json.dumps(idx,indent=2)+"\n")
print(json.dumps({a:{"sha256":assets[a]["image"]["sha256"],"bbox":list(staged[a][1].getchannel("A").getbbox())} for a in staged},indent=2))
