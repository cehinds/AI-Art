"""Extract complete connected components and uniform-normalize Glass Maze endcaps."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image
from scipy import ndimage
HERE=Path(__file__).resolve().parent;OUT=HERE.parent;CAND=OUT/'candidates/glass-maze-endcaps-v1'
IDS=(('great-race-transition-glass-maze-endcap-northeast','great-race-transition-glass-maze-endcap-northeast-candidate-sixview-v2.png'),('great-race-transition-glass-maze-endcap-northwest','great-race-transition-glass-maze-endcap-northwest-candidate-sixview-v1.png'))
VIEWS=('front','top','right','left','bottom','rear')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def getcomps(im):
 a=np.asarray(im.getchannel('A'));lab,n=ndimage.label(a>=32);out=[]
 for i,s in enumerate(ndimage.find_objects(lab),1):
  if s is None:continue
  y,x=s;area=int(np.count_nonzero(lab[s]==i))
  if area>1000:out.append((area,(x.start,y.start,x.stop,y.stop)))
 return sorted(out,key=lambda z:(z[1][0]+z[1][2])/2)
def main():
 CAND.mkdir(parents=True,exist_ok=True);sets=[]
 for oid,rawname in IDS:
  raw=OUT/'raw'/rawname;atlas=Image.open(raw).convert('RGBA');components=getcomps(atlas)
  if len(components)!=6:raise ValueError((oid,'expected 6 components',components))
  maxh=max(b[3]-b[1] for a,b in components);scale=172/maxh;entries=[]
  for view,(area,bbox) in zip(VIEWS,components):
   x0,y0,x1,y1=bbox;x0=max(0,x0-2);y0=max(0,y0-2);x1=min(atlas.width,x1+2);y1=min(atlas.height,y1+2)
   crop=atlas.crop((x0,y0,x1,y1));nw=max(1,round(crop.width*scale));nh=max(1,round(crop.height*scale));im=crop.resize((nw,nh),Image.Resampling.NEAREST)
   canvas=Image.new('RGBA',(256,256),(0,0,0,0));canvas.alpha_composite(im,((256-nw)//2,(256-nh)//2));dst=CAND/f'{oid}.{view}.png';canvas.save(dst)
   entries.append({'object_id':oid,'view':view,'candidate_path':str(dst.relative_to(OUT)),'candidate_sha256':sha(dst),'raw_atlas':str(raw.relative_to(OUT)),'raw_atlas_sha256':sha(raw),'component_bbox_threshold32':list(bbox),'component_area_threshold32':area,'uniform_scale':scale,'normalized_size':[nw,nh],'anchor_px':[128,128]})
  sets.append({'object_id':oid,'views':entries})
 spec={'candidate_id':'glass-maze-endcaps-v1','extraction':'six connected alpha components at threshold>=32, sorted by x-center; full component plus 2px padding; same uniform scale per object across all six views; nearest-neighbour into centered 256x256.','sets':sets}
 (CAND/'candidate.json').write_text(json.dumps(spec,indent=2)+'\n');print(json.dumps(spec,indent=2))
if __name__=='__main__':main()
