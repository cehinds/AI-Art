#!/usr/bin/env python3
"""Install Mongo base-pose overhead and underside with distinct blunt head."""
import hashlib,json,struct,os
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
PACK=Path(__file__).resolve().parents[2];VIEWS=PACK/"reusable/views-additional";RAW=VIEWS/"raw";OID="revamp--characters--mongo"
JOBS={"top":("exec-446fc705-b068-480f-ac3d-0b6bc9a6fd82","True orthographic TOP: broad blunt skull and snout at image-bottom, distinct from broad neck/torso; four limbs and long tapering tail at image-top. Blue dorsal scales, eye at head perimeter. Preserve pose and body width; no spindle silhouette."),
 "bottom":("exec-044bee30-6b72-4b3d-8182-03cb0e277c4b","True orthographic BOTTOM: broad jaw/chin at image-top, cream belly, four visible foot pads nearest camera, long tapering tail to image-bottom. Distinct broad head/torso, preserve pose and palette; no face aimed upward.")}
def sha(b):return hashlib.sha256(b).hexdigest()
idxp=VIEWS/"set-index.json";idx=json.loads(idxp.read_text());assets={a["id"]:a for a in idx["assets"]};staged={}
for view,(gen,prompt) in JOBS.items():
 at=RAW/f"{gen}.png"
 if not at.exists():at.write_bytes((Path("/workspace/generated_images")/f"{gen}.png").read_bytes())
 pp=RAW/f"{gen}.prompt.txt";pp.write_text(prompt+"\n")
 ab=at.read_bytes();im=Image.open(at).convert("RGBA");a=np.asarray(im)[:,:,3];L,n=ndimage.label(a>=16)
 if not n:raise SystemExit("No alpha")
 s=np.bincount(L.ravel());lab=int(np.argmax(s[1:])+1);ys,xs=np.where(L==lab);box=(int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1));crop=im.crop(box)
 aid=f"{OID}.{view}";mp=VIEWS/f"{aid}.json";ip=VIEWS/f"{aid}.png";meta=json.loads(mp.read_text());old=ip.read_bytes();src=PACK/meta["provenance"]["source_image"];sb=src.read_bytes();tb=Image.open(ip).convert("RGBA").getchannel("A").getbbox();tw,th=tb[2]-tb[0],tb[3]-tb[1]
 scale=min(tw/crop.width,th/crop.height);nw,nh=round(crop.width*scale),round(crop.height*scale);crop=crop.resize((nw,nh),Image.Resampling.LANCZOS)
 canvas=Image.new("RGBA",(256,256),(0,0,0,0));anchor=(128,128);canvas.alpha_composite(crop,(anchor[0]-nw//2,anchor[1]-nh//2))
 (RAW/f"{gen}.previous-{view}.png").write_bytes(old);meta["image"]["rgba_sha256"]=sha(struct.pack(">II",256,256)+canvas.tobytes())
 meta["provenance"].update({"source_atlas":f"reusable/views-additional/raw/{gen}.png","source_atlas_sha256":sha(ab),"generation_recipe":f"reusable/views-additional/raw/{gen}.prompt.txt",
  "notes":"inferred orthographic view, not recovered pixels; broad blunt head/snout, differentiated torso/tail, and source standing-pose limb arrangement preserved; hidden surfaces inferred",
  "crop_bounds_px":{"alpha_threshold":16,"alpha_bounds_global":list(box),"component_labels":[lab],"resized_bounds_px":[nw,nh],"canvas_offset_px":[anchor[0]-nw//2,anchor[1]-nh//2],"shared_scale":scale,"normalization":"uniform scale to fit prior accepted view bounds, common anchor"}})
 staged[aid]=(ip,canvas,meta,old,box,scale,sb)
for aid,(ip,canvas,meta,old,box,scale,sb) in staged.items():
 tmp=ip.with_suffix(".png.tmp");canvas.save(tmp,format="PNG",optimize=False);os.replace(tmp,ip);pb=ip.read_bytes();meta["image"]["sha256"]=sha(pb);(VIEWS/f"{aid}.json").write_text(json.dumps(meta,indent=2)+"\n");assets[aid].clear();assets[aid].update(meta)
 (RAW/f"{aid}.install.json").write_text(json.dumps({"asset_id":aid,"source_image":meta["provenance"]["source_image"],"source_sha256":sha(sb),"old_png_sha256":sha(old),"new_png_sha256":sha(pb),"atlas_sha256":meta["provenance"]["source_atlas_sha256"],"crop_bounds_xyxy":list(box),"installed_bbox":list(canvas.getchannel("A").getbbox()),"uniform_scale":scale},indent=2)+"\n")
idx["assets"]=[assets[a["id"]] for a in idx["assets"]];idxp.write_text(json.dumps(idx,indent=2)+"\n")
print(json.dumps({a:{"sha256":assets[a]["image"]["sha256"],"bbox":list(staged[a][1].getchannel("A").getbbox())} for a in staged},indent=2))
