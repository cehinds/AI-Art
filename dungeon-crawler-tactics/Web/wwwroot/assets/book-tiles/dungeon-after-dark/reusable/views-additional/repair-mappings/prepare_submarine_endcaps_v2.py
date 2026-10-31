"""Build corrected submarine endcap candidates with thin, footprint-aware plans."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image
from scipy import ndimage
HERE=Path(__file__).resolve().parent; OUT=HERE.parent
VIEWS=('front','top','right','left','bottom','rear')
IDS=('bubble-sea-submarine-metal-hull-endcap-northeast','bubble-sea-submarine-metal-hull-endcap-northwest')
PLAN_RAW={
 IDS[0]:('raw/bubble-sea-submarine-metal-hull-endcap-northeast-candidate-topbottom-v2.png','/workspace/generated_images/exec-85dbfb67-336e-4e3b-a8b0-77ee933a5ace.png'),
 IDS[1]:('raw/bubble-sea-submarine-metal-hull-endcap-northwest-candidate-topbottom-v2.png','/workspace/generated_images/exec-9e0daabb-e550-4e78-8b73-58991ee2dd03.png')}
CAND=OUT/'candidates/submarine-endcaps-v2'

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def comps(im,min_area=1000):
 a=np.asarray(im.getchannel('A')); labels,n=ndimage.label(a>=32); found=[]
 for i,sl in enumerate(ndimage.find_objects(labels),1):
  if sl is None: continue
  y,x=sl; area=int(np.count_nonzero(labels[sl]==i))
  if area>=min_area: found.append((area,(x.start,y.start,x.stop,y.stop)))
 return sorted(found,key=lambda z:(z[1][0]+z[1][2])/2)
def main():
 CAND.mkdir(parents=True,exist_ok=True); entries=[]
 for oid in IDS:
  rawv1=OUT/'raw'/f'{oid}-candidate-sixview-v1.png'; atlas=Image.open(rawv1).convert('RGBA'); ev=comps(atlas)
  if len(ev)!=6: raise ValueError((oid,'expected six candidate views',ev))
  # Reuse only the four root-accepted candidate elevations, in the same source atlas.
  for view,(area,bbox) in zip(VIEWS,ev):
   if view in ('top','bottom'): continue
   x0,y0,x1,y1=bbox; x0=max(0,x0-2);y0=max(0,y0-2);x1=min(atlas.width,x1+2);y1=min(atlas.height,y1+2)
   crop=atlas.crop((x0,y0,x1,y1)); # same approved candidate normalization: 172px highest elevation
   elev=comps(atlas); max_h=max(b[3]-b[1] for _,b in elev); scale=172.0/max_h
   nw=max(1,round(crop.width*scale)); nh=max(1,round(crop.height*scale)); im=crop.resize((nw,nh),Image.Resampling.NEAREST)
   canvas=Image.new('RGBA',(256,256),(0,0,0,0)); canvas.alpha_composite(im,((256-nw)//2,(256-nh)//2))
   dst=CAND/f'{oid}.{view}.png'; canvas.save(dst)
   entries.append({'object_id':oid,'view':view,'candidate_path':str(dst.relative_to(OUT)),'candidate_sha256':sha(dst),'raw_atlas':str(rawv1.relative_to(OUT)),'raw_atlas_sha256':sha(rawv1),'component_bbox_threshold32':list(bbox),'uniform_scale':scale,'normalized_size':[nw,nh],'reused_accepted_candidate_elevation':True})
  rawrel,original=PLAN_RAW[oid]; plan=Image.open(OUT/rawrel).convert('RGBA'); pcs=comps(plan)
  if len(pcs)!=2: raise ValueError((oid,'expected two plan views',pcs))
  # Both plan assets use a single uniform scale calibrated from their common world-width span.
  target_width=172
  for view,(area,bbox) in zip(('top','bottom'),pcs):
   x0,y0,x1,y1=bbox;x0=max(0,x0-2);y0=max(0,y0-2);x1=min(plan.width,x1+2);y1=min(plan.height,y1+2)
   crop=plan.crop((x0,y0,x1,y1));scale=target_width/crop.width
   nw=max(1,round(crop.width*scale));nh=max(1,round(crop.height*scale));im=crop.resize((nw,nh),Image.Resampling.NEAREST)
   canvas=Image.new('RGBA',(256,256),(0,0,0,0));canvas.alpha_composite(im,((256-nw)//2,(256-nh)//2))
   dst=CAND/f'{oid}.{view}.png';canvas.save(dst)
   entries.append({'object_id':oid,'view':view,'candidate_path':str(dst.relative_to(OUT)),'candidate_sha256':sha(dst),'raw_atlas':str(rawrel),'raw_atlas_sha256':sha(OUT/rawrel),'imagegen_result_path':original,'component_bbox_threshold32':list(bbox),'uniform_scale':scale,'normalized_size':[nw,nh],'axis_preserving_plan_calibration':True})
 sets=[{'object_id':oid,'views':[e for e in entries if e['object_id']==oid]} for oid in IDS]
 spec={'candidate_id':'submarine-endcaps-v2','extraction':'Connected alpha components threshold>=32, ordered by horizontal center. Elevations reused from v1 isolated six-view atlas; TOP/BOTTOM extracted from two-view plan atlas. Each source atlas view uses one uniform scale; crop includes full component plus 2px padding; nearest-neighbour into centered 256x256 canvas. No anisotropic resize.','sets':sets}
 (CAND/'candidate.json').write_text(json.dumps(spec,indent=2)+'\n'); print(json.dumps(spec,indent=2))
if __name__=='__main__':main()
