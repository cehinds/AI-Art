#!/usr/bin/env python3
"""Rebuild candidate-only service/cap views from retained atlases and same-target aliases."""
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
import numpy as np, json, hashlib, os

PACK='/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/dungeon-after-dark'
ROOT=PACK+'/reusable/views-additional/candidates/equipment-dark-future-eight-service-caps-20261026'
RAW=ROOT+'/raw'; OUT=ROOT+'/images'; os.makedirs(OUT,exist_ok=True)
VIEWS=['front','top','right','left','bottom','rear']
HAND=json.load(open('/workspace/scratch/equipment-dark-future-eight-service-caps-handoff-20261026.json'))
OBJECTS={o['object_id']:o for o in HAND['objects']}

def sha(p):
    return hashlib.sha256(open(p,'rb').read()).hexdigest()
def identify_components(path, cols, rows, threshold=64):
    im=Image.open(path).convert('RGBA'); a=np.asarray(im)[:,:,3]
    labels,n=ndimage.label(a>=threshold,structure=np.ones((3,3),dtype=np.uint8))
    cellw=im.width/cols; cellh=im.height/rows; result={}
    for i in range(1,n+1):
        yy,xx=np.where(labels==i)
        if not len(xx): continue
        # Only meaningful cell-sized components; tiny disconnected generator speckle is discarded.
        if len(xx)<100: continue
        cx=float(xx.mean()); cy=float(yy.mean())
        c=min(cols-1,int(cx/cellw)); r=min(rows-1,int(cy/cellh))
        key=(r,c)
        if key in result: raise ValueError(f'multiple significant components in cell {key}: {path}')
        result[key]=(i,(int(xx.min()),int(yy.min()),int(xx.max())+1,int(yy.max())+1),len(xx))
    if len(result)!=cols*rows: raise ValueError(f'expected {cols*rows} components, got {len(result)} for {path}: {result}')
    return im,labels,result

def normalized_component(atlas, labels, info, scale, canvas=256):
    i,(x0,y0,x1,y1),area=info
    arr=np.asarray(atlas.convert('RGBA'))[y0:y1,x0:x1].copy()
    lab=labels[y0:y1,x0:x1]
    # Keep the selected high-alpha silhouette and its immediate soft antialias edge only.
    sel=lab==i
    grow=ndimage.binary_dilation(sel,structure=np.ones((5,5),dtype=bool))
    arr[:,:,3]=np.where(grow,arr[:,:,3],0)
    arr[:,:,3]=np.where(arr[:,:,3]>=1,arr[:,:,3],0)
    h,w=arr.shape[:2]; nw=max(1,round(w*scale)); nh=max(1,round(h*scale))
    fg=Image.fromarray(arr,'RGBA').resize((nw,nh),Image.Resampling.NEAREST)
    out=Image.new('RGBA',(canvas,canvas),(0,0,0,0)); off=(canvas//2-nw//2,canvas//2-nh//2); out.alpha_composite(fg,off)
    return out, [x0,y0,x1,y1], [nw,nh], list(off)

# Generated station caps: exact 6x2 atlas. Extract by global 8-connected alpha components,
# not nominal cells, so silhouettes crossing cell bounds remain whole and observable.
station=RAW+'/station-caps-output-v2.png'
si,sl,sc=identify_components(station,6,2,64)
station_ids=['iron-stations-station-tiled-masonry-endcap-northwest','iron-stations-station-tiled-masonry-endcap-northeast']
recipes=[]; candidates={}
for ri,oid in enumerate(station_ids):
    infos=[sc[(ri,ci)] for ci in range(6)]
    maxdim=max(max(bb[2]-bb[0],bb[3]-bb[1]) for _,bb,_ in infos)
    scale=min(1.0,224/maxdim)
    # Shared isotropic scale per object across all six views.
    for ci,v in enumerate(VIEWS):
        info=infos[ci]; out,bbox,wh,off=normalized_component(si,sl,info,scale)
        name=f'{oid}.{v}.candidate-v2.png'; p=OUT+'/'+name; out.save(p)
        base=OBJECTS[oid]['views'][v]
        candidates[(oid,v)]={'path':p,'sha256':sha(p),'candidate_file':name,'recipe':{'raw_path':station,'raw_sha256':sha(station),'cell_grid':[6,2],'component_bbox_global_xyxy':bbox,'component_area_at_alpha64':info[2],'alpha_threshold':64,'connectivity':8,'uniform_scale_per_object':scale,'resized_dimensions':wh,'offset_px':off,'canvas':[256,256],'resampler':'NEAREST','alpha_mask':'selected global alpha>=64 component plus 2px dilation for antialias pixels'}}

# Safe-services generated atlas: six columns by four rows; use affected directions only.
safe=RAW+'/safe-service-tiles-output-v2.png'; ai,al,ac=identify_components(safe,6,4,64)
safe_ids=['safe-services-cream-service-tile-wall-northwest','safe-services-cream-service-tile-wall-northeast','safe-services-cream-service-tile-endcap-northwest','safe-services-cream-service-tile-endcap-northeast']
safe_targets={safe_ids[0]:['top','right','left','bottom'],safe_ids[1]:['top','bottom'],safe_ids[2]:['top','right','left','bottom'],safe_ids[3]:['top','bottom']}
for ri,oid in enumerate(safe_ids):
    infos=[ac[(ri,ci)] for ci in range(6)]
    maxdim=max(max(bb[2]-bb[0],bb[3]-bb[1]) for _,bb,_ in infos)
    scale=min(1.0,224/maxdim)
    for ci,v in enumerate(VIEWS):
        if v not in safe_targets[oid]: continue
        info=infos[ci]; out,bbox,wh,off=normalized_component(ai,al,info,scale)
        name=f'{oid}.{v}.candidate-v2.png'; p=OUT+'/'+name; out.save(p)
        candidates[(oid,v)]={'path':p,'sha256':sha(p),'candidate_file':name,'recipe':{'raw_path':safe,'raw_sha256':sha(safe),'cell_grid':[6,4],'component_bbox_global_xyxy':bbox,'component_area_at_alpha64':info[2],'alpha_threshold':64,'connectivity':8,'uniform_scale_per_object':scale,'resized_dimensions':wh,'offset_px':off,'canvas':[256,256],'resampler':'NEAREST','alpha_mask':'selected global alpha>=64 component plus 2px dilation for antialias pixels'}}

# Ghost Havana uses the already-approved same-target shallow elevations and native square top as
# conservative symmetry donors. No new pixels are painted; keep donor hashes and declared aliasing.
for oid in ['ghost-havana-weathered-stucco-north-cap','ghost-havana-weathered-stucco-west-cap']:
    ob=OBJECTS[oid]
    for v,donor in [('front','right'),('rear','left'),('bottom','top')]:
        src=ob['views'][donor]['path']; im=Image.open(src).convert('RGBA')
        name=f'{oid}.{v}.candidate-v2.png'; p=OUT+'/'+name; im.save(p)
        candidates[(oid,v)]={'path':p,'sha256':sha(p),'candidate_file':name,'recipe':{'method':'exact_same_target_pixel_alias','donor_view':donor,'donor_path':src,'donor_sha256':sha(src),'inference':'same-target shallow cap symmetry for opposite elevation; opaque underside inferred symmetric to native top'}}

# Keep exact generation prompts as standalone structured JSON, bound to the retained raw atlas.
STATION_PROMPT="A clean orthographic pixel-art 6-column by 2-row transparent atlas, columns FRONT, TOP, RIGHT, LEFT, BOTTOM, REAR; rows NW cap then NE cap. Native identity is a small plain gray stone cap. The same cap is a squat CUBE with a square footprint: TOP and BOTTOM are equal square silhouettes; FRONT, REAR, RIGHT, LEFT are all the same width as the square plan, each a low rectangular side face with the SAME height. Every view must have consistent world dimensions: use a 170px-wide square top/bottom, and four elevation faces each 170px wide by 100px high. Side views must not be narrower than front/rear. No perspective. Gray and charcoal stone with restrained dark grout, matching the first reference. The second reference gives orthographic shape only; ignore its colors and ornament. No gold, no blue, no pillar, no wall, no decoration. Each of 12 cells contains exactly one view fully centered, generous transparent cell gutters, no cell crossings, no labels, no drawn grid lines, no cast shadows, no glow. Crisp native pixel art."
SAFE_PROMPT="Create a 6-column by 4-row transparent orthographic pixel-art atlas. Columns exactly FRONT, TOP, RIGHT, LEFT, BOTTOM, REAR. Rows exactly: (1) safe-services-cream-service-tile-wall-northwest, a long wall along X; (2) safe-services-cream-service-tile-wall-northeast, a long wall along Y; (3) safe-services-cream-service-tile-endcap-northwest, a compact square cap; (4) safe-services-cream-service-tile-endcap-northeast, a rectangular long-Y cap. Use ONLY the cream tile, bright red horizontal band, blue cap/base, and dark outline palette shown in first reference. It is a Dark source plus accepted views contact. Ignore any other styles. NO GOLD, NO YELLOW, NO ORNAMENTS, NO BOSSES. Row1: FRONT/REAR broad cream-red-blue wall facades; TOP/BOTTOM are thin horizontal blue strips along X, with no gold ends; RIGHT/LEFT are narrow wall end elevations with red stripe and matching cream/blue layers. Row2: FRONT/REAR are narrow tile-wall end faces; RIGHT/LEFT are broad cream-red-blue facades; TOP/BOTTOM are thin vertical blue strips along Y, not a full facade. Row3: all four elevations are low compact tiled cap cuboid faces; TOP is a blue-rim cream square top footprint; BOTTOM plain opaque blue/cream square underside; no knobs. Row4: FRONT/REAR are narrow tiled ends; RIGHT/LEFT broad side faces; TOP is a blue/cream long-Y rectangular plan; BOTTOM matching plain blue/cream long-Y underside. Each cell contains exactly one complete axis-aligned principal view, no perspective, consistent object scale; transparent background, generous gutters, no labels/gridlines, nothing crosses cells. Make the red stripe a single horizontal band at the same vertical location in every upright elevation. Source artwork is pixel art; use crisp square pixels, not glow/shading."
for fn,prompt,refs,raw in [('station-caps-prompt-v2.json',STATION_PROMPT,['station-caps-sources-v1.png','station-caps-sameid-geometry-v1.png'],station),('safe-service-tiles-prompt-v2.json',SAFE_PROMPT,['safe-source-approved-views-v3.png'],safe)]:
    obj={'prompt':prompt,'references':[{'path':os.path.relpath(RAW+'/'+f,PACK),'sha256':sha(RAW+'/'+f)} for f in refs],'output_path':os.path.relpath(raw,PACK),'output_sha256':sha(raw)}
    open(RAW+'/'+fn,'w').write(json.dumps(obj,indent=2)+'\n')

# Versioned recipe manifest; all referenced paths are pack-root-relative, with candidate-path
# resolved under the candidate directory. Full sources/base views stay untouched.
script_path=ROOT+'/raw/build_candidates_v2.py'; script_sha=sha(script_path)
sets=[]
for (oid,v),rec in candidates.items():
    ob=OBJECTS[oid]; src=ob['source']; base=ob['views'][v]
    rawp=rec['recipe'].get('raw_path') or rec['recipe'].get('donor_path')
    rawrelative=os.path.relpath(rawp,PACK)
    rp=rec['recipe'].copy(); rp['raw_path']=rawrelative
    promptfile=('station-caps-prompt-v2.json' if oid in station_ids else 'safe-service-tiles-prompt-v2.json') if 'uniform_scale_per_object' in rp else None
    promptpath=(RAW+'/'+promptfile) if promptfile else None
    row={'object_id':oid,'view':v,'candidate_path':os.path.relpath(rec['path'],PACK),'candidate_sha256':rec['sha256'],'raw_path':rawrelative,'raw_sha256':sha(rawp),'prompt_path':os.path.relpath(promptpath,PACK) if promptpath else None,'prompt_sha256':sha(promptpath) if promptpath else None,'source_path':os.path.relpath(src['path'],PACK),'source_sha256':src['sha256'],'base_path':os.path.relpath(base['path'],PACK),'base_sha256':base['sha256'],'anchor_px':[128,128],'recipe':rp,'geometry_note':('Generated inferred orthographic view from source-faithful atlas; hidden construction is inferred, not recovered pixels.' if 'uniform_scale_per_object' in rp else 'Exact current same-target view alias; symmetry and hidden underside are inferred, not recovered pixels.'),'provenance_method':('generated' if 'uniform_scale_per_object' in rp else 'same_target_alias')}
    sets.append(row)
manifest={'candidate_id':'equipment-dark-future-eight-service-caps-v2','scope':'book-tiles/dungeon-after-dark','candidate_only':True,'reviewer':'page_inventory','installer':'views_dark_books','activated_handoff_path':'/workspace/scratch/equipment-dark-future-eight-service-caps-handoff-20261026.json','activated_handoff_sha256':sha('/workspace/scratch/equipment-dark-future-eight-service-caps-handoff-20261026.json'),'source_six_proof_path':'/tmp/page-qa-equipment-future-eight-service-caps-current-20261026-01.png.json','source_six_proof_sha256':sha('/tmp/page-qa-equipment-future-eight-service-caps-current-20261026-01.png.json'),'sets':sets,'reproducibility':{'script_path':os.path.relpath(script_path,PACK),'script_sha256':script_sha,'canvas':[256,256],'anchor_px':[128,128],'resampler':'PIL.Image.Resampling.NEAREST','alpha_component_threshold':64,'connectivity':8,'notes':'Extraction uses whole-atlas global connected components and does not crop to nominal cell boundaries. Per-object isotropic scale is shared across all six generated directions. Ghost cap candidates are exact same-target donor aliases.'}}
mp=ROOT+'/future-eight-candidate-manifest-v2.json'; open(mp,'w').write(json.dumps(manifest,indent=2)+'\n')

# Candidate-only source + current/candidate contact: rows object, cols source/current six with
# affected directions replaced by candidates. This is an inspection aid, not a pack asset.
cell=180; contact=Image.new('RGBA',(cell*7,cell*len(OBJECTS)),(230,230,230,255)); draw=ImageDraw.Draw(contact)
for ri,(oid,ob) in enumerate(OBJECTS.items()):
    paths=[ob['source']['path']]+[candidates.get((oid,v),{}).get('path',ob['views'][v]['path']) for v in VIEWS]
    for ci,p in enumerate(paths):
        im=Image.open(p).convert('RGBA'); a=im.getchannel('A').getbbox(); im=im.crop(a) if a else im
        im.thumbnail((138,132),Image.Resampling.NEAREST)
        x=ci*cell+(cell-im.width)//2; y=ri*cell+28+(132-im.height)//2
        # checkerboard under alpha
        bg=Image.new('RGBA',im.size,(220,220,220,255)); bg.alpha_composite(im); contact.alpha_composite(bg,(x,y))
        draw.text((ci*cell+3,ri*cell+5),['SOURCE']+VIEWS[0:][0:ci] if False else ('SOURCE' if ci==0 else VIEWS[ci-1]),fill=(0,0,0,255))
    draw.text((2,ri*cell+160),oid,fill=(0,0,0,255))
cp=ROOT+'/future-eight-source-current-candidate-contact-v2.png';contact.save(cp)
meta={'contact':os.path.relpath(cp,PACK),'contact_sha256':sha(cp),'manifest':os.path.relpath(mp,PACK),'manifest_sha256':sha(mp),'activated_handoff_sha256':manifest['activated_handoff_sha256'],'objects':[]}
for oid,ob in OBJECTS.items():
    meta['objects'].append({'object_id':oid,'source':ob['source'],'base_views':ob['views'],'candidates':{v:{'path':os.path.relpath(candidates[(oid,v)]['path'],PACK),'sha256':candidates[(oid,v)]['sha256']} for v in VIEWS if (oid,v) in candidates}})
open(ROOT+'/future-eight-source-current-candidate-contact-v2.json','w').write(json.dumps(meta,indent=2)+'\n')
print('manifest',mp,sha(mp),'sets',len(sets)); print('contact',cp,sha(cp)); print('candidates',len(candidates))
