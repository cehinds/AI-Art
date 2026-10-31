#!/usr/bin/env python3
"""Normalize/install the six generated views for the isolated crafting wall lantern."""
import hashlib,json,struct,os
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

PACK=Path(__file__).resolve().parents[2]; VIEWS=PACK/"reusable/views-additional"; RAW=VIEWS/"raw"
OID="concepts-progression-safe-room-crafting-wall-lantern"
MAIN="exec-8e8ae521-174d-4ce8-8928-30aa9ce20b64"
SIDES="exec-4785c7a4-9ef8-41e1-96d2-b0e7ac97aa62"
GEN={v:MAIN for v in ("front","top","bottom","rear")};GEN.update({"right":SIDES,"left":SIDES})
CAMERA={"front":"front face","top":"top cap and fixture depth","right":"narrow edge profile with inferred mount bracket","left":"opposite narrow edge profile with inferred mount bracket","bottom":"finial and base underside","rear":"plain inferred mounting backplate"}
def sha(b):return hashlib.sha256(b).hexdigest()
for gen in (MAIN,SIDES):
 src=Path("/workspace/generated_images")/f"{gen}.png"; out=RAW/f"{gen}.png"
 if not out.exists():out.write_bytes(src.read_bytes())
 (RAW/f"{gen}.prompt.txt").write_text(("Six-column orthographic atlas for the isolated wall-mounted enclosed gold lantern; columns FRONT, TOP, RIGHT, LEFT, BOTTOM, REAR. Strict aligned views; hidden geometry inferred.\n" if gen==MAIN else "Two-column targeted strict narrow RIGHT and LEFT profile atlas; the face glass is edge-on, narrow depth, small wall mounting bracket.\n"),encoding="utf-8")
idxp=VIEWS/"set-index.json";idx=json.loads(idxp.read_text())
if any(a["id"].startswith(OID+".") for a in idx["assets"]):raise SystemExit("Lantern leaves already exist; refusing duplicate install")
native=json.loads((PACK/"reusable/native"/f"{OID}.json").read_text())
source=PACK/native["image"]["path"]; source_bytes=source.read_bytes(); source_sha=sha(source_bytes)
views={}
for view in ("front","top","right","left","bottom","rear"):
 gen=GEN[view];atlas_path=RAW/f"{gen}.png";atlas_bytes=atlas_path.read_bytes();atlas=Image.open(atlas_path).convert("RGBA")
 cols=6 if gen==MAIN else 2;cw=atlas.width//cols
 col={"front":0,"top":1,"right":2,"left":3,"bottom":4,"rear":5}[view] if gen==MAIN else {"right":0,"left":1}[view]
 cell=atlas.crop((col*cw,0,(col+1)*cw,atlas.height));arr=np.asarray(cell);alpha=arr[:,:,3]
 labels,n=ndimage.label(alpha>=16)
 if not n:raise SystemExit(f"No alpha component for {view}")
 sizes=np.bincount(labels.ravel());label=int(np.argmax(sizes[1:])+1);ys,xs=np.where(labels==label)
 box=(int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1));crop=cell.crop(box)
 # Main atlas front/rear raw Z=536px; the targeted side atlas raw Z=804px.
 # Calibrate each generation request to the same 160px physical Z extent, then use
 # that one scalar for every silhouette in that atlas, including its plan views.
 # This preserves natural plan proportions rather than fitting each view to a box.
 scale=160/(804 if gen==SIDES else 536)
 nw,nh=round(crop.width*scale),round(crop.height*scale)
 crop=crop.resize((nw,nh),Image.Resampling.LANCZOS)
 canvas=Image.new("RGBA",(256,256),(0,0,0,0));anchor=(128,128);canvas.alpha_composite(crop,(anchor[0]-nw//2,anchor[1]-nh//2))
 aid=f"{OID}.{view}";imgpath=VIEWS/f"{aid}.png";metapath=VIEWS/f"{aid}.json";canvas.save(imgpath,optimize=False);pb=imgpath.read_bytes()
 name=f"Crafting wall lantern {view.title()}"
 meta={"id":aid,"name":name,"kind":"sprite","tags":sorted(set(native.get("tags",[])+["inferred-view",view])),
  "object_id":OID,"view":view,"image":{"path":f"reusable/views-additional/{aid}.png","width":256,"height":256,"sha256":sha(pb),"rgba_sha256":sha(struct.pack(">II",256,256)+canvas.tobytes())},
  "metadata_path":f"reusable/views-additional/{aid}.json","anchor_px":[128,128],
  "provenance":{"method":"generated","source_image":native["image"]["path"],"native_front":native["image"]["path"],"native_front_sha256":source_sha,
   "notes":f"inferred orthographic {view} view, not recovered pixels; {CAMERA[view]}; wall-mounted fixture identity preserved; unseen surfaces and mount depth explicitly inferred",
   "source_atlas":f"reusable/views-additional/raw/{gen}.png","source_atlas_sha256":sha(atlas_bytes),"generation_recipe":f"reusable/views-additional/raw/{gen}.prompt.txt",
   "crop_bounds_px":{"nominal_cell":{"column":col,"row":0,"bounds":[col*cw,0,cw,atlas.height]},"alpha_threshold":16,
    "alpha_bounds_global":[box[0]+col*cw,box[1],box[2]-box[0],box[3]-box[1]],"alpha_bounds_cell_xyxy":list(box),
    "component_labels":[label],"resized_bounds_px":[nw,nh],"canvas_offset_px":[anchor[0]-nw//2,anchor[1]-nh//2],"shared_scale":scale,
    "normalization":"largest alpha component at threshold16; uniform common Z scale; centered on common anchor"}}}
 metapath.write_text(json.dumps(meta,indent=2)+"\n");views[view]=aid;idx["assets"].append(meta)
sets=idx.setdefault("view_sets",[]);sets.append({"object_id":OID,"views":views,"complete":True,"notes":"Six generated orthographic views; wall mount, rear plate and hidden depth are explicitly inferred from the small source crop."})
idxp.write_text(json.dumps(idx,indent=2)+"\n")
(RAW/"crafting-wall-lantern-install.json").write_text(json.dumps({"object_id":OID,"source_image":native["image"]["path"],"source_sha256":source_sha,"views":views,"atlases":{g:{"path":f"reusable/views-additional/raw/{g}.png","sha256":sha((RAW/f"{g}.png").read_bytes())} for g in (MAIN,SIDES)},"common_z_height_px":160,"complete":True},indent=2)+"\n")
print(json.dumps({"object_id":OID,"views":views,"bounds":{v:Image.open(VIEWS/f"{OID}.{v}.png").convert("RGBA").getchannel("A").getbbox() for v in views}},indent=2))
