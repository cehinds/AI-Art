"""Isotropically calibrate canonical wardrobe overhead projection."""
from pathlib import Path
import hashlib,json,struct,shutil
from PIL import Image
OUT=Path(__file__).resolve().parent;PACK=OUT.parents[1];aid='menu-concepts-safe-room-services--carl-wardrobe.top';idxp=OUT/'set-index.json';idx=json.loads(idxp.read_text());a=next(x for x in idx['assets'] if x['id']==aid);p=PACK/a['image']['path'];old=p.read_bytes();oldhash=hashlib.sha256(old).hexdigest();bk=OUT/'raw'/'callback-inputs';bk.mkdir(parents=True,exist_ok=True);bp=bk/f'{aid}.before-uniform-plan-scale.png';
if not bp.exists():shutil.copy2(p,bp)
im=Image.open(p).convert('RGBA');scale=0.67;n=round(256*scale);small=im.resize((n,n),Image.Resampling.NEAREST);frame=Image.new('RGBA',(256,256));offset=(128-n//2,128-n//2);frame.alpha_composite(small,offset);frame.save(p,optimize=True);a['image']['sha256']=hashlib.sha256(p.read_bytes()).hexdigest();a['image']['rgba_sha256']=hashlib.sha256(struct.pack('>II',256,256)+frame.tobytes()).hexdigest();a['provenance']['postprocess_recipe']='reusable/views-additional/scale_carl_wardrobe_top.py';a['provenance']['postprocess']={'operation':'uniform-nearest-scale-about-anchor','scale':scale,'input_sha256':oldhash,'input_backup':f'reusable/views-additional/raw/callback-inputs/{aid}.before-uniform-plan-scale.png','anchor_px':[128,128]};(OUT/f'{aid}.json').write_text(json.dumps(a,indent=2)+'\n');
for j,x in enumerate(idx['assets']):
 if x['id']==aid:idx['assets'][j]=a
for g in idx['view_sets']:
 if g['object_id']=='menu-concepts-safe-room-services--carl-wardrobe':g['complete']=False;g['notes']='Wardrobe TOP uniform scale calibration awaiting independent review.';g['geometry_qa']={'status':'pending-review','views':['top'],'notes':'Single-door cabinet identity preserved; overhead size uniformly calibrated to elevation footprint.','atlas_self_inspected':True}
idxp.write_text(json.dumps(idx,indent=2)+'\n');(OUT/'raw'/'scale-carl-wardrobe-top.recipe.json').write_text(json.dumps({'id':aid,'scale':scale,'input_sha256':oldhash,'output_sha256':a['image']['sha256'],'offset':offset,'operation':'uniform-nearest-scale-about-anchor'},indent=2)+'\n');print(a['image']['sha256'])
