"""Isotropically calibrate the NE cap plans to accepted front/depth spans."""
from pathlib import Path
import hashlib,json,math
import numpy as np
from PIL import Image
from scipy import ndimage
HERE=Path(__file__).resolve().parent;OUT=HERE.parent;OID='great-race-transition-glass-maze-endcap-northeast';CAND=OUT/'candidates/glass-ne-plans-v3'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def component(p):
 im=Image.open(p).convert('RGBA');a=np.asarray(im.getchannel('A'));lab,n=ndimage.label(a>=32);cs=[]
 for i,sl in enumerate(ndimage.find_objects(lab),1):
  if sl is None:continue
  y,x=sl;area=int(np.count_nonzero(lab[sl]==i))
  if area>1000:cs.append((area,(x.start,y.start,x.stop,y.stop)))
 if len(cs)!=1:raise ValueError((p,'expected one connected plan',len(cs)))
 return im,cs[0]
def main():
 CAND.mkdir(parents=True,exist_ok=True);raws={v:OUT/'raw'/f'{OID}-{v}-v3.png' for v in ('top','bottom')};comps={v:component(p) for v,p in raws.items()}
 # Calibrate to live approved projections: front span about 61px and side depth about39px.
 widths=[];heights=[]
 for v,(im,(area,b)) in comps.items():widths.append(b[2]-b[0]);heights.append(b[3]-b[1])
 scale=math.sqrt((61/sum(widths)*2)*(39/sum(heights)*2))
 entries=[]
 for v,(im,(area,b)) in comps.items():
  x0,y0,x1,y1=b;x0=max(0,x0-2);y0=max(0,y0-2);x1=min(im.width,x1+2);y1=min(im.height,y1+2);crop=im.crop((x0,y0,x1,y1));nw=max(1,round(crop.width*scale));nh=max(1,round(crop.height*scale));r=crop.resize((nw,nh),Image.Resampling.NEAREST);c=Image.new('RGBA',(256,256),(0,0,0,0));c.alpha_composite(r,((256-nw)//2,(256-nh)//2));dst=CAND/f'{OID}.{v}.png';c.save(dst)
  req=json.loads((OUT/'prompts/glass-ne-post-cap-plans-v3-request-result.json').read_text());q=next(x for x in req if x['view']==v)
  entries.append({'view':v,'candidate_path':str(dst.relative_to(OUT)),'candidate_sha256':sha(dst),'raw_atlas':'reusable/views-additional/raw/'+raws[v].name,'raw_atlas_sha256':q['raw_sha256'],'prompt_path':q['prompt_path'],'prompt_sha256':q['prompt_sha256'],'reference_paths':q['reference_paths'],'reference_sha256':q['reference_sha256'],'component_bbox_threshold32':list(b),'component_area_threshold32':area,'crop_rect_with_2px_padding':[x0,y0,x1,y1],'uniform_scale':scale,'normalized_size':[nw,nh],'anchor_px':[128,128],'calibration_target_px':[61,39]})
 spec={'candidate_id':'glass-ne-plans-v3','object_id':OID,'views':entries,'normalization':'One uniform scale shared by TOP/BOTTOM, chosen by geometric mean of width-to-front and depth-to-side calibration factors. No anisotropic scaling. Preserve approved FRONT/RIGHT/LEFT/REAR pixels unchanged.'};(CAND/'candidate.json').write_text(json.dumps(spec,indent=2)+'\n');print(json.dumps(spec,indent=2))
if __name__=='__main__':main()
