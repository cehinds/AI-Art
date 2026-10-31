"""Source-extract Personal Space TOP and add inferred wood/plaster underside plans."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image
from scipy import ndimage
HERE=Path(__file__).resolve().parent;OUT=HERE.parent;PACK=OUT.parent.parent;SPEC=OUT/'candidates/corner-batch-personal-safe-v1.json';RAW=OUT/'raw/personal-space-corner-undersides-v1-atlas.png';OIDS=['personal-space-plaster-and-timber-inner-corner','personal-space-plaster-and-timber-outer-corner']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def comps(im):
 lab,n=ndimage.label(np.asarray(im.getchannel('A'))>=32);a=[]
 for i,s in enumerate(ndimage.find_objects(lab),1):
  if s is None:continue
  y,x=s;area=int(np.count_nonzero(lab[s]==i))
  if area>1000:a.append((area,(x.start,y.start,x.stop,y.stop)))
 return a
def main():
 data=json.loads(SPEC.read_text());batch=next(x for x in data['batches'] if x['candidate_id']=='corner-batch-personal-v1');bim=Image.open(RAW).convert('RGBA');bc=comps(bim);assert len(bc)==2,len(bc);req=json.loads((OUT/'prompts/personal-space-corner-undersides-v1-request-result.json').read_text());pbot=OUT/'prompts/personal-space-corner-undersides-v1.txt';ptop=OUT/'prompts/safe-services-native-top-plan-v1.txt'
 for ri,oid in enumerate(OIDS):
  g=next(x for x in batch['sets'] if x['object_id']==oid);target=g['target_plan_width_px'];source=PACK/'personal-space/components'/f'{oid}.png';src=Image.open(source).convert('RGBA');sc=comps(src);assert len(sc)==1,(oid,len(sc))
  for v,im,b,method,raw,pr,refs,refhash in [('top',src,sc[0][1],'exact-native-top-source',str(source.relative_to(PACK)),ptop,['personal-space/components/'+source.name],[sha(source)]),('bottom',bim,bc[ri][1],'generated-bottom-underside','reusable/views-additional/raw/'+RAW.name,'reusable/views-additional/prompts/'+pbot.name,req['reference_paths'],req['reference_sha256'])]:
   area,_= (sc[0] if v=='top' else bc[ri]);x0,y0,x1,y1=b;x0=max(0,x0-2);y0=max(0,y0-2);x1=min(im.width,x1+3);y1=min(im.height,y1+3);crop=im.crop((x0,y0,x1,y1));scale=target/crop.width;nw=round(crop.width*scale);nh=round(crop.height*scale);rs=crop.resize((nw,nh),Image.Resampling.NEAREST);canvas=Image.new('RGBA',(256,256),(0,0,0,0));canvas.alpha_composite(rs,((256-nw)//2,(256-nh)//2));dst=OUT/'candidates/corner-batch-personal-v1'/f'{oid}.{v}.png';canvas.save(dst);entry={'object_id':oid,'view':v,'candidate_path':str(dst.relative_to(OUT)),'candidate_sha256':sha(dst),'base_sha256':sha(PACK/'reusable/views-additional/images'/f'{oid}.{v}.png'),'raw_atlas':raw,'raw_atlas_sha256':sha(source if v=='top' else RAW),'prompt_path':str(pr.relative_to(PACK)) if isinstance(pr,Path) else pr,'prompt_sha256':sha(pr),'reference_paths':refs,'reference_sha256':refhash,'component_bbox_threshold32':list(b),'component_area_threshold32':area,'crop_rect_with_padding':[x0,y0,x1,y1],'uniform_scale':scale,'normalized_size':[nw,nh],'anchor_px':[128,128],'calibration_target_px':target,'method':method}
   g['views'].append(entry)
  print(oid,target,[(e['view'],e['normalized_size']) for e in g['views'] if e['view'] in ('top','bottom')])
 SPEC.write_text(json.dumps(data,indent=2)+'\n')
if __name__=='__main__':main()
