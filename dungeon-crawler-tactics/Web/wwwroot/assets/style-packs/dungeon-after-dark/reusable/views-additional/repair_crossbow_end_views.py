"""Deterministically extract and normalize two corrected Dark crossbow end views.
Run from the style-pack root with:
python3 reusable/views-additional/repair_crossbow_end_views.py reusable/views-additional/raw/arsenal-heavy-crossbow-front-rear-v1.recipe.json
"""
from pathlib import Path
import hashlib, json, os, struct, sys
import numpy as np
from PIL import Image
from scipy import ndimage
OUT=Path(__file__).resolve().parent
PACK=OUT.parent.parent
INDEX=OUT/'set-index.json'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main(recipe_path):
    recipe=json.loads((PACK/recipe_path).read_text())
    atlas_path=PACK/recipe['generated_atlas']; atlas=Image.open(atlas_path).convert('RGBA'); px=np.asarray(atlas)
    index=json.loads(INDEX.read_text()); assets={a['id']:a for a in index['assets']}; sets={s['object_id']:s for s in index['view_sets']}
    labels,_=ndimage.label(px[:,:,3]>int(recipe.get('alpha_threshold',32)))
    crops={}; rects={}
    for view,bounds in recipe['views'].items():
        x0,y0,x1,y1=bounds; cell=px[y0:y1,x0:x1]; lab,n=ndimage.label(cell[:,:,3]>int(recipe.get('alpha_threshold',32)))
        parts=[]
        for i,sl in enumerate(ndimage.find_objects(lab),1):
            if sl is None: continue
            ys,xs=sl; area=int(np.count_nonzero(lab[sl]==i))
            if area<int(recipe.get('min_component_area',24)): continue
            parts.append((i,area,(xs.start,ys.start,xs.stop,ys.stop)))
        if not parts: raise ValueError(f'{view}: no significant components in {bounds}')
        largest=max(p[1] for p in parts)
        chosen=[p for p in parts if p[1]>=largest*float(recipe.get('component_area_ratio',0.005))]
        xlo=min(p[2][0] for p in chosen); ylo=min(p[2][1] for p in chosen); xhi=max(p[2][2] for p in chosen); yhi=max(p[2][3] for p in chosen)
        mask=np.isin(lab,[p[0] for p in chosen]); rgba=cell.copy(); rgba[~mask]=0
        crop=Image.fromarray(rgba,'RGBA').crop((xlo,ylo,xhi,yhi)); crops[view]=crop
        rects[view]={'cell':[x0,y0,x1-x0,y1-y0],'alpha_bounds':[x0+xlo,y0+ylo,xhi-xlo,yhi-ylo],
                     'component_count':len(chosen),'component_areas':[p[1] for p in chosen],
                     'edge_alpha_counts':{'left':int((cell[:,0,3]>32).sum()),'right':int((cell[:,-1,3]>32).sum()),'top':int((cell[0,:,3]>32).sum()),'bottom':int((cell[-1,:,3]>32).sum())}}
    scale=float(recipe['target_width_px'])/max(c.width for c in crops.values())
    changed=[]
    for view,crop in crops.items():
        nw=max(1,round(crop.width*scale)); nh=max(1,round(crop.height*scale))
        if nw>256 or nh>256: raise ValueError(f'{view} clips at {nw}x{nh}')
        resized=crop.resize((nw,nh),Image.Resampling.NEAREST); canvas=Image.new('RGBA',(256,256),(0,0,0,0)); ox=(256-nw)//2; oy=(256-nh)//2; canvas.alpha_composite(resized,(ox,oy))
        aid=f"{recipe['object_id']}.{view}"; asset=assets[aid]; ip=PACK/asset['image']['path']; mp=PACK/asset['metadata_path']; ip.parent.mkdir(parents=True,exist_ok=True); canvas.save(ip,optimize=True); raw=canvas.tobytes()
        asset['image'].update({'width':256,'height':256,'sha256':sha(ip),'rgba_sha256':hashlib.sha256(struct.pack('>II',256,256)+raw).hexdigest()})
        asset['provenance'].update({'method':'generated','generated_atlas':recipe['generated_atlas'],'generated_atlas_sha256':sha(atlas_path),
            'source_contact_sheet':recipe['source_contact_sheet'],'source_contact_sheet_sha256':sha(PACK/recipe['source_contact_sheet']),
            'prompt_path':recipe['prompt_path'],'prompt_sha256':sha(PACK/recipe['prompt_path']),
            'source_rect':rects[view],'normalization':{'scale':scale,'offset_px':[ox,oy],'resampling':'nearest','frame_size':[256,256]},
            'rebuild_command':'python3 reusable/views-additional/repair_crossbow_end_views.py reusable/views-additional/raw/arsenal-heavy-crossbow-front-rear-v1.recipe.json',
            'notes':'Inferred orthographic end elevation; long stock axis is occluded and bow limbs/string project across X. Hidden end details are illustrative, not recovered pixels.'})
        mp.write_text(json.dumps(asset,indent=2)+'\n'); changed.append(view)
    s=sets[recipe['object_id']]; s['complete']=False; s['geometry_qa']={'status':'pending-review','reviewer':'independent-visual-review','changed_views':changed,'notes':['Corrected end elevations installed at a shared isotropic scale; current-hash independent review required.']}; s['notes']='Two corrected end elevations installed; pending independent review.'
    tmp=INDEX.with_suffix('.json.tmp');tmp.write_text(json.dumps(index,indent=2)+'\n');os.replace(tmp,INDEX)
    print(json.dumps({'object_id':recipe['object_id'],'changed_views':changed,'shared_scale':scale},indent=2))
if __name__=='__main__':
    if len(sys.argv)!=2: raise SystemExit('usage: repair_crossbow_end_views.py <pack-relative-recipe>')
    main(sys.argv[1])
