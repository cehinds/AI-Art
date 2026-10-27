"""Prepare source-guided orthographic corners for Broadcast and Necropolis."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image
from scipy import ndimage
HERE=Path(__file__).resolve().parent;OUT=HERE.parent;PACK=OUT.parent.parent;VIEWS=['front','right','left','rear']
GROUPS=[('broadcast','broadcast-portals-studio-partition-inner-corner','broadcast-portals-studio-partition-outer-corner',False),('necropolis','bubble-necropolis-ancient-tomb-masonry-inner-corner','bubble-necropolis-ancient-tomb-masonry-outer-corner',True)]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def components(im):
 lab,n=ndimage.label(np.asarray(im.getchannel('A'))>=32);r=[]
 for i,s in enumerate(ndimage.find_objects(lab),1):
  if s is None:continue
  y,x=s;area=int(np.count_nonzero(lab[s]==i))
  if area>1000:r.append((area,(x.start,y.start,x.stop,y.stop)))
 r.sort(key=lambda c:(c[1][1],c[1][0]));return r
def create_candidate(oid,view,im,b,area,target,method,raw,prompt,refs,refhash,dirkey):
 x0,y0,x1,y1=b;x0=max(0,x0-2);y0=max(0,y0-2);x1=min(im.width,x1+3);y1=min(im.height,y1+3);crop=im.crop((x0,y0,x1,y1));scale=target/crop.width;nw=round(crop.width*scale);nh=round(crop.height*scale);r=crop.resize((nw,nh),Image.Resampling.NEAREST);can=Image.new('RGBA',(256,256),(0,0,0,0));can.alpha_composite(r,((256-nw)//2,(256-nh)//2));dst=OUT/'candidates'/dirkey/f'{oid}.{view}.png';dst.parent.mkdir(parents=True,exist_ok=True);can.save(dst);idx=json.loads((OUT/'set-index.json').read_text());a={x['id']:x for x in idx['assets']}[f'{oid}.{view}'];return {'object_id':oid,'view':view,'candidate_path':str(dst.relative_to(OUT)),'candidate_sha256':sha(dst),'base_sha256':sha(PACK/a['image']['path']),'raw_atlas':raw,'raw_atlas_sha256':sha(PACK/raw if not str(raw).startswith('reusable/') else OUT/Path(raw).relative_to('reusable/views-additional')),'prompt_path':prompt,'prompt_sha256':sha(PACK/prompt if not str(prompt).startswith('reusable/') else OUT/Path(prompt).relative_to('reusable/views-additional')),'reference_paths':refs,'reference_sha256':refhash,'component_bbox_threshold32':list(b),'component_area_threshold32':area,'crop_rect_with_padding':[x0,y0,x1,y1],'uniform_scale':scale,'normalized_size':[nw,nh],'anchor_px':[128,128],'calibration_target_px':target,'method':method}
def main():
 idx=json.loads((OUT/'set-index.json').read_text());assets={a['id']:a for a in idx['assets']};batches=[]
 for key,inner,outer,needs_plans in GROUPS:
  rawrel=f'reusable/views-additional/raw/corner-batch-{key}-v2-atlas.png';rawpath=OUT/Path(rawrel).relative_to('reusable/views-additional');im=Image.open(rawpath).convert('RGBA');cs=components(im);assert len(cs)==8,(key,len(cs));promptrel=f'reusable/views-additional/prompts/corner-batch-{key}-v2.txt';req=json.loads((OUT/'prompts'/f'corner-batch-{key}-v2-request-result.json').read_text());rows=[]
  for ri,oid in enumerate([inner,outer]):
   top=Image.open(PACK/assets[oid+'.top']['image']['path']).convert('RGBA');tb=top.getchannel('A').getbbox();target=tb[2]-tb[0];views=[]
   for v,(area,b) in zip(VIEWS,cs[ri*4:(ri+1)*4]):views.append(create_candidate(oid,v,im,b,area,target,'source-guided-corner-elevation-atlas',rawrel,promptrel,req['reference_paths'],req['reference_sha256'],f'corner-batch-{key}-v2'))
   if needs_plans:
    source=PACK/assets[oid+'.front']['source']['source_image'];src=Image.open(source).convert('RGBA');sc=components(src);assert len(sc)==1,(oid,len(sc));area,b=sc[0];pr=OUT/'prompts/necropolis-native-top-plan-v2.txt';pr.write_text('Exact extraction of the full native source L-plan at alpha>=32 with two-pixel padding; uniformly normalize using nearest-neighbor. No redraw or recoloring.\n');views.append(create_candidate(oid,'top',src,b,area,target,'exact-native-top-source',str(source.relative_to(PACK)),'reusable/views-additional/prompts/necropolis-native-top-plan-v2.txt',[str(source.relative_to(PACK))],[sha(source)],f'corner-batch-{key}-v2'))
    bottomraw=OUT/'raw/necropolis-corner-undersides-v2-atlas.png';bot=Image.open(bottomraw).convert('RGBA');bc=components(bot);assert len(bc)==2,len(bc);ba,bb=bc[ri];views.append(create_candidate(oid,'bottom',bot,bb,ba,target,'generated-bottom-underside','reusable/views-additional/raw/'+bottomraw.name,'reusable/views-additional/prompts/necropolis-corner-undersides-v2.txt',req['reference_paths'],req['reference_sha256'],f'corner-batch-{key}-v2'))
   rows.append({'object_id':oid,'target_plan_width_px':target,'views':views})
  batches.append({'candidate_id':f'corner-batch-{key}-v2','atlas_layout':'2x4; inner,outer; front,right,left,rear','sets':rows})
 spec={'candidate_id':'corner-batch-broadcast-necropolis-v2','batches':batches,'normalization':'one isotropic scale per object shared across its repaired views'};p=OUT/'candidates/corner-batch-broadcast-necropolis-v2.json';p.write_text(json.dumps(spec,indent=2)+'\n');print(p)
if __name__=='__main__':main()
