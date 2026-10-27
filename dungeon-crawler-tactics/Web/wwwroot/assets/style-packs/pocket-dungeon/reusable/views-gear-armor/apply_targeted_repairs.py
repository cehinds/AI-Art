#!/usr/bin/env python3
"""Replay retained one-view repair recipes after a base atlas rebuild."""
import hashlib, json, struct
from pathlib import Path
from PIL import Image

OUT=Path(__file__).resolve().parent
ROOT=OUT.parent.parent

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def restore_current_independent_pass(index, oid, assets):
    report_path=ROOT/'reusable'/'legacy-view-review.json'
    if not report_path.is_file(): return False
    report=json.loads(report_path.read_text())
    record=next((r for r in report.get('sets',[]) if r.get('object_id')==oid),None)
    group=next((g for g in index['view_sets'] if g.get('object_id')==oid),None)
    if not record or not group or not record.get('complete') or record.get('status')!='passed': return False
    reviewer=(record.get('review') or {}).get('reviewer')
    reviewed_at=(record.get('review') or {}).get('reviewed_at')
    if reviewer not in ('root','page_inventory','reconstruction_design') or not reviewed_at: return False
    source=(ROOT/record['source']['path']).resolve()
    if not source.is_file() or sha(source)!=record['source'].get('sha256'): return False
    expected=group.get('views',{})
    if set(record.get('views',{}))!={'front','top','right','left','bottom','rear'}: return False
    for view,ref in record['views'].items():
        aid=ref.get('asset_id'); leaf=assets.get(aid)
        expected_id=expected.get(view)
        if isinstance(expected_id,dict): expected_id=expected_id.get('asset_id')
        if aid!=expected_id or not leaf or leaf.get('object_id')!=oid or leaf.get('view')!=view: return False
        p=(ROOT/ref['path']).resolve()
        if not p.is_file() or leaf.get('image',{}).get('path')!=ref['path'] or sha(p)!=ref.get('sha256'): return False
    group['complete']=True
    group['geometry_qa']={'status':'passed','evidence':'reusable/legacy-view-review.json','object_id':oid,
                          'reviewer':reviewer,'reviewed_at':reviewed_at,'source_sha256':record['source']['sha256'],
                          'image_hashes':{v:r['sha256'] for v,r in record['views'].items()}}
    return True

def apply_all():
    recipes=OUT/'raw'/'targeted-repairs'
    index_path=OUT/'set-index.json'
    index=json.loads(index_path.read_text())
    assets={a['id']:a for a in index['assets']}
    for recipe_path in sorted(recipes.glob('*.json')):
        recipe=json.loads(recipe_path.read_text())
        # The raw directory also contains append-only audit and batch records.
        # Only leaf-install recipes have the complete target/source contract.
        if not all(recipe.get(k) for k in ('object_id','view','input_image','input_sha256')):
            continue
        oid,view=recipe['object_id'],recipe['view']; aid=f'{oid}.{view}'
        raw=(ROOT/recipe['input_image']).resolve()
        if not raw.is_file() or sha(raw)!=recipe['input_sha256']:
            raise ValueError(f'{aid}: missing or changed generated source {raw}')
        meta_path=OUT/'images'/f'{aid}.json'; png_path=meta_path.with_suffix('.png')
        meta=json.loads(meta_path.read_text())
        if 'transformation' in recipe:
            im=Image.open(raw).convert('RGBA'); bbox=im.getchannel('A').getbbox()
            if not bbox: raise ValueError(f'{aid}: empty source alpha')
            crop=im.crop(bbox).rotate(recipe['transformation']['rotation_degrees_ccw'],expand=True,resample=Image.Resampling.NEAREST)
        else:
            im=Image.open(raw).convert('RGBA'); bbox=im.getchannel('A').getbbox()
            if not bbox: raise ValueError(f'{aid}: empty source alpha')
            crop=im.crop(bbox)
            if recipe.get('rotation_degrees_ccw'):
                crop=crop.rotate(recipe['rotation_degrees_ccw'],expand=True,resample=Image.Resampling.NEAREST)
        if recipe.get('flip_horizontal'):
            crop=crop.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        target_width=recipe.get('target_width_px')
        scale=(target_width/crop.width) if target_width else (204/max(crop.size))
        size=(max(1,round(crop.width*scale)),max(1,round(crop.height*scale)))
        crop=crop.resize(size,Image.Resampling.NEAREST); offset=((256-size[0])//2,(256-size[1])//2)
        canvas=Image.new('RGBA',(256,256),(0,0,0,0)); canvas.alpha_composite(crop,offset); canvas.save(png_path,optimize=True)
        meta['image'].update({'sha256':sha(png_path),'rgba_sha256':hashlib.sha256(struct.pack('>II',256,256)+canvas.tobytes()).hexdigest(),'width':256,'height':256})
        meta['provenance']['repair_recipe']=recipe_path.relative_to(ROOT).as_posix()
        if recipe.get('generated_atlas'):
            atlas=(ROOT/recipe['generated_atlas']).resolve()
            if not atlas.is_file() or sha(atlas)!=recipe.get('generated_atlas_sha256'):
                raise ValueError(f'{aid}: missing or changed retained atlas {atlas}')
            meta['provenance']['generated_atlas']=recipe['generated_atlas']
            meta['provenance']['generated_atlas_sha256']=recipe['generated_atlas_sha256']
        meta['provenance']['normalization']={'scale':scale,'offset_px':list(offset),'resampling':'nearest','frame_size':[256,256],'target_width_px':target_width}
        meta['provenance']['source_rect']={'alpha_bounds':list(bbox),'source_size':list(im.size)}
        if recipe.get('source_cell'):
            meta['provenance']['source_rect']['source_cell']=recipe['source_cell']
        meta['provenance']['notes']=recipe['notes']
        meta['image']['path']=png_path.relative_to(ROOT).as_posix()
        meta['metadata_path']=meta_path.relative_to(ROOT).as_posix()
        meta_path.write_text(json.dumps(meta,indent=2,ensure_ascii=False)+'\n')
        assets[aid].clear(); assets[aid].update(meta)
        for group in index['view_sets']:
            if group['object_id']==oid:
                group['complete']=False
                group['geometry_qa']={'status':'pending-review','reason':'Targeted repair recipe replayed; awaiting independent current-hash QA.'}
                break
        restore_current_independent_pass(index,oid,assets)
    # Base atlas processors recreate worker completion flags. Reapply every
    # published legacy review record, not just objects with repair recipes.
    report_path=ROOT/'reusable'/'legacy-view-review.json'
    if report_path.is_file():
        report=json.loads(report_path.read_text())
        for record in report.get('sets',[]):
            oid=record.get('object_id')
            group=next((g for g in index['view_sets'] if g.get('object_id')==oid),None)
            if not group: continue
            if restore_current_independent_pass(index,oid,assets):
                continue
            group['complete']=False
            group['geometry_qa']={'status':'pending-review','evidence':'reusable/legacy-view-review.json',
                                  'object_id':oid,'reason':'Published independent evidence does not match current source and all six PNG hashes.'}
    index_path.write_text(json.dumps(index,indent=2,ensure_ascii=False)+'\n')

if __name__=='__main__': apply_all()
