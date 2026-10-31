from PIL import Image
from pathlib import Path
import hashlib,json
ROOT=Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/dungeon-after-dark'); RV=ROOT/'reusable/views-additional'; C=RV/'candidates/equipment-dark-masonry-rail8-20261026'; RAW=C/'raw'; OUT=C/'images'
H=json.loads(Path('/workspace/scratch/equipment-dark-masonry-rail8-handoff-20261026.json').read_text())
ids=['faction-larracos-ancient-city-masonry-outer-corner','faction-larracos-ancient-city-masonry-inner-corner']; hobs={o['object_id']:o for o in H['objects']}
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def cropped(im,box,t=64):
 im=im.convert('RGBA').crop(box); a=im.getchannel('A').point(lambda v:255 if v>=t else 0); b=a.getbbox()
 if not b: raise ValueError('empty')
 return im.crop(b),[box[0]+b[0],box[1]+b[1],box[0]+b[2],box[1]+b[3]]
def canvasfit(im,target,mirror=False,by_height=False):
 if mirror: im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
 w,h=im.size;s=target/h if by_height else target/max(w,h);nw=max(1,round(w*s));nh=max(1,round(h*s));im=im.resize((nw,nh),Image.Resampling.NEAREST)
 cv=Image.new('RGBA',(256,256),(0,0,0,0));off=((256-nw)//2,(256-nh)//2);cv.alpha_composite(im,off);return cv,s,[nw,nh],list(off)
bot=Image.open(RAW/'larracos-bottoms-atlas-v3.png').convert('RGBA')
manifest={'candidate_id':'equipment-dark-masonry-rail8-larracos-v4','sets':[],'reproducibility':{'script_path':'reusable/views-additional/candidates/equipment-dark-masonry-rail8-20261026/raw/build_larracos_candidates_v3.py','resampler':'PIL.Image.Resampling.NEAREST','canvas':[256,256],'anchor_px':[128,128],'crop_threshold_alpha':64}}
for ri,oid in enumerate(ids):
 obj=hobs[oid]; source_rel=f'faction-larracos/components/{oid}.png'; source=ROOT/source_rel; src=Image.open(source).convert('RGBA'); scrop,sbox=cropped(src,(0,0,src.width,src.height),1)
 # Scene-specific generated broad elevation from v5. Mirror for opposite cameras; exact raw request retained.
 elevation_path=RAW/f'{oid}-front-v5.png'; elev=Image.open(elevation_path).convert('RGBA'); ecrop,ebox=cropped(elev,(0,0,elev.width,elev.height),1)
 # Generated broad underside has two row cells in outer/inner order.
 y0=ri*(bot.height//2); y1=(ri+1)*(bot.height//2); bcrop,bottombox=cropped(bot,(0,y0,bot.width,y1),64)
 reqrel=f'reusable/views-additional/candidates/equipment-dark-masonry-rail8-20261026/raw/{oid}-front-request-v5.json'
 req=RAW/f'{oid}-front-request-v5.json'
 # The front generation request is bound to these exact bytes; if absent, stop.
 if not req.exists(): raise FileNotFoundError(req)
 for view in ['front','rear','right','left','top','bottom']:
  if view=='top': crop=scrop; bbox=sbox; rawp=source; rawrel=source_rel; promptp=None; promptsha=None; maxdim=186; flip=False; note='native source pixels uniformly normalized; source-backed plan, not generated.'
  elif view=='bottom': crop=bcrop; bbox=bottombox; rawp=RAW/'larracos-bottoms-atlas-v3.png'; rawrel='reusable/views-additional/candidates/equipment-dark-masonry-rail8-20261026/raw/larracos-bottoms-atlas-v3.png'; promptp=RAW/'larracos-bottoms-request-v3.json'; maxdim=186; flip=False; note='generated opaque underside plaques; connected coral sprig retained for reviewer assessment; hidden undersurface inferred.'
  else:
   crop=ecrop; bbox=ebox; rawp=elevation_path; rawrel=f'reusable/views-additional/candidates/equipment-dark-masonry-rail8-20261026/raw/{oid}-front-v5.png'; promptp=req; maxdim=186; flip=view in ('rear','left')
   note='generated broad solid masonry elevation; opposite horizontal views use a rigid horizontal reflection to express inferred same-kit symmetry.'
  im,scale,dims,offset=canvasfit(crop,maxdim,flip,by_height=False)
  out=OUT/f'{oid}.{view}.v4.png';out.parent.mkdir(parents=True,exist_ok=True);im.save(out,optimize=False)
  base_rel=f'reusable/views-additional/images/{oid}.{view}.png'; base=ROOT/base_rel
  expected=obj['views'][view]['sha256']
  if sha(base)!=expected: raise RuntimeError(f'base changed {oid}.{view}')
  prompt_rel=f'reusable/views-additional/candidates/equipment-dark-masonry-rail8-20261026/raw/{promptp.name}' if promptp else None
  manifest['sets'].append({'object_id':oid,'view':view,'candidate_path':f'candidates/equipment-dark-masonry-rail8-20261026/images/{oid}.{view}.v4.png','candidate_sha256':sha(out),'raw_path':rawrel,'raw_sha256':sha(rawp),'prompt_path':prompt_rel,'prompt_sha256':sha(promptp) if promptp else None,'crop_bbox_alpha64':bbox,'uniform_scale':scale,'resized_dimensions':dims,'offset_px':offset,'anchor_px':[128,128],'base_path':base_rel,'base_sha256':expected,'source_path':source_rel,'source_sha256':sha(source),'geometry_note':note,'provenance_method':'generated' if view not in ('top',) else 'source-derived'})
out=C/'larracos-candidate-manifest-v4.json';out.write_text(json.dumps(manifest,indent=2)+'\n');print(len(manifest['sets']),sha(out))
