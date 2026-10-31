from PIL import Image
from pathlib import Path
import hashlib, json, math
ROOT=Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/dungeon-after-dark')
RV=ROOT/'reusable/views-additional'
CAND=RV/'candidates/equipment-dark-masonry-rail8-20261026'
RAW=CAND/'raw'; OUT=CAND/'images'
HAND=Path('/workspace/scratch/equipment-dark-masonry-rail8-handoff-20261026.json')
manifest=json.loads(HAND.read_text())
obj_ids=['faction-larracos-ancient-city-masonry-outer-corner','faction-larracos-ancient-city-masonry-inner-corner']
objdata={o['object_id']:o for o in manifest['objects']}

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def crop_alpha(im, box, threshold=64):
    im=im.convert('RGBA').crop(box)
    a=im.getchannel('A').point(lambda v:255 if v>=threshold else 0)
    b=a.getbbox()
    if b is None: raise ValueError(f'empty crop {box}')
    # retain original antialiasing at selected foreground extent
    return im.crop(b), [box[0]+b[0],box[1]+b[1],box[0]+b[2],box[1]+b[3]]
def fit(im, target_max, mirror=False, rotate=0):
    if mirror: im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    if rotate: im=im.rotate(rotate,expand=True,resample=Image.Resampling.NEAREST)
    w,h=im.size; s=target_max/max(w,h); nw=max(1,round(w*s)); nh=max(1,round(h*s))
    im=im.resize((nw,nh),Image.Resampling.NEAREST)
    canvas=Image.new('RGBA',(256,256),(0,0,0,0)); x=(256-nw)//2; y=(256-nh)//2; canvas.alpha_composite(im,(x,y))
    return canvas, s, [nw,nh], [x,y]
# Source atlases have two vertically stacked, isolated target rows in the exact requested order.
broad=Image.open(RAW/'larracos-broad-face-atlas-v1.png').convert('RGBA')
side=Image.open(RAW/'larracos-left-atlas-v2.png').convert('RGBA')
bottom=Image.open(RAW/'larracos-bottoms-atlas-v3.png').convert('RGBA')
# Native top plan is the original transparent source; no generated redraw.
result={'candidate_id':'equipment-dark-masonry-rail8-larracos-v1','sets':[],'reproducibility':{'script_path':'reusable/views-additional/candidates/equipment-dark-masonry-rail8-20261026/raw/build_larracos_candidates.py','resampler':'PIL.Image.Resampling.NEAREST','canvas':[256,256],'anchor_px':[128,128],'crop_threshold_alpha':64}}
# Save concise per-source recipe and candidate bytes; all paths are book-root-relative.
for row, oid in enumerate(obj_ids):
    source_rel=f"faction-larracos/components/{oid}.png"; source=ROOT/source_rel
    src=Image.open(source).convert('RGBA')
    # plan footprint scale aligned to the existing roughly 186px common XY span.
    src_crop,src_bbox=crop_alpha(src,(0,0,*src.size),threshold=1)
    top,topscale,topdims,topoff=fit(src_crop,186)
    # Broad face: one horizontal full-height wall surface; rear is its mirrored hidden-face inference.
    y0,y1=row*(broad.height//2),(row+1)*(broad.height//2)
    broadcrop,broadbox=crop_alpha(broad,(0,y0,broad.width,y1))
    # side/end profile: generated left elevation, right is mirrored same-kit symmetry.
    sy0,sy1=row*(side.height//2),(row+1)*(side.height//2)
    sidecrop,sidebox=crop_alpha(side,(0,sy0,side.width,sy1))
    by0,by1=row*(bottom.height//2),(row+1)*(bottom.height//2)
    bottomcrop,bottombox=crop_alpha(bottom,(0,by0,bottom.width,by1))
    # Common Z is calibrated from the broad elevation. Every other cardinal view uses that same isotropic height.
    zmax=166
    views={
      'front':(broadcrop,False,0,'generated broad-face atlas row; alpha-bounded isolated foreground'),
      'rear':(broadcrop,True,0,'horizontal reflection of generated front elevation; inferred unmarked reverse face'),
      'left':(sidecrop,False,0,'generated left-end elevation; alpha-bounded isolated foreground'),
      'right':(sidecrop,True,0,'horizontal reflection of generated left-end elevation; inferred opposite end face'),
      'top':(src_crop,False,0,'native source projection; original pixels uniformly enlarged to common plan span'),
      'bottom':(bottomcrop,False,0,'generated underside atlas row; flat gold cap plaques occlude upper knobs; attached coral is retained for reviewer assessment')
    }
    # Elevation scale all share one world-Z target; plan views share nominal XY maximum.
    records=[]
    for view,(crop,mirror,rot,note) in views.items():
      target=186 if view in ('top','bottom') else zmax
      canvas,scale,dims,offset=fit(crop,target,mirror=mirror,rotate=rot)
      outpath=OUT/f'{oid}.{view}.png'; outpath.parent.mkdir(parents=True,exist_ok=True); canvas.save(outpath,optimize=False)
      base=objdata[oid]['views'][view]['sha256']
      if sha(ROOT/f'reusable/views-additional/images/{oid}.{view}.png')!=base: raise ValueError(f'base changed: {oid}.{view}')
      rawpath={ 'front':'larracos-broad-face-atlas-v1.png','rear':'larracos-broad-face-atlas-v1.png','left':'larracos-left-atlas-v2.png','right':'larracos-left-atlas-v2.png','top':source_rel,'bottom':'larracos-bottoms-atlas-v3.png'}[view]
      raw_abs=ROOT/rawpath if view=='top' else RAW/rawpath
      # view-specific JSON prompt/processing receipt; top is exact source alias, with no API prompt.
      request_name={'front':'larracos-broad-face-request-v1.json','rear':'larracos-broad-face-request-v1.json','left':'larracos-left-request-v2.json','right':'larracos-left-request-v2.json','bottom':'larracos-bottoms-request-v3.json'}.get(view)
      prompt_rel=f'reusable/views-additional/candidates/equipment-dark-masonry-rail8-20261026/raw/{request_name}' if request_name else None
      records.append({'object_id':oid,'view':view,'candidate_path':f'candidates/equipment-dark-masonry-rail8-20261026/images/{oid}.{view}.png','candidate_sha256':sha(outpath),'raw_path':f'reusable/views-additional/candidates/equipment-dark-masonry-rail8-20261026/raw/{rawpath}' if view!='top' else source_rel,'raw_sha256':sha(raw_abs),'prompt_path':prompt_rel,'prompt_sha256':sha(RAW/request_name) if request_name else None,'crop_bbox_alpha64':src_bbox if view=='top' else (broadbox if view in ('front','rear') else sidebox if view in ('left','right') else bottombox),'uniform_scale':scale,'resized_dimensions':dims,'offset_px':offset,'base_sha256':base,'source_path':source_rel,'source_sha256':sha(source),'geometry_note':note,'inference_note':'generated inferred orthographic surfaces; not recovered source pixels' if view!='top' else 'native source view; original source pixels, uniformly scaled'})
    result['sets'].extend(records)
(CAND/'larracos-candidate-manifest-v1.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'sets':len(result['sets']),'sha256':sha(CAND/'larracos-candidate-manifest-v1.json')}))
