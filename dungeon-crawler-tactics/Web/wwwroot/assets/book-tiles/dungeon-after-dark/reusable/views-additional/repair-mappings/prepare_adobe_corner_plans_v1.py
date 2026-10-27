"""Prepare full source L top plans, generated L undersides, and opposite-view mirrors."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image,ImageOps
from scipy import ndimage
HERE=Path(__file__).resolve().parent;OUT=HERE.parent;BOOK=OUT.parent.parent;CAND=OUT/'candidates/adobe-corner-plans-v1'
IDS=('bubble-desert-adobe-desert-plaster-inner-corner','bubble-desert-adobe-desert-plaster-outer-corner')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def component(im):
 a=np.asarray(im.getchannel('A'));lab,n=ndimage.label(a>=32);cs=[]
 for i,sl in enumerate(ndimage.find_objects(lab),1):
  if sl is None:continue
  y,x=sl;area=int(np.count_nonzero(lab[sl]==i))
  if area>1000:cs.append((area,(x.start,y.start,x.stop,y.stop)))
 if len(cs)!=1:raise ValueError(f'expected one silhouette component got {len(cs)}')
 return cs[0]
def centered(im,scale):
 w,h=im.size;nw=max(1,round(w*scale));nh=max(1,round(h*scale));r=im.resize((nw,nh),Image.Resampling.NEAREST);c=Image.new('RGBA',(256,256),(0,0,0,0));c.alpha_composite(r,((256-nw)//2,(256-nh)//2));return c,(nw,nh)
def main():
 CAND.mkdir(parents=True,exist_ok=True);spec={'candidate_id':'adobe-corner-plans-v1','candidate_sets':[]}
 for oid in IDS:
  # Construct front from accepted rear and right from accepted left by exact horizontal reflection.
  entries=[]
  for view,srcview in [('front','rear'),('right','left')]:
   src=OUT/'images'/f'{oid}.{srcview}.png';im=Image.open(src).convert('RGBA');candidate=ImageOps.mirror(im);dst=CAND/f'{oid}.{view}.png';candidate.save(dst)
   entries.append({'view':view,'candidate_path':str(dst.relative_to(OUT)),'candidate_sha256':sha(dst),'method':'exact-horizontal-mirror','alias_from_asset_id':f'{oid}.{srcview}','alias_source_sha256':sha(src),'uniform_scale':1.0,'normalized_size':[256,256]})
  # TOP reuses the exact canonical native map-plan crop with isotropic normalization.
  srcplan=OUT/'raw'/f'{oid}-corner-source-crop.png';im=Image.open(srcplan).convert('RGBA');scale=172/max(im.size);candidate,size=centered(im,scale);dst=CAND/f'{oid}.top.png';candidate.save(dst)
  entries.append({'view':'top','candidate_path':str(dst.relative_to(OUT)),'candidate_sha256':sha(dst),'method':'exact-source-plan-uniform-normalization','source_reference_image':'reusable/views-additional/raw/'+srcplan.name,'source_reference_sha256':sha(srcplan),'source_rect':[0,0,im.width,im.height],'uniform_scale':scale,'normalized_size':list(size)})
  # BOTTOM uses one connected L silhouette from a source-guided generated atlas.
  raw=OUT/'raw'/('adobe-inner-corner-bottom-v2.png' if 'inner' in oid else 'adobe-outer-corner-bottom-v2.png');area,bbox=component(Image.open(raw).convert('RGBA'));im=Image.open(raw).convert('RGBA');x0,y0,x1,y1=bbox;x0=max(0,x0-2);y0=max(0,y0-2);x1=min(im.width,x1+2);y1=min(im.height,y1+2);crop=im.crop((x0,y0,x1,y1));scale=172/max(crop.size);candidate,size=centered(crop,scale);dst=CAND/f'{oid}.bottom.png';candidate.save(dst)
  prompt=OUT/'prompts'/('adobe-inner-corner-bottom-v2.txt' if 'inner' in oid else 'adobe-outer-corner-bottom-v2.txt')
  entries.append({'view':'bottom','candidate_path':str(dst.relative_to(OUT)),'candidate_sha256':sha(dst),'method':'source-guided-generated-underside','raw_atlas':'reusable/views-additional/raw/'+raw.name,'raw_atlas_sha256':sha(raw),'prompt_path':'reusable/views-additional/prompts/'+prompt.name,'prompt_sha256':sha(prompt),'source_reference_image':'reusable/views-additional/raw/'+srcplan.name,'source_reference_sha256':sha(srcplan),'component_bbox_threshold32':list(bbox),'component_area_threshold32':area,'crop_rect_with_2px_padding':[x0,y0,x1,y1],'uniform_scale':scale,'normalized_size':list(size)})
  spec['candidate_sets'].append({'object_id':oid,'views':entries,'preserve_views':['left','rear']})
 spec['extraction']='Only FRONT, RIGHT, TOP, BOTTOM. FRONT mirrors approved REAR, RIGHT mirrors approved LEFT; exact no-distortion horizontal symmetry. TOP reuses native source crop; BOTTOM extracts its full connected 4x4 L underside. All rescaling isotropic, nearest-neighbour, centered on 256x256.'
 (CAND/'candidate.json').write_text(json.dumps(spec,indent=2)+'\n');print(json.dumps({'sets':len(spec['candidate_sets']),'candidate_views':sum(len(x['views']) for x in spec['candidate_sets'])},indent=2))
if __name__=='__main__':main()
