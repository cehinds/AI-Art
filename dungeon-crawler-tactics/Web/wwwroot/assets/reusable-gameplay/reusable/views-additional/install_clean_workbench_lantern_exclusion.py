#!/usr/bin/env python3
"""Install five targeted lantern-removal projections; preserve accepted BOTTOM."""
import hashlib,json,struct,os
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

PACK=Path(__file__).resolve().parents[2];VIEWS=PACK/"reusable/views-additional";RAW=VIEWS/"raw"
OID="concepts-progression-safe-room-crafting-workbench"
CANDIDATES={
 "front":("exec-c6361c79-dbc5-45a0-b4e7-d97cc02aa2f2",
  "Make a localized object-removal edit to this exact front elevation pixel-art workbench. Preserve the complete workbench silhouette, legs, drawers, cabinet, tools, bottles, books and tabletop at precisely the same size and placement. Remove only the separate glowing gold wall lantern at far right above the bench; it is a separate wall fixture, not attached to or part of the workbench. Fill any resulting tabletop gap with continuation of the wood surface. Do not add walls, glow, lamp, or new props. Keep current front orthographic camera and exact canvas/scale; transparent background. No redesign or perspective changes."),
 "top":("exec-7879d73e-6b73-4258-b314-35a039de00f7",
  "Using the lantern-free overhead tabletop image as the sole layout guide, make a strict straight-down TOP orthographic projection of only the workbench's tabletop. Keep the same rectangular plank top and every tool at the same relative positions. Remove the drawer, cabinet, blue storage chest and legs under the tabletop entirely: outside the tabletop rectangle must be fully transparent. Replace the upright bottles with only their cap and small shoulder-ring overhead footprints, centered where each bottle stands; no long bottle side bodies. The wall lantern is separate and must remain absent. Keep the hammer, blue book, metal plate, dark square tool and wood planks unchanged. No perspective, no side faces, no under-table projection, no new objects."),
 "right":("exec-2c19cb40-cf59-44b9-8b82-b866c92f0757",
  "Edit this exact pixel-art RIGHT-SIDE workbench projection. Keep workbench, side panel, storage chest, tools and bottles at their existing positions and same silhouette/scale. Remove only the glowing gold wall-mounted lantern standing behind/on the far end; it is a separate wall fixture, not part of the workbench. Continue the wood tabletop edge or transparent background as appropriate; no lantern, wall, mount, or glow. Preserve strict right-side camera, transparent canvas, no redraw or added items."),
 "left":("exec-74fd7385-661e-477a-b7e3-895c415e1403",
  "Edit this exact pixel-art LEFT-SIDE workbench projection. Keep workbench, side panel, storage chest, tools and bottles at their existing positions and same silhouette/scale. Remove only the glowing gold wall-mounted lantern standing behind/on the far end; it is a separate wall fixture, not part of the workbench. Continue the wood tabletop edge or transparent background as appropriate; no lantern, wall, mount, or glow. Preserve strict left-side camera, transparent canvas, no redraw or added items."),
 "rear":("exec-7b3c6d7d-6f71-4242-90c9-d19124e4afc1",
  "Localized object-removal edit only. Keep this exact pixel-art REAR elevation of the workbench: preserve table width/height, plank border, drawers, metal cabinet, legs, tools and bottles exactly in place. Remove only the glowing gold wall-mounted lantern at the far left; it is a separate fixture outside the workbench. Do not replace it with any other item. Restore the plain wood worktop behind it, no wall or glow. Transparent background. Same camera, proportions and crop, no redesign or perspective.")
}
def sha(b):return hashlib.sha256(b).hexdigest()
idxp=VIEWS/"set-index.json";idx=json.loads(idxp.read_text());assets={a["id"]:a for a in idx["assets"]}
staged={}
for view,(gen,prompt) in CANDIDATES.items():
 src=Path("/workspace/generated_images")/f"{gen}.png";atlas=RAW/f"{gen}.png"
 if not atlas.exists():atlas.write_bytes(src.read_bytes())
 pp=RAW/f"{gen}.prompt.txt";pp.write_text(prompt+"\n")
 atlas_bytes=atlas.read_bytes();im=Image.open(atlas).convert("RGBA");a=np.asarray(im)[:,:,3]
 labels,n=ndimage.label(a>=16)
 if not n:raise SystemExit(f"No alpha component for {gen}")
 sizes=np.bincount(labels.ravel());label=int(np.argmax(sizes[1:])+1);ys,xs=np.where(labels==label)
 box=(int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1));crop=im.crop(box)
 aid=f"{OID}.{view}";mp=VIEWS/f"{aid}.json";ip=VIEWS/f"{aid}.png";meta=json.loads(mp.read_text())
 old=ip.read_bytes();tgt=Image.open(ip).convert("RGBA");tb=tgt.getchannel("A").getbbox();tw,th=tb[2]-tb[0],tb[3]-tb[1]
 scale=min(tw/crop.width,th/crop.height);nw,nh=round(crop.width*scale),round(crop.height*scale)
 crop=crop.resize((nw,nh),Image.Resampling.LANCZOS);canvas=Image.new("RGBA",(256,256),(0,0,0,0));anchor=(128,128);canvas.alpha_composite(crop,(anchor[0]-nw//2,anchor[1]-nh//2))
 (RAW/f"{gen}.previous-{view}.png").write_bytes(old)
 meta["image"]["rgba_sha256"]=sha(struct.pack(">II",256,256)+canvas.tobytes())
 meta["provenance"].update({
  "source_atlas":f"reusable/views-additional/raw/{gen}.png","source_atlas_sha256":sha(atlas_bytes),
  "generation_recipe":f"reusable/views-additional/raw/{gen}.prompt.txt",
  "notes":"inferred orthographic projection, not recovered pixels; separate wall-mounted gold lantern explicitly excluded from this clean workbench proxy; bench/tools and unseen surfaces remain inferred from source context",
  "crop_bounds_px":{"alpha_threshold":16,"alpha_bounds_global":list(box),"component_labels":[label],
   "resized_bounds_px":[nw,nh],"canvas_offset_px":[anchor[0]-nw//2,anchor[1]-nh//2],
   "shared_scale":scale,"normalization":"uniform scale to fit prior approved view bounds, no anisotropic stretch; centered on shared anchor"}})
 staged[aid]=(ip,canvas,meta,old,box,scale)
for aid,(ip,canvas,meta,old,box,scale) in staged.items():
 tmp=ip.with_suffix(".png.tmp");canvas.save(tmp,format="PNG",optimize=False);os.replace(tmp,ip)
 pb=ip.read_bytes();meta["image"]["sha256"]=sha(pb);(VIEWS/f"{aid}.json").write_text(json.dumps(meta,indent=2)+"\n")
 assets[aid].clear();assets[aid].update(meta)
 (RAW/f"{aid}.install.json").write_text(json.dumps({"asset_id":aid,"old_png_sha256":sha(old),"new_png_sha256":sha(pb),
  "source_image":meta["provenance"]["source_image"],"source_sha256":sha((PACK/meta["provenance"]["source_image"]).read_bytes()),
  "atlas":meta["provenance"]["source_atlas"],"atlas_sha256":meta["provenance"]["source_atlas_sha256"],
  "alpha_bounds_xyxy":list(box),"target_bbox":list(Image.open(ip).convert("RGBA").getchannel("A").getbbox()),
  "uniform_scale":scale,"context_exclusion":"wall-mounted lantern is separate canonical object"},indent=2)+"\n")
idx["assets"]=[assets[a["id"]] for a in idx["assets"]];idxp.write_text(json.dumps(idx,indent=2)+"\n")
(RAW/"workbench-lantern-exclusion-install.json").write_text(json.dumps({"object_id":OID,"changed_views":list(CANDIDATES),"preserved_view":"bottom","preserved_source":"reusable/native/concepts-progression-safe-room-crafting-workbench.png","excluded_fixture":"concepts-progression-safe-room-crafting-wall-lantern","installed_hashes":{a:assets[a]["image"]["sha256"] for a in [f"{OID}.{v}" for v in CANDIDATES]}},indent=2)+"\n")
print(json.dumps({a:{"sha256":assets[a]["image"]["sha256"],"bbox":list(staged[a][1].getchannel("A").getbbox())} for a in staged},indent=2))
