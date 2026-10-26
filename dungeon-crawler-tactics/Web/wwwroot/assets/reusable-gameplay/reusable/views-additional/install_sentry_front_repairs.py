#!/usr/bin/env python3
"""Install targeted head-on FRONT cameras for Sentry frames 2 and 3."""
import hashlib,json,struct,os
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
PACK=Path(__file__).resolve().parents[2];VIEWS=PACK/"reusable/views-additional";RAW=VIEWS/"raw"
JOBS={
 "expedition-enemies--sentry--frame-2":("exec-41f89d92-eaf1-49e9-973b-9a185aa2e998",
  "Generate head-on orthographic FRONT of exact frame-2 walking sentry. Correct old three-quarter view to centered frontal body, cyan lens aimed directly at camera, preserve stride, brass riveted shell, paired crown rings and all source proportions. No side face, new gear or pose change."),
 "expedition-enemies--sentry--frame-3":("exec-59d750f8-50ce-4063-ab05-37750618c213",
  "Generate head-on orthographic FRONT of exact frame-3 attacking sentry. Gun arm thrusts forward along world Y; foreshorten long barrel to a compact end-on muzzle in front of centered cyan lens, not horizontally across screen. Preserve asymmetric extended gun arm, bent other arm, stance, body mass, brass armor and rings; no perspective or extra weapon.")
}
def sha(b):return hashlib.sha256(b).hexdigest()
idxp=VIEWS/"set-index.json";idx=json.loads(idxp.read_text());assets={a["id"]:a for a in idx["assets"]};staged={}
for oid,(gen,prompt) in JOBS.items():
 atlaspath=RAW/f"{gen}.png"
 if not atlaspath.exists():atlaspath.write_bytes((Path("/workspace/generated_images")/f"{gen}.png").read_bytes())
 pp=RAW/f"{gen}.prompt.txt";pp.write_text(prompt+"\n")
 ab=atlaspath.read_bytes();im=Image.open(atlaspath).convert("RGBA");alpha=np.asarray(im)[:,:,3];L,n=ndimage.label(alpha>=16)
 if not n:raise SystemExit(f"No alpha in {gen}")
 s=np.bincount(L.ravel());lab=int(np.argmax(s[1:])+1);ys,xs=np.where(L==lab);box=(int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1));crop=im.crop(box)
 aid=f"{oid}.front";mp=VIEWS/f"{aid}.json";ip=VIEWS/f"{aid}.png";meta=json.loads(mp.read_text());old=ip.read_bytes();source=PACK/meta["provenance"]["source_image"];sb=source.read_bytes();tb=Image.open(ip).convert("RGBA").getchannel("A").getbbox();tw,th=tb[2]-tb[0],tb[3]-tb[1]
 scale=min(tw/crop.width,th/crop.height);nw,nh=round(crop.width*scale),round(crop.height*scale);crop=crop.resize((nw,nh),Image.Resampling.LANCZOS)
 canvas=Image.new("RGBA",(256,256),(0,0,0,0));anchor=(128,128);canvas.alpha_composite(crop,(anchor[0]-nw//2,anchor[1]-nh//2))
 (RAW/f"{gen}.previous-front.png").write_bytes(old)
 meta["image"]["rgba_sha256"]=sha(struct.pack(">II",256,256)+canvas.tobytes())
 meta["provenance"].update({"source_atlas":f"reusable/views-additional/raw/{gen}.png","source_atlas_sha256":sha(ab),"generation_recipe":f"reusable/views-additional/raw/{gen}.prompt.txt",
  "notes":"inferred orthographic head-on FRONT projection, not recovered pixels; Sentry camera and source attack/walk pose preserved; unseen surfaces inferred",
  "crop_bounds_px":{"alpha_threshold":16,"alpha_bounds_global":list(box),"component_labels":[lab],"resized_bounds_px":[nw,nh],"canvas_offset_px":[anchor[0]-nw//2,anchor[1]-nh//2],"shared_scale":scale,"normalization":"uniform scale to prior accepted front bounds; centered on shared anchor"}})
 staged[aid]=(ip,canvas,meta,old,box,scale,sb)
for aid,(ip,canvas,meta,old,box,scale,sb) in staged.items():
 tmp=ip.with_suffix(".png.tmp");canvas.save(tmp,format="PNG",optimize=False);os.replace(tmp,ip);pb=ip.read_bytes();meta["image"]["sha256"]=sha(pb)
 (VIEWS/f"{aid}.json").write_text(json.dumps(meta,indent=2)+"\n");assets[aid].clear();assets[aid].update(meta)
 (RAW/f"{aid}.install.json").write_text(json.dumps({"asset_id":aid,"source_image":meta["provenance"]["source_image"],"source_sha256":sha(sb),"old_png_sha256":sha(old),"new_png_sha256":sha(pb),"atlas_sha256":meta["provenance"]["source_atlas_sha256"],"crop_bounds_xyxy":list(box),"installed_bbox":list(canvas.getchannel("A").getbbox()),"uniform_scale":scale},indent=2)+"\n")
idx["assets"]=[assets[a["id"]] for a in idx["assets"]];idxp.write_text(json.dumps(idx,indent=2)+"\n")
print(json.dumps({a:{"sha256":assets[a]["image"]["sha256"],"bbox":list(staged[a][1].getchannel("A").getbbox())} for a in staged},indent=2))
