"""Prepare source-guided elevations for the Personal Space and Safe Services corner pairs."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image
from scipy import ndimage
HERE=Path(__file__).resolve().parent;OUT=HERE.parent;PACK=OUT.parent.parent
GROUPS=[('personal','personal-space-plaster-and-timber-inner-corner','personal-space-plaster-and-timber-outer-corner'),('safe','safe-services-cream-service-tile-inner-corner','safe-services-cream-service-tile-outer-corner')];VIEWS=['front','right','left','rear']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def components(p):
 im=Image.open(p).convert('RGBA'); lab,n=ndimage.label(np.asarray(im.getchannel('A'))>=32);found=[]
 for i,sl in enumerate(ndimage.find_objects(lab),1):
  if sl is None:continue
  y,x=sl;area=int(np.count_nonzero(lab[sl]==i))
  if area>1000:found.append((area,(x.start,y.start,x.stop,y.stop)))
 found.sort(key=lambda q:(q[1][1],q[1][0]));return im,found
def main():
 idx=json.loads((OUT/'set-index.json').read_text());assets={a['id']:a for a in idx['assets']};sets=[]
 for key,inner,outer in GROUPS:
  atlaspath=OUT/'raw'/f'corner-batch-{key}-v1-atlas.png';atlas,cs=components(atlaspath);assert len(cs)==8,(key,len(cs));rawname='reusable/views-additional/raw/'+atlaspath.name;prompt=OUT/'prompts'/f'corner-batch-{key}-v1.txt';req=json.loads((OUT/'prompts'/f'corner-batch-{key}-v1-request-result.json').read_text());refs=req['reference_paths'];oids=[inner,outer];rows=[]
  for ri,oid in enumerate(oids):
   comps=cs[ri*4:(ri+1)*4];top=Image.open(PACK/assets[oid+'.top']['image']['path']).convert('RGBA');tb=top.getchannel('A').getbbox();target=tb[2]-tb[0];scale=target/max(b[2]-b[0] for _,b in comps);views=[]
   for v,(area,b) in zip(VIEWS,comps):
    x0,y0,x1,y1=b;x0=max(0,x0-2);y0=max(0,y0-2);x1=min(atlas.width,x1+3);y1=min(atlas.height,y1+3);crop=atlas.crop((x0,y0,x1,y1));nw=round(crop.width*scale);nh=round(crop.height*scale);rs=crop.resize((nw,nh),Image.Resampling.NEAREST);canvas=Image.new('RGBA',(256,256),(0,0,0,0));canvas.alpha_composite(rs,((256-nw)//2,(256-nh)//2));dst=OUT/'candidates'/f'corner-batch-{key}-v1'/f'{oid}.{v}.png';dst.parent.mkdir(parents=True,exist_ok=True);canvas.save(dst);aid=f'{oid}.{v}'
    views.append({'object_id':oid,'view':v,'candidate_path':str(dst.relative_to(OUT)),'candidate_sha256':sha(dst),'base_sha256':sha(PACK/assets[aid]['image']['path']),'raw_atlas':rawname,'raw_atlas_sha256':sha(atlaspath),'prompt_path':'reusable/views-additional/prompts/'+prompt.name,'prompt_sha256':sha(prompt),'reference_paths':refs,'reference_sha256':req['reference_sha256'],'component_bbox_threshold32':list(b),'component_area_threshold32':area,'crop_rect_with_padding':[x0,y0,x1,y1],'uniform_scale':scale,'normalized_size':[nw,nh],'anchor_px':[128,128],'calibration_target_px':target})
   rows.append({'object_id':oid,'target_plan_width_px':target,'views':views})
  sets.append({'candidate_id':f'corner-batch-{key}-v1','atlas_layout':'2x4; row1 inner, row2 outer; columns front,right,left,rear','raw_atlas_sha256':sha(atlaspath),'sets':rows,'normalization':'single uniform scale per object across all four elevations; TOP/BOTTOM are retained'})
 spec={'candidate_id':'corner-batch-personal-safe-v1','batches':sets};dst=OUT/'candidates/corner-batch-personal-safe-v1.json';dst.parent.mkdir(parents=True,exist_ok=True);dst.write_text(json.dumps(spec,indent=2)+'\n');print(dst)
if __name__=='__main__':main()
