#!/usr/bin/env python3
"""Move only the small orange bottle-cap footprint to its canonical TOP location."""
import hashlib,json,struct,os
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
PACK=Path(__file__).resolve().parents[2];VIEWS=PACK/"reusable/views-additional";RAW=VIEWS/"raw"
OID="concepts-progression-safe-room-crafting-workbench";VIEW="top";GEN="exec-f4b2bf0f-8731-41fb-ac66-68a7672aa6c5"
ATLAS=RAW/f"{GEN}.png"
if not ATLAS.exists():ATLAS.write_bytes((Path("/workspace/generated_images")/f"{GEN}.png").read_bytes())
PROMPT=("Localized TOP-only edit: preserve clean tabletop and all tools. Keep the larger red cap left of the blue book; move only the small gold/orange cap to the far-right back edge matching the front view's blue bottle. Remove old small cap position, no duplicate. No lantern or under-table furniture.\n")
(RAW/f"{GEN}.prompt.txt").write_text(PROMPT)
def sha(b):return hashlib.sha256(b).hexdigest()
idxp=VIEWS/"set-index.json";idx=json.loads(idxp.read_text());assets={a["id"]:a for a in idx["assets"]}
aid=f"{OID}.{VIEW}";mp=VIEWS/f"{aid}.json";ip=VIEWS/f"{aid}.png";meta=json.loads(mp.read_text());source=PACK/meta["provenance"]["source_image"]
sourceb=source.read_bytes();old=ip.read_bytes();target=Image.open(ip).convert("RGBA");tb=target.getchannel("A").getbbox()
ab=ATLAS.read_bytes();im=Image.open(ATLAS).convert("RGBA");a=np.asarray(im)[:,:,3];L,n=ndimage.label(a>=16)
if not n:raise SystemExit("No alpha")
s=np.bincount(L.ravel());lab=int(np.argmax(s[1:])+1);ys,xs=np.where(L==lab);box=(int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1));crop=im.crop(box)
tw,th=tb[2]-tb[0],tb[3]-tb[1];scale=min(tw/crop.width,th/crop.height);nw,nh=round(crop.width*scale),round(crop.height*scale)
crop=crop.resize((nw,nh),Image.Resampling.LANCZOS);canvas=Image.new("RGBA",(256,256),(0,0,0,0));anchor=(128,128);canvas.alpha_composite(crop,(anchor[0]-nw//2,anchor[1]-nh//2))
(RAW/f"{GEN}.previous.png").write_bytes(old);tmp=ip.with_suffix(".png.tmp");canvas.save(tmp,format="PNG",optimize=False);os.replace(tmp,ip);pb=ip.read_bytes()
meta["image"]["sha256"]=sha(pb);meta["image"]["rgba_sha256"]=sha(struct.pack(">II",256,256)+canvas.tobytes())
meta["provenance"].update({"source_atlas":f"reusable/views-additional/raw/{GEN}.png","source_atlas_sha256":sha(ab),"generation_recipe":f"reusable/views-additional/raw/{GEN}.prompt.txt",
 "notes":"inferred orthographic TOP view, not recovered pixels; small orange bottle cap moved to far-right back edge matching canonical front placement; separate wall lantern excluded",
 "crop_bounds_px":{"alpha_threshold":16,"alpha_bounds_global":list(box),"component_labels":[lab],"resized_bounds_px":[nw,nh],"canvas_offset_px":[anchor[0]-nw//2,anchor[1]-nh//2],"shared_scale":scale,"normalization":"uniform scale to prior approved top bounds, centered on shared anchor"}})
mp.write_text(json.dumps(meta,indent=2)+"\n")
for a in idx["assets"]:
 if a["id"]==aid:a.clear();a.update(meta);break
else:raise SystemExit("asset missing")
idxp.write_text(json.dumps(idx,indent=2)+"\n")
(RAW/f"{GEN}.install.json").write_text(json.dumps({"asset_id":aid,"source_sha256":sha(sourceb),"old_png_sha256":sha(old),"new_png_sha256":sha(pb),"atlas_sha256":sha(ab),"crop_bounds_xyxy":list(box),"target_bbox_before":list(tb),"installed_bbox":list(canvas.getchannel("A").getbbox()),"uniform_scale":scale},indent=2)+"\n")
print(json.dumps({"id":aid,"sha256":meta["image"]["sha256"],"bbox":list(canvas.getchannel("A").getbbox())},indent=2))
