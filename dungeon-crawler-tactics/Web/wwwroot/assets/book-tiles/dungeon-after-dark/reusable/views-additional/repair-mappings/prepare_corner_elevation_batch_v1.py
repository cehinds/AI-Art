"""Extract six approved-looking corner elevation sets from three paired atlases."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image
from scipy import ndimage
HERE=Path(__file__).resolve().parent;OUT=HERE.parent
FAMILIES=[
 ('iron-tracks-corner-pair-elevations-v2.png',['iron-tracks-tunnel-stone-inner-corner','iron-tracks-tunnel-stone-outer-corner']),
 ('bubble-desert-pair-elevations-v1.png',['bubble-desert-adobe-desert-plaster-inner-corner','bubble-desert-adobe-desert-plaster-outer-corner']),
 ('jungle-corner-pair-elevations-v2.png',['hunting-jungle-vine-covered-ruin-stone-inner-corner','hunting-jungle-vine-covered-ruin-stone-outer-corner'])]
VIEWS=('front','right','left','rear');CAND=OUT/'candidates/corner-elevation-batch-v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def comps(im):
 a=np.asarray(im.getchannel('A'));lab,n=ndimage.label(a>=32);found=[]
 for i,sl in enumerate(ndimage.find_objects(lab),1):
  if sl is None:continue
  y,x=sl;area=int(np.count_nonzero(lab[sl]==i))
  if area>=1000:found.append((area,(x.start,y.start,x.stop,y.stop)))
 return found
def main():
 CAND.mkdir(parents=True,exist_ok=True);sets=[]
 for rawname,ids in FAMILIES:
  raw=OUT/'raw'/rawname;atlas=Image.open(raw).convert('RGBA');cs=comps(atlas)
  if len(cs)!=8:raise ValueError(f'{rawname}: expected 8 components, got {len(cs)}')
  cs.sort(key=lambda x:((x[1][1]+x[1][3])/2,(x[1][0]+x[1][2])/2))
  for ri,oid in enumerate(ids):
   row=cs[4*ri:4*(ri+1)];maxh=max(b[3]-b[1] for _,b in row);scale=172/maxh;entries=[]
   for view,(area,bbox) in zip(VIEWS,row):
    x0,y0,x1,y1=bbox;x0=max(0,x0-2);y0=max(0,y0-2);x1=min(atlas.width,x1+2);y1=min(atlas.height,y1+2);crop=atlas.crop((x0,y0,x1,y1));nw=max(1,round(crop.width*scale));nh=max(1,round(crop.height*scale));norm=crop.resize((nw,nh),Image.Resampling.NEAREST);canvas=Image.new('RGBA',(256,256),(0,0,0,0));canvas.alpha_composite(norm,((256-nw)//2,(256-nh)//2));dst=CAND/f'{oid}.{view}.png';canvas.save(dst)
    entries.append({'object_id':oid,'view':view,'candidate_path':str(dst.relative_to(OUT)),'candidate_sha256':sha(dst),'raw_atlas':str(raw.relative_to(OUT)),'raw_atlas_sha256':sha(raw),'component_bbox_threshold32':list(bbox),'component_area_threshold32':area,'crop_rect_with_2px_padding':[x0,y0,x1,y1],'uniform_scale':scale,'normalized_size':[nw,nh],'anchor_px':[128,128]})
   sets.append({'object_id':oid,'views':entries,'preserved_views':['top','bottom']})
 spec={'candidate_id':'corner-elevation-batch-v1','extraction':'Four connected alpha components per source-row, threshold>=32, ordered y-center then x-center; full silhouettes plus 2px padding. One isotropic scale per object row set to 172px max elevation height, nearest-neighbour, centered 256x256. Only FRONT/RIGHT/LEFT/REAR candidates; TOP/BOTTOM preserved exactly from current index.','sets':sets};(CAND/'candidate.json').write_text(json.dumps(spec,indent=2)+'\n');print(json.dumps({'sets':len(sets),'pngs':sum(len(s['views']) for s in sets)},indent=2))
if __name__=='__main__':main()
