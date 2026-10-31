"""Extract the exact 2x4 source-guided corner elevation atlas and normalize isotropically."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image
from scipy import ndimage
HERE=Path(__file__).resolve().parent;OUT=HERE.parent;PACK=OUT.parent.parent
ATLAS=OUT/'raw/hunting-river-palace-corners-elevations-v1-atlas.png';CAND=OUT/'candidates/river-palace-corners-elevations-v1';CAND.mkdir(parents=True,exist_ok=True)
OIDS=['hunting-river-river-palace-masonry-inner-corner','hunting-river-river-palace-masonry-outer-corner'];VIEWS=['front','right','left','rear']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bbox(im):
 a=np.asarray(im.getchannel('A')); lab,n=ndimage.label(a>=32);objs=[]
 for i,sl in enumerate(ndimage.find_objects(lab),1):
  if sl is None:continue
  y,x=sl; area=int(np.count_nonzero(lab[sl]==i));
  if area>1000:objs.append((area,(x.start,y.start,x.stop,y.stop)))
 return objs
def main():
 atlas=Image.open(ATLAS).convert('RGBA');comps=bbox(atlas);assert len(comps)==8,[(b,a) for a,b in comps]
 comps.sort(key=lambda z:(z[1][1],z[1][0]));idx=json.loads((OUT/'set-index.json').read_text());assets={a['id']:a for a in idx['assets']};rows=[];proof=[]
 for row,oid in enumerate(OIDS):
  objs=comps[row*4:(row+1)*4];top=Image.open(PACK/assets[oid+'.top']['image']['path']).convert('RGBA');targetw=top.getchannel('A').getbbox()[2]-top.getchannel('A').getbbox()[0]
  # One scale for all four elevations; match broad full-face span to accepted L-plan span.
  maxw=max(b[2]-b[0] for area,b in objs);scale=targetw/maxw
  rowentries=[]
  for view,(area,b) in zip(VIEWS,objs):
   x0,y0,x1,y1=b;crop=atlas.crop((max(0,x0-2),max(0,y0-2),min(atlas.width,x1+3),min(atlas.height,y1+3)));nw=max(1,round(crop.width*scale));nh=max(1,round(crop.height*scale));r=crop.resize((nw,nh),Image.Resampling.NEAREST);canvas=Image.new('RGBA',(256,256),(0,0,0,0));canvas.alpha_composite(r,((256-nw)//2,(256-nh)//2));dst=CAND/f'{oid}.{view}.png';canvas.save(dst)
   aid=f'{oid}.{view}';base=sha(PACK/assets[aid]['image']['path']);entry={'object_id':oid,'view':view,'candidate_path':str(dst.relative_to(OUT)),'candidate_sha256':sha(dst),'base_sha256':base,'raw_atlas':'reusable/views-additional/raw/'+ATLAS.name,'raw_atlas_sha256':sha(ATLAS),'prompt_path':'reusable/views-additional/prompts/hunting-river-palace-corners-elevations-v1.txt','prompt_sha256':sha(OUT/'prompts/hunting-river-palace-corners-elevations-v1.txt'),'reference_paths':['hunting-river/components/'+oid+'.png','reusable/views-additional/qa/corner-four-elevations-only-guide.png'],'reference_sha256':[sha(PACK/'hunting-river/components'/f'{oid}.png'),sha(OUT/'qa/corner-four-elevations-only-guide.png')],'component_bbox_threshold32':list(b),'component_area_threshold32':area,'crop_rect_with_padding':[max(0,x0-2),max(0,y0-2),min(atlas.width,x1+3),min(atlas.height,y1+3)],'uniform_scale':scale,'normalized_size':[nw,nh],'anchor_px':[128,128],'calibration_target_px':targetw}
   rowentries.append(entry)
  rows.append({'object_id':oid,'target_plan_width_px':targetw,'views':rowentries})
 spec={'candidate_id':'river-palace-corners-elevations-v1','atlas_layout':'2x4; row1 inner, row2 outer; columns front,right,left,rear','sets':rows,'normalization':'one isotropic scale per object shared across all four views; TOP/BOTTOM preserved'};(CAND/'candidate.json').write_text(json.dumps(spec,indent=2)+'\n');print(json.dumps(spec,indent=2))
if __name__=='__main__':main()
