#!/usr/bin/env python3
"""Install four corrected source-pose elevations for WALK3."""
from pathlib import Path
import hashlib,json,os,struct
from PIL import Image
import numpy as np
from scipy import ndimage
PACK=Path(__file__).resolve().parents[2];V=PACK/"reusable/views-additional";RAW=V/"raw"
OID="revamp--mongo--mongo--walk3";ATLAS=RAW/"ally-mongo-walk3-elevations-v1.png";REQUEST="exec-6cc847d2-15bf-4761-93fa-aed77aa55aa0";ORDER=["front","right","left","rear"]
def sha(b):return hashlib.sha256(b).hexdigest()
def rh(im):return sha(struct.pack(">II",*im.size)+im.convert("RGBA").tobytes())
idxp=V/"set-index.json";idx=json.loads(idxp.read_text());rec={a["id"]:a for a in idx["assets"]};atlas=Image.open(ATLAS).convert("RGBA");raw=ATLAS.read_bytes();cw=atlas.width/4;src=PACK/"reusable/native"/f"{OID}.png";srcsha=sha(src.read_bytes())
targets=[];news=[]
for v in ("front","right","left","rear"):
 b=Image.open(V/f"{OID}.{v}.png").convert("RGBA").getchannel("A").getbbox();targets.append(b[3]-b[1])
cells=[]
for i,v in enumerate(ORDER):
 x0,x1=round(i*cw),round((i+1)*cw);cell=atlas.crop((x0,0,x1,atlas.height));alpha=np.asarray(cell.getchannel("A"));labels,_=ndimage.label(alpha>=16);sizes=np.bincount(labels.ravel());sizes[0]=0;main=int(np.argmax(sizes));ys,xs=np.where(labels==main);box=(int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1))
 if not box:raise ValueError(f"empty {v}")
 crop=cell.crop(box);cells.append((v,x0,x1-x0,box,crop));news.append(crop.height)
scale=sum(targets)/len(targets)/(sum(news)/len(news));stage=[]
for v,x0,cwpx,box,crop in cells:
 nw,nh=max(1,round(crop.width*scale)),max(1,round(crop.height*scale));res=crop.resize((nw,nh),Image.Resampling.LANCZOS);canvas=Image.new("RGBA",(256,256),(0,0,0,0));off=(128-nw//2,128-nh//2);canvas.alpha_composite(res,off);aid=f"{OID}.{v}";out=V/f"{aid}.png";side=V/f"{aid}.json";meta=json.loads(side.read_text())
 if meta["provenance"]["source_image"]!=f"reusable/native/{OID}.png":raise ValueError("noncanonical source")
 stage.append((aid,v,out,side,meta,canvas,x0,cwpx,atlas.height,box,(nw,nh),off,sha(out.read_bytes())))
for aid,v,out,side,meta,canvas,x0,cwpx,ch,box,sz,off,old in stage:
 tmp=out.with_suffix(".png.tmp");canvas.save(tmp,format="PNG",optimize=False);os.replace(tmp,out);new=out.read_bytes();meta["image"]["sha256"]=sha(new);meta["image"]["rgba_sha256"]=rh(canvas);meta["provenance"].update({"source_image":f"reusable/native/{OID}.png","source_image_sha256":srcsha,"source_atlas":f"reusable/views-additional/raw/{ATLAS.name}","source_atlas_sha256":sha(raw),"generation_request_id":REQUEST,"generation_prompt":"reusable/views-additional/raw/ally-mongo-walk3-elevations-v1.prompt.txt","generation_recipe":"reusable/views-additional/install_ally_mongo_walk3_stride.py","notes":"Inferred orthographic views of the exact WALK3 pose; long forward leading stride retained across front, opposite profiles, and rear. Disconnected stray components outside the main body silhouette are excluded; no anatomy was painted or reshaped. Hidden surfaces are inferred, not recovered pixels.","crop_bounds_px":{"coordinate_format":"xywh","nominal_cell":{"bounds":[x0,0,cwpx,ch]},"alpha_threshold":16,"component_selection":"largest connected component, excluding detached fragments","alpha_bounds_global":[x0+box[0],box[1],box[2]-box[0],box[3]-box[1]],"resized_bounds_px":list(sz),"canvas_offset_px":list(off),"shared_anchor_px":[128,128],"uniform_scale":scale,"normalization":"one isotropic scale matching accepted elevation Z extents; shared anchor"}});side.write_text(json.dumps(meta,indent=2)+"\n");rec[aid].clear();rec[aid].update(meta);(RAW/f"{aid}.walk3-stride-20261026.json").write_text(json.dumps({"asset_id":aid,"source_image":meta["provenance"]["source_image"],"source_image_sha256":srcsha,"source_atlas":ATLAS.name,"source_atlas_sha256":sha(raw),"generation_request_id":REQUEST,"cell_crop_bounds_xywh":[x0+box[0],box[1],box[2]-box[0],box[3]-box[1]],"component_selection":"largest connected component","output_bbox_xywh":list(canvas.getchannel("A").getbbox()),"uniform_scale":scale,"old_png_sha256":old,"new_png_sha256":sha(new)},indent=2)+"\n")
idx["assets"]=[rec[a["id"]] for a in idx["assets"]];idxp.write_text(json.dumps(idx,indent=2)+"\n")
print(json.dumps({a[0]:list(a[5].getchannel("A").getbbox()) for a in stage},indent=2))
