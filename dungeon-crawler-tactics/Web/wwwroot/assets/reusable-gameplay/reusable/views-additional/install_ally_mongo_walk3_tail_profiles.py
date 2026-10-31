#!/usr/bin/env python3
"""Install Page/root-approved WALK3 full-tail right/left projections."""
from pathlib import Path
import hashlib,json,os
from PIL import Image
PACK=Path(__file__).resolve().parents[2];V=PACK/"reusable/views-additional";RAW=V/"raw";OID="revamp--mongo--mongo--walk3"
SRC=PACK/"reusable/native"/f"{OID}.png"
EXPECTED_SOURCE="2a4a824ec81fcb6bf933a90bef182c685edbd5554337f871ad780025083befb9"
OLD={"right":"b2c83e8d0192013e0ebeb6cf86f2cf8ed8b5b9b9cd0b5ae238667323c4b4a192","left":"cc41393f191fddadd2b3f6de091787ccb8b27b4b6b3d7cac3e38a49bcb2e3826"}
CANDIDATE={"right":"034913aeb230c8c2f34bcced3d3766551b905d529d65e79f518a41bf13e6cfed","left":"7603dc50fa94106a5da65df88ee5f18398e961df6114d1d4d87a57c12ae2bff7"}
ATLAS_SHA="fddacdf8272c5906dcf02b1a738479abb36952d0dd84d18bcb391f25c5d16dc0"
def sha(b):return hashlib.sha256(b).hexdigest()
if sha(SRC.read_bytes())!=EXPECTED_SOURCE:raise SystemExit("canonical source changed")
idxp=V/"set-index.json";idx=json.loads(idxp.read_text());records={a["id"]:a for a in idx["assets"]};staged=[]
for view in ("right","left"):
    live=V/f"{OID}.{view}.png";old=live.read_bytes()
    if sha(old)!=OLD[view]:raise SystemExit(f"{view} live view changed")
    cand=RAW/f"ally-mongo-walk3-{view}-profile-candidate-20261026.png";candidate=cand.read_bytes()
    if sha(candidate)!=CANDIDATE[view]:raise SystemExit(f"{view} retained candidate changed")
    staged.append((view,live,old,candidate,cand))
for view,live,old,candidate,cand in staged:
    aid=f"{OID}.{view}";side=V/f"{aid}.json";meta=json.loads(side.read_text());im=Image.open(cand).convert("RGBA")
    tmp=live.with_suffix(".png.tmp");tmp.write_bytes(candidate);os.replace(tmp,live)
    meta["image"]["sha256"]=sha(candidate);meta["image"]["rgba_sha256"]=hashlib.sha256(im.width.to_bytes(4,"big")+im.height.to_bytes(4,"big")+im.tobytes()).hexdigest()
    bounds={"right":[245,166,685,400],"left":[1240,165,684,401]}[view]
    meta["provenance"].update({"source_image":f"reusable/native/{OID}.png","source_image_sha256":EXPECTED_SOURCE,"source_atlas":"reusable/views-additional/raw/ally-mongo-walk3-sides-v2.png","source_atlas_sha256":ATLAS_SHA,"generation_request_id":"exec-680782aa-eafc-413a-9e49-1fd0d2fe93b4","generation_prompt":"reusable/views-additional/raw/ally-mongo-walk3-sides-v2.prompt.txt","generation_recipe":"reusable/views-additional/rebuild_ally_mongo_walk3_tail_profiles.py","notes":"Inferred orthographic WALK3 profile; full tapered tail tip retained with exact leading-stride pose. Hidden surfaces are inferred, not recovered pixels.","crop_bounds_px":{"coordinate_format":"xywh","alpha_threshold":16,"alpha_bounds_global":bounds,"resized_bounds_px":list(im.getchannel("A").getbbox()),"canvas_offset_px":[11,60],"shared_anchor_px":[128,128],"uniform_scale":0.3425,"normalization":"uniform scale calibrated to existing elevation Z extents; full source tail recovered from unclipped retained atlas"}})
    side.write_text(json.dumps(meta,indent=2)+"\n");records[aid].clear();records[aid].update(meta)
    (RAW/f"{aid}.tail-profile-install-20261026.json").write_text(json.dumps({"asset_id":aid,"source_image":f"reusable/native/{OID}.png","source_image_sha256":EXPECTED_SOURCE,"old_png_sha256":sha(old),"candidate_png_sha256":sha(candidate),"atlas_sha256":ATLAS_SHA,"generation_request_id":"exec-680782aa-eafc-413a-9e49-1fd0d2fe93b4","crop_bounds_xywh":bounds,"uniform_scale":0.3425},indent=2)+"\n")
idx["assets"]=[records[a["id"]] for a in idx["assets"]];idxp.write_text(json.dumps(idx,indent=2)+"\n")
print(json.dumps({v:records[f"{OID}.{v}"]["image"]["sha256"] for v in ("right","left")},indent=2))
