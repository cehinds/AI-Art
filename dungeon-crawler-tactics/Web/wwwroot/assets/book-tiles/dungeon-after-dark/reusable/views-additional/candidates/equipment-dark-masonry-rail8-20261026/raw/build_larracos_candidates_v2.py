# Immutable historical v2 recipe retained for reproducibility of the v2 diagnostic.
from PIL import Image
from pathlib import Path
import hashlib,json
ROOT=Path('/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/dungeon-after-dark');RV=ROOT/'reusable/views-additional';C=RV/'candidates/equipment-dark-masonry-rail8-20261026';RAW=C/'raw';OUT=C/'images'
H=json.loads(Path('/workspace/scratch/equipment-dark-masonry-rail8-handoff-20261026.json').read_text());ids=['faction-larracos-ancient-city-masonry-outer-corner','faction-larracos-ancient-city-masonry-inner-corner'];ho={o['object_id']:o for o in H['objects']}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def cropped(im,box,t=64):
 im=im.convert('RGBA').crop(box);a=im.getchannel('A').point(lambda v:255 if v>=t else 0);b=a.getbbox();return im.crop(b),[box[0]+b[0],box[1]+b[1],box[0]+b[2],box[1]+b[3]]
def fit(im,n,flip=False):
 if flip:im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
 w,h=im.size;s=n/max(w,h);nw=max(1,round(w*s));nh=max(1,round(h*s));im=im.resize((nw,nh),Image.Resampling.NEAREST);cv=Image.new('RGBA',(256,256),(0,0,0,0));off=((256-nw)//2,(256-nh)//2);cv.alpha_composite(im,off);return cv,s,[nw,nh],list(off)
bot=Image.open(RAW/'larracos-bottoms-atlas-v3.png').convert('RGBA');M={'candidate_id':'equipment-dark-masonry-rail8-larracos-v2','sets':[],'reproducibility':{'script_path':'reusable/views-additional/candidates/equipment-dark-masonry-rail8-20261026/raw/build_larracos_candidates_v2.py','resampler':'PIL.Image.Resampling.NEAREST','canvas':[256,256],'anchor_px':[128,128],'crop_threshold_alpha':64}}
for ri,oid in enumerate(ids):
 o=ho[oid];sr=f'faction-larracos/components/{oid}.png';sp=ROOT/sr;src=Image.open(sp).convert('RGBA');sc,sbox=cropped(src,(0,0,src.width,src.height),1)
 elev=Image.open(RAW/f'{oid}-front-v5.png').convert('RGBA');ec,ebox=cropped(elev,(0,0,elev.width,elev.height),1)
 by0=ri*(bot.height//2);by1=(ri+1)*(bot.height//2);bc,bbox=cropped(bot,(0,by0,bot.width,by1),64)
 req=RAW/f'{oid}-front-request-v5.json'
 for view in ['front','rear','right','left','top','bottom']:
  if view=='top':crop,box,rawp,rawrel,pr,maxdim,flip=sc,sbox,sp,sr,None,186,False;note='native source projection uniformly scaled'
  elif view=='bottom':crop,box,rawp,rawrel,pr,maxdim,flip=bc,bbox,RAW/'larracos-bottoms-atlas-v3.png','reusable/views-additional/candidates/equipment-dark-masonry-rail8-20261026/raw/larracos-bottoms-atlas-v3.png',RAW/'larracos-bottoms-request-v3.json',186,False;note='generated underside; attached coral retained for review'
  else:crop,box,rawp,rawrel,pr,maxdim,flip=ec,ebox,RAW/f'{oid}-front-v5.png',f'reusable/views-additional/candidates/equipment-dark-masonry-rail8-20261026/raw/{oid}-front-v5.png',req,166,view in ('rear','left');note='generated broad face, mirrored for inferred opposite camera'
  im,s,dims,off=fit(crop,maxdim,flip);out=OUT/f'{oid}.{view}.v2.png';out.parent.mkdir(parents=True,exist_ok=True);im.save(out,optimize=False)
  bp=f'reusable/views-additional/images/{oid}.{view}.png';base=ROOT/bp;bs=o['views'][view]['sha256']
  if sha(base)!=bs:raise ValueError('base changed')
  M['sets'].append({'object_id':oid,'view':view,'candidate_path':f'candidates/equipment-dark-masonry-rail8-20261026/images/{oid}.{view}.v2.png','candidate_sha256':sha(out),'raw_path':rawrel,'raw_sha256':sha(rawp),'prompt_path':f'reusable/views-additional/candidates/equipment-dark-masonry-rail8-20261026/raw/{pr.name}' if pr else None,'prompt_sha256':sha(pr) if pr else None,'crop_bbox_alpha64':box,'uniform_scale':s,'resized_dimensions':dims,'offset_px':off,'anchor_px':[128,128],'base_path':bp,'base_sha256':bs,'source_path':sr,'source_sha256':sha(sp),'geometry_note':note})
(C/'larracos-candidate-manifest-v2.json').write_text(json.dumps(M,indent=2)+'\n')
