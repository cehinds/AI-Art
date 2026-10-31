#!/usr/bin/env python3
"""Rebuild six-view assets from retained 6x3 atlases without network access.
Run `python3 split_atlas.py` from any directory. All inputs are pack-relative.
The retained atlas metadata records the object-to-row mapping; extraction groups
opaque connected components by the nearest expected grid-cell center and keeps
full component bounds, including overhangs and detached meaningful parts.
"""
from pathlib import Path
import hashlib, json, struct
import numpy as np
from PIL import Image
from scipy import ndimage

OUT=Path(__file__).resolve().parent
PACK=OUT.parents[1]
RAW=OUT/'raw'
VIEWS=['front','top','right','left','bottom','rear']
ALPHA_THRESHOLD=245
MIN_COMPONENT_AREA=4

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def rgba_sha(im): return hashlib.sha256(struct.pack('>II',*im.size)+im.convert('RGBA').tobytes()).hexdigest()
def dump(path,data): path.write_text(json.dumps(data,indent=2)+'\n')

def process_batch(meta_path):
    batch=json.loads(meta_path.read_text())
    if batch.get('usable') is False:
        print('skip marked-failed atlas:',meta_path.name)
        return [],[]
    raw_path=PACK/batch['file']
    im=Image.open(raw_path).convert('RGBA')
    mask=np.asarray(im.getchannel('A'))>=ALPHA_THRESHOLD
    labels,n=ndimage.label(mask,structure=np.ones((3,3),dtype=np.uint8))
    counts=np.bincount(labels.ravel())
    centers=ndimage.center_of_mass(mask,labels,range(1,n+1))
    boxes=ndimage.find_objects(labels)
    rows=len(batch['objects']); h=im.height/rows; w=im.width/6
    groups=[[[] for _ in range(6)] for _ in range(rows)]
    for lab,area in enumerate(counts[1:],1):
        if area<MIN_COMPONENT_AREA: continue
        cy,cx=centers[lab-1]
        row=int(np.argmin(np.abs((np.arange(rows)+.5)*h-cy)))
        col=int(np.argmin(np.abs((np.arange(6)+.5)*w-cx)))
        sl=boxes[lab-1]
        if sl is None: continue
        y0,y1=sl[0].start,sl[0].stop; x0,x1=sl[1].start,sl[1].stop
        groups[row][col].append({'label':lab,'area':int(area),'centroid':[float(cx),float(cy)],'bbox':[x0,y0,x1,y1]})
    manifest=json.loads((PACK/'manifest.json').read_text())
    source={a['id']:a for a in manifest['assets']}
    assets=[]; sets=[]
    for row,entry in enumerate(batch['objects']):
        oid=entry['object_id'] if isinstance(entry,dict) else entry
        src=source[oid]; crops=[]; group_records=[]
        for col,view in enumerate(VIEWS):
            members=groups[row][col]
            if not members:
                crops.append(None); group_records.append([]); continue
            x0=min(m['bbox'][0] for m in members); y0=min(m['bbox'][1] for m in members)
            x1=max(m['bbox'][2] for m in members); y1=max(m['bbox'][3] for m in members)
            crop=im.crop((x0,y0,x1,y1))
            labels_crop=labels[y0:y1,x0:x1]
            keep=np.isin(labels_crop,[m['label'] for m in members])
            crop.putalpha(Image.fromarray((keep*255).astype(np.uint8)))
            crops.append(crop); group_records.append(members)
        valid=[c for c in crops if c is not None]
        complete=len(valid)==6
        if not valid:
            sets.append({'object_id':oid,'views':{},'complete':False,'notes':'No opaque connected component assigned to this object row.'})
            continue
        scale=220/max(max(c.size) for c in valid)
        refs={}
        for view,crop,members in zip(VIEWS,crops,group_records):
            if crop is None: continue
            sz=[max(1,round(v*scale)) for v in crop.size]
            frame=Image.new('RGBA',(256,256),(0,0,0,0))
            frame.alpha_composite(crop.resize(sz,Image.Resampling.NEAREST),((256-sz[0])//2,248-sz[1]))
            aid=oid+'.'+view; dst=OUT/(aid+'.png'); frame.save(dst)
            metapath=dst.with_suffix('.json')
            data={'id':aid,'name':src['label']+' '+view,'kind':'tile' if src['category']=='terrain' else 'sprite',
              'tags':[src['collection'],view,'orthographic','inferred-view'],
              'image':{'path':dst.relative_to(PACK).as_posix(),'width':256,'height':256,'sha256':sha(dst),'rgba_sha256':rgba_sha(frame)},
              'object_id':oid,'view':view,'metadata_path':metapath.relative_to(PACK).as_posix(),'anchor_px':[128,248],
              'views':{'applicable':False,'complete':True,'reason':'individual principal-view image; grouped in the object view_set'},
              'provenance':{'method':'generated','source_image':src['file'],'generated_atlas':raw_path.relative_to(PACK).as_posix(),'generated_atlas_sha256':sha(raw_path),
                'normalization':{'alpha_threshold':ALPHA_THRESHOLD,'minimum_component_area':MIN_COMPONENT_AREA,'component_policy':'group opaque connected components by nearest logical row/column center; preserve full bounds','component_groups':members,'shared_scale':scale,'source_crop_size':list(crop.size),'render_size':sz,'canvas':[256,256],'resampling':'NEAREST','anchor_px':[128,248]},
                'notes':'Inferred orthographic view, not recovered pixels. Unseen surfaces are conservative extrapolations.'}}
            dump(metapath,data); assets.append(data); refs[view]=aid
        sets.append({'object_id':oid,'views':refs,'complete':complete and len(refs)==6,
          'notes':'Generated six-view orthographic set; unseen surfaces are inferred.' if complete else 'Incomplete generated set; one or more components were not assigned.'})
    recipe={'atlas_sha256':sha(raw_path),'grid':{'columns':6,'rows':rows,'view_order':VIEWS},
      'alpha_threshold':ALPHA_THRESHOLD,'minimum_component_area':MIN_COMPONENT_AREA,
      'batches':batch.get('objects',[]),'component_groups':[{ 'object_id':(e['object_id'] if isinstance(e,dict) else e),'row':r,
        'views':{VIEWS[c]:groups[r][c] for c in range(6)}} for r,e in enumerate(batch['objects'])],
      'normalizer':'reusable/views-scenery/split_atlas.py'}
    dump(raw_path.with_suffix('.recipe.json'),recipe)
    print(raw_path.name,len(assets),'assets',sum(s['complete'] for s in sets),'complete sets')
    return assets,sets

all_assets=[]; all_sets=[]
for meta in sorted(RAW.glob('*.provenance.json')):
    assets,sets=process_batch(meta); all_assets.extend(assets); all_sets.extend(sets)
index={'assets':all_assets,'view_sets':all_sets}
dump(OUT/'set-index.json',index)
print('total',len(all_assets),'assets across',len(all_sets),'sets')
