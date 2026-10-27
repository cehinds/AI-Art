"""Use exact native TOP plans and generated opaque source-palette BOTTOM plans for Safe Services."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image
from scipy import ndimage
HERE=Path(__file__).resolve().parent;OUT=HERE.parent;PACK=OUT.parent.parent;SPEC=OUT/'candidates/corner-batch-personal-safe-v1.json';BOTTOM=OUT/'raw/safe-services-corner-undersides-v1-atlas.png';OIDS=['safe-services-cream-service-tile-inner-corner','safe-services-cream-service-tile-outer-corner']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def comps(im):
 lab,n=ndimage.label(np.asarray(im.getchannel('A'))>=32);a=[]
 for i,s in enumerate(ndimage.find_objects(lab),1):
  if s is None:continue
  y,x=s;area=int(np.count_nonzero(lab[s]==i));
  if area>1000:a.append((area,(x.start,y.start,x.stop,y.stop)))
 return a
def main():
 data=json.loads(SPEC.read_text());batch=next(x for x in data['batches'] if x['candidate_id']=='corner-batch-safe-v1');bim=Image.open(BOTTOM).convert('RGBA');bc=comps(bim);assert len(bc)==2,len(bc)
 promptnative=OUT/'prompts/safe-services-native-top-plan-v1.txt';req=json.loads((OUT/'prompts/safe-services-corner-undersides-v1-request-result.json').read_text());
 for ri,oid in enumerate(OIDS):
  group=next(x for x in batch['sets'] if x['object_id']==oid);target=group['target_plan_width_px'];source=PACK/'safe-services/components'/f'{oid}.png';src=Image.open(source).convert('RGBA');sc=comps(src);assert len(sc)==1,(oid,len(sc));
  for view,im,b,method,raw,prompt,refs,refhash in [
   ('top',src,sc[0][1],'exact-native-top-source',str(source.relative_to(PACK)),promptnative,['safe-services/components/'+source.name],[sha(source)]),
   ('bottom',bim,bc[ri][1],'generated-bottom-underside','reusable/views-additional/raw/'+BOTTOM.name,OUT/'prompts/safe-services-corner-undersides-v1.txt',req['reference_paths'],req['reference_sha256'])]:
   area,_= (sc[0] if view=='top' else bc[ri]);x0,y0,x1,y1=b;x0=max(0,x0-2);y0=max(0,y0-2);x1=min(im.width,x1+3);y1=min(im.height,y1+3);crop=im.crop((x0,y0,x1,y1));scale=target/crop.width;nw=round(crop.width*scale);nh=round(crop.height*scale);r=crop.resize((nw,nh),Image.Resampling.NEAREST);canvas=Image.new('RGBA',(256,256),(0,0,0,0));canvas.alpha_composite(r,((256-nw)//2,(256-nh)//2));dst=OUT/'candidates/corner-batch-safe-v1'/f'{oid}.{view}.png';canvas.save(dst);entry={'object_id':oid,'view':view,'candidate_path':str(dst.relative_to(OUT)),'candidate_sha256':sha(dst),'base_sha256':sha(PACK/'reusable/views-additional/images'/f'{oid}.{view}.png'),'raw_atlas':raw,'raw_atlas_sha256':sha(source if view=='top' else BOTTOM),'prompt_path':str(prompt.relative_to(PACK)) if isinstance(prompt,Path) else prompt,'prompt_sha256':sha(prompt),'reference_paths':refs,'reference_sha256':refhash,'component_bbox_threshold32':list(b),'component_area_threshold32':area,'crop_rect_with_padding':[x0,y0,x1,y1],'uniform_scale':scale,'normalized_size':[nw,nh],'anchor_px':[128,128],'calibration_target_px':target,'method':method}
   group['views'].append(entry)
 SPEC.write_text(json.dumps(data,indent=2)+'\n');print(json.dumps({'object_id':oid,'plan_width':target,'added':[(e['view'],e['normalized_size'],e['method']) for e in group['views'] if e['view'] in ('top','bottom')]},indent=2))
if __name__=='__main__':main()
