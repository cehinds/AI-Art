#!/usr/bin/env python3
"""Install source-row-matched natural profiles and undersides with root-hash guards."""
import hashlib, importlib.util, json, shutil
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import label, find_objects
OUT=Path(__file__).resolve().parents[2]
BOOK=OUT.parents[1]
ROOT=Path('/workspace/scratch/view-qa-root.json')
IDS=['faction-larracos-drained-city-cobblestone-floor','faction-larracos-worn-drained-city-cobblestone-floor','faction-larracos-cracked-drained-city-cobblestone-floor','faction-larracos-wet-drained-city-cobblestone-floor','faction-larracos-drained-city-cobblestone-edge-transition']
VIEWS=['front','right','left','bottom','rear']
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def extract(path, expected, radius_x, radius_y):
    im=Image.open(path).convert('RGBA'); a=np.asarray(im)[:,:,3]>=64; lab,n=label(a,np.ones((3,3),dtype=np.uint8)); comps=[]
    for i,sl in enumerate(find_objects(lab),1):
        if sl is None: continue
        ys,xs=sl; area=int((lab[sl]==i).sum())
        if area<500: continue
        box=(xs.start,ys.start,xs.stop,ys.stop); cx=(box[0]+box[2])/2; cy=(box[1]+box[3])/2
        if abs(cx-expected[0])<=radius_x and abs(cy-expected[1])<=radius_y: comps.append((area,box,i))
    if not comps: raise RuntimeError(f'No object group near logical cell {expected} in {path}')
    # The intended tile is the largest opaque group assigned to this row/column.
    area,box,i=max(comps,key=lambda c:c[0]); crop=im.crop(box)
    # retain only the chosen full connected component; the alpha threshold defines
    # grouping, while original RGBA preserves antialiasing within its bound.
    return crop,box,area

def main():
    rootqa=json.loads(ROOT.read_text())['reviewed']; ixpath=OUT/'set-index.json'; index=json.loads(ixpath.read_text()); sets={s['object_id']:s for s in index['view_sets']}; assets={a['id']:a for a in index['assets']}
    # Fresh current-hash precondition; never touch any independently PASSed set.
    for oid in IDS:
        key='book-tiles/pocket-dungeon::'+oid; q=rootqa.get(key)
        if not q or q.get('status')=='pass': raise RuntimeError(f'{oid}: no current unresolved root review; skipping edits')
        s=sets[oid]
        for v,expected in q.get('image_hashes',{}).items():
            aid=s['views'][v]; path=BOOK/assets[aid]['image']['path']
            if sha(path)!=expected: raise RuntimeError(f'{oid}.{v}: source+six review hash is stale')
    profile=OUT/'raw/atlases/faction-larracos-natural-stone-profiles-v1.png'; bottom=OUT/'raw/atlases/faction-larracos-natural-stone-undersides-v1.png'
    ph,bh=sha(profile),sha(bottom)
    prof_cols={'front':(168,152,0),'right':(445,152,90),'left':(693,152,270),'rear':(1233,152,0)}
    row_y=[152,360,568,780,988]; profile_x={'front':168,'right':445,'left':693,'rear':1233}
    bottom_y=[194,478,763,1047,1331]
    recipe=OUT/'corrections.json'; spec=json.loads(recipe.read_text()); operations=[]
    backups=OUT/'raw/targeted-repairs'/'faction-larracos-natural-stone-profiles-v1';backups.mkdir(parents=True,exist_ok=True)
    for row,oid in enumerate(IDS):
        for view in VIEWS:
            source=profile if view!='bottom' else bottom
            expected=(profile_x[view],row_y[row]) if view!='bottom' else (512,bottom_y[row])
            crop,bbox,_=extract(source,expected,175 if view!='bottom' else 170,145)
            rotation=prof_cols[view][2] if view in prof_cols else 0
            if rotation==90: crop=crop.transpose(Image.Transpose.ROTATE_90)
            elif rotation==180: crop=crop.transpose(Image.Transpose.ROTATE_180)
            elif rotation==270: crop=crop.transpose(Image.Transpose.ROTATE_270)
            if view=='bottom':
                # Uniform nearest-neighbor calibration to the accepted 220px plan width.
                w=220; h=max(1,round(crop.height*w/crop.width)); scale=w/crop.width
            else:
                w,h=crop.size;scale=1.0
            if max(w,h)>256: raise RuntimeError(f'{oid}.{view} would clip: {(w,h)}')
            framed=Image.new('RGBA',(256,256),(0,0,0,0));crop=crop.resize((w,h),Image.Resampling.NEAREST);framed.alpha_composite(crop,((256-w)//2,248-h))
            aid=f'{oid}.{view}'; target=OUT/f'{aid}.png'; before=sha(target)
            # Save candidate to derive exact expected replay hash.
            candidate=backups/f'{aid}.candidate.png';framed.save(candidate,optimize=True); after=sha(candidate)
            meta=json.loads((OUT/f'{aid}.json').read_text()); refsha=sha(OUT/f'{oid}.top.png')
            source_rel=meta.get('provenance',{}).get('source_image'); prompt='raw/prompts/faction-larracos-natural-stone-undersides-v1.txt' if view=='bottom' else 'raw/prompts/faction-larracos-natural-stone-profiles-v1.txt'
            op={'type':'replace-generated-view','object_id':oid,'view':view,'before_sha256':before,'after_sha256':after,'atlas_path':(source.relative_to(OUT)).as_posix(),'atlas_sha256':bh if view=='bottom' else ph,'crop_bbox':list(bbox),'rotation_degrees':prof_cols[view][2] if view in prof_cols else 0,'render_size':[w,h],'scale':scale,'scale_axis':'width' if view=='bottom' else 'none','alpha_threshold':64,'component_policy':'largest opaque connected component grouped by expected logical row and column center; retain full bounds and discard detached foreign alpha islands','reference_view':'top','reference_sha256':refsha,'prompt_file':prompt,'reason':'Replaced the source-identified natural cobble tile profile with a row-matched orthographic projection; removed the generic metal tray/bolts, retained the accepted TOP, and inferred a natural material-matched substrate underside.'}
            operations.append(op)
    # Append before applying so the exact recipe is durable and replayable.
    known={(o.get('object_id'),o.get('view'),json.dumps(o.get('after_sha256'),sort_keys=True)) for o in spec['operations']}
    for op in operations:
        if (op['object_id'],op['view'],json.dumps(op['after_sha256'],sort_keys=True)) in known: raise RuntimeError('duplicate recipe output; unexpected rerun')
    spec['operations'].extend(operations);recipe.write_text(json.dumps(spec,indent=2)+'\n')
    helper=OUT/'apply_deterministic_view_fixes.py'; specmod=importlib.util.spec_from_file_location('viewfixes',helper); module=importlib.util.module_from_spec(specmod);specmod.loader.exec_module(module)
    results=[]
    for op in operations:
        results.append(module.apply(op,index,backups))
    ixpath.write_text(json.dumps(index,indent=2)+'\n')
    (backups/'install-result.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(results,indent=2))
if __name__=='__main__': main()
