#!/usr/bin/env python3
"""Install the corrected head-on FRONT for Katia's attack pose."""
import hashlib, json, struct
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

PACK=Path(__file__).resolve().parents[2]; VIEWS=PACK/"reusable/views-additional"; RAW=VIEWS/"raw"
OID="revamp--characters--katia--attack"; GEN="exec-278731c4-0345-4d45-88ee-1b1ea0d3191f"
ATLAS=RAW/f"{GEN}.png"; PROMPT=RAW/f"{GEN}.prompt.txt"
if not ATLAS.exists(): ATLAS.write_bytes((Path("/workspace/generated_images")/f"{GEN}.png").read_bytes())
PROMPT.write_text(
 "Generate one transparent pixel-art orthographic FRONT projection of the canonical "
 "Katia attack source. Preserve this exact attack phase: one oversized armored fist "
 "punches straight toward the viewer and is foreshortened into a compact fist/gauntlet "
 "near torso center, not a long arm stretched sideways. The other arm stays bent near "
 "waist; retain source leg stance, hair, outfit, gauntlets and body mass. A head-on "
 "camera aligned with world-Y punch axis; no pose/equipment substitution.\n",encoding="utf-8")
def sha(b): return hashlib.sha256(b).hexdigest()
index_path=PACK/"reusable/views-additional/set-index.json"; index=json.loads(index_path.read_text())
meta_path=VIEWS/f"{OID}.front.json"; img_path=VIEWS/f"{OID}.front.png"; meta=json.loads(meta_path.read_text())
source_path=PACK/meta["provenance"]["source_image"]; source_bytes=source_path.read_bytes(); old_bytes=img_path.read_bytes()
target=Image.open(img_path).convert("RGBA"); tb=target.getchannel("A").getbbox()
atlas_bytes=ATLAS.read_bytes(); im=Image.open(ATLAS).convert("RGBA"); a=np.asarray(im)[:,:,3]
labels,n=ndimage.label(a>=16)
if not n: raise SystemExit("No source alpha component")
sizes=np.bincount(labels.ravel()); label=int(np.argmax(sizes[1:])+1)
ys,xs=np.where(labels==label); box=(int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1))
crop=im.crop(box); tw,th=tb[2]-tb[0],tb[3]-tb[1]; scale=min(tw/crop.width,th/crop.height)
nw,nh=round(crop.width*scale),round(crop.height*scale); crop=crop.resize((nw,nh),Image.Resampling.LANCZOS)
canvas=Image.new("RGBA",(256,256),(0,0,0,0)); anchor=(128,128); canvas.alpha_composite(crop,(anchor[0]-nw//2,anchor[1]-nh//2))
(RAW/f"{GEN}.previous-front.png").write_bytes(old_bytes); canvas.save(img_path,optimize=False); png=img_path.read_bytes()
meta["image"]["sha256"]=sha(png); meta["image"]["rgba_sha256"]=sha(struct.pack(">II",256,256)+canvas.tobytes())
meta["provenance"].update({
 "source_atlas":f"reusable/views-additional/raw/{GEN}.png","source_atlas_sha256":sha(atlas_bytes),
 "generation_recipe":f"reusable/views-additional/raw/{GEN}.prompt.txt",
 "native_front":meta["provenance"]["source_image"],"native_front_sha256":sha(source_bytes),
 "notes":"inferred orthographic head-on front view, not recovered pixels; forward punch and off-hand placement are source-pose-preserving projections; hidden depth inferred",
 "crop_bounds_px":{"alpha_threshold":16,"alpha_bounds_global":list(box),"component_labels":[label],"resized_bounds_px":[nw,nh],"canvas_offset_px":[anchor[0]-nw//2,anchor[1]-nh//2],"shared_scale":scale,"normalization":"uniform scale to prior accepted front silhouette extent, centered on common anchor"}
})
meta_path.write_text(json.dumps(meta,indent=2)+"\n")
for item in index["assets"]:
 if item["id"]==meta["id"]: item.clear(); item.update(meta); break
else: raise SystemExit("Leaf absent from set-index")
index_path.write_text(json.dumps(index,indent=2)+"\n")
(RAW/f"{GEN}.install.json").write_text(json.dumps({"object_id":OID,"view":"front","source_image":meta["provenance"]["source_image"],"source_sha256":sha(source_bytes),"atlas":ATLAS.relative_to(PACK).as_posix(),"atlas_sha256":sha(atlas_bytes),"previous_png_sha256":sha(old_bytes),"installed_png_sha256":sha(png),"crop_bounds_xyxy":list(box),"target_bbox":list(tb),"installed_bbox":list(canvas.getchannel("A").getbbox()),"uniform_scale":scale,"alpha_threshold":16},indent=2)+"\n")
print(json.dumps({"id":meta["id"],"old_sha256":sha(old_bytes),"new_sha256":sha(png),"installed_bbox":canvas.getchannel("A").getbbox()},indent=2))
