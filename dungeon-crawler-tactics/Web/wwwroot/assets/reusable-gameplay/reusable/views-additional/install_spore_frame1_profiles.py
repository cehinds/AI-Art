#!/usr/bin/env python3
"""Install the two opposing true profiles for expedition Spore frame 1."""
import hashlib,json,struct,tempfile,os
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

PACK=Path(__file__).resolve().parents[2]; VIEWS=PACK/"reusable/views-additional"; RAW=VIEWS/"raw"
OID="expedition-enemies--spore--frame-1"
jobs={
 "right":("exec-763829c2-4206-4845-bad9-02f378bbabf3",
  "Generate a strict orthographic RIGHT-SIDE elevation of the exact Spore frame-1 stance. Show a true one-eye profile, narrow stem depth, mushroom cap as side overhang. Preserve source limbs, attack-ready pose, purple spotted cap, colors and anatomy. Transparent pixel art."),
 "left":("exec-3c65b203-57a3-4f8c-ab9f-7ab411167a4a",
  "Generate the exact opposite orthographic LEFT-SIDE elevation of the same Spore frame-1 stance. Face screen-right with only the opposite single eye visible, not a frontal two-eye face. Preserve source limbs, attack-ready pose, spotted cap, palette and anatomy. Transparent pixel art.")
}
def sha(b):return hashlib.sha256(b).hexdigest()
idxp=VIEWS/"set-index.json";idx=json.loads(idxp.read_text()); assets={a["id"]:a for a in idx["assets"]}
staged={}; entries={}
for view,(gen,prompt) in jobs.items():
 atlas_path=RAW/f"{gen}.png"
 if not atlas_path.exists(): atlas_path.write_bytes((Path("/workspace/generated_images")/f"{gen}.png").read_bytes())
 (RAW/f"{gen}.prompt.txt").write_text(prompt+"\n")
 atlas_bytes=atlas_path.read_bytes(); atlas=Image.open(atlas_path).convert("RGBA"); alpha=np.asarray(atlas)[:,:,3]
 labels,n=ndimage.label(alpha>=16)
 if not n: raise SystemExit(f"No foreground alpha: {gen}")
 sizes=np.bincount(labels.ravel()); label=int(np.argmax(sizes[1:])+1); ys,xs=np.where(labels==label)
 box=(int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)); crop=atlas.crop(box)
 aid=f"{OID}.{view}"; meta=json.loads((VIEWS/f"{aid}.json").read_text()); path=VIEWS/f"{aid}.png"
 old=path.read_bytes(); tgt=Image.open(path).convert("RGBA"); tb=tgt.getchannel("A").getbbox(); tw,th=tb[2]-tb[0],tb[3]-tb[1]
 scale=min(tw/crop.width,th/crop.height); nw,nh=round(crop.width*scale),round(crop.height*scale)
 crop=crop.resize((nw,nh),Image.Resampling.LANCZOS); canvas=Image.new("RGBA",(256,256),(0,0,0,0)); anchor=(128,128)
 canvas.alpha_composite(crop,(anchor[0]-nw//2,anchor[1]-nh//2))
 (RAW/f"{gen}.previous-{view}.png").write_bytes(old)
 meta["image"]["sha256"]=sha(canvas.tobytes()) if False else ""
 meta["image"]["rgba_sha256"]=sha(struct.pack(">II",256,256)+canvas.tobytes())
 meta["provenance"].update({"source_atlas":f"reusable/views-additional/raw/{gen}.png","source_atlas_sha256":sha(atlas_bytes),
  "generation_recipe":f"reusable/views-additional/raw/{gen}.prompt.txt",
  "notes":"inferred orthographic opposite side profile, not recovered pixels; strict perpendicular projection preserves native frame-1 stance and profile-facing eye; unseen surfaces inferred",
  "crop_bounds_px":{"alpha_threshold":16,"alpha_bounds_global":list(box),"component_labels":[label],"resized_bounds_px":[nw,nh],
   "canvas_offset_px":[anchor[0]-nw//2,anchor[1]-nh//2],"shared_scale":scale,
   "normalization":"uniform scale to prior accepted profile extent, centered on shared anchor"}})
 data=canvas.tobytes(); staged[aid]=(path,canvas,meta,old); entries[aid]=meta
for aid,(path,canvas,meta,old) in staged.items():
 tmp=path.with_suffix(".png.tmp");canvas.save(tmp,format="PNG",optimize=False);os.replace(tmp,path)
 pb=path.read_bytes();meta["image"]["sha256"]=sha(pb);(VIEWS/f"{aid}.json").write_text(json.dumps(meta,indent=2)+"\n");assets[aid].clear();assets[aid].update(meta)
 (RAW/f"{meta['provenance']['source_atlas'].split('/')[-1]}.{aid.split('.')[-1]}.install.json").write_text(json.dumps({
  "asset_id":aid,"old_png_sha256":sha(old),"new_png_sha256":sha(pb),"source_sha256":sha((PACK/meta["provenance"]["source_image"]).read_bytes()),
  "crop_bounds_xyxy":meta["provenance"]["crop_bounds_px"]["alpha_bounds_global"],"installed_bbox":list(canvas.getchannel("A").getbbox()),
  "scale":meta["provenance"]["crop_bounds_px"]["shared_scale"]},indent=2)+"\n")
idx["assets"]=[assets[a["id"]] for a in idx["assets"]];idxp.write_text(json.dumps(idx,indent=2)+"\n")
print(json.dumps({aid:{"png_sha256":assets[aid]["image"]["sha256"],"bbox":list(staged[aid][1].getchannel("A").getbbox())} for aid in staged},indent=2))
