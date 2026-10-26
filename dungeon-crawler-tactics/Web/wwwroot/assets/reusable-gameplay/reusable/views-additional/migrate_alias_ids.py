"""Re-key byte-identical source aliases to their canonical physical IDs, preserving view PNG pixels."""
from pathlib import Path
import hashlib, json
OUT=Path(__file__).resolve().parent; PACK=OUT.parents[1]; INDEX=OUT/'set-index.json'; BASE=json.loads((PACK/'reusable/index.json').read_text()); base={a['id']:a for a in BASE['assets']}; index=json.loads(INDEX.read_text()); assets={a['id']:a for a in index['assets']}; sets={s['object_id']:s for s in index['view_sets']}
migrations={f'room-kit--concept--stone-{s}':f'dungeon-stone--stone-{s}' for s in 'abcd'}
log=[]
for old,new in migrations.items():
    if old not in sets: continue
    if new in sets: raise RuntimeError(f'{new}: canonical set already exists')
    old_parent=base[old]; new_parent=base[new]
    old_bytes=(PACK/old_parent['image']['path']).read_bytes(); new_bytes=(PACK/new_parent['image']['path']).read_bytes()
    if hashlib.sha256(old_bytes).hexdigest()!=hashlib.sha256(new_bytes).hexdigest(): raise RuntimeError(f'{old} and {new} are not byte-identical')
    group=sets.pop(old); new_refs={}
    for view in ('front','top','right','left','bottom','rear'):
        old_id=group['views'][view]; old_meta=assets.pop(old_id); old_side=PACK/old_meta['metadata_path']; old_image=PACK/old_meta['image']['path']; new_id=f'{new}.{view}'; new_rel=f'reusable/views-additional/{new_id}.png'; new_side=OUT/f'{new_id}.json'
        if (PACK/new_rel).exists() or new_side.exists(): raise RuntimeError(f'{new_id}: output collision')
        old_image.rename(PACK/new_rel); old_side.rename(new_side)
        meta=json.loads(new_side.read_text()); meta['id']=new_id; meta['name']=f"{new_parent['name']} {view.title()}"; meta['kind']='tile'; meta['tags']=[*new_parent.get('tags',[]),'inferred-view',view]; meta['object_id']=new; meta['view']=view; meta['image']['path']=new_rel; meta['metadata_path']=new_side.relative_to(PACK).as_posix(); meta['provenance']['source_image']=new_parent['provenance']['source_image']; meta['provenance']['notes']='inferred orthographic view, not recovered pixels; canonical source tile is byte-identical to room-kit concept variant'; new_side.write_text(json.dumps(meta,indent=2)+'\n'); assets[new_id]=meta; new_refs[view]=new_id
    group.update({'object_id':new,'views':new_refs,'complete':False,'notes':'Six inferred orthographic views re-keyed from byte-identical room-kit concept source to canonical dungeon-stone asset; independent review pending.','geometry_qa':{'status':'pending-review','notes':'Alias ID migration verified by source RGBA/file hash; independent source-plus-six review required.'}}); sets[new]=group
    log.append({'from':old,'to':new,'source_sha256':hashlib.sha256(old_bytes).hexdigest(),'view_pngs_preserved_pixelwise':True})
# Update the deterministic batch recipe so offline normalization emits canonical IDs.
recipe_path=OUT/'raw/room-kit-ground-batch-001.recipe.json'; recipe=json.loads(recipe_path.read_text())
for obj in recipe['objects']:
    if obj['id'] in migrations:
        new=migrations[obj['id']]; parent=base[new]; obj['id']=new; obj['name']=parent['name']; obj['kind']='tile'; obj['tags']=parent.get('tags',[]); obj['source_image']=parent['provenance']['source_image']
recipe_path.write_text(json.dumps(recipe,indent=2)+'\n')
# Keep contact reconstruction aligned to canonical source IDs.
contact=OUT/'make_contact.py'; lines=contact.read_text().splitlines(); replacement={f"room-kit--concept--stone-{s}":f"dungeon-stone--stone-{s}" for s in 'abcd'}; lines=[line.replace(k,v) for line in lines for k,v in [('', '')]] if False else lines
for old,new in replacement.items(): lines=[line.replace(old,new) for line in lines]
contact.write_text('\n'.join(lines)+'\n')
index['assets']=list(assets.values()); index['view_sets']=list(sets.values()); INDEX.write_text(json.dumps(index,indent=2)+'\n'); (OUT/'raw/asset-id-migrations.json').write_text(json.dumps({'schema_version':1,'migrations':log},indent=2)+'\n'); print(json.dumps(log,indent=2))
