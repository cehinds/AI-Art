#!/usr/bin/env python3
"""Stage four targeted projections for Mongo SE walk1/walk2; never modifies live assets."""
from pathlib import Path
from PIL import Image, ImageDraw
import hashlib,json,struct
HERE=Path(__file__).resolve().parent; RAW=HERE/'raw'; OUT=RAW/'mongo-se-walk12-v2-candidates'; OUT.mkdir(exist_ok=True)
ATLAS=RAW/'mongo-se-walk12-tucked-wing-v2-20261026.png'; REQUEST='exec-15003868-31c8-4a3d-8110-36ae4fbf32fe'
POSES=['directional--mongo--se--walk1','directional--mongo--se--walk2']; VIEWS=['front','top','bottom','rear']
def sha(b):return hashlib.sha256(b).hexdigest()
def rgba_hash(im):return sha(struct.pack('>II',*im.size)+im.convert('RGBA').tobytes())
atlas_bytes=ATLAS.read_bytes(); atlas=Image.open(ATLAS).convert('RGBA'); assert atlas.size==(1774,887),atlas.size
cellw,cellh=atlas.width/4,atlas.height/2
cuts=[]; old_z=[]; old_y=[]; new_z=[]; new_y=[]
for row,oid in enumerate(POSES):
 for col,v in enumerate(VIEWS):
  x0=round(col*cellw);x1=round((col+1)*cellw);y0=round(row*cellh);y1=round((row+1)*cellh)
  cell=atlas.crop((x0,y0,x1,y1)); alpha=cell.getchannel('A').point(lambda a:255 if a>=16 else 0); box=alpha.getbbox()
  if not box:raise RuntimeError(f'empty {oid} {v}')
  if box[0]<=3 or box[1]<=3 or box[2]>=cell.width-3 or box[3]>=cell.height-3:raise RuntimeError(f'cell edge risk {oid} {v} {box} {cell.size}')
  crop=cell.crop(box); cuts.append((row,oid,v,(x0,y0,x1-x0,y1-y0),box,crop))
  if v=='front':new_z.append(crop.height)
  if v=='top':new_y.append(crop.height)
  if v=='front':
   old=Image.open(HERE/f'{oid}.{v}.png').convert('RGBA').getchannel('A').getbbox();old_z.append(old[3]-old[1])
  if v=='top':
   old=Image.open(HERE/f'{oid}.{v}.png').convert('RGBA').getchannel('A').getbbox();old_y.append(old[3]-old[1])
# A shared isotropic scale compromises between known front Z and plan Y extents.
scale=(sum(old_z)+sum(old_y))/(sum(new_z)+sum(new_y))
records=[]
for row,oid,v,cellbox,box,crop in cuts:
 size=(round(crop.width*scale),round(crop.height*scale)); resized=crop.resize(size,Image.Resampling.LANCZOS)
 canvas=Image.new('RGBA',(256,256),(0,0,0,0)); off=(128-size[0]//2,128-size[1]//2); canvas.alpha_composite(resized,off)
 path=OUT/f'{oid}.{v}.candidate.png';canvas.save(path,format='PNG',optimize=False)
 records.append({'object_id':oid,'view':v,'row':row,'candidate_path':str(path.relative_to(HERE)),'png_sha256':sha(path.read_bytes()),'rgba_sha256':rgba_hash(canvas),'cell_bounds_xywh':list(cellbox),'alpha_bbox_local_xyxy':list(box),'normalized_alpha_bbox_xyxy':list(canvas.getchannel('A').getbbox()),'resized_wh':list(size),'canvas_offset_xy':list(off),'uniform_scale':scale})
contact=Image.new('RGBA',(7*220,2*270),(48,48,52,255)); d=ImageDraw.Draw(contact)
for row,oid in enumerate(POSES):
 src=Image.open(HERE.parents[0]/'native'/f'{oid}.png').convert('RGBA');src.thumbnail((190,220),Image.Resampling.NEAREST)
 contact.alpha_composite(src,(15+(190-src.width)//2,row*270+34+(220-src.height)//2));d.text((5,row*270+8),f'{oid} SOURCE',fill='white')
 for i,v in enumerate(['front','top','right','left','bottom','rear']):
  rec=next((r for r in records if r['object_id']==oid and r['view']==v),None)
  path=HERE/rec['candidate_path'] if rec else HERE/f'{oid}.{v}.png'
  im=Image.open(path).convert('RGBA'); im.thumbnail((190,220),Image.Resampling.NEAREST)
  contact.alpha_composite(im,((i+1)*220+15+(190-im.width)//2,row*270+34+(220-im.height)//2));d.text(((i+1)*220+5,row*270+8),v.upper(),fill='white')
contact_path=OUT/'mongo-se-walk12-source-six-candidates.png';contact.save(contact_path,format='PNG',optimize=False)
report={'source_atlas':f'reusable/views-additional/raw/{ATLAS.name}','source_atlas_sha256':sha(atlas_bytes),'generation_request_id':REQUEST,'generation_output':f'/workspace/generated_images/{REQUEST}.png','generation_output_sha256':sha(atlas_bytes),'generation_prompt':'reusable/views-additional/raw/mongo-se-walk12-tucked-wing-v2-20261026.prompt.txt','cell_coordinate_format':'xywh','atlas_wh':list(atlas.size),'cell_wh_fractional':[cellw,cellh],'alpha_threshold':16,'scale_calibration':'single shared isotropic scale averaged from existing accepted front Z and top Y extents across the two walking poses','old_front_z_px':old_z,'old_top_y_px':old_y,'candidate_front_z_px':new_z,'candidate_top_y_px':new_y,'uniform_scale':scale,'anchor_px':[128,128],'candidates':records,'contact':str(contact_path),'contact_sha256':sha(contact_path.read_bytes())}
(OUT/'mongo-se-walk12-v2-stage-report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'uniform_scale':scale,'old_front_z':old_z,'old_top_y':old_y,'candidate_front_z':new_z,'candidate_top_y':new_y,'contact':str(contact_path),'contact_sha256':report['contact_sha256'],'candidate_bboxes':[{r['object_id']+'.'+r['view']:r['normalized_alpha_bbox_xyxy']} for r in records]},indent=2))
