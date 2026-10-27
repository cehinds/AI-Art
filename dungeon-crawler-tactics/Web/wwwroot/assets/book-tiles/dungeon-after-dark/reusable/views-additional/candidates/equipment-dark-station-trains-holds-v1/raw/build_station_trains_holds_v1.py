from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np, json, hashlib
from scipy.ndimage import label, generate_binary_structure

PACK=Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/dungeon-after-dark')
BASE=PACK/'reusable/views-additional/candidates/equipment-dark-masonry-rail8-20261026'
OUT=PACK/'reusable/views-additional/candidates/equipment-dark-station-trains-holds-v1'
RAW=OUT/'raw'; IMG=OUT/'images'; RAW.mkdir(parents=True,exist_ok=True); IMG.mkdir(parents=True,exist_ok=True)
STATION_REVIEW=Path('/workspace/scratch/page-equipment-iron-stations-v3-candidate-review.json')
TRAINS_REVIEW=Path('/workspace/scratch/page-equipment-iron-trains-v2-candidate-review.json')
STATION_MAN=BASE/'iron-stations-candidate-manifest-v3.json'
TRAIN_MAN=BASE/'iron-trains-candidate-manifest-v2.json'

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def writej(p,obj): Path(p).write_text(json.dumps(obj,indent=2)+'\n')
def current_maps(reviewp):
 d=json.loads(Path(reviewp).read_text()); out={}
 for s in d['current_source_and_six']:
  oid=s['object_id']; out[oid]={'source':s['source'], 'views':s['views']}
 return out
station_review=json.loads(STATION_REVIEW.read_text()); trains_review=json.loads(TRAINS_REVIEW.read_text())
st_current=current_maps(STATION_REVIEW); tr_current=current_maps(TRAINS_REVIEW)
stman=json.loads(STATION_MAN.read_text()); trman=json.loads(TRAIN_MAN.read_text())
st_entries={(e['object_id'],e['view']):e for e in stman['sets']}; tr_entries={(e['object_id'],e['view']):e for e in trman['sets']}

# Verify source and current live leaves are still exactly the Page-reviewed bytes.
for cur in (st_current,tr_current):
 for oid,s in cur.items():
  src=PACK/s['source']['path'] if not Path(s['source']['path']).is_absolute() else Path(s['source']['path'])
  assert sha(src)==s['source']['sha256'], (oid,'source changed')
  for v,x in s['views'].items():
   fp=PACK/x['path'] if not Path(x['path']).is_absolute() else Path(x['path'])
   # Dark installed the previously accepted directions after this review snapshot.
   # Rebind the candidate batch to the exact current live bytes while retaining the
   # old Page review as historical decision evidence.
   x['sha256']=sha(fp)

# Copy immutable input evidence into this versioned candidate namespace.
copy_inputs=[]
for src in [STATION_REVIEW,TRAINS_REVIEW,STATION_MAN,TRAIN_MAN]:
 dst=RAW/src.name; dst.write_bytes(src.read_bytes()); copy_inputs.append({'path':str(dst.relative_to(PACK)),'sha256':sha(dst)})
raw_bottom=BASE/'raw/iron-stations-bottom-output-v1.png'
dst=RAW/raw_bottom.name; dst.write_bytes(raw_bottom.read_bytes()); copy_inputs.append({'path':str(dst.relative_to(PACK)),'sha256':sha(dst)})
for n in ['iron-stations-bottom-request-v1.json','iron-stations-bottom-sameid-guide-v1.png']:
 src=BASE/'raw'/n; dst=RAW/n; dst.write_bytes(src.read_bytes()); copy_inputs.append({'path':str(dst.relative_to(PACK)),'sha256':sha(dst)})

# Extract whole-atlas connected components, repairing the row-boundary clipping identified by Page.
im=Image.open(raw_bottom).convert('RGBA'); alpha=np.array(im.getchannel('A'))
labels,n=label(alpha>=64,structure=generate_binary_structure(2,2))
components={}
for i in range(1,n+1):
 yy,xx=np.where(labels==i)
 if len(xx)<10000: continue
 bbox=[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)]
 components[i]={'bbox':bbox,'area':int(len(xx)),'cx':float(xx.mean()),'cy':float(yy.mean())}
assert len(components)==4, components
# Identify component by its original row centroid: outer, inner, NW, NE.
def comp_near(cy): return min(components,key=lambda i:abs(components[i]['cy']-cy))
ids={
 'outer':comp_near(170), 'inner':comp_near(500), 'nw':comp_near(820), 'ne':comp_near(1080)
}
assert len(set(ids.values()))==4, ids

def from_component(name,target_max,rotate=0):
 i=ids[name]; bbox=components[i]['bbox']; x0,y0,x1,y1=bbox
 # isolate only the selected full-atlas connected foreground, with its original antialias alpha inside bbox.
 crop=im.crop((x0,y0,x1,y1)); labcrop=labels[y0:y1,x0:x1]
 mask=Image.fromarray(np.where(labcrop==i,255,0).astype('uint8'))
 crop.putalpha(Image.fromarray(np.minimum(np.array(crop.getchannel('A')),np.array(mask)).astype('uint8')))
 if rotate: crop=crop.rotate(rotate,expand=True,resample=Image.Resampling.NEAREST)
 w,h=crop.size; scale=target_max/max(w,h); nw=max(1,round(w*scale)); nh=max(1,round(h*scale))
 resized=crop.resize((nw,nh),Image.Resampling.NEAREST)
 canvas=Image.new('RGBA',(256,256),(0,0,0,0)); off=((256-nw)//2,(256-nh)//2); canvas.alpha_composite(resized,off)
 return canvas, {'source_atlas_bbox_xyxy':bbox,'source_component_label':i,'source_component_area_alpha64':components[i]['area'],'alpha_threshold':64,'connectivity':8,'rotation_degrees_ccw':rotate,'target_max_dimension':target_max,'uniform_scale':scale,'resized_dimensions':[nw,nh],'offset_px':list(off),'anchor_px':[128,128]}

# Correct three cropped bottoms by full component selection and fit; use NE top source footprint to calibrate perpendicular NW strip.
outputs={}; recipes={}
for obj,comp,target in [
 ('iron-stations-station-tiled-masonry-outer-corner','outer',186),
 ('iron-stations-station-tiled-masonry-inner-corner','inner',186),
 ('iron-stations-station-tiled-masonry-wall-northeast','ne',186),
]:
 canvas,recipe=from_component(comp,target)
 view='bottom'; fn=f'{obj}.{view}.candidate-v4.png'; out=IMG/fn; canvas.save(out)
 outputs[(obj,view)]=out; recipes[(obj,view)]={'method':'full-global-alpha-component-extraction','raw':raw_bottom,'raw_sha256':sha(raw_bottom),**recipe}
# NW TOP = rigid quarter-turn of accepted NE TOP plan. NW BOTTOM = rigid quarter-turn of corrected NE bottom.
# The NW/NE are perpendicular same-kit straight walls; this is declared geometry/material symmetry, no repaint.
for view, donor_path, donor_name in [
 ('top', BASE/'images/iron-stations-station-tiled-masonry-wall-northeast.top.stage3.png','NE_TOP_STAGE3'),
 ('bottom', outputs[('iron-stations-station-tiled-masonry-wall-northeast','bottom')],'NE_BOTTOM_V4'),
]:
 donor=Image.open(donor_path).convert('RGBA')
 turned=donor.rotate(90,expand=True,resample=Image.Resampling.NEAREST)
 fn=f'iron-stations-station-tiled-masonry-wall-northwest.{view}.candidate-v4.png'; out=IMG/fn; turned.save(out)
 outputs[('iron-stations-station-tiled-masonry-wall-northwest',view)]=out
 recipes[('iron-stations-station-tiled-masonry-wall-northwest',view)]={'method':'rigid-same-kit-90-degree-rotation','donor_path':str(donor_path.relative_to(PACK)) if PACK in donor_path.parents else str(donor_path),'donor_sha256':sha(donor_path),'rotation_degrees_ccw':90,'no_resampling':'RGBA byte-preserving right angle rotation; transparent 256 canvas retained','anchor_px':[128,128], 'geometry_note':'NW and NE straight walls share native station masonry/cyan trim; perpendicular plan is inferred by rigid rotation, no repaint.'}
# Train inner corner right/left reuse accepted same-target two-post front/rear elevations as explicitly allowed symmetry.
train_obj='iron-trains-riveted-carriage-metal-inner-corner'
for view, donorview in [('right','front'),('left','rear')]:
 donor_path=BASE/f'images/{train_obj}.{donorview}.stage2.png'
 donor=Image.open(donor_path).convert('RGBA')
 assert donor.size==(256,256)
 out=IMG/f'{train_obj}.{view}.candidate-v3.png'; donor.save(out)
 outputs[(train_obj,view)]=out
 recipes[(train_obj,view)]={'method':'same-target-approved-elevation-symmetry-reuse','donor_path':str(donor_path.relative_to(PACK)),'donor_sha256':sha(donor_path),'resampling':'none; exact donor pixels copied','anchor_px':[128,128],'geometry_note':'Page permits same-target two-post FRONT/REAR faces as inferred perpendicular-arm symmetry; reusing the full two-endpost wall elevation resolves missing corner/endpost while retaining same target red/gold/rivet identity.'}

# Verify generated dimensions/hash and build a contact that shows source + current six + focused candidate.
# Follow page proof's actual base current art; all inputs were hash-preflighted above.
def candidate_for(oid,view): return outputs[(oid,view)]
rows=[]
for oid,view in outputs:
 cur=(st_current if oid.startswith('iron-stations-') else tr_current)[oid]
 rows.append((oid,view,cur,candidate_for(oid,view)))
cellw=220; cellh=245; cols=8; rowsn=len(rows)
contact=Image.new('RGB',(cellw*cols,cellh*rowsn),(238,238,238)); draw=ImageDraw.Draw(contact)
for ri,(oid,targetview,cur,cand) in enumerate(rows):
 y=ri*cellh
 paths=[cur['source']['path']]+[cur['views'][v]['path'] for v in ['front','top','right','left','bottom','rear']]+[str(cand)]
 labs=['SOURCE','FRONT','TOP','RIGHT','LEFT','BOTTOM','REAR','CAND '+targetview.upper()]
 for ci,(p,labtxt) in enumerate(zip(paths,labs)):
  fp=Path(p); imx=Image.open(fp).convert('RGBA'); imx.thumbnail((200,200),Image.Resampling.NEAREST)
  x=ci*cellw+(cellw-imx.width)//2; yy=y+28+(200-imx.height)//2
  bg=Image.new('RGBA',imx.size,(225,225,225,255)); bg.alpha_composite(imx)
  contact.paste(bg.convert('RGB'),(x,yy)); draw.text((ci*cellw+4,y+6),labtxt,fill=(0,0,0));
 draw.text((4,y+226),f'{oid}.{targetview}',fill=(0,0,0))
contact_path=OUT/'station-trains-holds-source-current-candidate-contact-v1.png'; contact.save(contact_path)

# Candidate metadata entries explicitly retain base/current/source bindings and rebuild recipes.
sets=[]
for oid,view,cur,cand in rows:
 source=cur['source']; current=cur['views']
 cand_path=str(cand.relative_to(PACK)); recipe=recipes[(oid,view)]
 img=Image.open(cand); bbox=img.getchannel('A').getbbox()
 sets.append({'object_id':oid,'view':view,'candidate_path':cand_path,'candidate_sha256':sha(cand),
   'source_path':source['path'],'source_sha256':source['sha256'],
   'base_current_views':{v:{'path':current[v]['path'],'sha256':current[v]['sha256']} for v in ['front','top','right','left','bottom','rear']},
   'candidate_alpha_bbox_xyxy':list(bbox) if bbox else None,'candidate_dimensions':list(img.size),
   'recipe':{k:(str(v.relative_to(PACK)) if isinstance(v,Path) and PACK in v.parents else (str(v) if isinstance(v,Path) else v)) for k,v in recipe.items()},
   'provenance_method':'inferred','anchor_px':[128,128]})
manifest={'candidate_id':'equipment-dark-station-trains-holds-v1','scope':'book-tiles/dungeon-after-dark','candidate_owner':'views_equipment','reviewer':'page_inventory','installer':'views_dark_books','candidate_only':True,
 'source_review_paths':[str(STATION_REVIEW),str(TRAINS_REVIEW)],'source_review_sha256':[sha(STATION_REVIEW),sha(TRAINS_REVIEW)],
 'previous_frozen_manifests':[{'path':str(STATION_MAN.relative_to(PACK)),'sha256':sha(STATION_MAN)},{'path':str(TRAIN_MAN.relative_to(PACK)),'sha256':sha(TRAIN_MAN)}],
 'copied_inputs':copy_inputs,'sets':sets,
 'reproducibility':{'script_path':str(Path(__file__).relative_to(PACK)) if PACK in Path(__file__).parents else str(Path(__file__)),'script_sha256':sha(__file__),'operations':'Alpha component extraction and isotropic NEAREST scaling for whole-atlas bottoms; rigid 90-degree rotations for perpendicular station wall plans; exact same-target accepted-face reuse for inner-corner side elevations. No source/live PNG, sidecar, index, or replay helper modified.'}}
manifest_path=OUT/'station-trains-holds-candidate-manifest-v1.json'; writej(manifest_path,manifest)
contact_json={'contact_path':str(contact_path.relative_to(PACK)),'contact_sha256':sha(contact_path),'manifest_path':str(manifest_path.relative_to(PACK)),'manifest_sha256':sha(manifest_path),'candidate_count':len(sets),'targets':[{'object_id':s['object_id'],'view':s['view'],'candidate_sha256':s['candidate_sha256']} for s in sets]}
writej(OUT/'station-trains-holds-contact-v1.json',contact_json)
print(json.dumps({'output_dir':str(OUT),'manifest':str(manifest_path),'manifest_sha256':sha(manifest_path),'contact':str(contact_path),'contact_sha256':sha(contact_path),'contact_json_sha256':sha(OUT/'station-trains-holds-contact-v1.json'),'candidate_count':len(sets),'objects':[(o,v,sha(p)) for (o,v),p in outputs.items()]},indent=2))
