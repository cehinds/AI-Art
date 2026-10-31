"""Rebuild only reviewed-candidate Donut attack/hit plan projections."""
from pathlib import Path
import hashlib,json,struct
import numpy as np
from PIL import Image
from scipy import ndimage
PACK=Path(__file__).resolve().parents[3]
OUT=PACK/'reusable/views-additional'
ATLAS_REL='reusable/views-additional/raw/donut-attack-hit-plan-corrections.png'
ATLAS=PACK/ATLAS_REL
img=Image.open(ATLAS).convert('RGBA'); arr=np.asarray(img); labels,n=ndimage.label(arr[:,:,3]>=245,np.ones((3,3),dtype=np.uint8))
# Main connected object in each cell; hit TOP from row2/column1 was inspected and rejected, so it is retained raw only.
cells=[('revamp--characters--donut--attack','top',2,0.3661710037174721),('revamp--characters--donut--attack','bottom',3,0.3661710037174721),('revamp--characters--donut--hit','bottom',46,140/450)]
recipe_rel='reusable/views-additional/raw/donut-attack-hit-plan-corrections.recipe.json'; raw_hash=hashlib.sha256(ATLAS.read_bytes()).hexdigest()
recipe={'request_id':'exec-a5b8ebb6-f882-432a-b377-a78a36a840ce','source_atlas':ATLAS_REL,'source_atlas_sha256':raw_hash,'layout':'two rows (attack, hit), two columns (top, bottom)','cells':{'attack.top':{'component_label':2,'scale':0.3661710037174721,'target_height_px':197},'attack.bottom':{'component_label':3,'scale':0.3661710037174721,'target_height_px':197},'hit.bottom':{'component_label':46,'scale':140/450,'target_height_px':140},'hit.top':{'component_label':52,'installed':False,'reason':'self-inspection found a 3/4 face/body elevation rather than overhead view'}}}
(PACK/recipe_rel).write_text(json.dumps(recipe,indent=2)+'\n')
idxp=OUT/'set-index.json'; idx=json.loads(idxp.read_text()); amap={a['id']:a for a in idx['assets']}
for oid,view,lab,scale in cells:
 aid=f'{oid}.{view}'; meta=amap[aid]
 yy,xx=np.where(labels==lab); bounds=[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)]
 crop=img.crop(bounds); mask=labels[bounds[1]:bounds[3],bounds[0]:bounds[2]]==lab; crop.putalpha(Image.fromarray((mask*255).astype('uint8')))
 w=round(crop.width*scale); h=round(crop.height*scale); crop=crop.resize((w,h),Image.Resampling.NEAREST); offset=(128-w//2,128-h//2); frame=Image.new('RGBA',(256,256)); frame.alpha_composite(crop,offset)
 dest=PACK/meta['image']['path']; backup=OUT/'raw/callback-inputs'/f'{aid}.before-plan-correction.png'; backup.parent.mkdir(parents=True,exist_ok=True); backup.write_bytes(dest.read_bytes()); frame.save(dest,optimize=True); enc=dest.read_bytes(); meta['image']['sha256']=hashlib.sha256(enc).hexdigest(); meta['image']['rgba_sha256']=hashlib.sha256(struct.pack('>II',256,256)+frame.tobytes()).hexdigest()
 meta['provenance'].update({'source_atlas':ATLAS_REL,'source_atlas_sha256':raw_hash,'generation_recipe':recipe_rel,'crop_bounds_px':{'alpha_bounds_global':bounds,'component_labels':[lab],'resized_bounds_px':[w,h],'canvas_offset_px':list(offset),'shared_scale':scale,'alpha_threshold':245,'row':0 if 'attack' in oid else 1,'column':0 if view=='top' else 1}})
 meta['provenance']['notes']='Inferred orthographic pose-specific projection. Attack reaching-paw phase retained in plan; underside shows belly and paw pads, with dorsal surfaces occluded. Hidden surfaces are illustrative, not recovered.'
 Path(PACK/meta['metadata_path']).write_text(json.dumps(meta,indent=2)+'\n');amap[aid]=meta
 print(aid,bounds,[w,h],offset,meta['image']['sha256'])
# Canonical source target is the exact pose crop for all siblings; preserve atlas as reference provenance.
for oid in ('revamp--characters--donut--attack','revamp--characters--donut--hit'):
 src_rel=f'reusable/native/{oid}.png'; src=PACK/src_rel; source_hash=hashlib.sha256(src.read_bytes()).hexdigest()
 for v in ('front','top','right','left','bottom','rear'):
  aid=f'{oid}.{v}';meta=amap[aid];p=meta['provenance'];old=p.get('source_image')
  if old and old!=src_rel:p['reference_source_image']=old
  p['source_image']=src_rel;p['native_front']=src_rel;p['native_front_sha256']=source_hash
  Path(PACK/meta['metadata_path']).write_text(json.dumps(meta,indent=2)+'\n');amap[aid]=meta
for i,a in enumerate(idx['assets']):idx['assets'][i]=amap[a['id']]
for g in idx['view_sets']:
 if g['object_id'] in ('revamp--characters--donut--attack','revamp--characters--donut--hit'):
  g['complete']=False;g['geometry_qa']={'status':'pending-review','views':['top','bottom'] if g['object_id'].endswith('attack') else ['front','top','bottom'],'atlas_self_inspected':True,'notes':'Only phase-specific plan candidates updated; hit top candidate rejected and preserved raw. Await Page independent review.'}
idxp.write_text(json.dumps(idx,indent=2)+'\n')
