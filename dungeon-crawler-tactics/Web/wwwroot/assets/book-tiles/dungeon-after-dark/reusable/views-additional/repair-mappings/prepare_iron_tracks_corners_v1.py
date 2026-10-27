"""Extract the four-elevation row atlas for Iron Tracks corner geometry."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image
from scipy import ndimage
HERE=Path(__file__).resolve().parent;OUT=HERE.parent;RAW=OUT/'raw/iron-tracks-corner-pair-elevations-v2.png';CAND=OUT/'candidates/iron-tracks-corner-elevations-v1'
PAIRS=[('iron-tracks-tunnel-stone-inner-corner','inner'),('iron-tracks-tunnel-stone-outer-corner','outer')];VIEWS=('front','right','left','rear')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 im=Image.open(RAW).convert('RGBA');a=np.asarray(im.getchannel('A'));lab,n=ndimage.label(a>=32);cs=[]
 for i,sl in enumerate(ndimage.find_objects(lab),1):
  if sl is None:continue
  y,x=sl;area=int(np.count_nonzero(lab[sl]==i))
  if area>=1000:cs.append((area,(x.start,y.start,x.stop,y.stop)))
 cs.sort(key=lambda z:((z[1][1]+z[1][3])/2,(z[1][0]+z[1][2])/2))
 if len(cs)!=8:raise ValueError(f'expected 8 components, got {len(cs)}')
 CAND.mkdir(parents=True,exist_ok=True);sets=[]
 for ri,(oid,role) in enumerate(PAIRS):
  group=cs[ri*4:(ri+1)*4];maxh=max(b[3]-b[1] for _,b in group);scale=172/maxh;entries=[]
  for view,(area,bbox) in zip(VIEWS,group):
   x0,y0,x1,y1=bbox;x0=max(0,x0-2);y0=max(0,y0-2);x1=min(im.width,x1+2);y1=min(im.height,y1+2);crop=im.crop((x0,y0,x1,y1));nw=max(1,round(crop.width*scale));nh=max(1,round(crop.height*scale));norm=crop.resize((nw,nh),Image.Resampling.NEAREST);canvas=Image.new('RGBA',(256,256),(0,0,0,0));canvas.alpha_composite(norm,((256-nw)//2,(256-nh)//2));dst=CAND/f'{oid}.{view}.png';canvas.save(dst)
   entries.append({'object_id':oid,'view':view,'candidate_path':str(dst.relative_to(OUT)),'candidate_sha256':sha(dst),'raw_atlas':str(RAW.relative_to(OUT)),'raw_atlas_sha256':sha(RAW),'component_bbox_threshold32':list(bbox),'component_area_threshold32':area,'crop_rect_with_2px_padding':[x0,y0,x1,y1],'uniform_scale':scale,'normalized_size':[nw,nh],'anchor_px':[128,128]})
  sets.append({'object_id':oid,'views':entries})
 spec={'candidate_id':'iron-tracks-corner-elevations-v1','extraction':'Eight connected alpha components threshold>=32, sorted by y-center then x-center; rows map inner then outer, columns FRONT/RIGHT/LEFT/REAR. Each row uses one uniform scale calibrated to 172px maximum elevation height. Full component plus 2px padding; nearest-neighbour; centered 256x256. Only four elevations generated; preserve existing TOP/BOTTOM plans.','sets':sets};(CAND/'candidate.json').write_text(json.dumps(spec,indent=2)+'\n');print(json.dumps(spec,indent=2))
if __name__=='__main__':main()
