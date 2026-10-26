#!/usr/bin/env python3
"""Install corrected rat plan projections, retaining each pose's own source."""
from __future__ import annotations
import hashlib, json, os, struct
from pathlib import Path
from PIL import Image

PACK = Path(__file__).resolve().parents[2]
VIEWS = PACK / "reusable/views-additional"
RAW = VIEWS / "raw"
OBJECTS = ["revamp--enemies--rat", "revamp--enemies--rat--walk", "revamp--enemies--rat--hit"]
ATLASES = {
    "top": "rat-three-top-v1-20261026.png",
    "bottom": "rat-three-bottom-v2-20261026.png",
}

def sha(b): return hashlib.sha256(b).hexdigest()
def rgba_hash(im): return sha(struct.pack(">II", *im.size) + im.convert("RGBA").tobytes())

idx_path = VIEWS / "set-index.json"
index = json.loads(idx_path.read_text())
records = {a["id"]: a for a in index["assets"]}
staged = []
for view, atlas_name in ATLASES.items():
    atlas_path = RAW / atlas_name
    atlas_bytes = atlas_path.read_bytes()
    atlas = Image.open(atlas_path).convert("RGBA")
    cw = atlas.width / 3
    for i, oid in enumerate(OBJECTS):
        aid = f"{oid}.{view}"
        output = VIEWS / f"{aid}.png"
        sidecar = VIEWS / f"{aid}.json"
        meta = json.loads(sidecar.read_text())
        source = PACK / "reusable/native" / f"{oid}.png"
        if meta["provenance"]["source_image"] != f"reusable/native/{oid}.png":
            raise ValueError(f"{aid}: refusing noncanonical source")
        x0, x1 = round(i*cw), round((i+1)*cw)
        cell = atlas.crop((x0, 0, x1, atlas.height))
        bounds = cell.getchannel("A").point(lambda x: 255 if x >= 16 else 0).getbbox()
        if not bounds: raise ValueError(f"empty cell {i} in {atlas_name}")
        crop = cell.crop(bounds)
        fimg = Image.open(VIEWS / f"{oid}.front.png").convert("RGBA")
        fbox = fimg.getchannel("A").getbbox()
        side_boxes = [Image.open(VIEWS / f"{oid}.{v}.png").convert("RGBA").getchannel("A").getbbox() for v in ("right", "left")]
        target_x = fbox[2]-fbox[0]
        target_y = sum(b[2]-b[0] for b in side_boxes)/2
        scale = min(target_x/crop.width, target_y/crop.height)
        nw, nh = max(1,round(crop.width*scale)), max(1,round(crop.height*scale))
        resized = crop.resize((nw,nh),Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA",(256,256),(0,0,0,0)); offset=(128-nw//2,128-nh//2);canvas.alpha_composite(resized,offset)
        staged.append((aid, output, sidecar, meta, canvas, atlas_name, sha(atlas_bytes), i, x0, x1-x0, atlas.height, bounds, (nw,nh), offset, scale, source, sha(source.read_bytes())))

# All six candidate images and source guards are ready before installation.
for aid, output, sidecar, meta, canvas, atlas_name, atlas_sha, i, x0, cw, ch, bounds, resized, offset, scale, source, source_sha in staged:
    old = output.read_bytes()
    tmp = output.with_suffix(".png.tmp"); canvas.save(tmp,format="PNG",optimize=False);os.replace(tmp,output)
    new=output.read_bytes(); meta["image"]["sha256"]=sha(new);meta["image"]["rgba_sha256"]=rgba_hash(canvas)
    meta["provenance"].update({
        "source_image": f"reusable/native/{source.stem}.png",
        "source_image_sha256": source_sha,
        "source_atlas": f"reusable/views-additional/raw/{atlas_name}",
        "source_atlas_sha256": atlas_sha,
        "generation_recipe": "reusable/views-additional/install_rat_plan_tail_repairs_20261026.py",
        "notes": "Inferred orthographic plan projection from the exact native pose. Preserves the source's distinctive lateral tail curl and individual limb/rearing pose; hidden ventral surfaces are inferred, not recovered pixels.",
        "crop_bounds_px": {
            "coordinate_format": "xywh",
            "nominal_cell": {"bounds": [x0,0,cw,ch]},
            "alpha_threshold": 16,
            "alpha_bounds_global": [x0+bounds[0],bounds[1],bounds[2]-bounds[0],bounds[3]-bounds[1]],
            "resized_bounds_px": list(resized),
            "canvas_offset_px": list(offset),
            "shared_anchor_px": [128,128],
            "uniform_scale": scale,
            "normalization": "isotropic scale matching accepted front-view X width and mean right/left side-profile Y length, centered at shared anchor",
        }
    })
    sidecar.write_text(json.dumps(meta,indent=2)+"\n");records[aid].clear();records[aid].update(meta)
    (RAW/f"{aid}.plan-repair-20261026.json").write_text(json.dumps({"asset_id":aid,"source_image":meta["provenance"]["source_image"],"source_image_sha256":source_sha,"source_atlas":atlas_name,"source_atlas_sha256":atlas_sha,"cell_index":i,"crop_bounds_xywh":[x0+bounds[0],bounds[1],bounds[2]-bounds[0],bounds[3]-bounds[1]],"output_bbox_xywh":list(canvas.getchannel("A").getbbox()),"uniform_scale":scale,"old_png_sha256":sha(old),"new_png_sha256":sha(new)},indent=2)+"\n")
index["assets"]=[records[a["id"]] for a in index["assets"]];idx_path.write_text(json.dumps(index,indent=2)+"\n")
print(json.dumps({x[0]:{"bbox":list(x[4].getchannel("A").getbbox()),"scale":x[14]} for x in staged},indent=2))
