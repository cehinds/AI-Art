#!/usr/bin/env python3
"""Install the head-on FRONT projection for Cinder frame 2."""
import hashlib,json,struct,os
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
PACK=Path(__file__).resolve().parents[2];VIEWS=PACK/"reusable/views-additional";RAW=VIEWS/"raw"
OID="expedition-enemies--cinder--frame-2";GEN="exec-877f7c0d-9da3-4702-a32d-06a1fa0d939a"
ATLAS=RAW/f"{GEN}.png"
if not ATLAS.exists():ATLAS.write_bytes((Path("/workspace/generated_images")/f"{GEN}.png").read_bytes())
prompt="Generate one strict orthographic FRONT projection of the same frame-2 fire beetle. Correct the old FRONT's side profile to head-on: centered bilateral beetle head/mandibles, paired front legs and armored shell directly from front. Preserve exact phase, orange-red shell, black-gold markings, flame mane, limb count and proportions. Transparent background, no perspective, extra limbs or gear.\n"
(RAW/f"{GEN}.prompt.txt").write_text(prompt)
def sha(b):return hashlib.sha256(b).hexdigest()
idxp=VIEWS/"set-index.json";idx=json.loads(idxp.read_text());aid=f"{OID}.front";assets={a["id"]:a for a in idx["assets"]}
meta=json.loads((VIEWS/f"{aid}.json").read_text());ip=VIEWS/f"{aid}.png";old=ip.read_bytes();source=PACK/meta["provenance"]["source_image"];sb=source.read_bytes();tb=Image.open(ip).convert("RGBA").getchannel("A").getbbox()
ab=ATLAS.read_bytes();im=Image.open(ATLAS).convert("RGBA");a=np.asarray(im)[:,:,3];L,n=ndimage.label(a>=16)
if not n:raise SystemExit("No foreground alpha")
s=np.bincount(L.ravel());lab=int(np.argmax(s[1:])+1);ys,xs=np.where(L==lab);box=(int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1));crop=im.crop(box)
tw,th=tb[2]-tb[0],tb[3]-tb[1];scale=min(tw/crop.width,th/crop.height);nw,nh=round(crop.width*scale),round(crop.height*scale);crop=crop.resize((nw,nh),Image.Resampling.LANCZOS)
canvas=Image.new("RGBA",(256,256),(0,0,0,0));anchor=(128,128);canvas.alpha_composite(crop,(anchor[0]-nw//2,anchor[1]-nh//2))
(RAW/f"{GEN}.previous.png").write_bytes(old);tmp=ip.with_suffix(".png.tmp");canvas.save(tmp,format="PNG",optimize=False);os.replace(tmp,ip);pb=ip.read_bytes()
meta["image"]["sha256"]=sha(pb);meta["image"]["rgba_sha256"]=sha(struct.pack(">II",256,256)+canvas.tobytes())
meta["provenance"].update({"source_atlas":f"reusable/views-additional/raw/{GEN}.png","source_atlas_sha256":sha(ab),"generation_recipe":f"reusable/views-additional/raw/{GEN}.prompt.txt",
 "notes":"inferred orthographic head-on FRONT, not recovered pixels; preserves source frame-2 fire beetle identity and phase; hidden surfaces inferred",
 "crop_bounds_px":{"alpha_threshold":16,"alpha_bounds_global":list(box),"component_labels":[lab],"resized_bounds_px":[nw,nh],"canvas_offset_px":[anchor[0]-nw//2,anchor[1]-nh//2],"shared_scale":scale,"normalization":"uniform scale to fit prior approved view bounds, centered at common anchor"}})
(VIEWS/f"{aid}.json").write_text(json.dumps(meta,indent=2)+"\n")
for a in idx["assets"]:
 if a["id"]==aid:a.clear();a.update(meta);break
else:raise SystemExit("Target leaf absent")
idxp.write_text(json.dumps(idx,indent=2)+"\n")
(RAW/f"{GEN}.install.json").write_text(json.dumps({"asset_id":aid,"source_image":meta["provenance"]["source_image"],"source_sha256":sha(sb),"atlas_sha256":sha(ab),"old_png_sha256":sha(old),"new_png_sha256":sha(pb),"crop_bounds_xyxy":list(box),"target_bbox":list(tb),"installed_bbox":list(canvas.getchannel("A").getbbox()),"uniform_scale":scale},indent=2)+"\n")
print(json.dumps({"id":aid,"sha256":meta["image"]["sha256"],"bbox":list(canvas.getchannel("A").getbbox())},indent=2))
