#!/usr/bin/env python3
"""Install one corrected head-on FRONT for Katia's distinct walk3 phase."""
import hashlib, json, struct
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

PACK = Path(__file__).resolve().parents[2]
VIEWS = PACK / "reusable/views-additional"
RAW = VIEWS / "raw"
OID = "revamp--characters--katia--walk3"
GEN = "exec-13cb7d2e-794b-4ef7-aeb0-a96fe89a4a5e"
ATLAS = RAW / f"{GEN}.png"
PROMPT = RAW / f"{GEN}.prompt.txt"
if not ATLAS.exists():
    ATLAS.write_bytes((Path("/workspace/generated_images") / f"{GEN}.png").read_bytes())
PROMPT.write_text(
    "Create one pixel-art orthographic FRONT projection of the same fantasy woman "
    "in the source walk3 phase. Correct the old side-facing front to a head-on "
    "camera; preserve the distinctive long stride, one forward leg and one trailing "
    "leg, purple hair, dark outfit, oversized gray armored gauntlet, palette and "
    "proportions. TOP/profile family defines world-Y facing, so forward reach is "
    "foreshortened. Transparent background; no equipment or pose substitution.\n",
    encoding="utf-8",
)

def sha(b): return hashlib.sha256(b).hexdigest()

index_path = PACK / "reusable/views-additional/set-index.json"
index = json.loads(index_path.read_text())
meta_path = VIEWS / f"{OID}.front.json"
img_path = VIEWS / f"{OID}.front.png"
meta = json.loads(meta_path.read_text())
source_path = PACK / meta["provenance"]["source_image"]
source_bytes = source_path.read_bytes()
old_bytes = img_path.read_bytes()
target = Image.open(img_path).convert("RGBA")
target_bbox = target.getchannel("A").getbbox()
atlas_bytes = ATLAS.read_bytes()
im = Image.open(ATLAS).convert("RGBA")
a = np.asarray(im)[:, :, 3]
labels, n = ndimage.label(a >= 16)
if n == 0: raise SystemExit("No foreground alpha in retained atlas")
sizes = np.bincount(labels.ravel())
label = int(np.argmax(sizes[1:]) + 1)
ys, xs = np.where(labels == label)
box = (int(xs.min()), int(ys.min()), int(xs.max()+1), int(ys.max()+1))
crop = im.crop(box)
tw, th = target_bbox[2]-target_bbox[0], target_bbox[3]-target_bbox[1]
scale = min(tw/crop.width, th/crop.height)
nw, nh = round(crop.width*scale), round(crop.height*scale)
crop = crop.resize((nw,nh),Image.Resampling.LANCZOS)
canvas=Image.new("RGBA",(256,256),(0,0,0,0)); anchor=(128,128)
canvas.alpha_composite(crop,(anchor[0]-nw//2,anchor[1]-nh//2))

(RAW / f"{GEN}.previous-front.png").write_bytes(old_bytes)
canvas.save(img_path,optimize=False)
png=img_path.read_bytes()
meta["image"]["sha256"]=sha(png)
meta["image"]["rgba_sha256"]=sha(struct.pack(">II",256,256)+canvas.tobytes())
meta["provenance"].update({
 "source_atlas":f"reusable/views-additional/raw/{GEN}.png",
 "source_atlas_sha256":sha(atlas_bytes),
 "generation_recipe":f"reusable/views-additional/raw/{GEN}.prompt.txt",
 "native_front":meta["provenance"]["source_image"],
 "native_front_sha256":sha(source_bytes),
 "notes":"inferred orthographic head-on front view, not recovered pixels; exact long-stride walk3 phase retained from source; unseen depth and far-side details are inferred",
 "crop_bounds_px":{"alpha_threshold":16,"alpha_bounds_global":list(box),"component_labels":[label],
  "resized_bounds_px":[nw,nh],"canvas_offset_px":[anchor[0]-nw//2,anchor[1]-nh//2],
  "shared_scale":scale,"normalization":"uniform scale to prior accepted front silhouette extent, centered on common anchor"},
})
meta_path.write_text(json.dumps(meta,indent=2)+"\n")
for item in index["assets"]:
 if item["id"]==meta["id"]: item.clear(); item.update(meta); break
else: raise SystemExit("Target leaf missing from index")
index_path.write_text(json.dumps(index,indent=2)+"\n")
(RAW/f"{GEN}.install.json").write_text(json.dumps({
 "object_id":OID,"view":"front","source_image":meta["provenance"]["source_image"],
 "source_sha256":sha(source_bytes),"atlas":ATLAS.relative_to(PACK).as_posix(),
 "atlas_sha256":sha(atlas_bytes),"previous_png_sha256":sha(old_bytes),
 "installed_png_sha256":sha(png),"crop_bounds_xyxy":list(box),
 "target_bbox":list(target_bbox),"installed_bbox":list(canvas.getchannel("A").getbbox()),
 "uniform_scale":scale,"alpha_threshold":16
},indent=2)+"\n")
print(json.dumps({"id":meta["id"],"old_sha256":sha(old_bytes),"new_sha256":sha(png),
 "target_bbox":target_bbox,"installed_bbox":canvas.getchannel("A").getbbox()},indent=2))
