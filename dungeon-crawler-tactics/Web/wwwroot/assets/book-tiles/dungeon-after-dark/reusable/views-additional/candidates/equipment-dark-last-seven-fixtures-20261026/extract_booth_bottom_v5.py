from PIL import Image,ImageDraw
import numpy as np,json,hashlib
from pathlib import Path
B=Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/dungeon-after-dark/reusable/views-additional/candidates/equipment-dark-last-seven-fixtures-20261026')
src=B/'images/safe-services-restaurant-dining-booth.bottom.png'; im=Image.open(src).convert('RGBA')
# Move the existing generated circular pedestal foot axially into the camera projection, removing the visible vertical Z-shaft.
# Preserve the original two long-Y seat-base footprints and central tabletop underside; only mask/reposition the circular end.
box=(109,142,147,179); disk=im.crop(box)
mask=Image.new('L',disk.size,0);d=ImageDraw.Draw(mask);d.ellipse((0,0,disk.width-1,disk.height-1),fill=255)
disk.putalpha(Image.composite(disk.getchannel('A'),Image.new('L',disk.size,0),mask))
canvas=im.copy();draw=ImageDraw.Draw(canvas);draw.rectangle((109,125,147,179),fill=(0,0,0,0))
# Keep original platform underside; paste foot circle immediately below its central rim, centered on same XY.
# alpha_composite preserves antialiased pixels from generated source.
canvas.alpha_composite(disk,(109,126))
out=B/'images/safe-services-restaurant-dining-booth.bottom.focused-v5.png';canvas.save(out)
rec={'object_id':'safe-services-restaurant-dining-booth','view':'bottom','method':'deterministic mask and rigid translate of generated central round pedestal end; all other source pixels preserved','input_path':str(src),'input_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'mask_region_xyxy':[109,125,147,179],'disk_source_crop_xyxy':list(box),'disk_shape':'circular alpha mask; generated pixels retained','disk_destination_xy':[109,126],'output_path':str(out),'output_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'canvas':[256,256],'anchor_px':[128,128]}
(B/'booth-bottom-v5-recipe.json').write_text(json.dumps(rec,indent=2)+'\n');print(json.dumps(rec,indent=2))
