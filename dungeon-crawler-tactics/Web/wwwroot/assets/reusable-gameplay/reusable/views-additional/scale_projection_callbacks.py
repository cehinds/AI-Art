"""Deterministic isotropic scale callbacks for selected generated projections."""
from pathlib import Path
import hashlib, json, struct, shutil
from PIL import Image

OUT=Path(__file__).resolve().parent
PACK=OUT.parents[1]
BACKUP=OUT/'raw'/'callback-inputs'
SCALES={
 'menu-concepts-safe-room-services--carl-potted-plant': {'bottom':0.60},
 'menu-concepts-safe-room-services--training-plant': {'bottom':0.45},
 'menu-concepts-safe-room-services--training-gray-crate': {'top':0.74,'bottom':0.74},
 'menu-concepts-safe-room-services--training-wood-crate': {'top':0.62,'bottom':0.62},
}
index_path=OUT/'set-index.json'
index=json.loads(index_path.read_text())
assets={a['id']:a for a in index['assets']}
changes=[]
for oid,views in SCALES.items():
    group=next(g for g in index['view_sets'] if g['object_id']==oid)
    for view,scale in views.items():
        aid=f'{oid}.{view}'; meta=assets[aid]
        p=PACK/meta['image']['path']
        raw=p.read_bytes(); old_hash=hashlib.sha256(raw).hexdigest()
        BACKUP.mkdir(parents=True,exist_ok=True)
        backup=BACKUP/f'{aid}.before-isotropic-scale.png'
        if not backup.exists(): shutil.copy2(p,backup)
        im=Image.open(p).convert('RGBA')
        scaled=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST)
        frame=Image.new('RGBA',im.size)
        offset=(128-scaled.width//2,128-scaled.height//2)
        frame.alpha_composite(scaled,offset)
        frame.save(p,optimize=True)
        meta['image']['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
        meta['image']['rgba_sha256']=hashlib.sha256(struct.pack('>II',256,256)+frame.tobytes()).hexdigest()
        meta.setdefault('provenance',{})['postprocess_recipe']='reusable/views-additional/scale_projection_callbacks.py'
        meta['provenance']['postprocess']={'operation':'uniform-nearest-scale-about-anchor','scale':scale,'input_sha256':old_hash,'input_backup':f'reusable/views-additional/raw/callback-inputs/{aid}.before-isotropic-scale.png','anchor_px':[128,128]}
        (OUT/f'{aid}.json').write_text(json.dumps(meta,indent=2)+'\n')
        changes.append({'id':aid,'scale':scale,'input_sha256':old_hash,'output_sha256':meta['image']['sha256'],'bbox':frame.getchannel('A').getbbox()})
    group['complete']=False
    group['notes']='Targeted uniform plan-footprint calibration awaiting independent review.'
    group['geometry_qa']={'status':'pending-review','views':list(views),'notes':'Isotropic plan projection scale corrected from source/pot or accepted elevation footprint; pending fresh independent review.','atlas_self_inspected':True}
index['assets']=list(assets.values())
index_path.write_text(json.dumps(index,indent=2)+'\n')
(OUT/'raw'/'scale-projection-callbacks.recipe.json').write_text(json.dumps({'changes':changes},indent=2)+'\n')
print(json.dumps(changes))
