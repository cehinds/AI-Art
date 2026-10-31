"""Deterministically swap mis-keyed left/right profiles for three Donut poses."""
from pathlib import Path
import hashlib,json,struct,shutil
from PIL import Image
OUT=Path(__file__).resolve().parent;PACK=OUT.parents[1];RAW=OUT/'raw'/'donut-profile-rekey';RAW.mkdir(parents=True,exist_ok=True);idxp=OUT/'set-index.json';idx=json.loads(idxp.read_text());assets={a['id']:a for a in idx['assets']};objects=['revamp--characters--donut--windup','revamp--characters--donut--attack','revamp--characters--donut--hit'];changes=[]
for oid in objects:
    # Retain byte-identical pre-rekey projections for deterministic replay.
    srcs={v:PACK/assets[f'{oid}.{v}']['image']['path'] for v in ('right','left')}
    for v,p in srcs.items():
        target=RAW/f'{oid}.{v}.before-rekey.png'
        if not target.exists():shutil.copy2(p,target)
    for dest_view,source_view in (('right','left'),('left','right')):
        aid=f'{oid}.{dest_view}';source=RAW/f'{oid}.{source_view}.before-rekey.png';source_hash=hashlib.sha256(source.read_bytes()).hexdigest();im=Image.open(source).convert('RGBA');dest=PACK/assets[aid]['image']['path'];im.save(dest,optimize=True);m=assets[aid];m['image']['sha256']=hashlib.sha256(dest.read_bytes()).hexdigest();m['image']['rgba_sha256']=hashlib.sha256(struct.pack('>II',im.width,im.height)+im.tobytes()).hexdigest();m['provenance']['axis_remap']={'recipe':'reusable/views-additional/rekey_donut_profiles.py','source_asset_id':f'{oid}.{source_view}','source_path':f'reusable/views-additional/raw/donut-profile-rekey/{oid}.{source_view}.before-rekey.png','source_sha256':source_hash,'rotation':None};m['provenance']['notes']='Inferred orthographic profile; camera-side assignment re-keyed to the fixed world-Y heading. Original opposite-side source projection is retained as replay input; hidden surfaces remain inferred.';(OUT/f'{aid}.json').write_text(json.dumps(m,indent=2)+'\n');changes.append({'id':aid,'source_view':source_view,'source_sha256':source_hash,'output_sha256':m['image']['sha256']})
    group=next(g for g in idx['view_sets'] if g['object_id']==oid);group['complete']=False;group['notes']='RIGHT/LEFT profiles re-keyed to consistent fixed world-Y camera convention; pending fresh independent review.';group['geometry_qa']={'status':'pending-review','views':['right','left'],'notes':'Image bytes are re-keyed from the two accepted opposite profiles without flips or geometric edits.','atlas_self_inspected':True}
for i,a in enumerate(idx['assets']):
 if a['id'] in assets:idx['assets'][i]=assets[a['id']]
idxp.write_text(json.dumps(idx,indent=2)+'\n');(OUT/'raw'/'donut-profile-rekey.recipe.json').write_text(json.dumps({'objects':objects,'rekeys':changes},indent=2)+'\n');print(json.dumps(changes))
