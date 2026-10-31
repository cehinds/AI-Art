#!/usr/bin/env python3
"""Install folded-wing WALK2 principal views from a four-direction atlas."""
from pathlib import Path
import hashlib,json,os,struct
from PIL import Image
PACK=Path(__file__).resolve().parents[2];V=PACK/"reusable/views-additional";RAW=V/"raw"
OID="revamp--mongo--mongo--walk2";ATLAS=RAW/"ally-mongo-walk2-front-top-bottom-rear-v1.png";REQUEST="exec-48c1e8fa-70e4-4f07-8101-e713c7b4c588"
ORDER=["front","top","bottom","rear"]
def sha(b):return hashlib.sha256(b).hexdigest()
def rh(im):return sha(struct.pack(">II",*im.size)+im.convert("RGBA").tobytes())
idxp=V/"set-index.json";idx=json.loads(idxp.read_text());rec={a["id"]:a for a in idx["assets"]};im=Image.open(ATLAS).convert("RGBA");raw=ATLAS.read_bytes();cw=im.width/4
src=PACK/"reusable/native"/f"{OID}.png";srcsha=sha(src.read_bytes())
oldz=[];newz=[];cells=[]
for vw in ("front","rear"):
 b=Image.open(V/f"{OID}.{vw}.png").convert("RGBA").getchannel("A").getbbox();oldz.append(b[3]-b[1])
for i,vw in enumerate(ORDER):
 x0,x1=round(i*cw),round((i+1)*cw);cell=im.crop((x0,0,x1,im.height));box=cell.getchannel("A").point(lambda x:255 if x>=16 else 0).getbbox()
 if not box:raise ValueError(f"empty {vw}")
 crop=cell.crop(box);cells.append((vw,x0,x1-x0,box,crop))
 if vw in ("front","rear"):newz.append(crop.height)
scale=(sum(oldz)/len(oldz))/(sum(newz)/len(newz));stage=[]
for vw,x0,cwpx,box,crop in cells:
 nw,nh=max(1,round(crop.width*scale)),max(1,round(crop.height*scale));res=crop.resize((nw,nh),Image.Resampling.LANCZOS);canvas=Image.new("RGBA",(256,256),(0,0,0,0));off=(128-nw//2,128-nh//2);canvas.alpha_composite(res,off)
 aid=f"{OID}.{vw}";out=V/f"{aid}.png";side=V/f"{aid}.json";meta=json.loads(side.read_text())
 if meta["provenance"]["source_image"]!=f"reusable/native/{OID}.png":raise ValueError(f"noncanonical source {aid}")
 stage.append((aid,vw,out,side,meta,canvas,x0,cwpx,im.height,box,(nw,nh),off,sha(out.read_bytes())))
for aid,vw,out,side,meta,canvas,x0,cwpx,ch,box,sz,off,oldsha in stage:
 tmp=out.with_suffix(".png.tmp");canvas.save(tmp,format="PNG",optimize=False);os.replace(tmp,out);new=out.read_bytes();meta["image"]["sha256"]=sha(new);meta["image"]["rgba_sha256"]=rh(canvas)
 meta["provenance"].update({"source_image":f"reusable/native/{OID}.png","source_image_sha256":srcsha,"source_atlas":f"reusable/views-additional/raw/{ATLAS.name}","source_atlas_sha256":sha(raw),"generation_request_id":REQUEST,"generation_prompt":"reusable/views-additional/raw/ally-mongo-walk2-front-top-bottom-rear-v1.prompt.txt","generation_recipe":"reusable/views-additional/install_ally_mongo_walk2_folded_wings.py","notes":"Generated inferred orthographic view for exact WALK2 source pose; pink wings remain folded alongside torso in all cameras; hidden surfaces inferred, not recovered pixels.","crop_bounds_px":{"coordinate_format":"xywh","nominal_cell":{"bounds":[x0,0,cwpx,ch]},"alpha_threshold":16,"alpha_bounds_global":[x0+box[0],box[1],box[2]-box[0],box[3]-box[1]],"resized_bounds_px":list(sz),"canvas_offset_px":list(off),"shared_anchor_px":[128,128],"uniform_scale":scale,"normalization":"one isotropic scale calibrated from accepted front/rear elevation Z height; shared anchor"}})
 side.write_text(json.dumps(meta,indent=2)+"\n");rec[aid].clear();rec[aid].update(meta);(RAW/f"{aid}.folded-wings-20261026.json").write_text(json.dumps({"asset_id":aid,"source_image":meta["provenance"]["source_image"],"source_image_sha256":srcsha,"source_atlas":ATLAS.name,"source_atlas_sha256":sha(raw),"generation_request_id":REQUEST,"cell_crop_bounds_xywh":[x0+box[0],box[1],box[2]-box[0],box[3]-box[1]],"output_bbox_xywh":list(canvas.getchannel("A").getbbox()),"uniform_scale":scale,"old_png_sha256":oldsha,"new_png_sha256":sha(new)},indent=2)+"\n")
idx["assets"]=[rec[a["id"]] for a in idx["assets"]];idxp.write_text(json.dumps(idx,indent=2)+"\n")
print(json.dumps({a[0]:list(a[5].getchannel("A").getbbox()) for a in stage},indent=2))
