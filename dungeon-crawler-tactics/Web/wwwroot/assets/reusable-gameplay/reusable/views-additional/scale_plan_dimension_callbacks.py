"""Replayable uniform plan-dimension corrections for documented gameplay holds."""
from pathlib import Path
import hashlib,json,struct,shutil
from PIL import Image
OUT=Path(__file__).resolve().parent;PACK=OUT.parents[1]; BACKUP=OUT/'raw'/'callback-inputs';BACKUP.mkdir(parents=True,exist_ok=True)
SCALES={
 'room-kit--floors--oil-floor':{'top':1.27,'bottom':1.27},
 'room-kit--floors--water-floor':{'top':1.26,'bottom':1.26},
 'room-kit--walls--wall-corner':{'top':1.32,'bottom':1.32},
 'menu-concepts-safe-room-services--training-metal-chest':{'top':0.73,'bottom':0.73},
}
idxp=OUT/'set-index.json';idx=json.loads(idxp.read_text());assets={a['id']:a for a in idx['assets']}; changes=[]
for oid,views in SCALES.items():
    group=next(g for g in idx['view_sets'] if g['object_id']==oid)
    for view,scale in views.items():
        aid=f'{oid}.{view}';meta=assets[aid];dest=PACK/meta['image']['path'];original=dest.read_bytes(); oldhash=hashlib.sha256(original).hexdigest()
        backup=BACKUP/f'{aid}.before-plan-dimension.png'
        if not backup.exists():shutil.copy2(dest,backup)
        im=Image.open(dest).convert('RGBA');nw=round(256*scale);nh=round(256*scale)
        resized=im.resize((nw,nh),Image.Resampling.NEAREST);frame=Image.new('RGBA',(256,256));offset=(128-nw//2,128-nh//2);frame.alpha_composite(resized,offset);frame.save(dest,optimize=True)
        meta['image']['sha256']=hashlib.sha256(dest.read_bytes()).hexdigest();meta['image']['rgba_sha256']=hashlib.sha256(struct.pack('>II',256,256)+frame.tobytes()).hexdigest()
        meta['provenance']['postprocess_recipe']='reusable/views-additional/scale_plan_dimension_callbacks.py';meta['provenance']['postprocess']={'operation':'uniform-nearest-scale-about-anchor','scale':scale,'input_sha256':oldhash,'input_backup':f'reusable/views-additional/raw/callback-inputs/{aid}.before-plan-dimension.png','anchor_px':[128,128]}
        (OUT/f'{aid}.json').write_text(json.dumps(meta,indent=2)+'\n');changes.append({'id':aid,'scale':scale,'input_sha256':oldhash,'output_sha256':meta['image']['sha256'],'bbox':frame.getchannel('A').getbbox()})
    group['complete']=False;group['notes']='Plan-dimension callback awaiting independent review.';group['geometry_qa']={'status':'pending-review','views':list(views),'notes':'Isotropic plan scale calibrated against current-hash source review and accepted elevation span; awaiting fresh review.','atlas_self_inspected':True}
idx['assets']=list(assets.values());idxp.write_text(json.dumps(idx,indent=2)+'\n')
(OUT/'raw'/'scale-plan-dimension-callbacks.recipe.json').write_text(json.dumps({'changes':changes},indent=2)+'\n');print(json.dumps(changes))
