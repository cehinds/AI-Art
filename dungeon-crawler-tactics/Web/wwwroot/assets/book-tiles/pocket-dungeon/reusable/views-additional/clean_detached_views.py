#!/usr/bin/env python3
"""Remove isolated alpha guide artifacts from specified view PNGs and refresh hashes."""
import argparse, hashlib, json, shutil, struct
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

OUT=Path(__file__).resolve().parent
BOOK=OUT.parents[1]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('targets',nargs='+',help='object_id or object_id.view')
    ap.add_argument('--view',default='top',help='default view when target omits .view')
    ap.add_argument('--remove-bbox',help='Remove only the connected component enclosed by x0,y0,x1,y1; restore from retained before-image first.')
    args=ap.parse_args()
    idxp=OUT/'set-index.json';idx=json.loads(idxp.read_text())
    rawdir=OUT/'raw'/'targeted-cleanups';rawdir.mkdir(parents=True,exist_ok=True)
    results=[]
    for target in args.targets:
        if '.' in target and target.rsplit('.',1)[1] in {'front','top','right','left','bottom','rear'}: oid,view=target.rsplit('.',1)
        else: oid,view=target,args.view
        png=OUT/f'{oid}.{view}.png'; side=OUT/f'{oid}.{view}.json'
        meta=json.loads(side.read_text())
        raw=rawdir/f'{oid}.{view}.before.png'
        if not raw.exists(): shutil.copy2(png,raw)
        image=Image.open(raw if args.remove_bbox else png).convert('RGBA')
        rgba=np.asarray(image); alpha=rgba[:,:,3]
        labels,n=ndimage.label(alpha>=245,structure=np.ones((3,3),dtype=np.uint8))
        counts=np.bincount(labels.ravel()); main=int(np.argmax(counts[1:])+1)
        boxes=ndimage.find_objects(labels)
        removed=[]
        for i,sl in enumerate(boxes,1):
            if sl is not None and i!=main:
                removed.append({'pixels':int(counts[i]),'bbox':[int(sl[1].start),int(sl[0].start),int(sl[1].stop),int(sl[0].stop)]})
        if args.remove_bbox:
            wanted=[int(x) for x in args.remove_bbox.split(',')]
            if len(wanted)!=4: raise ValueError('--remove-bbox requires x0,y0,x1,y1')
            x0,y0,x1,y1=wanted;remove=[]
            for i,sl in enumerate(boxes,1):
                if sl is not None and sl[1].start<=x0 and sl[1].stop>=x1 and sl[0].start<=y0 and sl[0].stop>=y1: remove.append(i)
            if len(remove)!=1: raise ValueError(f'expected one component in bbox {wanted}, found {len(remove)}')
            clean=image.copy();outalpha=alpha.copy();outalpha[np.isin(labels,remove)]=0;clean.putalpha(Image.fromarray(outalpha.astype(np.uint8)));method='remove-only-component-in-bbox';removed=[{'label':remove[0],'bbox':wanted}]
        else:
            keep=(labels==main); clean=image.copy();clean.putalpha(Image.fromarray((keep*alpha).astype(np.uint8)));method='retain-largest-connected-alpha-component-at-threshold-245'
        clean.save(png,optimize=True)
        rawbytes=png.read_bytes();meta['image']['sha256']=hashlib.sha256(rawbytes).hexdigest();meta['image']['rgba_sha256']=hashlib.sha256(struct.pack('>II',*clean.size)+clean.tobytes()).hexdigest();meta['geometry_qa']='pending-review'
        recipe={'method':method,'input_before':raw.relative_to(BOOK).as_posix(),'input_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'output_sha256':meta['image']['sha256'],'remove_bbox':args.remove_bbox,'removed_components':removed}
        meta['provenance']['cleanup']=recipe;side.write_text(json.dumps(meta,indent=2)+'\n')
        asset=next(a for a in idx['assets'] if a.get('id')==meta['id']);asset.clear();asset.update(meta)
        group=next(s for s in idx['view_sets'] if s.get('object_id')==oid);group['complete']=False;group['geometry_qa']='pending-review'
        group['notes']=group.get('notes','')+' Detached alpha guide cleanup; awaiting independent current-hash review.'
        results.append({'object_id':oid,'view':view,'sha256':meta['image']['sha256'],'removed_components':removed})
    idxp.write_text(json.dumps(idx,indent=2)+'\n')
    print(json.dumps(results,indent=2))

if __name__=='__main__': main()
