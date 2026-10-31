#!/usr/bin/env python3
"""Install the asymmetric Juicer frame-3 overhead and underside projections."""
import hashlib,json,struct,os
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
PACK=Path(__file__).resolve().parents[2];VIEWS=PACK/"reusable/views-additional";RAW=VIEWS/"raw"
OID="bosses--juicer--frame-3"
JOBS={
 "top":("exec-0ab3395d-5b92-4ccf-9722-20e7c5ede092","Strict orthographic top-down view of the canonical throwing pose. Preserve wide muscular torso, source tail/legs and asymmetric arms: one throwing arm reaches forward along world Y toward the single projectile, the other stays bent near waist. No symmetric raised arms. Head at image-bottom, tail at top; retain one projectile in same position."),
 "bottom":("exec-c8869f61-83ac-4535-9cb5-1a50fcbc9378","Strict orthographic bottom-up view of the exact same canonical throwing pose. Preserve wide muscular torso, tail/legs and asymmetric arms: one throwing arm reaches forward along world Y toward the single projectile, the other stays bent near waist. No symmetric raised arms. Show true underside, head at image-top and tail at bottom, opposite the top view; retain one projectile at same forward position.")
}
def sha(b):return hashlib.sha256(b).hexdigest()
idxp=VIEWS/"set-index.json";idx=json.loads(idxp.read_text());assets={a["id"]:a for a in idx["assets"]};staged={}
for view,(gen,prompt) in JOBS.items():
 atlaspath=RAW/f"{gen}.png"
 if not atlaspath.exists():atlaspath.write_bytes((Path("/workspace/generated_images")/f"{gen}.png").read_bytes())
 pp=RAW/f"{gen}.prompt.txt";pp.write_text(prompt+"\n")
 ab=atlaspath.read_bytes();im=Image.open(atlaspath).convert("RGBA");a=np.asarray(im)[:,:,3];labels,n=ndimage.label(a>=16);sizes=np.bincount(labels.ravel())
 ids=[int(i) for i in np.where(sizes>20)[0] if i!=0]
 if not ids:raise SystemExit(f"No major components in {gen}")
 mask=np.isin(labels,ids);ys,xs=np.where(mask);box=(int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1));crop=im.crop(box)
 aid=f"{OID}.{view}";mp=VIEWS/f"{aid}.json";ip=VIEWS/f"{aid}.png";meta=json.loads(mp.read_text());old=ip.read_bytes();target=Image.open(ip).convert("RGBA");tb=target.getchannel("A").getbbox();tw,th=tb[2]-tb[0],tb[3]-tb[1]
 scale=min(tw/crop.width,th/crop.height);nw,nh=round(crop.width*scale),round(crop.height*scale);crop=crop.resize((nw,nh),Image.Resampling.LANCZOS)
 canvas=Image.new("RGBA",(256,256),(0,0,0,0));anchor=(128,128);canvas.alpha_composite(crop,(anchor[0]-nw//2,anchor[1]-nh//2))
 (RAW/f"{gen}.previous-{view}.png").write_bytes(old)
 meta["image"]["rgba_sha256"]=sha(struct.pack(">II",256,256)+canvas.tobytes())
 meta["provenance"].update({"source_atlas":f"reusable/views-additional/raw/{gen}.png","source_atlas_sha256":sha(ab),
  "generation_recipe":f"reusable/views-additional/raw/{gen}.prompt.txt",
  "notes":"inferred orthographic throwing-pose projection, not recovered pixels; one extended throwing arm and one bent off-hand preserve source asymmetry/body mass; projectile count and placement are source-guided; hidden surfaces inferred",
  "crop_bounds_px":{"alpha_threshold":16,"alpha_bounds_global":list(box),"component_labels":ids,"resized_bounds_px":[nw,nh],"canvas_offset_px":[anchor[0]-nw//2,anchor[1]-nh//2],"shared_scale":scale,"normalization":"uniform scale to fit prior target view bounds; body and projectile retained together"}})
 staged[aid]=(ip,canvas,meta,old,box,scale)
for aid,(ip,canvas,meta,old,box,scale) in staged.items():
 tmp=ip.with_suffix(".png.tmp");canvas.save(tmp,format="PNG",optimize=False);os.replace(tmp,ip);pb=ip.read_bytes()
 meta["image"]["sha256"]=sha(pb);(VIEWS/f"{aid}.json").write_text(json.dumps(meta,indent=2)+"\n");assets[aid].clear();assets[aid].update(meta)
 (RAW/f"{aid}.install.json").write_text(json.dumps({"asset_id":aid,"old_png_sha256":sha(old),"new_png_sha256":sha(pb),"source_image":meta["provenance"]["source_image"],"source_sha256":sha((PACK/meta["provenance"]["source_image"]).read_bytes()),"atlas":meta["provenance"]["source_atlas"],"atlas_sha256":meta["provenance"]["source_atlas_sha256"],"crop_bounds_xyxy":list(box),"installed_bbox":list(canvas.getchannel("A").getbbox()),"uniform_scale":scale},indent=2)+"\n")
idx["assets"]=[assets[a["id"]] for a in idx["assets"]];idxp.write_text(json.dumps(idx,indent=2)+"\n")
print(json.dumps({a:{"sha256":assets[a]["image"]["sha256"],"bbox":list(staged[a][1].getchannel("A").getbbox())} for a in staged},indent=2))
