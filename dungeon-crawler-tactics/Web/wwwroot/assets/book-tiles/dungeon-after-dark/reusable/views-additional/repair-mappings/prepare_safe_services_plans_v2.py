"""Extract corrected horizontal L plans, matching accepted Safe Services elevations."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image
from scipy import ndimage
HERE=Path(__file__).resolve().parent;OUT=HERE.parent;PACK=OUT.parent.parent;OID=['safe-services-cream-service-tile-inner-corner','safe-services-cream-service-tile-outer-corner'];VIEWS=['top','bottom'];RAW=OUT/'raw/safe-services-corner-plans-v2-atlas.png'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def components(im):
 lab,n=ndimage.label(np.asarray(im.getchannel('A'))>=32);r=[]
 for i,s in enumerate(ndimage.find_objects(lab),1):
  if s is None:continue
  y,x=s;area=int(np.count_nonzero(lab[s]==i))
  if area>1000:r.append((area,(x.start,y.start,x.stop,y.stop)))
 r.sort(key=lambda q:(q[1][1],q[1][0]));return r
idx=json.loads((OUT/'set-index.json').read_text());assets={x['id']:x for x in idx['assets']};im=Image.open(RAW).convert('RGBA');cs=components(im);assert len(cs)==4,len(cs);req=json.loads((OUT/'prompts/safe-services-corner-plans-v2-request-result.json').read_text());sets=[]
for ri,oid in enumerate(OID):
 front=Image.open(PACK/assets[oid+'.front']['image']['path']).convert('RGBA');target=front.getchannel('A').getbbox()[2]-front.getchannel('A').getbbox()[0];views=[]
 for v,(area,b) in zip(VIEWS,cs[ri*2:(ri+1)*2]):
  x0,y0,x1,y1=b;x0=max(0,x0-2);y0=max(0,y0-2);x1=min(im.width,x1+3);y1=min(im.height,y1+3);crop=im.crop((x0,y0,x1,y1));scale=target/crop.width;nw=round(crop.width*scale);nh=round(crop.height*scale);rs=crop.resize((nw,nh),Image.Resampling.NEAREST);can=Image.new('RGBA',(256,256),(0,0,0,0));can.alpha_composite(rs,((256-nw)//2,(256-nh)//2));p=OUT/'candidates/safe-services-plans-v2'/f'{oid}.{v}.png';p.parent.mkdir(parents=True,exist_ok=True);can.save(p);aid=f'{oid}.{v}';views.append({'object_id':oid,'view':v,'candidate_path':str(p.relative_to(OUT)),'candidate_sha256':sha(p),'base_sha256':sha(PACK/assets[aid]['image']['path']),'raw_atlas':'reusable/views-additional/raw/'+RAW.name,'raw_atlas_sha256':sha(RAW),'prompt_path':'reusable/views-additional/prompts/safe-services-corner-plans-v2.txt','prompt_sha256':sha(OUT/'prompts/safe-services-corner-plans-v2.txt'),'reference_paths':req['reference_paths'],'reference_sha256':req['reference_sha256'],'component_bbox_threshold32':list(b),'component_area_threshold32':area,'crop_rect_with_padding':[x0,y0,x1,y1],'uniform_scale':scale,'normalized_size':[nw,nh],'anchor_px':[128,128],'calibration_target_px':target})
 sets.append({'object_id':oid,'views':views,'target_span':target})
spec={'candidate_id':'safe-services-plans-v2','sets':sets,'normalization':'one isotropic plan scale per object, calibrated to accepted face span'};(OUT/'candidates/safe-services-plans-v2.json').write_text(json.dumps(spec,indent=2)+'\n');print(json.dumps(spec,indent=2))
